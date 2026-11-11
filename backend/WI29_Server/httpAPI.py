'''
httpAPI.py


The backend router file.

Builds the FastAPI application: it asks the composition root (Container.py) for the services, mounts the
routers of the interface layer, and serves the frontend. The routes themselves are in interface/.
'''

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

from WI29_Server.Container import Container, buildContainer
from WI29_Server.interface.AuthRoutes import buildAuthRouter
from WI29_Server.interface.ErrorHandlers import registerErrorHandlers
from WI29_Server.interface.FileRoutes import buildFileRouter


class HttpAPI(FastAPI):
    def __init__(self, container: Optional[Container] = None):
        self.container = container or buildContainer()
        seed = self.container.seedAdmin

        @asynccontextmanager
        async def lifespan(app):
            asyncio.get_running_loop().run_in_executor(None, seed)
            yield

        super().__init__(lifespan=lifespan)
        registerErrorHandlers(self)

        """ Testing purposes. If this is executed, it will override the static files bound at the root URL.
        @self.get("/")
        def read_root():
            return {"message": "Hello over HTTPS!"} """

        # Do the lightweight ones first before the static files. If the static files are done first
        # it will make the favicon.ico function done after the static files, potentially causing unnecessary 404s.
        # That is, the browser's automatic 404 requests will be displayed, because said function(s) aren't executed.
        @self.get("/favicon.ico", include_in_schema=False)
        def favicon():
            # avoids noisy 404s from browsers auto-requesting a favicon
            return Response(status_code=204)

        # API routes here
        c = self.container
        self.include_router(buildAuthRouter(c.auth, c.google, c.settings.sessionSeconds))
        self.include_router(buildFileRouter(c.auth, c.files))

        # Static files (frontend) binded to the root/public URL (provided by the Tunneling service)
        # CONNECTS "app" folder to the backend
        self.mount("/", StaticFiles(directory=c.settings.staticDir, html=True), name="static")
