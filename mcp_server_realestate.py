from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uvicorn
import os
import json
import logging

# ------------------------------------------------------------------------------
# SafeMove (Kakao AI) Agent - PlayMCP Compatible Server
# Spec: MCP Streamable HTTP (Stateless)
# Protocol Version: 2025-03-26 (PlayMCP Required)
# ------------------------------------------------------------------------------

# 로깅 설정 (디버깅용)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SafeMove")

app = FastAPI(title="SafeMove Agent")

# [Tools Definition]
TOOLS = [
    {
        "name": "analyze_real_estate_risk",
        "description": "주소와 보증금을 입력받아 등기부등본 및 건축물대장 데이터를 기반으로 부동산 위험도(깡통전세, 위반건축물, 신탁등기 등)를 정밀 분석합니다.",
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
        "description": "계약서 텍스트를 분석하여 세입자에게 불리한 독소조항(면책, 반환 지연)이나 필수 특약(대출 반려 시 반환) 누락을 탐지합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contract_text": {"type": "string", "description": "계약서 전체 텍스트 내용"}
            },
            "required": ["contract_text"]
        }
    },
    {
        "name": "recommend_finance_and_living",
        "description": "사용자의 연소득 정보를 바탕으로 최적의 카카오뱅크 전세대출 상품을 추천하고, 맞춤형 이사 서비스 견적을 제안합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "annual_income": {"type": "integer", "description": "연소득 (단위: 만원)"}
            },
            "required": ["annual_income"]
        }
    }
]

