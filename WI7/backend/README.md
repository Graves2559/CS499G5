# Backend — setup & run

Terminal commands only, run from inside this `backend/` folder.

## 1. Create a venv and install dependencies

**Windows:**
```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Mac:**
```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 2. Make sure Ollama is running with a model pulled

```
ollama pull llama3.1:8b
```
(Ollama runs as a background service once installed -- you don't need to
separately "start" it, just make sure the app/service is running. `ollama
list` shows what's pulled.)

## 3. Run the server

**Windows:**
```
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

**Mac:**
```
.venv/bin/python -m uvicorn main:app --reload --port 8000
```

Leave this running in its own terminal. `--reload` restarts the server
automatically when you edit a file, which is convenient while adding new
routers for future work items.

## 4. Check it's alive

Visit http://localhost:8000/health in a browser -- should show
`{"status":"ok"}`. FastAPI also gives you free interactive docs at
http://localhost:8000/docs where you can try the `/api/define` endpoint
directly without the frontend at all.

## Adding the next work item (e.g. summarize)

1. Copy `routers/define.py` to `routers/summarize.py`, change the prompt
   template, request/response field names, and route path (`/summarize`
   instead of `/define`).
2. In `main.py`, add:
   ```python
   from routers import summarize
   app.include_router(summarize.router, prefix="/api", tags=["summarize"])
   ```
3. That's it -- `llm.py` (the actual Ollama call) doesn't need to change.

## Notes

- `allow_origins=["*"]` in `main.py` is intentionally wide open for local
  development. Tighten it to your real frontend's URL before this is
  anything but a local demo.
- If a request to `/api/define` comes back with a 502, check that Ollama is
  running and that the model named in `llm.py`'s `DEFAULT_MODEL` has
  actually been pulled (`ollama list`).
