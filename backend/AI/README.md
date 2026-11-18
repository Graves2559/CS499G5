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

Provider implementations should be wired in `WI29_Server/Container.py`.
The frontend should send model IDs, not provider-specific configuration.

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