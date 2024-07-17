#!/usr/bin/env python3
import json
from dotenv import load_dotenv
import asyncio
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, APIRouter
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTask
from fastapi.responses import HTMLResponse, JSONResponse
import httpx  # httpx streaming allows for larger files & less memory usage
import websockets
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


async def get_rpc_resp(request, network, path=None):
    try:
        network = network.lower()
        logger.calc(config.API_URLS[network])
        url = config.API_URLS[network]["rpc"]
        if path is None and url.endswith("/"):
            url = url[:-1]
        if path is not None:
            url = f"{url}/{path}"
        logger.calc(url)
        if request.method == "POST":
            data = await request.json()
            logger.calc(data)
            r = requests.post(url, json=data)
        else:
            r = requests.get(url)
        return JSONResponse(r.json())
    except:
        logger.warning(r.text)


@app.get("/")
def welcome(request: Request):
    return {
        "message": "Welcome to the Blockpi proxy API!",
        "supported_networks": list(config.API_URLS.keys()),
        "info": "See /docs for API documentation",
    }


@app.get("/api/v1/healthcheck")
def healthcheck(request: Request):
    return {"status": "online"}


@app.get("/rpc/{network}/{path:path}")
async def get_rpc(request: Request, network: str, path: str):
    network = network.lower()
    if network not in config.API_URLS:
        return JSONResponse({"error": f"network {network} not supported!"})
    return await get_rpc_resp(request, network, path)


@app.post("/rpc/{network}/")
async def get_rpc(request: Request, network: str):
    network = network.lower()
    if network not in config.API_URLS:
        return JSONResponse({"error": f"network {network} not supported!"})
    return await get_rpc_resp(request, network)


@app.post("/rpc/{network}")
async def get_rpc(request: Request, network: str):
    network = network.lower()
    if network not in config.API_URLS:
        return JSONResponse({"error": f"network {network} not supported!"})
    return await get_rpc_resp(request, network)


async def forward_messages_from_client_to_upstream(client_ws: WebSocket, upstream_ws):
    try:
        while True:
            message = await client_ws.receive_text()
            if not upstream_ws.open:
                break
            await upstream_ws.send(message)
    except (WebSocketDisconnect, websockets.exceptions.ConnectionClosedError):
        pass
    except Exception as e:
        print(f"Error forwarding message from client to upstream: {e}")


async def forward_messages_from_upstream_to_client(upstream_ws, client_ws: WebSocket):
    try:
        async for message in upstream_ws:
            await client_ws.send_text(message)
    except (WebSocketDisconnect, websockets.exceptions.ConnectionClosedError):
        pass
    except Exception as e:
        print(f"Error forwarding message from upstream to client: {e}")


async def connect_to_upstream(client_ws: WebSocket, network: str):
    try:
        network = network.lower()
        if network not in config.API_URLS:
            upstream_ws_url = "wss://echo.websocket.org"
        else:
            upstream_ws_url = config.API_URLS[network]["wss"]
        if upstream_ws_url.endswith("/"):
            upstream_ws_url = upstream_ws_url[:-1]

        async with websockets.connect(upstream_ws_url) as upstream_ws:
            # Send a ping message to keep the connection alive
            asyncio.create_task(ping_pong(upstream_ws))

            # Forward messages between the client and upstream WebSocket
            await asyncio.gather(
                forward_messages_from_client_to_upstream(client_ws, upstream_ws),
                forward_messages_from_upstream_to_client(upstream_ws, client_ws),
            )
    except Exception as e:
        print(f"Upstream connection error: {e}")
        await client_ws.close()


async def ping_pong(websocket):
    try:
        while websocket.open:
            await websocket.ping()
            await asyncio.sleep(10)
    except Exception as e:
        print(f"Ping/pong error: {e}")


@app.websocket("/rpc/{network}/websocket")
async def ws_proxy(websocket: WebSocket, network: str):
    await websocket.accept()
    try:
        await connect_to_upstream(websocket, network)
    except Exception as e:
        print(f"Proxy error: {e}")
    finally:
        await websocket.close()


@app.websocket("/ws/{network}/websocket")
async def websocket_proxy(websocket: WebSocket, network: str):
    await websocket.accept()
    try:
        await connect_to_upstream(websocket, network)
    except Exception as e:
        print(f"Proxy error: {e}")
    finally:
        await websocket.close()


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
