"""
Offline OCR service using PaddleOCR.
Replaces Google Cloud Vision API for fully offline document text extraction.
Supports English and Hindi.  Accepts PDF, JPG, and PNG inputs.
"""

import asyncio
import logging
import os
import time
from typing import List, Tuple

# PaddlePaddle environment flags — must be set before importing paddleocr.
os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

# Detect CUDA availability at import time
try:
    import paddle
    if paddle.device.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0:
        _DEVICE: str = "gpu"
        print(f"[OCR] CUDA detected — using GPU ({paddle.device.cuda.device_count()} device(s))")
    else:
        _DEVICE = "cpu"
        print("[OCR] No CUDA GPU detected — using CPU")
except Exception as e:
    _DEVICE = "cpu"
    print(f"[OCR] Could not query CUDA ({e}) — falling back to CPU")

import cv2
import numpy as np
import pypdfium2 as pdfium
from paddleocr import PaddleOCR
from PIL import Image

logger = logging.getLogger("ocr_service")

SUPPORTED_LANGS = {"auto", "en", "hi"}
_OCR_LANGS = {"en", "hi"}

# ---------------------------------------------------------------------------
# PaddleOCR singletons — one per language
# ---------------------------------------------------------------------------

_ocr_instances: dict[str, PaddleOCR] = {}


def _get_ocr(lang: str = "en") -> PaddleOCR:
    """Return a lazily-initialised PaddleOCR instance for *lang*."""
    if lang not in _OCR_LANGS:
        raise ValueError(f"Unsupported OCR language '{lang}'.")

    if lang not in _ocr_instances:
        logger.info(
            "Initialising PaddleOCR engine (lang=%s, device=%s) ...", lang, _DEVICE
        )
        start = time.perf_counter()
        _ocr_instances[lang] = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            device=_DEVICE,
        )
        elapsed = time.perf_counter() - start
        logger.info(
            "PaddleOCR engine (lang=%s, device=%s) loaded in %.2fs",
            lang, _DEVICE, elapsed,
        )

    return _ocr_instances[lang]


def is_engine_ready() -> bool:
    """Check whether the default OCR engine can be instantiated."""
    try:
        _get_ocr("en")
        return True
    except Exception:
        logger.exception("OCR engine health-check failed")
        return False


# ---------------------------------------------------------------------------
# Reading-order sorting
# ---------------------------------------------------------------------------

def _sort_boxes_reading_order(
    results: list,
    line_threshold_ratio: float = 0.5,
) -> Tuple[List[str], float]:
    """Sort OCR bounding-box results into natural reading order.

    Legal documents are read top-to-bottom then left-to-right.  PaddleOCR may
    return boxes in detection order which can be jumbled.  This function groups
    boxes into logical "lines" based on vertical proximity, then sorts each
    line left-to-right.

    Returns
    -------
    tuple[list[str], float]
        (ordered_text_fragments, average_confidence)
    """
    if not results:
        return [], 0.0

    entries = []
    total_conf = 0.0
    for bbox, (text, confidence) in results:
        ys = [pt[1] for pt in bbox]
        xs = [pt[0] for pt in bbox]
        mid_y = sum(ys) / len(ys)
        min_x = min(xs)
        height = max(ys) - min(ys)
        entries.append((mid_y, min_x, height, text))
        total_conf += confidence

    avg_conf = total_conf / len(entries) if entries else 0.0

    # Sort primarily by vertical midpoint
    entries.sort(key=lambda e: e[0])

    avg_height = sum(e[2] for e in entries) / len(entries) if entries else 1
    threshold = avg_height * line_threshold_ratio

    # Group into lines
    lines: list[list[tuple]] = []
    current_line: list[tuple] = [entries[0]]

    for entry in entries[1:]:
        if abs(entry[0] - current_line[-1][0]) <= threshold:
            current_line.append(entry)
        else:
            lines.append(current_line)
            current_line = [entry]
    lines.append(current_line)

    # Sort each line left-to-right, then flatten
    ordered_texts: List[str] = []
    for line in lines:
        line.sort(key=lambda e: e[1])
        ordered_texts.extend(e[3] for e in line)

    return ordered_texts, avg_conf


# ---------------------------------------------------------------------------
# Image preprocessing — improves OCR on handwriting and low-quality scans
# ---------------------------------------------------------------------------

