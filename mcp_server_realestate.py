import asyncio
import json
import logging
import os  # os 모듈 추가 (환경변수 읽기용)
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# --- 1. 라이브러리 유무 확인 및 호환성 계층 (Polyfill) ---
try:
    from mcp.server import Server
    from mcp.server.sse import SseServerTransport
    import mcp.types as types
    from sse_starlette.sse import EventSourceResponse
    HAS_MCP = True
    logger.info("✅ MCP Library found. Running in full mode.")
except ImportError:
    HAS_MCP = False
    logger.warning("⚠️ MCP Library NOT found. Running in SIMULATION mode (Dependency-free).")
    
    # --- MOCK CLASSES START ---
    class MockTypes:
        class Tool:
            def __init__(self, name, description, inputSchema):
                self.name = name
                self.description = description
                self.inputSchema = inputSchema
        class TextContent:
            def __init__(self, type, text):
                self.type = type
                self.text = text
        class ImageContent: pass
        class EmbeddedResource: pass
    
    types = MockTypes()

    class Server:
        def __init__(self, name):
            self.name = name
            self.tool_callback = None
            self.list_tools_callback = None
        def list_tools(self):
            def decorator(func):
                self.list_tools_callback = func
                return func
            return decorator
        def call_tool(self):
            def decorator(func):
                self.tool_callback = func
                return func
            return decorator

    class SseServerTransport:
        def __init__(self, endpoint):
            self.endpoint = endpoint
            self.queue = asyncio.Queue()
            self.server = None 
        async def connect_sse(self, scope, receive, send):
            return self.queue
        async def handle_post_message(self, scope, receive, send):
            request = Request(scope, receive)
            try:
                data = await request.json()
                method = data.get("method")
                id_ = data.get("id")
                result = None
                
                if method == "initialize":
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "serverInfo": {"name": "mock-server", "version": "1.0"}
                    }
                elif method == "tools/list":
                    if self.server and self.server.list_tools_callback:
                        tools = await self.server.list_tools_callback()
                        result = {"tools": [{"name": t.name, "description": t.description, "inputSchema": t.inputSchema} for t in tools]}
                elif method == "tools/call":
                    if self.server and self.server.tool_callback:
                        params = data.get("params", {})
                        name = params.get("name")
                        args = params.get("arguments", {})
                        content = await self.server.tool_callback(name, args)
                        result = {"content": [{"type": c.type, "text": c.text} for c in content]}
                elif method == "notifications/initialized":
                    return 
                
                if id_ is not None:
                    response_msg = {"jsonrpc": "2.0", "id": id_, "result": result}
                    await self.queue.put(response_msg)
            except Exception as e:
                logger.error(f"Error handling message: {e}")

    def EventSourceResponse(generator):
        async def stream_wrapper():
            async for event in generator:
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
        return StreamingResponse(stream_wrapper(), media_type="text/event-stream")
    # --- MOCK CLASSES END ---

# --- 2. 서버 로직 ---
mcp_server = Server("my-demo-server")

@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="hello_mcp",
            description="인사를 반환하고 MCP 연결을 테스트합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "인사할 사람의 이름"}
                },
                "required": ["name"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
    if name == "hello_mcp":
        user_name = arguments.get("name", "Friend")
        return [
            types.TextContent(
                type="text",
                text=f"안녕하세요, {user_name}님! Play MCP에서 서버가 정상적으로 인식되었습니다."
            )
        ]
    raise ValueError(f"Unknown tool: {name}")

# --- 3. FastAPI 설정 ---
sse_transport = SseServerTransport("/messages")
if not HAS_MCP:
    sse_transport.server = mcp_server

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/sse")
async def handle_sse(request: Request):
    if HAS_MCP:
        async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
            async def event_generator():
                async for message in streams:
                    yield {"event": "message", "data": message}
            return EventSourceResponse(event_generator())
    else:
        queue = await sse_transport.connect_sse(None, None, None)
        async def event_generator():
            while True:
                message = await queue.get()
                yield {"event": "message", "data": message}
        return EventSourceResponse(event_generator())

@app.post("/messages")
async def handle_messages(request: Request):
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)
    return Response(status_code=200)

if __name__ == "__main__":
    # 중요: Railway가 제공하는 PORT 환경변수를 사용해야 합니다.
    # 없으면 기본값으로 8000을 사용합니다.
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
