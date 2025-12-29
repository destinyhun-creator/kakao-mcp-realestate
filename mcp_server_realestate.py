from fastmcp import FastMCP
import os

mcp = FastMCP(
    name="SafeMove Real Estate Agent",
    version="1.0.0",
    description="MCP 기반 안심 부동산 전세사기 예방 AI 에이전트"
)

@mcp.tool()
async def analyze_registry_risk(address: str, owner_name: str) -> dict:
    """
    다방 매물 + 공공데이터 기반 전세사기 위험도 분석 (샘플)
    """
    if "빌라" in address or "망원" in address:
        return {
            "status": "WARNING",
            "risk_score": 82,
            "message": "깡통전세 위험 가능성 높음",
            "details": {
                "registry": "선순위 근저당 과다",
                "ownership": "최근 소유권 변경",
                "building": "정상"
            },
            "recommendation": [
                "전세보증금 반환보증 가입",
                "특약: 잔금일까지 권리변동 금지"
            ]
        }

    return {
        "status": "SAFE",
        "risk_score": 12,
        "message": "권리관계 안전",
        "details": {
            "registry": "근저당 없음",
            "ownership": "소유자 일치",
            "building": "정상"
        }
    }

@mcp.tool()
def safemove_checklist(contract_type: str) -> dict:
    """
    전세/월세 계약 체크리스트 + 금융 연계
    """
    base = [
        "공인중개사 등록 여부 확인",
        "임대인 신분증 확인",
        "전자계약 가능 여부"
    ]

    if contract_type == "전세":
        return {
            "type": "전세",
            "checklist": base + [
                "전세보증금 반환보증 확인",
                "국세·지방세 완납 증명",
                "특약 OCR 검증"
            ],
            "finance": [
                "카카오뱅크 HF 전월세보증금 대출",
                "카카오뱅크 청년 전월세 대출"
            ]
        }

    return {
        "type": "월세",
        "checklist": base + [
            "관리비 포함 내역 확인",
            "소액임차인 최우선변제 확인"
        ],
        "finance": ["카카오뱅크 월세보증금 대출"]
    }

if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