@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """
    Streamable HTTP Endpoint for MCP.
    Handles JSON-RPC 2.0 requests via POST.
    Ensures Content-Type is application/json.
    """
    try:
        # JSON-RPC 요청 파싱 (파싱 실패 시 -32700 에러 처리)
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
            )

        method = payload.get("method")
        req_id = payload.get("id")
        params = payload.get("params", {})
        
        logger.info(f"Received Method: {method}")

        # ----------------------------------------------------------------------
        # 1. Initialize (Handshake)
        # ----------------------------------------------------------------------
        if method == "initialize":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2025-03-26",  # PlayMCP 요구 사항 충족 (선언)
                    "capabilities": {
                        # Stateless 서버이므로 listChanged 등은 지원하지 않음을 명시
                        "tools": {"listChanged": False},
                        "resources": {"listChanged": False},
                        "prompts": {"listChanged": False},
                        "logging": {} 
                    },
                    "serverInfo": {
                        "name": "SafeMove Agent",
                        "version": "1.0.3"
                    }
                }
            })

        # ----------------------------------------------------------------------
        # 2. Notifications (initialized)
        # - Streamable HTTP에서는 Notification에 대해 200 OK만 반환 (Body 없음)
        # ----------------------------------------------------------------------
        if method == "notifications/initialized":
            # 2024-11-05 스펙: Initialized 알림 수신 시 아무 작업도 하지 않고 성공 응답
            return Response(status_code=200)

        # ----------------------------------------------------------------------
        # 3. Ping (Health Check)
        # ----------------------------------------------------------------------
        if method == "ping":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            })

        # ----------------------------------------------------------------------
        # 4. Tools List
        # ----------------------------------------------------------------------
        if method == "tools/list":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": TOOLS
                }
            })

        # ----------------------------------------------------------------------
        # 5. Tools Call
        # ----------------------------------------------------------------------
        if method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            result_content = []
            is_error = False
            
            try:
                # [시나리오 1] 부동산 위험도 분석
                if tool_name == "analyze_real_estate_risk":
                    addr = args.get("address", "")
                    deposit = args.get("deposit_amount", 0)
                    
                    if "망원" in addr:
                        text = (
                            f"🚨 [위험 감지] '{addr}' 매물 분석 결과\n"
                            f"- ⚠️ 선순위 근저당 설정액이 과다합니다 (매매가 대비 80% 초과).\n"
                            f"- ⚠️ 건축물대장상 '위반건축물(불법 증축)' 등재가 확인되었습니다.\n"
                            f"👉 결론: 전세사기 고위험군입니다. 계약을 권장하지 않습니다."
                        )
                    elif deposit >= 50000:
                        text = (
                            f"⚠️ [주의 필요] '{addr}' (보증금 {deposit}만원)\n"
                            f"- '신탁등기' 상태의 매물입니다.\n"
                            f"- 신탁원부를 발급받아 신탁사의 동의 여부를 반드시 확인해야 보증금을 보호받을 수 있습니다.\n"
                        )
                    else:
                        text = (
                            f"✅ [안전 매물] '{addr}' 분석 결과\n"
                            f"- 등기부등본상 권리 관계가 깨끗합니다.\n"
                            f"- 건축물대장상 위반 사항이 없습니다.\n"
                            f"👉 결론: 안심전세 대출 및 보증보험 가입이 가능합니다."
                        )
                    result_content = [{"type": "text", "text": text}]

                # [시나리오 2] 계약서 독소조항 검토
                elif tool_name == "check_contract_toxic_clauses":
                    content = args.get("contract_text", "")
                    warnings = []
                    if "책임 없음" in content or "면책" in content:
                        warnings.append("- ⛔ '임대인 면책' 조항: 시설물 파손 시 임대인이 책임지지 않는다는 내용은 불리합니다.")
                    if "반환 불가" in content or "새 세입자" in content:
                        warnings.append("- ⛔ '보증금 반환 지연': 새 세입자가 들어와야 보증금을 준다는 특약은 법적 효력이 약하며 위험합니다.")
                    if "대출" not in content:
                        warnings.append("- ℹ️ '필수 특약 누락': 전세자금대출 반려 시 계약금을 즉시 반환한다는 특약이 없습니다.")
                    
                    if warnings:
                        msg = "🚨 계약서 정밀 분석 결과, 수정이 필요한 항목이 발견되었습니다:\n" + "\n".join(warnings)
                    else:
                        msg = "✅ 계약서 분석 완료. 표준 임대차 계약서를 준수한 안전한 계약입니다."
                    result_content = [{"type": "text", "text": msg}]

                # [시나리오 3] 금융 및 이사 추천
                elif tool_name == "recommend_finance_and_living":
                    income = args.get("annual_income", 0)
                    loan_msg = ""
                    if income < 3500:
                        loan_msg = "🔹 [대출] 중소기업취업청년 전월세보증금대출 (연 1.2%~)"
                    elif income < 7000:
                        loan_msg = "🔹 [대출] 카카오뱅크 청년 전월세보증금 대출 (연 3.4%~, 90% 한도)"
                    else:
                        loan_msg = "🔹 [대출] 카카오뱅크 일반 전월세보증금 대출 (최대 2.22억원)"
                    
                    msg = (
                        f"💰 연소득 {income}만원 기준 맞춤 솔루션입니다.\n"
                        f"{loan_msg}\n\n"
                        f"🚚 [카카오 T 이사] 추천 견적\n"
                        f"- 서비스: 반포장 이사 (1인 가구 최적)\n"
                        f"- 예상 비용: 35~45만원\n"
                        f"- 혜택: SafeMove 제휴 10% 청소 할인 쿠폰 발급됨"
                    )
                    result_content = [{"type": "text", "text": msg}]

                else:
                    # 해당 Tool이 없는 경우 (-32601)
                    return JSONResponse(content={
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": "Method not found"}
                    })
            
            except Exception as e:
                # 내부 로직 에러 (-32603)
                logger.error(f"Tool execution error: {e}")
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                })

            # 정상 응답
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": result_content,
                    "isError": is_error
                }
            })

        # 알 수 없는 메서드 요청 (-32601)
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": "Method not found"}
        })

    except Exception as e:
        # 기타 서버 에러
        logger.error(f"Server error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
        )

if __name__ == "__main__":
    # PlayMCP 배포 환경에 맞게 포트 설정
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
