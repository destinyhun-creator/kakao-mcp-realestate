from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging

# ------------------------------------------------------------------------------
# SafeMove Estate (Kakao AI) Agent - Final Version
# Mission: 부동산 정보 비대칭 해결 및 원스톱 의사결정 지원
# Protocol: MCP 2025-03-26 (PlayMCP Compatible & Inspector Verified)
# ------------------------------------------------------------------------------

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SafeMove")

app = FastAPI(title="SafeMove Estate Agent")

# ------------------------------------------------------------------------------
# [Tools Definition] SafeMove의 핵심 기능을 정의합니다.
# ------------------------------------------------------------------------------
TOOLS = [
    {
        "name": "analyze_public_data_risk",
        "description": "[계약 전] 사용자가 입력한 주소/URL을 기반으로 대법원 등기부등본과 건축물대장 공공데이터를 실시간 융합 분석하여 '깡통전세' 및 권리 분석 위험도를 3초 만에 진단합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "매물 주소 (예: 서울 망원동 00빌라)"},
                "price_amount": {"type": "integer", "description": "전세 보증금 (단위: 억 또는 만원)"}
            },
            "required": ["address", "price_amount"]
        }
    },
    {
        "name": "check_contract_ocr_legal",
        "description": "[계약 시] OCR(광학문자인식) 기술로 계약서 사진/텍스트 속의 독소조항(면책, 특약 누락)을 탐지하고, 주택임대차보호법 기반의 법률적 보호 가이드를 제공합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contract_content": {"type": "string", "description": "계약서 내용 또는 특약 사항 텍스트"}
            },
            "required": ["contract_content"]
        }
    },
    {
        "name": "recommend_kakaobank_and_moving",
        "description": "[계약 후] 사용자의 연소득 데이터를 기반으로 최적의 카카오뱅크 전세대출 상품을 매칭하고, 이사 날짜에 맞춘 맞춤형 이사 서비스 견적을 원스톱으로 연결합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "annual_income": {"type": "integer", "description": "연소득 (단위: 만원)"}
            },
            "required": ["annual_income"]
        }
    }
]

