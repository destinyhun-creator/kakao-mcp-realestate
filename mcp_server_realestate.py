import os
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# =================================================================
# 1. RAG 지식 베이스 (표준임대차계약서 & 주택임대차보호법 학습 데이터)
# =================================================================
LEGAL_KNOWLEDGE = """
[전세사기 예방 필수 지식 & 표준계약서 핵심]
1. [필수 특약 1] "임대인은 잔금 지급일 다음 날까지 임차주택에 저당권 등 담보권을 설정하지 않는다." (위반 시 즉시 해지 및 손해배상)
2. [필수 특약 2] "임대인의 국세/지방세 체납이 확인되거나, 전세반환보증 가입이 불가능한 경우 계약을 무효로 하고 계약금을 즉시 반환한다."
3. [대항력] 전입신고와 점유를 마친 '다음 날 0시'부터 효력이 발생하므로, 당일 근저당 설정 여부를 반드시 확인해야 함.
4. [독소조항 예시] "시설물 파손 시 임차인이 무조건 원상복구한다" (자연 마모는 제외한다는 문구 필요), "계약 후 임대인이 변경되어도 승계한다" (보증금 반환 거부 가능성 주의)
"""

# =================================================================
# 2. MCP 서버 초기화 (에러 방지를 위해 인자 최소화)
# =================================================================
mcp = FastMCP("SafeMove Real Estate Agent")

# =================================================================
# 3. AI 엔진 (OpenAI를 '카카오 AI'처럼 튜닝)
# =================================================================
async def call_kakao_brain(system_role: str, user_query: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # 키 없을 때 (데모용 폴백)
    if not api_key:
        return "[DEMO] API 키가 없습니다. 하지만 로직은 정상 작동 중입니다."

    final_system_prompt = f"""
    당신은 '카카오(Kakao)'의 부동산 안심 AI 에이전트 'SafeMove'입니다.
    
    [역할]
    1. 사용자의 내 집 마련/전세 계약을 돕는 든든한 파트너입니다.
    2. 말투는 "해요체"를 쓰며, 친절하고 명확하게 설명하세요. (이모지 활용 😊)
    3. 해결책 제안 시, 반드시 '카카오 생태계(뱅크, T, 맵, 페이)'를 연결해서 제안하세요.
    
    [보유 지식 - RAG]
    {LEGAL_KNOWLEDGE}
    
    {system_role}
    """

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": final_system_prompt},
                        {"role": "user", "content": user_query},
                    ],
                    "temperature": 0.3 # 법률/금융 정보이므로 보수적으로 설정
                },
                timeout=20,
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI 연결 중 오류가 발생했습니다: {str(e)}"

# =================================================================
# Tool 1: 다방 URL 분석 & 깡통전세 판독
# =================================================================
@mcp.tool(description="다방/네이버부동산 매물 URL을 입력하면 등기부등본과 건축물대장을 가상으로 크롤링하여 위험도를 분석합니다.")
async def analyze_listing_url(url: str) -> str:
    """
    URL에서 매물 정보를 추출하고 공공데이터를 조회하여 리포트를 작성합니다.
    """
    # 1. 가상의 크롤링 로직 (URL 키워드로 시뮬레이션)
    # 실제로는 여기서 Python Selenium/BeautifulSoup이 돌거나 공공데이터 API를 찌릅니다.
    if "빌라" in url or "망원" in url:
        address = "서울시 마포구 망원동 456-78 (다세대주택)"
        price = 30000 # 3억
        # 위험 시나리오 데이터
        public_data = {
            "등기부": "선순위 근저당 2억 5천만원 설정 (매매가 대비 83% - 깡통전세 위험)",
            "건축물대장": "위반건축물 등재 (불법 확장, 전세대출 불가)",
            "소유자": "최근 1개월 내 변경됨 (법인)"
        }
        is_danger = True
    else:
        address = "서울시 강남구 역삼동 123-45 (아파트)"
        price = 50000 # 5억
        # 안전 시나리오 데이터
        public_data = {
            "등기부": "을구 깨끗함 (근저당 0원)",
            "건축물대장": "적법 건축물",
            "소유자": "5년 거주 개인 1주택자"
        }
        is_danger = False

    # 2. AI 분석 요청
    prompt = f"""
    [분석 요청]
    사용자가 보고 있는 매물 URL: {url}
    추출된 주소: {address}
    보증금: {price}만원
    
    [공공데이터 조회 결과]
    - 등기부등본: {public_data['등기부']}
    - 건축물대장: {public_data['건축물대장']}
    - 소유자 정보: {public_data['소유자']}
    
    위 데이터를 바탕으로 이 집이 안전한지 위험한지 분석해주고,
    주변 시세와 비교(가상)해서 적정 가격인지도 멘트해줘.
    """
    
    return await call_kakao_brain("당신은 권리분석 전문가입니다.", prompt)


