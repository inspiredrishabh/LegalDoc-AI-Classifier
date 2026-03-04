from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path


class Settings(BaseSettings):
    # Server
    PORT: int = 8000
    DEBUG: bool = False

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # OCR — offline PaddleOCR engine
    # Language: "auto" (detect en/hi), "en" for English, "hi" for Hindi
    OCR_LANG: str = "auto"

    # LLM
    LLM_MODE: str = "local"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"

    # Data paths
    DATA_DIR: Path = Path(__file__).resolve().parent.parent.parent / "data"
    ACTS_DIR: Path | None = None
    QA_DIR: Path | None = None

    # Upload
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: Path = Path("uploads")

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    def model_post_init(self, __context):
        if self.ACTS_DIR is None:
            self.ACTS_DIR = self.DATA_DIR / "acts"
        if self.QA_DIR is None:
            self.QA_DIR = self.DATA_DIR / "qa"
        if not self.ACTS_DIR.exists():
            raise ValueError(f"Acts directory not found: {self.ACTS_DIR}")
        if not self.QA_DIR.exists():
            raise ValueError(f"QA directory not found: {self.QA_DIR}")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
