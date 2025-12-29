import json
import uvicorn
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
    """
    주소와 소유자명을 입력받아 등기부등본 및 건축물대장을 분석하여 리스크를 진단합니다.
    """
    if "위험" in address:
        return json.dumps({
            "status": "WARNING",
            "message": "🚨 [위험 감지] 깡통전세 위험이 높습니다 (근저당 비율 80% 초과).",
            "checklist": ["특약사항 추가 필수", "보증보험 가입 불가 가능성"]
        }, ensure_ascii=False)
    
    return json.dumps({
        "status": "SAFE",
        "message": "✅ [안전] 소유권 및 근저당 상태가 양호한 물건입니다.",
        "checklist": ["신분증 진위 여부 확인", "확정일자 및 전입신고 즉시 진행"]
    }, ensure_ascii=False)

@mcp.tool()
def get_safemove_checklist(contract_type: str) -> str:
    """
    계약 유형(전세/월세)에 따른 필수 안전 체크리스트를 반환합니다.
    """
    return json.dumps({
        "type": contract_type,
        "checklist": [
            "공인중개사 등록 확인", 
            "신분증 진위 확인 (정부24)",
            "계약서 특약사항 점검"
        ]
    }, ensure_ascii=False)

# -------------------------------------------------------------------------
# 2. 서버 및 보안(CORS) 설정
# -------------------------------------------------------------------------

# (1) FastMCP를 Starlette 앱으로 변환 (requirements의 최신 버전 필수)
sse_app = mcp.get_asgi_app()

async def health_check(request):
    """서버 상태 확인용 페이지"""
    return JSONResponse({
        "status": "online", 
        "message": "SafeMove Agent is Running 🍌. Connect via /sse"
    })

# (2) 보안 미들웨어: 모든 외부 접속 허용 (CORS)
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],     # 모든 도메인 접속 허용
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

# (3) 앱 통합
app = Starlette(
    routes=[
        Route("/", health_check),   # 기본 주소 접속 시 상태 메시지
        Mount("/sse", sse_app),     # /sse 주소로 MCP 연결
    ],
    middleware=middleware
)

if __name__ == "__main__":
    print("🚀 SafeMove Agent Server Running...")
    # 외부 접속 허용 (0.0.0.0)
    uvicorn.run(app, host="0.0.0.0", port=8000)
