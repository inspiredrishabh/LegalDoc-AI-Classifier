"""Tests for QA service - verifies parity with JS qaMatcher + qaRetriever."""
from app.utils.text_processing import normalize, jaccard_similarity
from app.services.qa_service import QAService
from app.models.schemas import QAPair


# --- normalize() parity tests ---

def test_normalize_lowercase():
    assert normalize("HELLO WORLD") == "hello world"


def test_normalize_strips_special_chars():
    assert normalize("Section 437 CrPC?") == "section 437 crpc"


def test_normalize_collapses_whitespace():
    assert normalize("  hello   world  ") == "hello world"


def test_normalize_removes_punctuation():
    assert normalize("what is murder under IPC?!") == "what is murder under ipc"


# --- jaccard_similarity() parity tests ---
# JS uses: intersection.length / Math.max(A.size, B.size)

def test_similarity_identical():
    a = normalize("bail under crpc")
    assert jaccard_similarity(a, a) == 1.0


def test_similarity_partial():
    a = normalize("bail under crpc")
    b = normalize("bail crpc section")
    # A = {"bail", "under", "crpc"} (3)
    # B = {"bail", "crpc", "section"} (3)
    # intersection = {"bail", "crpc"} (2)
    # max(3, 3) = 3
    # result = 2/3 ~ 0.6667
    result = jaccard_similarity(a, b)
    assert abs(result - 2 / 3) < 0.001


def test_similarity_no_overlap():
    a = normalize("hello world")
    b = normalize("foo bar")
    assert jaccard_similarity(a, b) == 0.0


def test_similarity_uses_max_not_union():
    """Verify we use max(|A|, |B|) not |A union B|."""
    a = "a b c"
    b = "a b c d"
    # intersection = {a, b, c} = 3
    # max(3, 4) = 4
    # result = 3/4 = 0.75
    # Standard Jaccard would be 3/4 = 0.75 (same here because union = 4)
    # But test with different: a="a b", b="a c d"
    # intersection = {a} = 1
    # max(2, 3) = 3, result = 1/3 ~ 0.333
    # standard Jaccard: 1/4 = 0.25 (union = {a,b,c,d} = 4)
    result = jaccard_similarity("a b", "a c d")
    assert abs(result - 1 / 3) < 0.001


# --- QAService tests ---

def test_qa_service_finds_exact_match():
    qa_data = [
        QAPair(source="TEST", question="what is bail", answer="Bail is..."),
        QAPair(source="TEST", question="what is murder", answer="Murder is..."),
    ]
    svc = QAService(qa_data)
    result = svc.find_answer("what is bail")
    assert result is not None
    assert result["confidence"] == 1.0
    assert result["answer"] == "Bail is..."


def test_qa_service_returns_none_below_threshold():
    qa_data = [
        QAPair(source="TEST", question="what is bail under crpc", answer="..."),
    ]
    svc = QAService(qa_data)
    # Very different query
    result = svc.find_answer("motor vehicle accident claim", threshold=0.6)
    assert result is None


def test_qa_service_default_threshold():
    qa_data = [
        QAPair(source="TEST", question="what is bail under crpc", answer="Bail..."),
    ]
    svc = QAService(qa_data)
    # Similar enough to pass 0.6 threshold
    result = svc.find_answer("bail under crpc")
    assert result is not None
    assert result["confidence"] >= 0.6
