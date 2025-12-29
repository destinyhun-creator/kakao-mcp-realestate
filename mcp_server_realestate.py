from fastmcp import FastMCP
import os

# ------------------------------------------------------------------
# MCP 서버 생성 (description ❌)
# ------------------------------------------------------------------
mcp = FastMCP(
    name="SafeMove Real Estate Agent",
    version="1.0.0"
)

# ------------------------------------------------------------------
# Tool 1: 등기부 / 건축물 위험도 분석
# ------------------------------------------------------------------
@mcp.tool()
async def analyze_registry_risk(address: str, owner_name: str) -> dict:
    """
    [부동산 위험도 분석 Agent]
    - 다방 매물 주소 기반
    - 등기부등본 / 건축물대장 리스크를 시뮬레이션 분석
    - 깡통전세, 선순위 근저당 위험 탐지
    """

    if "빌라" in address or "망원" in address:
        return {
            "status": "WARNING",
            "risk_score": 82,
            "summary": "깡통전세 위험 가능성 높음",
            "details": {
                "registry": "선순위 근저당 과다",
                "ownership": "최근 소유권 변경 이력",
                "building": "정상 건축물"
            },
            "recommendation": [
                "전세보증금 반환보증 필수",
                "특약: 잔금일까지 권리변동 금지"
            ]
        }

    return {
        "status": "SAFE",
        "risk_score": 12,
        "summary": "권리관계 안전",
        "details": {
            "registry": "근저당 없음",
            "ownership": "소유자 일치",
            "building": "정상"
        },
        "recommendation": [
            "확정일자 및 전입신고 즉시 진행"
        ]
    }

# ------------------------------------------------------------------
# Tool 2: 계약 체크리스트 + 금융 연계
# ------------------------------------------------------------------
@mcp.tool()
def safemove_checklist(contract_type: str) -> dict:
    """
    [전·월세 계약 안전 체크리스트 Agent]
    - 계약 유형에 따른 필수 확인사항
    - 카카오뱅크 전월세 대출 연계 가이드
    """

    base = [
        "공인중개사 등록 여부 확인",
        "임대인 신분증 진위 확인",
        "전자계약 가능 여부 확인"
    ]

    if contract_type == "전세":
        return {
            "type": "전세",
            "checklist": base + [
                "전세보증금 반환보증 가입 가능 여부",
                "국세·지방세 완납 증명서",
                "계약서 특약 OCR 검증"
            ],
            "finance": [
                "카카오뱅크 HF 전월세보증금 대출",
                "카카오뱅크 청년 전월세 대출"
            ]
        }

    return {
        "type": "월세",
        "checklist": base + [
            "관리비 포함 항목 확인",
            "소액임차인 최우선변제 범위 확인"
        ],
        "finance": [
            "카카오뱅크 월세보증금 대출"
        ]
    }

# ------------------------------------------------------------------
# 서버 실행 (Railway 호환)
# ------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