# =================================================================
# Tool 2: 계약서 OCR 독소조항 탐지 (RAG)
# =================================================================
@mcp.tool(description="계약서 사진에서 추출한 텍스트를 입력하면, 독소조항을 찾고 필수 특약 누락을 경고합니다.")
async def analyze_contract_ocr(ocr_text: str) -> str:
    """
    Vision API로 추출된 텍스트를 분석합니다.
    """
    prompt = f"""
    [사용자 계약서 내용 (OCR 추출)]
    "{ocr_text}"
    
    [임무]
    1. 위 내용이 당신이 알고 있는 '표준임대차계약서' 및 '필수 특약'과 비교했을 때 무엇이 빠졌는지 찾아내세요.
    2. 세입자에게 불리한 독소조항(수리비 전가, 반환 지연 등)이 숨어있는지 탐지하세요.
    3. 수정 제안 문구를 구체적으로 써주세요.
    """
    
    return await call_kakao_brain("당신은 부동산 전문 변호사입니다.", prompt)


# =================================================================
# Tool 3: 카카오 원스톱 서비스 (대출/이사/청소)
# =================================================================
@mcp.tool(description="소득, 보증금, 이사날짜를 입력하면 카카오뱅크 대출과 이사/청소 견적을 한 번에 제안합니다.")
async def kakao_one_stop_service(annual_income_manwon: int, target_deposit_manwon: int, move_date: str) -> str:
    """
    AI 판단 없이 로직 기반으로 정확한 금융 상품과 서비스를 매칭합니다.
    """
    # 1. 대출 상품 매칭 로직
    if annual_income_manwon <= 3500 and target_deposit_manwon <= 20000:
        bank_product = "🏦 카카오뱅크 청년 전월세보증금 대출 (최저 연 3.4%~)"
        limit = "보증금의 90%까지"
    elif annual_income_manwon > 10000:
        bank_product = "🏦 카카오뱅크 전월세보증금 대출 (일반)"
        limit = "최대 2.22억원"
    else:
        bank_product = "🏦 카카오뱅크 HF 전월세보증금 대출"
        limit = "보증금의 80%까지"

    # 2. 결과 생성 (AI가 예쁘게 포장)
    prompt = f"""
    [사용자 정보]
    - 연소득: {annual_income_manwon}만원
    - 목표 보증금: {target_deposit_manwon}만원
    - 이사 희망일: {move_date}
    
    [시스템 추천 결과]
    - 금융: {bank_product} (한도: {limit})
    - 이사: 🚛 카카오 T 이사 (예상 견적: 20평 기준 80만원, 파손 책임 보상)
    - 청소: ✨ 카카오 입주청소 파트너 (예상 견적: 평당 1.2만원)
    
    위 추천 결과를 바탕으로, 사용자가 '카카오 앱' 하나로 이 모든 걸 해결할 수 있다는 점을 강조해서 
    원스톱 플랜을 브리핑해줘. 이사 날짜에 맞춰서 무엇을 미리 신청해야 하는지도 알려줘.
    """
    
    return await call_kakao_brain("당신은 카카오뱅크 & 라이프 플래너입니다.", prompt)


# =================================================================
# 서버 실행 (Railway 배포용 설정)
# =================================================================
if __name__ == "__main__":
    # Railway가 할당해주는 PORT 환경변수를 받아옵니다.
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 SafeMove(Kakao AI) Agent running on port {port}...")
    
    # SSE 모드로 실행 (외부 접속 허용)
    mcp.run(transport="sse", host="0.0.0.0", port=port)
