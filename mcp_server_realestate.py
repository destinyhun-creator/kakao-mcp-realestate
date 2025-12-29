import json
import httpx
from fastmcp import FastMCP
from typing import List, Dict, Optional

# SafeMove MCP 서버 초기화
mcp = FastMCP("SafeMove Real Estate Agent")

# -------------------------------------------------------------------------
# [도구 1] 부동산 등기부등본 리스크 분석 (예시 로직)
# -------------------------------------------------------------------------
@mcp.tool()
async def analyze_registry_risk(address: str, owner_name: str) -> str:
    """
    주소와 소유자명을 입력받아 등기부등본상의 기본적인 리스크(가압류, 근저당 등)를 분석합니다.
    실제 API 연동 전 단계의 모의 로직입니다.
    """
    # 실제로는 공공데이터 포털이나 대법원 인터넷 등기소 API를 연동해야 합니다.
    # 여기서는 예시로 안전/위험 시나리오를 반환합니다.
    
    print(f"DEBUG: Analyzing registry for {address}, Owner: {owner_name}")
    
    # 모의 로직: 주소에 '위험'이 포함되면 경고 리턴
    if "위험" in address:
        return json.dumps({
            "status": "WARNING",
            "message": "해당 물건은 근저당 설정 비율이 시세 대비 80%를 초과하여 '깡통전세' 위험이 있습니다.",
            "checklist": ["근저당 말소 조건 확인 필수", "보증보험 가입 불가능 가능성 높음"]
        }, ensure_ascii=False)
    
    return json.dumps({
        "status": "SAFE",
        "message": "소유권 관계가 명확하며, 선순위 근저당이 확인되지 않는 안전한 물건입니다.",
        "checklist": ["계약 시 신분증 진위 여부만 재확인", "특약사항에 전입신고 익일까지 권리변동 금지 조항 추가 권장"]
    }, ensure_ascii=False)

# -------------------------------------------------------------------------
# [도구 2] 전세사기 예방 체크리스트 제공
# -------------------------------------------------------------------------
@mcp.tool()
def get_safemove_checklist(contract_type: str) -> str:
    """
    계약 유형(전세/월세/매매)에 따른 필수 안전 체크리스트를 반환합니다.
    """
    common_checks = [
        "공인중개사 정상 등록 여부 확인 (국가공간정보포털)",
        "집주인 신분증 진위 확인 (정부24)",
        "건축물대장 위반건축물 등재 여부 확인"
    ]
    
    specific_checks = []
    if contract_type == "전세":
        specific_checks = [
            "전세보증금 반환보증 가입 가능 여부 사전 확인",
            "선순위 채권 금액 + 전세보증금이 주택가격의 70~80% 이하인지 확인",
            "국세/지방세 완납 증명서 요구"
        ]
    elif contract_type == "월세":
        specific_checks = [
            "소액임차인 최우선변제금 해당 여부 확인",
            "관리비 내역 세부 확인 (전기/수도 포함 여부)"
        ]
    
    result = {
        "contract_type": contract_type,
        "checklist": common_checks + specific_checks
    }
    return json.dumps(result, ensure_ascii=False, indent=2)

# -------------------------------------------------------------------------
# 서버 구동부 (수정된 부분)
# -------------------------------------------------------------------------
# 오류 원인: starlette_app = mcp.get_starlette_app() 메서드 부재
# 해결: mcp.run()을 사용하여 직접 서버를 구동합니다.
# Docker 컨테이너 등에서 실행 시 'host'를 '0.0.0.0'으로 설정해야 외부 접근이 가능합니다.

if __name__ == "__main__":
    print("🚀 SafeMove MCP 서버가 구동됩니다. (Target Port: 8000)")
    try:
        # transport='sse'는 SSE(Server-Sent Events) 방식을 사용함을 명시
        # host='0.0.0.0'은 모든 네트워크 인터페이스에서의 접속을 허용 (Docker 필수)
        mcp.run(transport="sse", port=8000, host="0.0.0.0")
    except Exception as e:
        print(f"❌ 서버 실행 중 치명적인 오류 발생: {e}")
