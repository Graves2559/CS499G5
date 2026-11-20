from fastapi import APIRouter, Depends, File as UploadFileDependency, Form, UploadFile

from CommonErrors.Errors import ValidationError
from AI.application.AIWorkflowService import AIOperation, AIWorkflowService
from AI.application.ModelCatalogService import ModelCatalogService
from AI.domain.Models import ModelInfo
from AI.interface.Schema import AIResultResponse, ModelResponse
from WI29_Server.application.AuthService import AuthService
from WI29_Server.application.FileService import FileService
from WI29_Server.interface.Session import makeCurrentUser


def _to_response(model: ModelInfo) -> ModelResponse:
    return ModelResponse(
        id=model.id,
        name=model.name,
        kind=model.kind,
        available=model.available,
    )


def buildAIRouter(
    catalog: ModelCatalogService,
    workflow: AIWorkflowService,
    auth: AuthService,
    files: FileService,
) -> APIRouter:
    # Keep route functions thin: validate HTTP input, call an application service,
    # and translate domain results into response schemas.
    router = APIRouter(prefix="/api/ai", tags=["AI"])

    @router.get("/models", response_model=list[ModelResponse])
    def listModels() -> list[ModelResponse]:
        return [_to_response(model) for model in catalog.list_models()]

    current_user = makeCurrentUser(auth)

    @router.post("/process", response_model=AIResultResponse)
    def process(
        operation: AIOperation = Form(...),
        output_entry_id: str = Form(...),
        output_parent_id: str = Form(...),
        output_name: str = Form(...),
        ocr_model_id: str | None = Form(None),
        llm_model_id: str | None = Form(None),
        upload: UploadFile = UploadFileDependency(...),
        username: str = Depends(current_user),
    ) -> AIResultResponse:
        content = upload.file.read()
        input_entry_id = upload.filename or "input"

        from FolderStructure_User.StorageNode import File

        input_file = File()
        input_file.setEntryID(input_entry_id)
        input_file.setName(input_entry_id)
        input_file.setData(content)

        if operation in (AIOperation.OCR, AIOperation.BOTH):
            if ocr_model_id is None:
                raise ValidationError("ocr_model_id is required for OCR operations")
            catalog.require_model(ocr_model_id, "ocr")
        if operation in (AIOperation.LLM, AIOperation.BOTH):
            if llm_model_id is None:
                raise ValidationError("llm_model_id is required for LLM operations")
            catalog.require_model(llm_model_id, "summarizer")

        output_file = workflow.execute(
            operation,
            input_file,
            output_entry_id,
            ocr_model_id,
            llm_model_id,
        )
        output_data = output_file.getData()
        if not isinstance(output_data, str):
            raise TypeError("AI output must be text before it is saved.")

        files.putFile(
            username,
            output_file.getEntryID(),
            output_parent_id,
            output_name,
            f"Output from {operation.value}.",
            output_data.encode("utf-8"),
        )
        return AIResultResponse(
            entry_id=output_file.getEntryID(),
            name=output_name,
            data=output_data,
            operation=operation.value,
            ocr_model_id=ocr_model_id,
            llm_model_id=llm_model_id,
        )

    return router