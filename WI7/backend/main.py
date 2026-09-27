"""
Entry point for the ClosedAI backend.

Goal for this file:
    - Create the FastAPI app
    - Let the frontend (a different origin/port) actually call it without
      the browser blocking the request -- that's what CORS middleware is for
    - Mount the /define router so its route shows up
    - Add a throwaway health-check route so you can confirm the server is
      alive before wiring up the frontend

Once this is filled in, run it from this backend/ folder with:
    uvicorn main:app --reload --port 8000

("main:app" refers to this file and whatever you name the FastAPI instance
below -- keep it named `app` unless you also change how you invoke uvicorn.)
"""

# TODO: from fastapi import FastAPI
# TODO: from fastapi.middleware.cors import CORSMiddleware
# TODO: from routers import define


# TODO: create the app instance, e.g. app = FastAPI(title="...")


# TODO: register CORS middleware on the app.
# Look up FastAPI's app.add_middleware(CORSMiddleware, ...) -- it takes
# allow_origins / allow_methods / allow_headers. For local dev, allowing
# everything ("*") is fine; tighten it once there's a real frontend URL.


# TODO: include the define router with app.include_router(...).
# Give it prefix="/api" so its route ends up at /api/define.
#
# When the next work item (e.g. summarize) gets its own router, this should
# be the ONLY thing that changes in this file: one more
# app.include_router(...) call, plus the matching import above.


# TODO: add a GET /health route that returns something like
# {"status": "ok"}. Once this file works, check it by visiting
# http://localhost:8000/health in a browser before touching the frontend.