def _preprocess_image(image: np.ndarray) -> np.ndarray:
    """Clean up an image to improve OCR accuracy.

    Pipeline: grayscale → denoise → CLAHE contrast → adaptive threshold → BGR.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(denoised)
    binary = cv2.adaptiveThreshold(
        contrast, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31, C=10,
    )
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


# ---------------------------------------------------------------------------
# Detection extraction (supports PaddleOCR 2.x and 3.x output formats)
# ---------------------------------------------------------------------------

def _extract_detections(raw_results: list) -> list:
    """Convert PaddleOCR results to ``(bbox, (text, score))`` tuples."""
    detections = []
    if not raw_results:
        return detections

    for result in raw_results:
        # PaddleOCR 3.x returns dicts
        if isinstance(result, dict):
            texts = result.get("rec_texts", [])
            scores = result.get("rec_scores", [])
            polys = result.get("rec_polys", [])
            for poly, text, score in zip(polys, texts, scores):
                detections.append((poly, (text, score)))
        # PaddleOCR 2.x returns list of (bbox, (text, conf))
        elif isinstance(result, (list, tuple)):
            for item in result:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    detections.append((item[0], item[1]))
    return detections


# ---------------------------------------------------------------------------
# Single-image OCR
# ---------------------------------------------------------------------------

def _ocr_image_single(
    image: np.ndarray, lang: str, page_label: str,
) -> Tuple[str, float]:
    """Run a single-language OCR pass. Returns ``(text, confidence)``."""
    start = time.perf_counter()
    processed = _preprocess_image(image)
    ocr = _get_ocr(lang)
    raw_results = ocr.ocr(processed)
    elapsed = time.perf_counter() - start
    logger.info("%s (lang=%s) processed in %.2fs", page_label, lang, elapsed)

    detections = _extract_detections(raw_results)
    if not detections:
        logger.warning("No text detected on %s (lang=%s)", page_label, lang)
        return "", 0.0

    ordered, avg_conf = _sort_boxes_reading_order(detections)
    return " ".join(ordered), avg_conf


def _ocr_image_auto(
    image: np.ndarray, page_label: str,
) -> Tuple[str, float]:
    """Run both en and hi OCR, keep the higher-confidence result per region."""
    start = time.perf_counter()
    processed = _preprocess_image(image)

    en_raw = _get_ocr("en").ocr(processed)
    hi_raw = _get_ocr("hi").ocr(processed)

    en_dets = _extract_detections(en_raw)
    hi_dets = _extract_detections(hi_raw)

    elapsed = time.perf_counter() - start
    logger.info(
        "%s (lang=auto, en=%d hi=%d regions) processed in %.2fs",
        page_label, len(en_dets), len(hi_dets), elapsed,
    )

    best: dict[tuple, tuple] = {}

    def _key(poly):
        ys = [pt[1] for pt in poly]
        xs = [pt[0] for pt in poly]
        return (round(sum(ys) / len(ys), 1), round(min(xs), 1))

    for poly, (text, score) in en_dets:
        k = _key(poly)
        if k not in best or score > best[k][1][1]:
            best[k] = (poly, (text, score))

    for poly, (text, score) in hi_dets:
        k = _key(poly)
        if k not in best or score > best[k][1][1]:
            best[k] = (poly, (text, score))

    detections = list(best.values())
    if not detections:
        logger.warning("No text detected on %s (lang=auto)", page_label)
        return "", 0.0

    ordered, avg_conf = _sort_boxes_reading_order(detections)
    return " ".join(ordered), avg_conf


def _ocr_image(
    image: np.ndarray, lang: str, page_label: str = "image",
) -> Tuple[str, float]:
    """Run OCR on a single image. Returns ``(text, confidence)``."""
    if lang == "auto":
        return _ocr_image_auto(image, page_label)
    return _ocr_image_single(image, lang, page_label)


# ---------------------------------------------------------------------------
# PDF processing  (bytes → images → OCR)
# ---------------------------------------------------------------------------

def _process_pdf_bytes(
    pdf_bytes: bytes, lang: str,
) -> Tuple[str, int, float]:
    """Process PDF bytes. Returns ``(raw_text, page_count, avg_confidence)``."""
    logger.info("Converting PDF to images for OCR ...")
    pdf = pdfium.PdfDocument(pdf_bytes)
    n_pages = len(pdf)
    logger.info("PDF has %d page(s)", n_pages)

    all_text: List[str] = []
    total_conf = 0.0

    for idx in range(n_pages):
        page = pdf[idx]
        # Render at 300 DPI for good OCR quality
        bitmap = page.render(scale=300 / 72)
        pil_image = bitmap.to_pil().convert("RGB")
        img_array = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        text, conf = _ocr_image(img_array, lang, page_label=f"Page {idx + 1}")
        all_text.append(text)
        total_conf += conf

    pdf.close()

    avg_conf = total_conf / n_pages if n_pages > 0 else 0.0
    raw_text = "\n".join(all_text)
    return raw_text, n_pages, avg_conf


# ---------------------------------------------------------------------------
# Image processing  (bytes → OCR)
# ---------------------------------------------------------------------------

def _process_image_bytes(
    image_bytes: bytes, lang: str,
) -> Tuple[str, float]:
    """Process image bytes. Returns ``(raw_text, confidence)``."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    return _ocr_image(img, lang, page_label="Page 1")


# ---------------------------------------------------------------------------
# Public service class — drop-in replacement for Google Vision VisionService
# ---------------------------------------------------------------------------

class VisionService:
    """Offline OCR service using PaddleOCR.

    Drop-in replacement for the former Google Cloud Vision based service.
    The public interface (``extract_text``, ``extract_text_from_pdf``) and
    return format (``{raw_text, page_count, confidence_score}``) are identical
    so no downstream code changes are required.
    """

    def __init__(self, lang: str = "auto"):
        self._lang = lang

    async def extract_text(self, image_bytes: bytes) -> dict:
        """Extract text from image bytes using PaddleOCR.

        Returns dict with keys: raw_text, page_count, confidence_score.
        """
        text, confidence = await asyncio.to_thread(
            _process_image_bytes, image_bytes, self._lang,
        )
        return {
            "raw_text": text,
            "page_count": 1,
            "confidence_score": round(confidence, 4),
        }

    async def extract_text_from_pdf(self, pdf_bytes: bytes) -> dict:
        """Extract text from PDF bytes using PaddleOCR + pypdfium2.

        Returns dict with keys: raw_text, page_count, confidence_score.
        """
        raw_text, page_count, confidence = await asyncio.to_thread(
            _process_pdf_bytes, pdf_bytes, self._lang,
        )
        return {
            "raw_text": raw_text,
            "page_count": page_count,
            "confidence_score": round(confidence, 4),
        }
