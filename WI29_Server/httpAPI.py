
'''
httpAPI.py


The backend router file.

Defines backend routes and endpoints for the REST/HTTP API (in this case, FastAPI), 
per respective type of Client requests.
'''

from fastapi import FastAPI, Response


class HttpAPI(FastAPI):
    def __init__(self):
        super().__init__()

        @self.get("/")
        def read_root():
            return {"message": "Hello over HTTPS!"}


        @self.get("/favicon.ico", include_in_schema=False)
        def favicon():
            # avoids noisy 404s from browsers auto-requesting a favicon
            return Response(status_code=204)


            



