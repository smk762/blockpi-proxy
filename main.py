#!/usr/bin/env python3
import json
from dotenv import load_dotenv
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import (
    Request,
    FastAPI,
    WebSocket,
    APIRouter
)
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTask
from fastapi.responses import HTMLResponse

    
import httpx # httpx streaming allows for larger files & less memory usage

from config import ConfigFastAPI
load_dotenv()
config = ConfigFastAPI()

app = FastAPI(openFASTAPI_TAGS=config.FASTAPI["TAGS"])
router = APIRouter()
if config.FASTAPI["USE_MIDDLEWARE"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.FASTAPI["CORS_ORIGINS"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

networks = {
    "cosmos": {
        "rpc": config.COSMOS_RPC_URL
    }
}

@app.get("/", tags=["api"])
def get_response(request: Request):
    return {"info": "go to /docs for API documentation"}

@app.get("/api/v1/healthcheck", tags=["api"])
def get_response(request: Request):
    return {"status": "online"}


async def get_rpc_resp(network, path):
    client = httpx.AsyncClient(base_url=networks[network]['rpc'])
    req = client.build_request("GET", path)
    r = await client.send(req, stream=True)
    return StreamingResponse(
        r.aiter_raw(),
        background=BackgroundTask(r.aclose),
        headers=r.headers
   )


@app.get("/rpc/cosmos/{path:path}", tags=["BlockPi"])
async def cosmos_rpc(path: str):
    return await get_rpc_resp("cosmos", path)


if __name__ == "__main__":
    print("Starting FastAPI...")
    print(config.FASTAPI)
    if None not in [config.FASTAPI["SSL_KEY"], config.FASTAPI["SSL_CERT"]]:
        uvicorn.run(
            "main:app",
            host=config.FASTAPI["HOST"],
            port=config.FASTAPI["PORT"],
            ssl_keyfile=config.FASTAPI["SSL_KEY"],
            ssl_certfile=config.FASTAPI["SSL_CERT"],
        )
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=config.FASTAPI["PORT"])


# See for an example of upstream proxy with FastAPI https://github.com/tiangolo/fastapi/issues/1788
# Why not just use nginx? The FastAPI layer allows for more flexibility and control over the API and future auth implementations.
