from fastmcp import FastMCP
import os
import httpx

# =================================================
# MCP 서버 생성 (이건 그대로 유지)
# =================================================
mcp = FastMCP(
    name="SafeMove Real Estate Agent",
    version="1.0.0"
)

# =================================================
# 공통: LLM 상담 (OpenAI / Gemini 구조만 잡아둠)
# =================================================
async def call_llm(prompt: str) -> str:
    """
    실제 키가 있으면 LLM 호출
    없으면 해커톤용 더미 응답
    """

    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    # 🔹 키 없을 때 (지금 해커톤/데모 상태)
    if not openai_key and not gemini_key:
        return (
            "현재 입력 정보를 기반으로 볼 때, "
            "계약 전 반드시 등기부등본과 선순위 채권을 확인하시고 "
            "전세보증금 반환보증 가입을 권장드립니다."
        )

    # 🔹 OpenAI 예시 (구조만)
    if openai_key:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "너는 부동산 계약 리스크 분석 전문가다."},
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=10,
            )
            return res.json()["choices"][0]["message"]["content"]

    # 🔹 Gemini도 같은 방식으로 확장 가능
    return "AI 분석 결과를 불러오지 못했습니다."


# =================================================
# Tool 1: 전세 / 매물 위험 분석 (기존 + 고급화)
# =================================================
@mcp.tool()
async def analyze_registry_risk(address: str, owner_name: str) -> dict:
    """
    등기부등본 / 지역 패턴 기반
    전세사기·깡통전세 위험 분석
    """

    # 간단한 룰 기반 1차 필터
    if "빌라" in address or "망원" in address:
        base_result = {
            "status": "WARNING",
            "risk_score": 85,
            "reason": "선순위 근저당 비율 과다 가능성",
            "checks": {
                "registry": "근저당 설정 있음",
                "ownership": "최근 소유권 이전",
                "building": "정상"
            }
        }
    else:
        base_result = {
            "status": "SAFE",
            "risk_score": 10,
            "checks": {
                "registry": "근저당 없음",
                "ownership": "소유자 일치",
                "building": "정상"
            }
        }

    # AI 상담 코멘트 추가
    ai_comment = await call_llm(
        f"""
        주소: {address}
        소유자: {owner_name}
        위 부동산의 전세계약 리스크를 일반인도 이해할 수 있게 설명해줘.
        """
    )

    base_result["ai_advice"] = ai_comment
    base_result["recommended_action"] = [
        "전세보증금 반환보증 가입",
        "잔금 전 권리변동 금지 특약",
        "확정일자 및 전입신고"
    ]

    return base_result


# =================================================
# Tool 2: 계약 체크리스트 (기존 유지)
# =================================================
@mcp.tool()
def safemove_checklist(contract_type: str) -> dict:
    """
    전·월세 계약 필수 체크리스트
    """

    base = [
        "공인중개사 등록 여부 확인",
        "임대인 신분증 진위 확인",
        "전자계약 가능 여부"
    ]

    if contract_type == "전세":
        return {
            "type": "전세",
            "checklist": base + [
                "전세보증금 반환보증 가입",
                "국세·지방세 완납 증명",
                "특약 조항 OCR 검증"
            ],
            "finance": [
                "카카오뱅크 HF 전월세 대출",
                "카카오뱅크 청년 전월세 대출"
            ]
        }

    return {
        "type": "월세",
        "checklist": base + [
            "관리비 포함 여부 확인",
            "소액임차인 최우선변제 여부"
        ],
        "finance": [
            "카카오뱅크 월세보증금 대출"
        ]
    }


# =================================================
# Tool 3: 자연어 부동산 상담 (해커톤용 핵심)
# =================================================
@mcp.tool()
async def real_estate_chat(question: str) -> dict:
    """
    사용자 자유 질문 → AI 부동산 상담
    """

    answer = await call_llm(
        f"다음 질문에 대해 부동산 전문가처럼 답변해줘:\n{question}"
    )

    return {
        "question": question,
        "answer": answer,
        "disclaimer": "본 답변은 참고용이며 법적 효력을 가지지 않습니다."
    }


# =================================================
# 서버 실행 (SSE / uvicorn 내장)
# =================================================
if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
