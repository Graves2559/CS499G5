# AI backend module

The AI module separates the HTTP API and application services from concrete
OCR and LLM providers.

- `domain/` contains provider-independent types.
- `application/` contains use cases and ports.
- `infrastructure/` contains provider adapters and model configuration.
- `interface/` contains FastAPI routes and HTTP schemas.

The frontend can retrieve the approved button choices with:

```text
GET /api/ai/models
```

AI processing uses one multipart endpoint:

```text
POST /api/ai/process
```

Required form fields are `operation`, `output_entry_id`, `output_parent_id`,
`output_name`, and `upload`. Send `ocr_model_id` for `ocr`/`both`, and
`llm_model_id` for `llm`/`both`. The endpoint saves the generated text in the
user's output folder and returns the output data.

Provider implementations should be wired in `WI29_Server/Container.py`.
The frontend should send model IDs, not provider-specific configuration.

The default model choices are:

- `rapidocr-standard`: standard/printed font OCR.
- `trocr-handwritten`: handwriting recognition through TrOCR.
- `llama3.1:8b`: document summarization through Ollama.

The `OCRModelRouter` selects the OCR adapter from the model ID. This keeps
standard-font OCR and handwriting recognition interchangeable at the application
boundary while allowing the frontend to use buttons instead of provider details.

## StorageNode workflow

AI services use `FolderStructure_User.StorageNode.File` as the boundary object:

1. The caller creates `inputFile`, sets its name/entry ID, and calls `setData`.
2. OCR or LLM reads `inputFile.getData()`.
3. The service creates `outputFile`, calls `setEntryID`, `setName`, and `setData`.
4. The caller persists `outputFile` through the storage/database layer.

`AIWorkflowService` exposes the three operations:

- `AIOperation.OCR`: input file -> OCR output file.
- `AIOperation.LLM`: input file -> summary output file.
- `AIOperation.BOTH`: input file -> intermediate OCR text -> final summary output file.

The workflow does not save to the database itself. This keeps persistence in the
existing storage layer and makes the services easy to test with in-memory files.

## Demonstration status

### OCR and text recognition

- **US01 printed-text OCR:** In progress. `rapidocr-standard` accepts an uploaded
  image, extracts text, saves the text output, and displays it in the Output
  panel. The panel includes a **Copy text** button.
- **US013 handwriting recognition:** Open/extension. `trocr-handwritten` is
  implemented as an optional adapter, but it requires the TrOCR dependencies and
  model to be installed before it can be demonstrated.
- OCR failures are returned as application errors and shown by the frontend as
  an alert/status message.

Pipeline:

```text
Upload Image -> POST /api/ai/process -> StorageNode.File
-> RapidOCR/TrOCR -> outputFile.setData(text)
-> FileService.putFile -> Output panel -> Copy text
```

### AI document summarization

- **US07 summarization:** Implemented through Ollama.
- **US014 summary interface:** Implemented through the same Output panel.
- `llama3.1:8b` is the default configured summarizer.
- Empty input and input over 12,000 characters are rejected.
- Generated summaries are saved in the user's Output folder and returned in
  the API response.

Pipeline:

```text
Upload Document -> OCR (when needed) -> Ollama prompt
-> SummaryResult -> outputFile -> FileService.putFile -> Output panel
```

### Custom prompts

- **US020 custom prompts:** Open/stretch goal.
- The current default prompt is:

```text
Summarize the following text. Keep important facts and do not invent information.
```

Custom prompt input is not required for the current MVP and is not exposed by
the frontend yet.