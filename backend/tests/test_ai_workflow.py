import pytest

from AI.application.AIWorkflowService import AIOperation, AIWorkflowService
from AI.application.LLMService import LLMService
from AI.application.ModelCatalogService import ModelCatalogService
from AI.application.OCRService import OCRService
from AI.domain.Results import OCRResult, SummaryResult
from AI.infrastructure.StaticModelCatalog import StaticModelCatalog
from AI.infrastructure.OCRModelRouter import OCRModelRouter
from CommonErrors.Errors import ValidationError
from FolderStructure_User.StorageNode import File


class FakeOCR:
    def extract_text(self, input_file, model_id):
        return OCRResult(f"ocr:{input_file.getData()}", model_id)


class FakeLLM:
    def summarize_file(self, input_file, model_id):
        return SummaryResult(f"summary:{input_file.getData()}", model_id)

    def summarize_text(self, text, model_id):
        return SummaryResult(f"summary:{text}", model_id)


@pytest.fixture
def source():
    file = File()
    file.setEntryID("input")
    file.setName("input.txt")
    file.setData("source")
    return file


@pytest.fixture
def workflow():
    return AIWorkflowService(OCRService(FakeOCR()), LLMService(FakeLLM()))


def test_both_creates_final_storage_file(workflow, source):
    output = workflow.execute(AIOperation.BOTH, source, "output", "rapidocr", "llama3.1:8b")
    assert output.getEntryID() == "output"
    assert output.getData() == "summary:ocr:source"


def test_llm_requires_a_model(workflow, source):
    with pytest.raises(ValidationError):
        workflow.execute(AIOperation.LLM, source, "output")


def test_catalog_rejects_unavailable_model():
    catalog = ModelCatalogService(StaticModelCatalog())
    with pytest.raises(ValidationError):
        catalog.require_model("mistral:7b", "summarizer")


def test_ocr_model_router_selects_requested_engine(source):
    class Engine:
        def extract_text(self, input_file, model_id):
            return OCRResult(model_id, model_id)

    result = OCRModelRouter({
        "rapidocr-standard": Engine(),
        "trocr-handwritten": Engine(),
    }).extract_text(source, "trocr-handwritten")
    assert result.text == "trocr-handwritten"
