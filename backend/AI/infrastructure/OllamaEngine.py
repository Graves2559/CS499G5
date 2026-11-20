from typing import Any

from CommonErrors.Errors import ExternalServiceError, ValidationError
from AI.domain.Results import SummaryResult
from FolderStructure_User.StorageNode import File


MAX_SUMMARY_INPUT = 12000
DEFAULT_SUMMARY_PROMPT = "Summarize the following text. Keep important facts and do not invent information."


class OllamaEngine:
    def __init__(self, default_model: str = "llama3.1:8b"):
        self.default_model = default_model

    def summarize_file(self, input_file: File, model_id: str) -> SummaryResult:
        data = input_file.getData()
        if isinstance(data, bytes):
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValidationError("LLM input must be UTF-8 text.") from error
        else:
            text = str(data)
        return self.summarize_text(text, model_id)

    def summarize_text(self, text: str, model_id: str) -> SummaryResult:
        text = text.strip()
        if not text:
            raise ValidationError("Text to summarize must not be empty.")
        if len(text) > MAX_SUMMARY_INPUT:
            raise ValidationError(f"Text to summarize must be {MAX_SUMMARY_INPUT} characters or fewer.")

        model = model_id or self.default_model
        prompt = (
            f"{DEFAULT_SUMMARY_PROMPT}\n\n"
            f"{text}"
        )
        try:
            import ollama
            response: Any = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
        except ollama.ResponseError as error:
            raise ExternalServiceError(
                f"Summarization failed using Ollama model '{model}'."
            ) from error
        except (ConnectionError, TimeoutError, OSError) as error:
            raise ExternalServiceError("Ollama could not be reached.") from error

        try:
            result = response["message"]["content"].strip()
        except (KeyError, TypeError) as error:
            raise ExternalServiceError("The AI model returned an invalid response.") from error

        if not result:
            raise ExternalServiceError("The AI model returned an empty summary.")
        return SummaryResult(result, model)

