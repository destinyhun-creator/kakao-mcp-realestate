from fastmcp import FastMCP

# ✅ stateless 옵션 없음
mcp = FastMCP(
    name="SafeMove MCP Real Estate Agent"
)

# -------------------------------------------------
# Tool 1: 부동산 위험도 분석 (데모)
# -------------------------------------------------
@mcp.tool()
def analyze_real_estate(address: str, price: int) -> dict:
    """
    Analyze real estate risk (demo).
    """
    risk = "LOW"
    reason = "No major risk detected."

    if price >= 300_000_000:
        risk = "MEDIUM"
        reason = "High price area, registry check recommended."

    return {
        "address": address,
        "price": price,
        "risk_level": risk,
        "summary": reason,
        "data_source": "demo",
    }

# -------------------------------------------------
# Tool 2: 계약서 독소조항 점검 (데모)
# -------------------------------------------------
@mcp.tool()
def contract_clause_check(contract_text: str) -> dict:
    warnings = []

    if "책임 없음" in contract_text:
        warnings.append("임대인 책임 면제 조항 의심")

    if "보증금 반환 불가" in contract_text:
        warnings.append("보증금 반환 관련 위험 문구")

    return {
        "warnings": warnings,
        "safe": len(warnings) == 0,
        "note": "Demo legal analysis",
    }

# -------------------------------------------------
# Tool 3: 전세대출 & 이사 가이드 (데모)
# -------------------------------------------------
@mcp.tool()
def move_and_loan_guide(income: int) -> dict:
    return {
        "loan_available": income >= 30_000_000,
        "bank": "KakaoBank (demo)",
        "moving_checklist": [
            "전입신고",
            "확정일자 받기",
            "전세보증보험 확인",
            "이사 당일 계량기 촬영",
        ],
    }

# -------------------------------------------------
# 🚀 Run (PlayMCP 인식 포인트)
# -------------------------------------------------
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",  # ⭐ 핵심
        host="0.0.0.0",
        port=8000,
        path="/mcp",                  # ⭐ 핵심
    )
