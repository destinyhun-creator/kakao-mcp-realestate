import asyncio
import logging
import os
import sys

# FastMCP 대신 표준(Low-level) Server와 타입을 가져옵니다.
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# 1. 로깅 설정
log_file_path = os.path.join(os.getcwd(), "mcp_debug.log")
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("=== MCP 서버(표준 방식) 시작 시도 ===")

# 2. 서버 인스턴스 생성
app = Server("DebugServer-Standard")

# 3. 도구 목록 정의 (list_tools)
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    logging.info("Client가 도구 목록(list_tools)을 요청했습니다.")
    return [
        types.Tool(
            name="ping",
            description="연결 상태를 확인하는 핑 도구",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="echo",
            description="메시지를 반환하는 에코 도구",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "반환할 메시지"}
                },
                "required": ["message"],
            },
        ),
    ]

# 4. 도구 실행 로직 (call_tool)
@app.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    logging.info(f"도구 실행 요청 받음: {name}, 인자: {arguments}")
    
    try:
        if name == "ping":
            return [
                types.TextContent(
                    type="text",
                    text="Pong! (표준 호환 모드로 응답함)"
                )
            ]
            
        elif name == "echo":
            if not arguments or "message" not in arguments:
                raise ValueError("Message argument is required")
                
            msg = arguments["message"]
            return [
                types.TextContent(
                    type="text",
                    text=f"Echo: {msg}"
                )
            ]
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logging.error(f"도구 실행 중 오류 발생: {e}")
        raise

# 5. 메인 실행부 (Stdio Transport & Shutdown Logic)
async def main():
    logging.info("Stdio Transport 연결 대기 중...")
    
    # stdio_server()는 컨텍스트 매니저로, 블록을 빠져나갈 때 스트림을 자동으로 닫아줍니다.
    async with stdio_server() as (read_stream, write_stream):
        logging.info("Stdio 연결 성공, 초기화 시작")
        try:
            # app.run()은 Player가 연결을 끊을 때까지 계속 실행됩니다 (While True와 유사)
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        except asyncio.CancelledError:
            # Player가 강제로 종료했을 때 발생하는 취소 에러 처리
            logging.info("서버 작업이 취소되었습니다 (Async Cancelled).")
            raise
        except Exception as e:
            logging.error(f"실행 중 예기치 않은 오류 발생: {e}")
            raise
        finally:
            # 정상 종료든 에러 종료든 반드시 실행되는 블록
            logging.info("=== MCP 서버가 안전하게 종료되었습니다 (Graceful Shutdown) ===")

if __name__ == "__main__":
    try:
        # Windows/Mac 공통 호환성을 위한 비동기 실행
        asyncio.run(main())
    except KeyboardInterrupt:
        # 터미널에서 Ctrl+C 등을 눌렀을 때
        logging.info("사용자 키보드 인터럽트로 종료됨")
    except Exception as e:
        # 그 외 실행조차 못하고 죽었을 때
        logging.critical(f"치명적 오류(Main): {e}")
