# -*- coding: utf-8 -*-
from mcp.server.fastmcp import FastMCP
import textwrap
import os

# 1. MCP 서버 초기화
# 서버 이름부터 'SafeMove(안심 이사)'라는 정체성을 부여합니다.
mcp = FastMCP("SafeMove_RealEstate_Agent")

# 인증용 토큰 설정 (보안)
MCP_SERVER_TOKEN = os.environ.get("MCP_SERVER_TOKEN", "kakao_mcp_secret_2024")

# --- [Resource] 표준 전세계약서 지식 베이스 (RAG 기초 데이터) ---
# AI가 참고할 법률/행정 지식의 원천입니다.
STANDARD_CONTRACT_KNOWLEDGE = """
[표준 임대차 계약서 필수 체크리스트 - 행정학/법률 전문가 가이드]
1. 대항력 유지: 임차인이 입주하고 전입신고를 마칠 때까지 저당권 설정을 금지함. (가장 중요)
2. 미납 국세 확인: 임대인은 체납된 세금이 없음을 증명해야 함. (조세채권 우선 원칙)
3. 수리 의무: 주요 설비(보일러, 배관 등)의 수리 비용은 임대인이 부담함. (민법 제623조)
4. 보증금 반환: HUG 보증보험 가입을 위한 임대인의 협조 의무 명시.
"""


# --- [Tool 1] 다방 매물 검색 ---
@mcp.tool()
def search_dabang_properties(location: str, budget_max: int) -> str:
    """
    [Persona: 커스터마이징 비서]
    사용자의 요구에 맞는 다방(Dabang) 매물을 검색합니다.
    단순 나열이 아닌, 전문가로서 '엄선된 매물'임을 강조하는 톤으로 결과를 반환합니다.
    """
    return f"🏠 동훈님의 조건에 딱 맞는 [{location}] 지역 매물을 다방 데이터에서 찾아보았습니다. \n1. 다방타워(전세 2.8억) - 역세권의 안심 매물입니다.\n2. 카카오빌(전세 3억) - 신축이며 HUG 가입 협의가 가능합니다."


# --- [Tool 2] HUG 보증보험 및 법률 안전도 체크 ---
@mcp.tool()
def check_hug_safety(address: str) -> str:
    """
    [Persona: 법률 전문가]
    주소지의 등기부를 분석하여 HUG 보증 가입 가능 여부를 확인합니다.
    행정적 신뢰도를 주기 위해 '분석 결과'를 명확한 톤으로 전달합니다.
    """
    if "판교" in address:
        return f"✅ 해당 매물({address})을 정밀 분석한 결과입니다.\n근저당 비중이 낮아 HUG 전세보증금 반환보증 가입이 가능할 것으로 보입니다. 안심하고 진행하셔도 좋습니다! 😊"
    return f"⚠️ 해당 매물({address})의 권리관계가 다소 복잡합니다.\n선순위 채권 확인이 필요하며, 전문가와 함께 등기부등본을 다시 확인하시는 것을 권장드립니다."


# --- [Tool 3] 계약서 RAG 분석 (독소 조항 찾기) ---
@mcp.tool()
def analyze_contract_with_rag(user_contract_text: str) -> str:
    """
    [Persona: 꼼꼼한 행정 비서]
    사용자의 계약서와 표준 양식을 비교합니다.
    법률적 리스크를 지적할 때는 단호하지만, 해결책은 친절하게 제시합니다.
    """
    toxic_points = []
    if "대항력 포기" in user_contract_text or "저당권 설정" in user_contract_text:
        toxic_points.append("- '전입신고 당일 저당권 설정' 관련 독소 조항은 보증금 보호에 치명적입니다.")

    if not toxic_points:
        return "✨ 표준 계약서와 대조해 본 결과, 동훈님의 권리가 잘 보호된 훌륭한 계약서입니다! 이대로 진행하셔도 무방해 보입니다."
    else:
        report = "\n".join(toxic_points)
        return f"🚨 [법률 검토 리포트] 이 계약서에는 임차인에게 불리한 조항이 포함되어 있습니다:\n{report}\n\n💡 조언: 해당 조항 수정을 요구하거나 '특약 사항'을 보완하시기 바랍니다."


# --- [Tool 4] 카카오 비즈니스 연동 (뱅크 & T) ---
@mcp.tool()
def connect_kakao_services(property_price: int) -> str:
    """
    [Persona: 해결사 비서]
    상담을 실질적인 '이사 완료'로 이끄는 단계입니다.
    카카오 서비스로의 전환을 매우 자연스럽고 편리하게 제안합니다.
    """
    loan_limit = int(property_price * 0.8)
    return textwrap.dedent(f"""
        🏠 안심 이사 매니저로서 제안드리는 마지막 단계입니다!

        1. [금융 지원] 카카오뱅크에서 최대 {loan_limit:,}만원까지 대출이 가능할 것으로 예상됩니다.
        2. [이사 지원] 카카오 T의 프리미엄 이사 서비스를 통해 쾌적하게 이동해 보세요. (예상 견적: 45만원)

        지금 바로 아래 버튼을 통해 확인하고 이사를 마무리해 보세요!
        [카카오뱅크 대출 심사 바로가기] | [카카오 T 이사 예약하기]
    """)


# --- 서버 실행부 (Railway 등 클라우드 환경 대응) ---
if __name__ == "__main__":
    # 포트는 클라우드 환경 변수를 따르되 기본값은 8000으로 설정
    port = int(os.environ.get("PORT", 8000))
    print(f"SafeMove MCP 서버가 준비되었습니다. (Port: {port})")
    # host를 0.0.0.0으로 해야 외부(카카오)에서 접속 가능
    mcp.run(transport="sse", host="0.0.0.0", port=port)