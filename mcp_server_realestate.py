from fastmcp import FastMCP

mcp = FastMCP(
    name="SafeMove MCP Real Estate Agent",
    stateless=True,              # ⭐ 중요
)

# -----------------------------
# Tool 1: 부동산 위험도 분석 (데모)
# -----------------------------
@mcp.tool()
def analyze_real_estate(address: str, price: int) -> dict:
    """
    Analyze real estate risk based on address and price.
    (Demo version for PlayMCP submission)
    """
    risk_level = "LOW"
    reason = "No critical issues found in registry or building records."

    if price > 250_000_000:
        risk_level = "MEDIUM"
        reason = "Price is relatively high; verify mortgage and ownership."

    return {
        "address": address,
        "price": price,
        "risk_level": risk_level,
        "summary": reason,
        "note": "Demo analysis (no external crawling)",
    }

# -----------------------------
# Tool 2: 계약서 독소조항 점검 (데모)
# -----------------------------
@mcp.tool()
def contract_clause_check(text: str) -> dict:
    """
    Detect risky clauses in rental contract text.
    """
    warnings = []

    if "책임 없음" in text:
        warnings.append("임대인 책임 면제 조항 의심")

    if "보증금 반환 불가" in text:
        warnings.append("보증금 반환 관련 위험 문구")

    return {
        "warnings": warnings,
        "safe": len(warnings) == 0,
        "note": "Demo clause analysis",
    }

# -----------------------------
# Tool 3: 전세대출 & 이사 체크리스트 (데모)
# -----------------------------
@mcp.tool()
def move_and_loan_guide(income: int) -> dict:
    """
    Provide demo loan eligibility and moving checklist.
    """
    eligible = income >= 30_000_000

    return {
        "loan_eligible": eligible,
        "bank": "KakaoBank (demo)",
        "moving_checklist": [
            "전입신고",
            "확정일자 받기",
            "전세보증보험 확인",
            "이사 당일 계량기 사진 촬영",
        ],
    }

# -----------------------------
# 🚀 Run (Streamable HTTP)
# -----------------------------
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",  # ⭐⭐⭐ 이게 핵심
        host="0.0.0.0",
        port=8000,
        path="/mcp",                  # ⭐ PlayMCP가 찾는 엔드포인트
    )
