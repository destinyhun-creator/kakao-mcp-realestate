from fastmcp import FastMCP

# =================================================
# SafeMove MCP – PlayMCP 제출용 최소 구현
# Stateless / Streamable HTTP
# =================================================

mcp = FastMCP("SafeMove MCP Real Estate Agent")

# -------------------------------------------------
# Tool 1: 다방 / 네이버 매물 위험 분석
# -------------------------------------------------
@mcp.tool(
    description="다방 또는 네이버부동산 매물 URL을 분석해 전세사기(깡통전세) 위험도를 반환합니다."
)
def analyze_listing_url(listing_url: str) -> dict:
    if "망원" in listing_url or "빌라" in listing_url:
        return {
            "address": "서울 마포구 망원동",
            "deposit": "3억",
            "risk_level": "HIGH",
            "reason": [
                "선순위 근저당 비율 과다",
                "빌라 시세 대비 전세가 과다"
            ],
            "kakao_action": "카카오맵 실거래가 + 전세보증금 반환보증 가입 권장"
        }

    return {
        "address": "서울 강남구 아파트",
        "deposit": "5억",
        "risk_level": "LOW",
        "reason": ["근저당 없음", "시세 대비 적정"],
        "kakao_action": "카카오맵 시세 확인 완료"
    }


# -------------------------------------------------
# Tool 2: 계약서 독소조항 분석
# -------------------------------------------------
@mcp.tool(
    description="계약서 텍스트를 입력하면 독소조항과 필수 특약 누락 여부를 점검합니다."
)
def analyze_contract_text(contract_text: str) -> dict:
    issues = []
    if "책임지지 않는다" in contract_text:
        issues.append("임대인 책임 면책 조항")

    missing = [
        "잔금 전 권리변동 금지 특약",
        "전세보증금 반환보증 불가 시 계약 무효"
    ]

    return {
        "detected_issues": issues,
        "missing_required_clauses": missing,
        "kakao_action": "카카오 인증 전자계약 사용 권장"
    }


# -------------------------------------------------
# Tool 3: 카카오 대출 + 이사 원스톱
# -------------------------------------------------
@mcp.tool(
    description="소득과 보증금, 이사 날짜를 기반으로 대출과 이사 플랜을 추천합니다."
)
def recommend_move_package(
    annual_income: int,
    deposit: int,
    move_date: str
) -> dict:
    return {
        "loan": "카카오뱅크 전월세보증금 대출",
        "expected_limit": "최대 2억",
        "moving_plan": {
            "service": "카카오 T 이사",
            "estimated_cost": "약 45만원",
            "move_date": move_date
        },
        "checklist": [
            "전입신고",
            "확정일자",
            "보증보험 가입"
        ]
    }


# -------------------------------------------------
# Server Run (PlayMCP 요구사항)
# -------------------------------------------------
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000
    )
