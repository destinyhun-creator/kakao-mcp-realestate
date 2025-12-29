from fastmcp import FastMCP
import json
import os
from datetime import datetime

mcp = FastMCP(
    name="SafeMove MCP Real Estate Agent",
    description="카카오 생태계 연계 전세·계약·대출·이사 원큐 처리 행동형 부동산 AI"
)

# 1️⃣ 다방 매물 + 시세 + 근저당 위험 분석
@mcp.tool()
def analyze_listing_risk(listing_url: str) -> str:
    result = {
        "input_listing_url": listing_url,
        "address": "서울 마포구 망원동",
        "property_type": "빌라",
        "market_price": "매매 시세 약 3.6억",
        "jeonse_price": "전세 3억",
        "mortgage_detected": True,
        "mortgage_ratio": "매매가 대비 78%",
        "risk_score": 87,
        "risk_reason": [
            "근저당 설정 금액 과다",
            "시세 대비 전세가율 높음",
            "빌라 유형 전세사기 위험군"
        ],
        "ai_judgement": "깡통전세 고위험",
        "recommendation": [
            "전세보증금 반환보증 가입 필수",
            "근저당 말소 조건 특약 요구"
        ]
    }
    return json.dumps(result, ensure_ascii=False, indent=2)

# 2️⃣ 계약서 OCR + 독소조항 분석
@mcp.tool()
def analyze_contract_image(image_description: str) -> str:
    result = {
        "image_summary": image_description,
        "detected_risk_clause": [
            "임대인 책임 면책 조항 포함",
            "전세보증금 반환 기한 불명확"
        ],
        "missing_special_clause": [
            "잔금일까지 추가 권리설정 금지",
            "보증보험 가입 불가 시 계약 해제 조항"
        ],
        "ai_comment": "임차인에게 불리한 계약 구조",
        "action_required": "특약 수정 또는 계약 재검토 권장"
    }
    return json.dumps(result, ensure_ascii=False, indent=2)

# 3️⃣ 카카오뱅크 전세대출 + 이사 패키지
@mcp.tool()
def recommend_move_package(
    deposit: int,
    income_level: str,
    move_date: str
) -> str:
    result = {
        "deposit_amount": f"{deposit}원",
        "income_level": income_level,
        "recommended_loan": {
            "product": "카카오뱅크 청년 전월세보증금 대출",
            "expected_limit": "최대 2억",
            "expected_rate": "연 3%대"
        },
        "moving_service": {
            "estimated_cost": "약 45만원",
            "included": [
                "원룸/빌라 이사",
                "포장이사 기본",
                "엘리베이터 사용 기준"
            ]
        },
        "cleaning_service": "입주청소 패키지 추천",
        "move_date": move_
