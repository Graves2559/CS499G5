from enum import StrEnum

from AI.application.LLMService import LLMService
from AI.application.OCRService import OCRService
from FolderStructure_User.StorageNode import File


class AIOperation(StrEnum):
    OCR = "ocr"
    LLM = "llm"
    BOTH = "both"


class AIWorkflowService:
    """Coordinates the three user-visible operations without persisting files."""

    def __init__(self, ocr: OCRService, llm: LLMService):
        self.ocr = ocr
        self.llm = llm

    def execute(
        self,
        operation: AIOperation,
        input_file: File,
        output_entry_id: str,
        ocr_model_id: str | None = None,
        llm_model_id: str | None = None,
    ) -> File:
        # The caller (route/controller) can pass the returned File to StorageManager/DB.
        if operation is AIOperation.OCR:
            if ocr_model_id is None:
                raise ValueError("ocr_model_id is required for OCR")
            return self.ocr.process_file(input_file, output_entry_id, ocr_model_id)

        if operation is AIOperation.LLM:
            if llm_model_id is None:
                raise ValueError("llm_model_id is required for LLM")
            return self.llm.process_file(input_file, output_entry_id, llm_model_id)

        if operation is AIOperation.BOTH:
            if ocr_model_id is None or llm_model_id is None:
                raise ValueError("ocr_model_id and llm_model_id are required for BOTH")
            # OCR creates an intermediate File; the LLM consumes only its data,
            # then creates the final output File.
            ocr_file = self.ocr.process_file(input_file, f"{output_entry_id}:ocr", ocr_model_id)
            return self.llm.process_text(ocr_file.getData(), output_entry_id, llm_model_id)

        raise ValueError(f"Unsupported AI operation: {operation}")
