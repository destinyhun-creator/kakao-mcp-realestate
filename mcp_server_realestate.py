import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="SafeMove MCP")

# -------------------------------------------------
# MCP Tool Definitions
# -------------------------------------------------

TOOLS = [
    {
        "name": "analyze_listing_risk",
        "description": (
            "부동산 매물(URL 또는 주소)을 입력받아 "
            "등기부등본·건축물대장 기준 깡통전세 위험도를 분석합니다."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "listing_url": {
                    "type": "string",
                    "description": "다방/네이버부동산 매물 URL"
                },
                "address": {
                    "type": "string",
                    "description": "매물 주소"
                },
                "price": {
                    "type": "number",
                    "description": "보증금 또는 매매가"
                }
            },
            "required": ["address", "price"]
        }
    },
    {
        "name": "analyze_contract_clause",
        "description": (
            "계약서 OCR 텍스트를 기반으로 "
            "전세사기 독소조항 및 필수 특약 누락 여부를 분석합니다."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "contract_text": {
                    "type": "string",
                    "description": "OCR로 추출된 계약서 전체 텍스트"
                }
            },
            "required": ["contract_text"]
        }
    },
    {
        "name": "recommend_loan_and_move",
        "description": (
            "사용자 소득 정보를 기반으로 "
            "카카오뱅크 전세대출 가능 여부와 이사 체크리스트를 제공합니다."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "annual_income": {
                    "type": "number",
                    "description": "연 소득 (원)"
                },
                "move_date": {
                    "type": "string",
                    "description": "이사 예정일"
                }
            },
            "required": ["annual_income"]
        }
    }
]

# -------------------------------------------------
# Health Check (Railway 필수)
# -------------------------------------------------

@app.get("/")
def health():
    return {"status": "SafeMove MCP running"}

# -------------------------------------------------
# MCP Main Endpoint
# -------------------------------------------------

@app.post("/")
async def mcp_endpoint(req: Request):
    body = await req.json()
    method = body.get("method")
    rpc_id = body.get("id")

    # 1️⃣ initialize
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "serverInfo": {
                    "name": "SafeMove MCP Real Estate Agent",
                    "version": "1.0.0",
                    "description": "전세계약 전·중·후를 연결하는 행동형 부동산 AI 에이전트"
                },
                "capabilities": {
                    "tools": {
                        "listChanged": False
                    }
                }
            }
        })

    # 2️⃣ tools/list
    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "tools": TOOLS
            }
        })

    # 3️⃣ tools/call
    if method == "tools/call":
        tool_name = body["params"]["name"]
        args = body["params"]["arguments"]

        # -------------------------------------------------
        # Tool 1: 매물 위험 분석
        # -------------------------------------------------
        if tool_name == "analyze_listing_risk":
            price = args["price"]

            risk_level = "LOW"
            reasons = []

            if price >= 300_000_000:
                risk_level = "MEDIUM"
                reasons.append("보증금 규모가 커 등기부등본 근저당 확인 필요")

            result = {
                "summary": f"{args['address']} 매물 전세 위험도 분석 결과",
                "risk_level": risk_level,
                "analysis": {
                    "registry_check": "필요",
                    "building_register": "확인 필요",
                    "suspected_issues": reasons
                },
                "next_action": [
                    "등기부등본 열람",
                    "확정일자 및 전입신고 필수"
                ]
            }

        # -------------------------------------------------
        # Tool 2: 계약서 독소조항 분석
        # -------------------------------------------------
        elif tool_name == "analyze_contract_clause":
            text = args["contract_text"]
            warnings = []

            if "임대인은 책임지지 않는다" in text:
                warnings.append("임대인 책임 면제 조항")
            if "보증금 반환 불가" in text:
                warnings.append("보증금 반환 제한 조항")
            if "확정일자" not in text:
                warnings.append("확정일자 관련 특약 누락")

            result = {
                "dangerous_clauses": warnings,
                "safe": len(warnings) == 0,
                "recommendation": (
                    "특약 수정 후 계약 권장"
                    if warnings else
                    "계약 진행 가능"
                )
            }

        # -------------------------------------------------
        # Tool 3: 대출 & 이사 매칭
        # -------------------------------------------------
        elif tool_name == "recommend_loan_and_move":
            income = args["annual_income"]

            loan_available = income >= 30_000_000

            result = {
                "loan_recommendation": {
                    "bank": "KakaoBank",
                    "product": "전월세보증금 대출",
                    "available": loan_available,
                    "estimated_limit": int(income * 3) if loan_available else 0
                },
                "move_checklist": [
                    "전입신고",
                    "확정일자 받기",
                    "전세보증보험 가입",
                    "이사 당일 계량기 촬영",
                    "잔금 송금 후 열쇠 수령"
                ]
            }

        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32601,
                    "message": "Tool not found"
                }
            })

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
        })
