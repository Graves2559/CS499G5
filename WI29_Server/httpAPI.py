
'''
httpAPI.py


The backend router file.

Defines backend routes and endpoints for the REST/HTTP API (in this case, FastAPI), 
per respective type of Client requests.
'''

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles


class HttpAPI(FastAPI):
    def __init__(self):
        super().__init__()

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


        # Static files (frontend) binded to the root/public URL (provided by the Tunneling service)
        self.mount("/", StaticFiles(directory="dist", html=True), name="static")
            



