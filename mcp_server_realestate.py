import json
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# -------------------------------------------------------------------------
# 1. MCP 서버 및 도구 정의 (기능 구현부)
# -------------------------------------------------------------------------
mcp = FastMCP("SafeMove Real Estate Agent")

@mcp.tool()
async def analyze_registry_risk(address: str, owner_name: str) -> str:
    """
    주소와 소유자명을 입력받아 등기부등본 및 건축물대장을 분석하여 리스크를 진단합니다.
    (다방 매물, 대법원 등기소, 국토부 데이터 연동 시뮬레이션)
    """
    print(f"DEBUG: Analyzing registry for {address}, Owner: {owner_name}")
    
    # 시뮬레이션 로직: '위험'이라는 단어가 주소에 있으면 경고 발생
    if "위험" in address or "빌라" in address:
        return json.dumps({
            "status": "WARNING",
            "risk_score": 85,
            "message": "🚨 [위험 감지] 깡통전세 위험이 높습니다 (근저당 비율 80% 초과).",
            "details": {
                "registry_check": "선순위 근저당 설정 과다",
                "owner_check": "최근 3개월 내 소유자 변경 이력 있음 (주의)",
                "building_check": "위반 건축물 등재 여부: 없음"
            },
            "recommendation": ["전세보증금 반환보증 가입 필수", "특약사항에 '잔금일 익일까지 권리변동 금지' 조항 추가"]
        }, ensure_ascii=False)
    
    return json.dumps({
        "status": "SAFE",
        "risk_score": 10,
        "message": "✅ [안전] 소유권 및 근저당 상태가 양호한 물건입니다.",
        "details": {
            "registry_check": "깨끗함 (근저당 없음)",
            "owner_check": "소유자 신원 일치",
            "building_check": "정상 건축물"
        },
        "recommendation": ["안심전세 대출 진행 가능", "확정일자 및 전입신고 즉시 진행"]
    }, ensure_ascii=False)

@mcp.tool()
def get_safemove_checklist(contract_type: str) -> str:
    """
    계약 유형(전세/월세)에 따른 필수 안전 체크리스트와 카카오뱅크 대출 상품을 추천합니다.
    """
    common_checks = [
        "공인중개사 정상 등록 여부 확인 (국가공간정보포털)",
        "신분증 진위 확인 (정부24 / 모바일 신분증)",
        "카카오톡 지갑으로 전자계약서 서명 가능 여부 확인"
    ]
    
    result = {
        "contract_type": contract_type,
        "checklist": common_checks,
        "financial_guide": []
    }

    if contract_type == "전세":
        result["checklist"].extend([
            "전세보증금 반환보증 가입 조건 사전 확인",
            "국세/지방세 완납 증명서 요구"
        ])
        result["financial_guide"] = [
            "💰 추천: 카카오뱅크 HF 전월세보증금 대출 (최대 2.22억)",
            "💰 청년: 카카오뱅크 청년 전월세보증금 대출 (만 34세 이하, 90% 한도)"
        ]
    elif contract_type == "월세":
        result["checklist"].extend([
            "소액임차인 최우선변제금 범위 확인",
            "관리비 세부 내역서 요청 (전기/수도 포함 여부)"
        ])
        result["financial_guide"] = ["💰 월세 보증금 대출 상품 비교"]
    
    return json.dumps(result, ensure_ascii=False, indent=2)

# -------------------------------------------------------------------------
# 2. 웹 브라우저 접속자를 위한 안내 페이지 (HTML)
# -------------------------------------------------------------------------
async def homepage(request):
    """
    심사위원이나 사용자가 브라우저로 접속했을 때 보여줄 안내 페이지입니다.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SafeMove - 카카오 AI 부동산 에이전트</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; 
                background-color: #FEE500; 
                color: #191919; 
                text-align: center; 
                padding: 40px; 
                margin: 0;
            }
            .container { 
                background: white; 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 40px; 
                border-radius: 20px; 
                box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
            }
            h1 { font-size: 28px; margin-bottom: 10px; color: #3C1E1E; }
            .icon { font-size: 80px; margin-bottom: 20px; }
            .badge { 
                background: #3C1E1E; 
                color: #FEE500; 
                padding: 5px 12px; 
                border-radius: 20px; 
                font-size: 14px; 
                font-weight: bold; 
            }
            .code-box { 
                background: #f4f4f4; 
                padding: 15px; 
                border-radius: 10px; 
                font-family: monospace; 
                word-break: break-all; 
                color: #d63031; 
                margin: 20px 0;
                font-weight: bold;
            }
            .desc { color: #555; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">🏠🍌</div>
            <span class="badge">SafeMove Agent</span>
            <h1>카카오 AI 부동산 보안관</h1>
            <p class="desc">
                반갑습니다! 저는 <b>SafeMove MCP 서버</b>입니다.<br>
                다방 매물 분석부터 카카오뱅크 대출 추천까지<br>
                안전한 이사를 책임집니다.
            </p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <h3>🔌 연결 방법 (Endpoint)</h3>
            <p class="desc">Claude Desktop 설정에 아래 주소를 등록하세요.</p>
            <div class="code-box">
                https://web-production-e7772.up.railway.app/sse
            </div>
            <p class="desc" style="font-size: 14px; color: #888;">
                * 상태: 🟢 정상 작동 중 (CORS Open)
            </p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

# -------------------------------------------------------------------------
# 3. Starlette 앱 설정 (CORS 보안 해제 및 라우팅)
# -------------------------------------------------------------------------

# (1) MCP 기능을 ASGI 앱으로 변환
sse_app = mcp.get_asgi_app()

# (2) 보안 미들웨어 설정 (외부 접속 허용)
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],     # 모든 도메인 허용
        allow_credentials=True,
        allow_methods=["*"],     # 모든 메서드 허용
        allow_headers=["*"],     # 모든 헤더 허용
    )
]

# (3) 메인 앱 생성 및 경로 연결
app = Starlette(
    routes=[
        Route("/", homepage),    # 기본 주소: 안내 페이지
        Mount("/sse", sse_app),  # /sse 주소: MCP 연결
    ],
    middleware=middleware
)

# -------------------------------------------------------------------------
# 4. 서버 구동
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 SafeMove Agent Server Running...")
    # Starlette 앱을 uvicorn으로 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)
