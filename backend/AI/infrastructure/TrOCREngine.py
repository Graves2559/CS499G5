from io import BytesIO
from typing import Any

from CommonErrors.Errors import ExternalServiceError, ValidationError
from AI.domain.Results import OCRResult
from FolderStructure_User.StorageNode import File


class TrOCREngine:
    """Handwriting OCR adapter using Hugging Face TrOCR."""

    def __init__(self, model_name: str = "microsoft/trocr-base-handwritten"):
        self.model_name = model_name
        self._processor: Any = None
        self._model: Any = None

    def extract_text(self, input_file: File, model_id: str) -> OCRResult:
        data = input_file.getData()
        if not isinstance(data, bytes):
            raise ValidationError("OCR input must contain image bytes.")

        try:
            from PIL import Image
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            import torch

            if self._processor is None or self._model is None:
                self._processor = TrOCRProcessor.from_pretrained(self.model_name)
                self._model = VisionEncoderDecoderModel.from_pretrained(self.model_name)

            image = Image.open(BytesIO(data)).convert("RGB")
            pixel_values = self._processor(images=image, return_tensors="pt").pixel_values
            with torch.no_grad():
                generated_ids = self._model.generate(pixel_values)
            text = self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        except (ImportError, OSError) as error:
            raise ExternalServiceError("TrOCR is not installed or its model could not be loaded.") from error
        except (ValueError, RuntimeError) as error:
            raise ExternalServiceError("TrOCR failed to process the input file.") from error

        if not text:
            raise ExternalServiceError("TrOCR returned no text.")
        return OCRResult(text, model_id)
