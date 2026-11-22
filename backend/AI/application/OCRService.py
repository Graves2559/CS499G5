from AI.application.Ports import OCREngine
from FolderStructure_User.StorageNode import File


class OCRService:
    def __init__(self, engine: OCREngine):
        self.engine = engine

    def process_file(self, input_file: File, output_entry_id: str, model_id: str) -> File:
        """Create an output File containing OCR text; persistence remains the caller's job."""
        self._require_input(input_file)
        result = self.engine.extract_text(input_file, model_id)

        output_file = File()
        output_file.setEntryID(output_entry_id)
        output_file.setName(output_entry_id)
        output_file.setData(result.text)
        return output_file

    @staticmethod
    def _require_input(input_file: File) -> None:
        if not isinstance(input_file, File):
            raise TypeError("input_file must be a FolderStructure_User.StorageNode.File")