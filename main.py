#!/usr/bin/env python3
import json
from dotenv import load_dotenv
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, APIRouter
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTask
from fastapi.responses import HTMLResponse, JSONResponse
import httpx  # httpx streaming allows for larger files & less memory usage
from websockets import connect
from logger import logger
import requests


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


async def get_rpc_resp(request, network, path):
    network = network.lower()
    url = f'{config.API_URLS[network]["rpc"]}{path}'
    if request.method == "POST":
        data = await request.json()
        # Sees blockpi wants the post sent as get *shrug*
        # This is a hack to get around that, and might not
        # work for all networks. Further testing is needed.
        r = requests.get(url, json=data)
    else:
        r = requests.get(url)
    return JSONResponse(r.json())


async def get_ws_resp(websocket: WebSocket, network):
    network = network.lower()
    await websocket.accept()
    if network not in config.API_URLS:
        upstream_ws_url = "wss://echo.websocket.org"
    else:
        upstream_ws_url = config.API_URLS[network]["wss"]
    if upstream_ws_url.endswith("/"):
        upstream_ws_url = upstream_ws_url[:-1]
    async with connect(upstream_ws_url) as upstream_ws:
        try:
            while True:
                if network not in config.API_URLS:
                    await websocket.send_text(str({"error": f"network {network} not supported!"}))
                    raise WebSocketDisconnect
                else:
                    data = await websocket.receive_text()
                    await upstream_ws.send(data)
                    response = await upstream_ws.recv()
                    await websocket.send_text(response)
        except WebSocketDisconnect:
            await websocket.close()
        except Exception as e:
            await websocket.close()
            raise e



@app.get("/")
def welcome(request: Request):
    return {
        "message": "Welcome to the Blockpi proxy API!",
        "supported_networks": list(config.API_URLS.keys()),
        "info": "See /docs for API documentation"
    }


@app.get("/api/v1/healthcheck")
def healthcheck(request: Request):
    return {"status": "online"}


@app.api_route(
    "/rpc/{network}/{path:path}",
    methods=["GET", "POST", "OPTIONS"],
)
async def get_rpc(request: Request, network: str, path: str):
    network = network.lower()
    if network not in config.API_URLS:
        return JSONResponse({"error": f"network {network} not supported!"})
    return await get_rpc_resp(request, network, path)


@app.websocket("/rpc/{network}/websocket")
async def websocket_proxy(websocket: WebSocket, network: str):
    network = network.lower()
    return await get_ws_resp(websocket, network)


@app.websocket("/ws/{network}/websocket")
async def websocket_proxy(websocket: WebSocket, network: str):
    network = network.lower()
    return await get_ws_resp(websocket, network)


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
