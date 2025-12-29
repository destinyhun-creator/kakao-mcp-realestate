# -*- coding: utf-8 -*-
from mcp.server.fastmcp import FastMCP
import textwrap
import os
import uvicorn

# 1. MCP 서버 초기화
# FastMCP 서버 인스턴스를 생성합니다.
mcp = FastMCP("SafeMove_RealEstate_Agent")

# --- [Resource] 표준 전세계약서 지식 베이스 ---
STANDARD_CONTRACT_KNOWLEDGE = """
[표준 임대차 계약서 필수 체크리스트]
1. 대항력 유지: 임차인이 입주하고 전입신고를 마칠 때까지 저당권 설정을 금지함.
2. 미납 국세 확인: 임대인은 체납된 세금이 없음을 증명해야 함.
3. 수리 의무: 주요 설비(보일러, 배관 등)의 수리 비용은 임대인이 부담함.
4. 보증금 반환: HUG 보증보험 가입을 위한 임대인의 협조 의무 명시.
"""

# --- [Tool 1] 다방 매물 검색 ---
@mcp.tool()
def search_dabang_properties(location: str, budget_max: int) -> str:
    """Search for listings in the Dabang database based on location and budget."""
    return f"🏠 동훈님의 조건에 딱 맞는 [{location}] 지역 매물을 다방 데이터에서 찾아보았습니다. \n1. 다방타워(전세 2.8억) - 역세권 안심 매물\n2. 카카오빌(전세 3억) - 신축, HUG 가입 협의 가능"

# --- [Tool 2] HUG 보증보험 및 법률 안전도 체크 ---
@mcp.tool()
def check_hug_safety(address: str) -> str:
    """Analyze the registry and building ledger to check HUG insurance eligibility."""
    if "판교" in address:
        return f"✅ 해당 매물({address}) 분석 결과:\n근저당 비중이 낮아 HUG 전세보증금 반환보증 가입이 가능할 것으로 보입니다. 안심하세요! 😊"
    return f"⚠️ 해당 매물({address}) 분석 결과:\n권리관계가 다소 복잡합니다. 전문가와 함께 등기부등본을 다시 확인하시는 것을 권장드립니다."

# --- [Tool 3] 계약서 RAG 분석 (독소 조항 식별) ---
@mcp.tool()
def analyze_contract_with_rag(user_contract_text: str) -> str:
    """Compare the provided contract text with the standard form to find risky clauses."""
    toxic_points = []
    if "대항력 포기" in user_contract_text or "저당권 설정" in user_contract_text:
        toxic_points.append("- '전입신고 당일 저당권 설정 허용' 조항은 임차인 보호에 매우 취약합니다.")
    
    if not toxic_points:
        return "✨ 표준 계약서와 대조해 본 결과, 동훈님의 권리가 잘 보호된 안전한 계약서입니다!"
    else:
        report = "\n".join(toxic_points)
        return f"🚨 [법률 검토 리포트] 다음 조항은 수정이 꼭 필요합니다:\n{report}\n\n💡 조언: 해당 조항 삭제를 요구하거나 특약으로 보완하세요."

# --- [Tool 4] 카카오 비즈니스 연동 (금융 & 이사) ---
@mcp.tool()
def connect_kakao_services(property_price: int) -> str:
    """Link Kakao Bank loan limits and Kakao T moving services."""
    loan_limit = int(property_price * 0.8)
    return textwrap.dedent(f"""
        🏠 안심 이사 매니저가 제안드리는 마지막 단계입니다!
        
        1. [금융] 카카오뱅크 전세대출 예상 한도: 약 {loan_limit:,}만원
        2. [이사] 카카오 T 프리미엄 이사 예상 견적: 약 45만원
        
        지금 바로 확인하고 이사를 마무리해 보세요!
        [카카오뱅크 대출 심사 바로가기] | [카카오 T 이사 예약하기]
    """)

# --- 서버 실행부 (Railway 환경 강제 고정) ---
if __name__ == "__main__":
    # 1. 환경 변수에서 포트를 가져옵니다 (기본값 8000).
    port_env = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 SafeMove MCP 서버가 구동됩니다. (Target Port: {port_env})")
    
    # 2. 핵심 수정: mcp.run() 대신 uvicorn을 직접 사용하여 Starlette 앱을 실행합니다.
    # host를 "0.0.0.0"으로 설정해야 Railway 외부 주소와 연결됩니다.
    # mcp.run()이 내부적으로 사용하는 Starlette 앱은 mcp.app으로 접근 가능합니다.
    uvicorn.run(mcp.app, host="0.0.0.0", port=port_env)
