from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import os
import json

app = FastAPI()

# ==============================================================================
# 1. 툴(기능) 명세서 정의
# PlayMCP에게 "나는 이런 기능을 수행할 수 있어"라고 알려주는 부분입니다.
# ==============================================================================
TOOLS = [
    {
        "name": "analyze_real_estate_risk",
        "description": "주소와 보증금을 입력받아 등기부등본 및 건축물대장 기반 위험도(깡통전세, 위반건축물)를 분석합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "매물 주소 (예: 망원동 빌라)"},
                "deposit_amount": {"type": "integer", "description": "보증금 액수 (단위: 만원)"}
            },
            "required": ["address", "deposit_amount"]
        }
    },
    {
        "name": "check_contract_toxic_clauses",
        "description": "계약서 내용을 분석하여 세입자에게 불리한 독소조항(면책, 반환 지연)이나 필수 특약 누락을 탐지합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contract_text": {"type": "string", "description": "계약서 텍스트 내용"}
            },
            "required": ["contract_text"]
        }
    },
    {
        "name": "recommend_finance_and_living",
        "description": "사용자의 연소득을 기준으로 최적의 카카오뱅크 전세대출 상품과 맞춤형 이사 서비스를 추천합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "annual_income": {"type": "integer", "description": "연소득 (단위: 만원)"}
            },
            "required": ["annual_income"]
        }
    }
]

# ==============================================================================
# 2. 메인 엔드포인트 (/mcp)
# PlayMCP와 소통하는 유일한 창구입니다. (Stateless 방식)
# ==============================================================================
@app.post("/mcp")
async def mcp_endpoint(req: Request):
    try:
        body = await req.json()
    except:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    method = body.get("method")
    rpc_id = body.get("id") # Notification인 경우 None일 수 있음
    params = body.get("params", {})

    # --------------------------------------------------------------------------
    # [A] Initialize (핸드셰이크) - 서버 정보 제공
    # --------------------------------------------------------------------------
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "SafeMove Agent",
                    "version": "1.0.0"
                }
            }
        }

    # --------------------------------------------------------------------------
    # [B] Notifications (initialized 등) - 빈 응답 반환
    # MCP 규약상 Notification은 응답을 기대하지 않지만, HTTP 요청 종결을 위해 200 OK 반환
    # --------------------------------------------------------------------------
    if method == "notifications/initialized":
        return JSONResponse(content={"jsonrpc": "2.0", "id": rpc_id, "result": True})

    # --------------------------------------------------------------------------
    # [C] Ping - 연결 상태 확인 (Inspector 필수)
    # --------------------------------------------------------------------------
    if method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {}
        }

    # --------------------------------------------------------------------------
    # [D] Tools List - 기능 목록 제공
    # --------------------------------------------------------------------------
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "tools": TOOLS
            }
        }

    # --------------------------------------------------------------------------
    # [E] Tools Call - 실제 기능 수행 (시나리오 로직)
    # --------------------------------------------------------------------------
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        result_text = ""

        # --- 🏠 1. 부동산 위험도 분석 시나리오 ---
        if tool_name == "analyze_real_estate_risk":
            addr = args.get("address", "")
            deposit = args.get("deposit_amount", 0)
            
            # [시나리오] 망원동은 위험, 비싼 집은 주의, 나머지는 안전
            if "망원" in addr:
                result_text = (
                    f"🚨 [위험 감지] '{addr}' 분석 결과입니다.\n"
                    f"- ⚠️ 건물 소유주의 선순위 근저당 설정액이 매매가의 80%를 초과합니다. (깡통전세 위험)\n"
                    f"- ⚠️ 건축물대장상 '위반건축물(불법 증축)' 등재가 확인되었습니다.\n"
                    f"👉 결론: 전세보증보험 가입이 불가능한 매물입니다. 계약을 권장하지 않습니다."
                )
            elif deposit >= 50000: # 5억 이상
                result_text = (
                    f"⚠️ [주의 요망] '{addr}' (보증금 {deposit}만원) 분석 결과입니다.\n"
                    f"- 해당 매물은 '신탁등기' 상태입니다.\n"
                    f"- 신탁원부를 발급받아 신탁사의 동의 여부를 반드시 확인해야 합니다.\n"
                    f"👉 조언: 신탁사 동의서 없이 계약 시 보증금을 보호받을 수 없습니다."
                )
            else:
                result_text = (
                    f"✅ [안전 매물] '{addr}' 분석 결과입니다.\n"
                    f"- 등기부등본상 소유권 관계가 명확하며, 근저당 설정이 없습니다.\n"
                    f"- 건축물대장상 위반 사항이 없습니다.\n"
                    f"👉 결론: 안심하고 계약을 진행하셔도 좋습니다. 카카오뱅크 대출 심사가 가능합니다."
                )

        # --- 📜 2. 계약서 독소조항 분석 시나리오 ---
        elif tool_name == "check_contract_toxic_clauses":
            text = args.get("contract_text", "")
            risks = []
            
            if "책임 없음" in text or "면책" in text:
                risks.append("- ⚠️ '임대인 면책' 조항 발견: 시설물 파손 시 임대인이 책임지지 않는다는 문구는 불리합니다.")
            if "반환 불가" in text or "새 세입자" in text:
                risks.append("- ⚠️ '보증금 반환 지연' 위험: 새 세입자가 들어와야 돈을 준다는 특약은 삭제를 요구하세요.")
            if "대출" not in text:
                risks.append("- ℹ️ '필수 특약 누락': 전세자금대출 반려 시 계약금 반환 특약이 없습니다.")

            if risks:
                result_text = "🚨 계약서 검토 결과, 수정이 필요한 항목이 발견되었습니다.\n" + "\n".join(risks)
            else:
                result_text = "✅ 계약서 검토 완료. 표준 임대차 계약서를 준수한 안전한 내용입니다."

        # --- 💰 3. 대출 및 이사 추천 시나리오 ---
        elif tool_name == "recommend_finance_and_living":
            income = args.get("annual_income", 0)
            
            loan_info = ""
            if income < 3500:
                loan_info = "🔹 추천 상품: 중소기업취업청년 전월세보증금대출 (연 1.2%~)"
            elif income < 7000:
                loan_info = "🔹 추천 상품: 카카오뱅크 청년 전월세보증금 대출 (연 3.4%~, 90% 한도)"
            else:
                loan_info = "🔹 추천 상품: 카카오뱅크 일반 전월세보증금 대출 (최대 2.22억원)"

            result_text = (
                f"💰 연소득 {income}만원 기준 맞춤 제안입니다.\n"
                f"{loan_info}\n\n"
                f"🚚 [카카오 T 이사] 견적 제안:\n"
                f"- 추천 서비스: 반포장 이사 (1인 가구 최적)\n"
                f"- 예상 비용: 약 35~45만원\n"
                f"- 혜택: 'SafeMove' 통해 예약 시 입주청소 10% 할인 쿠폰 제공"
            )

        # --- 예외 처리 ---
        else:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32601, "message": "Method not found"}
            }

        # 결과 반환
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "content": [{"type": "text", "text": result_text}],
                "isError": False
            }
        }

    # 그 외 알 수 없는 요청
    return JSONResponse(content={"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32600, "message": "Invalid Request"}})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # PlayMCP는 0.0.0.0 호스트를 요구함
    uvicorn.run(app, host="0.0.0.0", port=port)
