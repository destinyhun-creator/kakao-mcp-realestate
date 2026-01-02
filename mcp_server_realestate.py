import uvicorn
from mcp.server.fastapi import FastMCP
import os
import re

# 1. MCP 서버 초기화 (이름: SafeMove Real Estate Agent)
# dependencies: mcp, uvicorn, fastapi
mcp = FastMCP("SafeMove Real Estate Agent")

# ==========================================
# 🏠 Tool 1: 부동산 깡통전세 위험도 분석
# ==========================================
@mcp.tool()
def analyze_real_estate(address: str, deposit_price: int, market_price_estimate: int = 0) -> str:
    """
    주소와 보증금 가격을 입력받아 '깡통전세' 위험도를 분석합니다.
    공공데이터(등기부등본, 건축물대장) 모의 분석 결과를 반환합니다.

    Args:
        address: 부동산 주소 (예: 서울시 마포구 망원동 123-4)
        deposit_price: 전세/월세 보증금 (단위: 원)
        market_price_estimate: (선택) 주변 시세 추정치. 입력 없으면 자동 추산.
    """
    # 실제 공공데이터 API 연동 전, 데모를 위한 로직입니다.
    
    # 시세가 입력되지 않았으면 보증금의 1.2배로 가정 (위험군 테스트)
    estimated_price = market_price_estimate if market_price_estimate > 0 else int(deposit_price * 1.1)
    
    # 깡통전세 비율 계산 (보증금 / 매매가)
    debt_ratio = (deposit_price / estimated_price) * 100
    
    risk_level = "안전"
    warning_msg = "특이사항 없습니다. 안심하고 계약하셔도 좋습니다."
    
    # 위험도 로직
    if debt_ratio >= 80:
        risk_level = "위험 (깡통전세 주의)"
        warning_msg = f"매매가 대비 전세가율이 {debt_ratio:.1f}%로 매우 높습니다. 보증금 반환이 어려울 수 있습니다."
    elif debt_ratio >= 70:
        risk_level = "주의"
        warning_msg = "전세가율이 다소 높습니다. 전세보증보험 가입이 필수입니다."

    # 등기부등본 시뮬레이션 (특정 키워드가 주소에 있으면 근저당 설정된 것으로 간주)
    registry_notes = []
    if "빌라" in address or "다세대" in address:
        registry_notes.append("⚠️ [갑구] 소유자: 신탁회사 신탁등기 여부 확인 필요")
    if debt_ratio >= 80:
        registry_notes.append(f"⚠️ [을구] 근저당권 설정: 채권최고액 {int(estimated_price * 0.3):,}원 존재 (가정)")

    result = {
        "분석_대상": address,
        "전세가율": f"{debt_ratio:.1f}%",
        "위험도": risk_level,
        "진단_결과": warning_msg,
        "등기부_체크포인트": registry_notes,
        "건축물대장_체크": "위반건축물 표기 없음 (정상)"
    }

    return str(result)

# ==========================================
# 📜 Tool 2: 계약서 OCR 독소조항 탐지
# ==========================================
@mcp.tool()
def check_contract_toxic_clauses(contract_text: str) -> str:
    """
    계약서 내용(OCR 추출 텍스트)을 분석하여 독소조항이나 필수 특약 누락을 찾아냅니다.

    Args:
        contract_text: 계약서 사진에서 추출한 텍스트 내용
    """
    warnings = []
    required_clauses = [
        "전세반환보증", 
        "근저당", 
        "대항력", 
        "임차권등기"
    ]
    
    # 1. 독소조항 탐지 (불리한 문구)
    toxic_patterns = [
        (r"보증금.*반환.*책임.*없음", "🚨 '보증금 반환 책임 회피' 조항이 발견되었습니다. 절대 동의하면 안 됩니다."),
        (r"시설물.*수리.*임차인.*부담", "⚠️ 시설물 수리 비용을 임차인에게 전가하는 조항이 있습니다. (통상적 마모는 임대인 부담입니다)"),
        (r"계약.*중도.*해지.*불가", "⚠️ 중도 해지 불가 조항은 법적으로 효력이 제한될 수 있으나 불리할 수 있습니다.")
    ]

    for pattern, msg in toxic_patterns:
        if re.search(pattern, contract_text):
            warnings.append(msg)

    # 2. 필수 특약 누락 확인
    missing = []
    for req in required_clauses:
        if req not in contract_text:
            missing.append(req)

    # 결과 생성
    analysis_summary = "✅ 계약서가 전반적으로 안전합니다."
    if warnings or missing:
        analysis_summary = "❌ 계약서 수정이 강력히 권장됩니다."

    result = {
        "종합_진단": analysis_summary,
        "발견된_독소조항": warnings if warnings else ["발견되지 않음"],
        "누락된_필수키워드": missing if missing else ["모두 포함됨"],
        "카카오_조언": "필수 특약이 누락되었다면 '전세보증보험 가입 불가 시 계약 무효' 특약을 반드시 넣어주세요."
    }
    
    return str(result)

# ==========================================
# 💰 Tool 3: 카카오뱅크 대출 & 이사 매칭
# ==========================================
@mcp.tool()
def guide_loan_and_move(annual_income: int, target_deposit: int) -> str:
    """
    사용자의 연소득과 목표 보증금을 기반으로 카카오뱅크 대출 상품을 추천하고 이사 체크리스트를 제공합니다.

    Args:
        annual_income: 연소득 (단위: 원)
        target_deposit: 목표 전세 보증금 (단위: 원)
    """
    
    # 대출 한도 단순 계산 (예: 연소득의 3.5배 ~ 4배)
    max_loan_limit = annual_income * 3.5
    if max_loan_limit > 222_000_000: # 청년 전월세 기준 상한선 예시
        max_loan_limit = 222_000_000
        
    can_afford = max_loan_limit >= (target_deposit * 0.8) # 보증금의 80% 대출 가정
    
    recommendation = {
        "추천_상품": "카카오뱅크 청년 전월세보증금 대출",
        "예상_금리": "최저 연 3.45% ~",
        "대출_가능_한도": f"{int(max_loan_limit/10000)}만원 예상",
        "판정": "대출 가능 승인 확률 높음 ✅" if can_afford else "한도 부족 가능성 있음 ⚠️ (추가 자금 필요)"
    }
    
    checklist = [
        "D-30: 현재 집주인에게 이사 통보",
        "D-14: 이사짐 센터 견적 비교 (SafeMove 파트너스 추천)",
        "D-7: 공과금 정산 및 가스 철거 예약",
        "D-Day: 잔금 이체 및 전입신고/확정일자 (오전 9시 즉시)"
    ]

    result = {
        "금융_솔루션": recommendation,
        "이사_체크리스트": checklist,
        "SafeMove_OneStop": "대출 신청부터 이사 견적까지 앱에서 한 번에 신청하시겠습니까?"
    }

    return str(result)

# Railway 등 배포 환경을 위한 설정
if __name__ == "__main__":
    # Railway가 제공하는 PORT 환경변수를 사용, 없으면 8080 (중요!)
    port = int(os.environ.get("PORT", 8080))
    # 0.0.0.0으로 열어야 외부 접속 가능
    mcp.run(transport='sse', port=port, host='0.0.0.0')
