#!/usr/bin/env python3
import json
from dotenv import load_dotenv
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, FastAPI, WebSocket, APIRouter
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTask
from fastapi.responses import HTMLResponse
import httpx  # httpx streaming allows for larger files & less memory usage
from httpx_ws import aconnect_ws
from logger import logger


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

networks = {"cosmos": {"rpc": config.COSMOS_RPC_URL}}


@app.get("/", tags=["api"])
def get_response(request: Request):
    return {"info": "go to /docs for API documentation"}


@app.get("/api/v1/healthcheck", tags=["api"])
def get_response(request: Request):
    return {"status": "online"}


async def get_rpc_resp(network, path):
    client = httpx.AsyncClient(base_url=networks[network]["rpc"])
    req = client.build_request("GET", path)
    r = await client.send(req, stream=True)
    return StreamingResponse(
        r.aiter_raw(), background=BackgroundTask(r.aclose), headers=r.headers
    )


async def get_wss_resp(network, path):
    url = f"{networks[network]['rpc']}/websocket"
    client = httpx.AsyncClient()
    async with aconnect_ws(url, client) as ws:
        message = await ws.receive_text()
        print(message)
        return message


@app.get("/rpc/cosmos/{path:path}", tags=["BlockPi"])
async def get_rpc(path: str):
    return await get_rpc_resp("cosmos", path)


@app.post("/rpc/cosmos/{path:path}", tags=["BlockPi"])
async def post_rpc(path: str):
    logger.info(f"POST request to {path}")
    return await get_rpc_resp("cosmos", path)


@app.websocket("/rpc/cosmos/{path:path}")
async def wss_rpc(path: str):
    return await get_wss_resp("cosmos", path)


# TODO: Not working yet, needs review.
def websocket_endpoint(*, websocket: WebSocket, path: str, q: int | None = None):
    websocket.accept()
    while True:
        data = websocket.receive_text()
        if q is not None:
            websocket.send_text(f"Query parameter q is: {q}")
        logger.info(f"Received data: {data}")
        return websocket.send_text(data)


if __name__ == "__main__":
    print("Starting FastAPI...")
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
