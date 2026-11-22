from AI.application.Ports import Summarizer
from FolderStructure_User.StorageNode import File


class LLMService:
    def __init__(self, summarizer: Summarizer):
        self.summarizer = summarizer

    def process_file(self, input_file: File, output_entry_id: str, model_id: str) -> File:
        """Run LLM-only processing and place the result into a new StorageNode File."""
        self._require_input(input_file)
        result = self.summarizer.summarize_file(input_file, model_id)
        return self._output_file(output_entry_id, result.text)

    def process_text(self, text: str, output_entry_id: str, model_id: str) -> File:
        """Run the LLM stage on text produced by a preceding OCR stage."""
        result = self.summarizer.summarize_text(text, model_id)
        return self._output_file(output_entry_id, result.text)

    @staticmethod
    def _output_file(entry_id: str, data: str) -> File:
        output_file = File()
        output_file.setEntryID(entry_id)
        output_file.setName(entry_id)
        output_file.setData(data)
        return output_file

    @staticmethod
    def _require_input(input_file: File) -> None:
        if not isinstance(input_file, File):
            raise TypeError("input_file must be a FolderStructure_User.StorageNode.File")