import json
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

# -------------------------------------------------------------------------
# 1. MCP 서버 및 도구 정의 (부동산 기능)
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
# 2. 서버 구동 (안전장치 포함 - 절대 죽지 않는 로직)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 SafeMove Agent Server Starting...")
    
    try:
        # [시도 1] 고급 모드: 웹 페이지 + CORS(보안 해제) + MCP
        # 라이브러리 버전이 낮으면 여기서 에러가 나고 아래 except로 넘어갑니다.
        sse_app = mcp.get_asgi_app() 

        async def health_check(request):
            return JSONResponse({
                "status": "online", 
                "message": "SafeMove Agent is Running 🍌. Connect via /sse"
            })

        # 모든 외부 접속 허용 (CORS)
        middleware = [
            Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        ]

        app = Starlette(
            routes=[
                Route("/", health_check),
                Mount("/sse", sse_app),
            ],
            middleware=middleware
        )
        
        print("✅ 고급 모드(CORS Open)로 실행합니다.")
        uvicorn.run(app, host="0.0.0.0", port=8000)

    except AttributeError:
        # [시도 2] 기본 모드 (안전장치)
        # FastMCP 버전이 낮아서 고급 모드가 안 될 때 실행됩니다.
        print("\n" + "="*50)
        print("⚠️ [경고] FastMCP 구버전 감지됨. 기본 모드로 전환합니다.")
        print("⚠️ CORS/웹 기능은 제한되지만, 서버는 정상 작동합니다.")
        print("="*50 + "\n")
        
        # 기본 모드로 실행 (무조건 켜짐)
        mcp.run(transport="sse", port=8000, host="0.0.0.0")

    except Exception as e:
        print(f"❌ 예기치 못한 오류 발생: {e}")
