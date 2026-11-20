from CommonErrors.Errors import ExternalServiceError, ValidationError
from AI.domain.Results import OCRResult
from FolderStructure_User.StorageNode import File


class RapidOCREngine:
    def __init__(self):
        self._engine = None

    def extract_text(self, input_file: File, model_id: str) -> OCRResult:
        data = input_file.getData()
        if not isinstance(data, bytes):
            raise ValidationError("OCR input must contain image or PDF bytes.")

        try:
            if self._engine is None:
                from rapidocr import RapidOCR
                self._engine = RapidOCR()
            result = self._engine(data)
            texts = getattr(result, "txts", None)
        except (ImportError, OSError) as error:
            raise ExternalServiceError("RapidOCR is not installed or could not load its models.") from error
        except (ValueError, RuntimeError) as error:
            raise ExternalServiceError("RapidOCR failed to process the input file.") from error

        if not texts:
            raise ExternalServiceError("RapidOCR returned no text.")
        return OCRResult("\n".join(str(text) for text in texts), model_id)