'''
main.py 

Author: Trinh Pham

To be used as the main entry point for the WI29 module.
'''

import uvicorn
from fastapi import FastAPI, Response

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello over HTTPS!"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    # avoids noisy 404s from browsers auto-requesting a favicon
    return Response(status_code=204)


def main():
    # HTTPS is terminated by ngrok; uvicorn just serves plain HTTP for the tunnel to forward to
    # host 0.0.0.0 binds all network interfaces so the ngrok agent (and LAN clients) can reach this server
    # reload=False: uvicorn's --reload spawns a second process that duplicates the listening
    # socket on macOS, which causes external connections to randomly get reset
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        loop="asyncio",
        log_level="debug",
    )


if __name__ == "__main__":
    main()
