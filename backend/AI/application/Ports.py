# AI/application/Ports.py
from typing import Protocol

from AI.domain.Models import ModelInfo
from AI.domain.Results import OCRResult, SummaryResult
from FolderStructure_User.StorageNode import File


class ModelCatalog(Protocol):
    # Implement this in infrastructure so the application layer never imports Ollama or OCR libraries.
    def list_models(self) -> list[ModelInfo]:
        ...


class OCREngine(Protocol):
    # The adapter reads input_file.getData() and returns normalized text.
    # Do not return a provider-specific response object from this boundary.
    def extract_text(self, input_file: File, model_id: str) -> OCRResult:
        ...


class Summarizer(Protocol):
    # This is the single-file operation: the adapter receives a StorageNode File.
    def summarize_file(self, input_file: File, model_id: str) -> SummaryResult:
        ...

    # This is used by the combined OCR -> LLM operation. It receives immediate OCR text,
    # so it does not need to manufacture a temporary File just to call the LLM.
    def summarize_text(self, text: str, model_id: str) -> SummaryResult:
        ...