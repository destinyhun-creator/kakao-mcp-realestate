import os
import json
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# =================================================
# 1. MCP 서버 정의 (FastMCP - SSE 모드용)
# =================================================
mcp = FastMCP(
    name="SafeMove Real Estate Agent",
    description="전세사기 예방, 계약서 분석, 대출/이사 추천을 수행하는 AI 에이전트",
    port=8000
)

# =================================================
# 2. 헬퍼 함수: LLM 호출 (OpenAI Only)
# =================================================
async def call_llm(system_prompt: str, user_prompt: str) -> str:
    """OpenAI API를 사용하여 분석 결과를 생성합니다."""
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # 키가 없을 때 (해커톤 시연용 더미 응답)
    if not api_key:
        return "[데모 모드] API 키가 없습니다. 하지만 분석 로직은 정상 작동 중입니다. (실제 연결 시 AI 답변이 생성됩니다)"

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
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=20,
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI 분석 중 오류 발생: {str(e)}"

# =================================================
# Tool 1: 매물 위험도 분석 (등기부 + 건축물대장)
# =================================================
@mcp.tool()
async def analyze_property_risk(address: str, deposit_amount: int) -> str:
    """
    주소와 보증금을 입력받아 깡통전세 및 위반건축물 여부를 분석합니다.
    실제로는 대법원 등기소/세움터 API를 크롤링하는 로직이 들어갑니다.
    """
    
    # [시나리오] 망원동 빌라는 위험하다고 가정 (데모용 로직)
    is_danger = "망원" in address or "빌라" in address
    
    if is_danger:
        risk_level = "❌ 위험 (계약 권장하지 않음)"
        details = (
            "- 등기부등본: 선순위 근저당 2.5억 설정됨 (매매가 대비 80% 초과)\n"
            "- 건축물대장: '위반건축물' 등재 (전세대출 불가 가능성 높음)\n"
            "- 소유자: 최근 3개월 내 소유권 변경 이력 있음 (바지사장 의심)"
        )
    else:
        risk_level = "✅ 안전 (계약 가능)"
        details = (
            "- 등기부등본: 근저당 없음 (깨끗함)\n"
            "- 건축물대장: 적법 건축물\n"
            "- 소유자: 5년 이상 거주 중인 1주택자"
        )

    # AI에게 최종 리포트 작성 요청
    prompt = f"""
    주소: {address}
    보증금: {deposit_amount}만원
    분석 데이터: {details}
    
    위 데이터를 바탕으로 사용자에게 위험도를 경고하고, 구체적인 행동 가이드를 알려줘.
    """
    
    ai_advice = await call_llm("너는 전세사기 예방 전문가다.", prompt)
    
    return f"[{risk_level}]\n\n{details}\n\n💡 전문가 조언:\n{ai_advice}"

# =================================================
# Tool 2: 계약서 OCR 및 독소조항 분석
# =================================================
@mcp.tool()
async def analyze_contract_ocr(contract_text: str) -> str:
    """
    (Vision 기능 대체) OCR로 추출된 계약서 텍스트나 특약 사항을 분석하여 
    독소조항이나 필수 특약 누락을 찾아냅니다.
    """
    
    # 필수 특약 체크리스트
    required_clauses = [
        "전세보증금 반환보증 가입 불가 시 계약 무효",
        "잔금 익일까지 등기부 권리변동 금지",
        "임대인의 국세/지방세 완납 증명"
    ]
    
    prompt = f"""
    사용자가 입력한 계약서 특약 내용:
    "{contract_text}"
    
    1. 위 내용에 세입자에게 불리한 독소조항이 있는지 찾아줘.
    2. 다음 필수 특약이 포함되어 있는지 확인해줘: {', '.join(required_clauses)}
    3. 빠진 내용이 있다면 추가하라고 강력하게 조언해줘.
    """
    
    return await call_llm("너는 부동산 법률 전문가다.", prompt)

# =================================================
# Tool 3: 카카오뱅크 대출 & 이사/청소 매칭
# =================================================
@mcp.tool()
async def recommend_loan_and_moving(
    annual_income: int, 
    target_deposit: int, 
    move_date: str
) -> dict:
    """
    사용자의 소득, 보증금, 이사 날짜를 기반으로 
    최적의 카카오뱅크 대출 상품과 이사 서비스를 추천합니다.
    """
    
    # 1. 대출 상품 추천 로직 (간이)
    loan_products = []
    
    if annual_income <= 3500 and target_deposit <= 20000:
        loan_products.append({
            "상품명": "카카오뱅크 청년 전월세보증금 대출",
            "한도": "최대 2억원 (보증금의 90%)",
            "특징": "만 19~34세 무주택 청년 대상 최저 금리"
        })
    
    loan_products.append({
        "상품명": "카카오뱅크 HF 전월세보증금 대출",
        "한도": "최대 2.22억원 (보증금의 80%)",
        "특징": "재직 1년 이상 직장인 추천"
    })

    # 2. 이사/청소 견적 (카카오 T 이사 / 청소연구소 연동 시나리오)
    moving_service = {
        "예상_이사일": move_date,
        "서비스_제안": [
            "🚛 카카오 T 이사: 소형 이사(1톤) 예상 견적 35만원~",
            "✨ 입주 청소 매칭: 전용 59㎡ 기준 예상 25만원~"
        ],
        "체크리스트": [
            f"{move_date} 2주 전: 엘리베이터 보양 신청",
            f"{move_date} 당일: 공과금(수도/전기/가스) 정산",
            "전입신고 및 확정일자 즉시 신청"
        ]
    }

    return {
        "user_info": {"income": f"{annual_income}만원", "target": f"{target_deposit}만원"},
        "recommended_loans": loan_products,
        "moving_plan": moving_service
    }

# =================================================
# 서버 실행 (SSE Transport)
# =================================================
# FastMCP는 기본적으로 uvicorn을 사용하여 SSE 서버를 띄웁니다.
if __name__ == "__main__":
    # Railway 등 클라우드 환경에서는 호스트 0.0.0.0이 필수입니다.
    mcp.run(transport="sse")
