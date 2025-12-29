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
# 1. MCP 서버 및 도구 정의 (기능 완전 복구 버전)
# -------------------------------------------------------------------------
mcp = FastMCP("SafeMove Real Estate Agent")

@mcp.tool()
async def analyze_registry_risk(address: str, owner_name: str) -> str:
    """
    주소와 소유자명을 입력받아 등기부등본 및 건축물대장을 분석하여 리스크를 진단합니다.
    (다방 매물, 대법원 등기소, 국토부 데이터 연동 시뮬레이션)
    """
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
            "국세/지방세 완납 증명서 요구",
            "계약서 특약 내 '독소조항' 유무 확인 (카카오 OCR)"
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
        result["financial_guide"] = ["💰 카카오뱅크 월세 보증금 대출 상품 비교"]
    
    return json.dumps(result, ensure_ascii=False, indent=2)

# -------------------------------------------------------------------------
# 2. 서버 구동 (CORS 보안 해제 및 실행)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"🚀 SafeMove Server Starting... (Lib Version: {fastmcp.__version__})")
    
    try:
        # [핵심] MCP를 웹 앱으로 변환 (requirements.txt 업데이트 덕분에 가능)
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
        # 혹시라도 라이브러리 업데이트가 꼬였을 때를 대비한 비상 안전장치
        print("❌ 고급 모드 실행 실패. 기본 모드로 전환합니다.")
        mcp.run(transport="sse", port=8000, host="0.0.0.0")
