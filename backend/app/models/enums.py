from enum import Enum


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnswerMethod(str, Enum):
    QA_DATASET = "qa_dataset"
    LLM = "llm"
    FALLBACK = "fallback"
    NO_LLM = "no_llm"
    ERROR = "error"
