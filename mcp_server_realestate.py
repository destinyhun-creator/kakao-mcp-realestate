from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# -----------------------------
# MCP Tool Definitions
# -----------------------------

TOOLS = [
    {
        "name": "analyze_real_estate",
        "description": "부동산 주소와 가격으로 전세 위험도를 분석합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {"type": "string"},
                "price": {"type": "integer"}
            },
            "required": ["address", "price"]
        }
    },
    {
        "name": "contract_clause_check",
        "description": "계약서 문구에서 전세사기 독소조항을 탐지합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contract_text": {"type": "string"}
            },
            "required": ["contract_text"]
        }
    },
    {
        "name": "move_and_loan_guide",
        "description": "소득 기준 전세대출 가능 여부와 이사 체크리스트를 제공합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "income": {"type": "integer"}
            },
            "required": ["income"]
        }
    }
]

# -----------------------------
# MCP Endpoint
# -----------------------------

@app.post("/mcp")
async def mcp_endpoint(req: Request):
    body = await req.json()
    method = body.get("method")
    rpc_id = body.get("id")

    # 1️⃣ initialize (필수)
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "serverInfo": {
                    "name": "SafeMove MCP Real Estate Agent",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        })

    # 2️⃣ ping
    if method == "ping":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {}
        })

    # 3️⃣ tools/list
    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "tools": TOOLS
            }
        })

    # 4️⃣ tools/call
    if method == "tools/call":
        params = body.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})

        # ---- Tool Logic ----
        if name == "analyze_real_estate":
            price = args["price"]
            risk = "LOW"
            reason = "No major risk detected."

            if price >= 300_000_000:
                risk = "MEDIUM"
                reason = "High price area, registry check recommended."

            result = {
                "address": args["address"],
                "price": price,
                "risk_level": risk,
                "summary": reason
            }

        elif name == "contract_clause_check":
            text = args["contract_text"]
            warnings = []

            if "책임 없음" in text:
                warnings.append("임대인 책임 면제 조항 의심")
            if "보증금 반환 불가" in text:
                warnings.append("보증금 반환 관련 위험 문구")

            result = {
                "warnings": warnings,
                "safe": len(warnings) == 0
            }

        elif name == "move_and_loan_guide":
            income = args["income"]
            result = {
                "loan_available": income >= 30_000_000,
                "bank": "KakaoBank (demo)",
                "moving_checklist": [
                    "전입신고",
                    "확정일자 받기",
                    "전세보증보험 확인",
                    "이사 당일 계량기 촬영"
                ]
            }

        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found"
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
