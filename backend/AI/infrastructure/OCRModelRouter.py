from AI.application.Ports import OCREngine
from AI.domain.Results import OCRResult
from FolderStructure_User.StorageNode import File


class OCRModelRouter:
    """Selects an OCR implementation without exposing providers to application code."""

    def __init__(self, engines: dict[str, OCREngine]):
        self.engines = engines

    def extract_text(self, input_file: File, model_id: str) -> OCRResult:
        engine = self.engines.get(model_id)
        if engine is None:
            raise ValueError(f"No OCR engine is configured for model '{model_id}'.")
        return engine.extract_text(input_file, model_id)