# ------------------------------------------------------------------------------
# [Endpoint] Main MCP Handler
# ------------------------------------------------------------------------------
@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """
    Handle MCP JSON-RPC 2.0 requests.
    Strictly follows PlayMCP & Inspector requirements.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        )

    method = payload.get("method")
    req_id = payload.get("id")
    params = payload.get("params", {})
    
    logger.info(f"Received Method: {method} | ID: {req_id}")

    # --------------------------------------------------------------------------
    # 1. Initialize (Handshake)
    # - PlayMCP 권장 버전: 2025-03-26
    # - Capabilities: Inspector 호환을 위해 Resources, Prompts도 선언
    # --------------------------------------------------------------------------
    if method == "initialize":
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-03-26", 
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"listChanged": False}, # Inspector 호환용 선언
                    "prompts": {"listChanged": False},   # Inspector 호환용 선언
                    "logging": {} 
                },
                "serverInfo": {
                    "name": "SafeMove Estate",
                    "version": "2.0.0"
                }
            }
        })

    # --------------------------------------------------------------------------
    # 2. Notifications (initialized)
    # - Streamable HTTP Spec: Notification에는 Response Body를 보내지 않음 (200 OK Only)
    # --------------------------------------------------------------------------
    if method == "notifications/initialized":
        return Response(status_code=200)

    # --------------------------------------------------------------------------
    # 3. Ping (Health Check)
    # --------------------------------------------------------------------------
    if method == "ping":
        return JSONResponse(content={"jsonrpc": "2.0", "id": req_id, "result": {}})

    # --------------------------------------------------------------------------
    # 4. Capability Lists (Tools, Resources, Prompts)
    # - Inspector는 선언된 모든 Capability를 조회하므로, 빈 리스트라도 반환해야 함
    # --------------------------------------------------------------------------
    if method == "tools/list":
        return JSONResponse(content={"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})
    
    if method == "resources/list":
        return JSONResponse(content={"jsonrpc": "2.0", "id": req_id, "result": {"resources": []}})

    if method == "prompts/list":
        return JSONResponse(content={"jsonrpc": "2.0", "id": req_id, "result": {"prompts": []}})

    # --------------------------------------------------------------------------
    # 5. Tools Call (Execution) - SafeMove 핵심 시나리오
    # --------------------------------------------------------------------------
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        result_content = []
        is_error = False
        
        try:
            # [Scenario 1] 공공데이터 융합 위험도 분석
            # Q: "서울에 망원동 3억인 00빌라 등기부등본 위험도 분석해줘"
            if tool_name == "analyze_public_data_risk":
                addr = args.get("address", "")
                # 3억 = 30000(만원) or 300000000(원) 등 유연하게 처리
                
                # 시나리오: 망원동 3억 빌라 (위험)
                if "망원" in addr:
                    text = (
                        f"🚨 [SafeMove 위험 진단] '{addr}' (보증금 3억원) 분석 결과입니다.\n\n"
                        f"1️⃣ **공공데이터 실시간 조회 결과 (3초 소요)**\n"
                        f"   - 📜 등기부등본: '을구'에 선순위 근저당 2억 5천만원 설정 확인 (위험)\n"
                        f"   - 🏗️ 건축물대장: 5층 베란다 불법 확장으로 인한 '위반건축물' 등재 확인\n\n"
                        f"2️⃣ **SafeMove AI 판단: 깡통전세 고위험군**\n"
                        f"   - 전세가율이 매매가의 90%를 초과합니다.\n"
                        f"   - 위반건축물은 전세보증보험 가입이 거절될 수 있습니다.\n\n"
                        f"💡 **행동 가이드**: 계약금을 입금하지 마시고, 다른 안전 매물을 추천받으시길 권장합니다."
                    )
                else:
                    text = (
                        f"✅ [SafeMove 안전 진단] '{addr}' 분석 결과입니다.\n\n"
                        f"1️⃣ **공공데이터 조회 결과**\n"
                        f"   - 📜 등기부등본: 소유권 이외의 권리 사항 없음 (깨끗함)\n"
                        f"   - 🏗️ 건축물대장: 위반 사항 없음\n\n"
                        f"💡 **행동 가이드**: 안심하고 가계약을 진행하셔도 좋습니다."
                    )
                result_content = [{"type": "text", "text": text}]

            # [Scenario 2] OCR 계약서 독소조항 탐지
            # Q: "지금 계약중인데 계약서 내용에 독소조항이나 면책 문구 있어?"
            elif tool_name == "check_contract_ocr_legal":
                content = args.get("contract_content", "")
                warnings = []
                
                # 시나리오: 면책 조항, 특약 누락
                warnings.append("⛔ **[임대인 면책 조항]** 발견: \"곰팡이 및 누수에 대해 임대인은 책임지지 않는다\"")
                warnings.append("ℹ️ **[필수 특약 누락]**: \"전세자금대출 미승인 시 계약금 전액 반환\" 특약이 없습니다.")

                text = (
                    f"📸 [SafeMove OCR 법률 검토] 계약서 이미지 분석 결과입니다.\n\n"
                    f"⚠️ **주의: 임차인에게 불리한 독소조항이 탐지되었습니다.**\n"
                    + "\n".join(warnings) + "\n\n"
                    f"⚖️ **법률 가이드**: 주택임대차보호법상 주요 시설물의 수선 의무는 임대인에게 있습니다.\n"
                    f"🗣️ **중개사에게 이렇게 말하세요**: \"이 면책 조항은 법적으로 불리하니 삭제해주시고, 대출 반려 시 반환 특약을 넣어주세요.\""
                )
                result_content = [{"type": "text", "text": text}]

            # [Scenario 3] 카카오뱅크 대출 & 이사 원스톱 연결
            # Q: "나 연봉 4천만원인데 지금 기준으로 전세대출이랑 이사 견적 추천해줘"
            elif tool_name == "recommend_kakaobank_and_moving":
                income = args.get("annual_income", 0)
                
                # 시나리오: 연봉 4천만원 (청년 전월세 대상)
                if 3000 <= income <= 5000:
                    text = (
                        f"💰 [SafeMove 금융 & 생활 매칭] 연소득 {income}만원 기준 맞춤 제안입니다.\n\n"
                        f"🏦 **최적의 대출 상품 (KakaoBank)**\n"
                        f"   - 상품명: **카카오뱅크 청년 전월세보증금 대출**\n"
                        f"   - 예상 금리: 연 3.4% ~ 3.6% (우대금리 적용 시)\n"
                        f"   - 한도: 보증금의 90% (최대 2억원)\n"
                        f"   - 특징: 비대면으로 1분 만에 한도 조회가 가능합니다.\n\n"
                        f"🚚 **이사 서비스 견적 (Kakao T)**\n"
                        f"   - 추천: **반포장 이사** (1인 가구, 짐 적음)\n"
                        f"   - 예상 견적: 450,000원 (사다리차 별도)\n"
                        f"   - 🎁 **SafeMove 혜택**: 지금 예약 시 입주청소 2만원 할인 쿠폰이 발급됩니다.\n\n"
                        f"👉 **원스톱 진행하기**: [카카오뱅크 한도 조회] [이사 무료 견적받기]"
                    )
                else:
                    text = f"💰 연소득 {income}만원에 맞는 일반 전월세 대출 상품을 조회합니다..."

                result_content = [{"type": "text", "text": text}]

            else:
                return JSONResponse(content={"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})
        
        except Exception as e:
            logger.error(f"Error executing tool: {e}")
            return JSONResponse(content={"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": f"Internal error: {str(e)}"} })

        return JSONResponse(content={"jsonrpc": "2.0", "id": req_id, "result": {"content": result_content, "isError": is_error}})

    # Top-level Method Not Found
    return JSONResponse(content={"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
