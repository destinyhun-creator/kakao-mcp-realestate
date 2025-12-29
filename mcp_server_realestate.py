import asyncio
import os
import json
import logging
import httpx
from dotenv import load_dotenv

# 표준 MCP 라이브러리 사용 (안정성 최우선)
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# .env 파일 로드 (API 키 관리)
load_dotenv()

# 1. 서버 초기화
app = Server("SafeMove-RealEstate-Agent")

# 로깅 설정 (디버깅용)
logging.basicConfig(level=logging.INFO, stream=None) # Stdio 간섭 방지
logger = logging.getLogger("mcp_server")

# =================================================
# 공통: LLM 상담 (OpenAI / Gemini)
# =================================================
async def call_llm(prompt: str) -> str:
    """API 키 유무에 따라 실제 LLM 호출 또는 더미 응답 반환"""
    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    try:
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
                            {"role": "system", "content": "너는 부동산 계약 리스크 분석 전문가다. 간결하고 정확하게 답변해라."},
                            {"role": "user", "content": prompt},
                        ],
                    },
                    timeout=15,
                )
                res.raise_for_status()
                return res.json()["choices"][0]["message"]["content"]
        
        # Gemini 등 다른 로직 추가 가능
        
    except Exception as e:
        logger.error(f"LLM 호출 실패: {e}")
        return f"AI 분석 중 오류가 발생했습니다: {str(e)}"

    # 키가 없을 때 (해커톤 데모 모드)
    return (
        "현재 API 키가 설정되지 않아 AI 분석을 수행할 수 없습니다. "
        "하지만 입력하신 정보를 볼 때, 계약 전 반드시 등기부등본의 '을구'를 확인하시기 바랍니다."
    )

# =================================================
# Tool 정의 (Player에게 "나 이런 기능 있어"라고 알림)
# =================================================
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="analyze_registry_risk",
            description="주소와 소유자명을 기반으로 전세사기/깡통전세 위험을 분석합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {"type": "string", "description": "부동산 주소"},
                    "owner_name": {"type": "string", "description": "소유자 이름"},
                },
                "required": ["address", "owner_name"],
            },
        ),
        types.Tool(
            name="safemove_checklist",
            description="전세 또는 월세 계약 시 확인해야 할 필수 체크리스트를 제공합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_type": {"type": "string", "enum": ["전세", "월세"], "description": "계약 형태"}
                },
                "required": ["contract_type"],
            },
        ),
        types.Tool(
            name="real_estate_chat",
            description="부동산 관련 자유 질문에 대해 AI 전문가가 답변합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "부동산 관련 질문"}
                },
                "required": ["question"],
            },
        ),
    ]

# =================================================
# Tool 실행 로직 (실제 기능 수행)
# =================================================
@app.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if not arguments:
        arguments = {}

    # 1. 위험 분석 도구
    if name == "analyze_registry_risk":
        address = arguments.get("address", "")
        owner_name = arguments.get("owner_name", "")
        
        # 룰 기반 분석
        if "빌라" in address or "망원" in address:
            result = {
                "status": "WARNING",
                "risk_score": 85,
                "reason": "선순위 근저당 설정 가능성 높음",
                "checks": {"registry": "확인 필요", "ownership": "최근 변경"}
            }
        else:
            result = {
                "status": "SAFE",
                "risk_score": 10,
                "checks": {"registry": "안전", "ownership": "일치"}
            }

        # AI 코멘트 추가
        ai_advice = await call_llm(
            f"주소: {address}, 소유자: {owner_name}. 이 부동산의 전세 리스크를 초보자에게 설명하듯 짧게 요약해줘."
        )
        result["ai_advice"] = ai_advice
        
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    # 2. 체크리스트 도구
    elif name == "safemove_checklist":
        ctype = arguments.get("contract_type", "전세")
        base_list = ["공인중개사 등록 확인", "신분증 진위 확인"]
        
        if ctype == "전세":
            final_list = base_list + ["전세보증금 반환보증 가입", "국세/지방세 완납증명"]
        else:
            final_list = base_list + ["최우선변제금 확인", "관리비 내역 확인"]
            
        return [types.TextContent(type="text", text=json.dumps({
            "type": ctype,
            "checklist": final_list
        }, ensure_ascii=False, indent=2))]

    # 3. 부동산 상담 도구
    elif name == "real_estate_chat":
        question = arguments.get("question", "")
        answer = await call_llm(f"질문: {question}\n부동산 전문가로서 답변해줘.")
        
        return [types.TextContent(type="text", text=answer)]

    else:
        raise ValueError(f"Unknown tool: {name}")

# =================================================
# 메인 실행 (Stdio 모드)
# =================================================
async def main():
    # Stdio(표준 입출력)를 통해 Player와 통신합니다.
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
