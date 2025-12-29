import os
import json
from fastmcp import FastMCP

# MCP 서버 생성
mcp = FastMCP(
    name="SafeMove Real Estate Agent",
    description="부동산 계약 리스크 분석 및 전세사기 예방 AI 에이전트"
)

# ===============================
# Tool 1: 등기부 위험 분석
# ===============================
@mcp.tool()
def analyze_registry_risk(address: str, owner_name: str) -> str:
    if "빌라" in address or "망원" in address:
        result = {
            "status": "WARNING",
            "risk_score": 85,
            "reason": "선순위 근저당 설정 가능성 높음",
            "advice": "등기부등본 을구를 반드시 확인하세요."
        }
    else:
        result = {
            "status": "SAFE",
            "risk_score": 10,
            "advice": "현재 정보 기준으로 큰 위험은 없어 보입니다."
        }

    return json.dumps(result, ensure_ascii=False, indent=2)

# ===============================
# Tool 2: 계약 체크리스트
# ===============================
@mcp.tool()
def safemove_checklist(contract_type: str) -> str:
    base = ["공인중개사 등록 확인", "신분증 진위 확인"]

    if contract_type == "전세":
        checklist = base + [
            "등기부등본 을구 확인",
            "전세보증금 반환보증 가입 여부"
        ]
    else:
        checklist = base + [
            "관리비 체납 여부",
            "최우선변제금 확인"
        ]

    return json.dumps({
        "contract_type": contract_type,
        "checklist": checklist
    }, ensure_ascii=False, indent=2)

# ===============================
# Tool 3: 자유 상담
# ===============================
@mcp.tool()
def real_estate_chat(question: str) -> str:
    return f"부동산 전문가 답변: {question}에 대해 계약 전 리스크를 꼼꼼히 확인하세요."

# ===============================
# 서버 실행 (PlayMCP 필수)
# ===============================
if __name__ == "__main__":
    # ⚠️ /sse 경로 + SSE 방식
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        path="/sse"
    )
