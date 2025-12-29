import json
import uvicorn
import fastmcp
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

# -------------------------------------------------------------------------
# 1. MCP 서버 및 도구 정의
# -------------------------------------------------------------------------
mcp = FastMCP("SafeMove Real Estate Agent")

@mcp.tool()
async def analyze_registry_risk(address: str, owner_name: str) -> str:
    """등기부등본 및 건축물대장 분석"""
    if "위험" in address:
        return json.dumps({
            "status": "WARNING",
            "message": "🚨 [위험 감지] 깡통전세 위험 (근저당 80% 초과)",
            "checklist": ["특약사항 필수", "보증보험 불가 가능성"]
        }, ensure_ascii=False)
    
    return json.dumps({
        "status": "SAFE",
        "message": "✅ [안전] 권리관계 깨끗함",
        "checklist": ["신분증 확인", "확정일자 진행"]
    }, ensure_ascii=False)

@mcp.tool()
def get_safemove_checklist(contract_type: str) -> str:
    """계약 유형별 필수 체크리스트"""
    return json.dumps({
        "type": contract_type,
        "checklist": ["공인중개사 등록 확인", "신분증 진위 확인", "특약 점검"]
    }, ensure_ascii=False)

# -------------------------------------------------------------------------
# 2. 서버 구동 (CORS 보안 해제 및 실행)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"🚀 SafeMove Server Starting... (Lib Version: {fastmcp.__version__})")
    
    try:
        # [핵심] MCP를 웹 앱으로 변환 (requirements.txt 덕분에 가능해진 기능)
        sse_app = mcp.get_asgi_app()

        async def health_check(request):
            return JSONResponse({"status": "online", "message": "SafeMove Agent Ready 🍌"})

        # [핵심] Player MCP 등 외부 접속을 허용하는 '보안 해제' 설정
        middleware = [
            Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        ]

        # 앱 통합
        app = Starlette(
            routes=[
                Route("/", health_check),
                Mount("/sse", sse_app),
            ],
            middleware=middleware
        )
        
        print("✅ 고급 모드(CORS Open) 실행 성공! Player MCP 접속 가능.")
        uvicorn.run(app, host="0.0.0.0", port=8000)

    except AttributeError:
        # 혹시라도 업데이트가 안 됐을 경우를 대비한 안전장치
        print("❌ 업데이트 실패. 기본 모드로 실행합니다. (Player MCP 접속 불가)")
        mcp.run(transport="sse", port=8000, host="0.0.0.0")
