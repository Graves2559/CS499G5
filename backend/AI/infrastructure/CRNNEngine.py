""" text-line image → CNN → sequence of features across image width
                 → BiLSTM → character scores + CTC blank
                 → CTC decoding → text
Important: a basic CRNN usually recognizes a cropped text line, not a whole page. Your adapter will need line detection/cropping before recognition—or a separate text-detection stage—if the input is a page image. If PDFs are supported, also decide how to rasterize their pages.

For the adapter, keep the same boundary as the OCREngine protocol: accept a File and model_id, validate the bytes, and return normalized text in OCRResult. Load the model lazily, use inference mode for predictions, and keep training outside the request path. Add the engine to the dependency wiring in Container.py and its display entry to StaticModelCatalog.py.

For training, start with labeled line-image/transcript pairs. Resize to a consistent height while preserving aspect ratio, pad or bucket by width, and calculate CTC input lengths from the CNN’s output widths. Track character error rate (CER) and word error rate (WER) on a held-out set split by source document, rather than only reporting training loss.

I haven’t changed any files; this is a suggested design that fits the existing project structure.

 """

from io import BytesIO
from typing import Any

from CommonErrors.Errors import ExternalServiceError, ValidationError
from AI.domain.Results import OCRResult
from FolderStructure_User.StorageNode import File

class CRNNEngine:
    """Personally developed CRNN adapter for text-line OCR."""

    def __init__(self, model_name: str = "crnn-model"):
        self.model_name = model_name
        self._model: Any = None

    def extract_text(self, input_file: File, model_id: str) -> OCRResult:
        data = input_file.getData()
        if not isinstance(data, bytes):
            raise ValidationError("OCR input must contain image bytes.")

        try:
            from PIL import Image
            import torch

            if self._model is None:
                # Load your CRNN model here
                self._model = self.load_model(self.model_name)

            image = Image.open(BytesIO(data)).convert("L")  # Convert to grayscale
            # Preprocess the image for the CRNN model (resize, normalize, etc.)
            preprocessed_image = self.preprocess_image(image)
            with torch.no_grad():
                text = self._model.predict(preprocessed_image)
        except (ImportError, OSError) as error:
            raise ExternalServiceError("CRNN is not installed or its model could not be loaded.") from error
        except (ValueError, RuntimeError) as error:
            raise ExternalServiceError("CRNN failed to process the input file.") from error

        if not text:
            raise ExternalServiceError("CRNN returned no text.")
        return OCRResult(text, model_id)

    def load_model(self, model_name: str) -> Any:
        # Implement model loading logic here
        pass

    def preprocess_image(self, image: Image.Image) -> Any:
        # Implement image preprocessing logic here
        pass