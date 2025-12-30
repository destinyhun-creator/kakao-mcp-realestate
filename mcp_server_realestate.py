from fastmcp import FastMCP
import os

# 1. 서버 초기화 (이름은 간단하게 유지)
mcp = FastMCP("SafeMove")

# 2. 도구 정의: 복잡한 로직 제거, 순수 입력->출력 구조
# PlayMCP 호환성을 위해 return type을 dict로 고정하고, description을 간소화했습니다.

@mcp.tool()
def analyze_listing(url: str) -> dict:
    """Analyze real estate listing URL for risks."""
    # 실제로는 크롤링/LLM을 쓰지 않고, URL 패턴에 따라 모의(Mock) 데이터를 반환합니다.
    # PlayMCP는 이 서버가 '어떤 형식의 데이터'를 주는지 스키마를 확인하고 싶어하기 때문입니다.
    
    if "망원" in url or "빌라" in url:
        return {
            "status": "warning",
            "address": "서울 마포구 망원동 (예시 데이터)",
            "deposit_price": 300000000,
            "risk_score": 85,
            "risk_factors": [
                "전세가율 80% 초과 위험",
                "건축물대장상 위반건축물 표기",
                "선순위 근저당 설정 과다"
            ],
            "recommendation": "계약 보류 또는 반환보증 가입 필수 확인"
        }
    else:
        return {
            "status": "safe",
            "address": "서울 강남구 역삼동 (예시 데이터)",
            "deposit_price": 500000000,
            "risk_score": 10,
            "risk_factors": [],
            "recommendation": "안전 매물로 판단됨"
        }

@mcp.tool()
def check_contract_clauses(contract_text: str) -> dict:
    """Check rental contract text for toxic clauses."""
    # 계약서 텍스트에 특정 키워드가 있는지 확인하는 결정론적 로직
    
    toxic_keywords = ["임대인 면책", "수리비 임차인 부담", "보증금 반환 지연"]
    found_risks = [k for k in toxic_keywords if k in contract_text]
    
    if found_risks:
        return {
            "is_safe": False,
            "detected_risks": found_risks,
            "advice": "특약 사항 삭제 요청 필요"
        }
    else:
        return {
            "is_safe": True,
            "detected_risks": [],
            "advice": "표준 임대차 계약서 준수 확인됨"
        }

@mcp.tool()
def recommend_financial_package(income_monthly: int, deposit_needed: int) -> dict:
    """Recommend loan and moving services based on income."""
    # 수입과 보증금에 따른 단순 계산 로직
    
    max_loan = income_monthly * 12 * 5  # 단순 예시: 연봉의 5배
    
    if max_loan < deposit_needed:
        return {
            "feasibility": "low",
            "max_loan_amount": max_loan,
            "gap_amount": deposit_needed - max_loan,
            "recommended_product": "중소기업 청년 전세대출 (한도 확인 필요)"
        }
    else:
        return {
            "feasibility": "high",
            "max_loan_amount": max_loan,
            "recommended_product": "카카오뱅크 전월세 보증금 대출",
            "additional_services": ["카카오 T 이사 견적: 약 50만원", "입주 청소 할인 쿠폰"]
        }

# 3. 서버 실행 (SSE 방식)
if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
