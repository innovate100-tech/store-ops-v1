"""
전략 엔진 v4 - 건강검진 통합
전략 6개 후보 생성기
"""
from typing import Dict, List, Optional
from enum import Enum

# 전략 타입 enum
class StrategyType(Enum):
    SURVIVAL = "SURVIVAL"
    MARGIN = "MARGIN"
    COST = "COST"
    PORTFOLIO = "PORTFOLIO"
    ACQUISITION = "ACQUISITION"
    OPERATIONS = "OPERATIONS"


# 전략 타입별 기본 CTA 매핑
STRATEGY_CTA_MAP = {
    StrategyType.SURVIVAL: {
        "label": "수익 구조 설계",
        "page_key": "수익 구조 설계실",
        "params": {}
    },
    StrategyType.MARGIN: {
        "label": "메뉴 수익 구조 설계",
        "page_key": "메뉴 수익 구조 설계실",
        "params": {}
    },
    StrategyType.COST: {
        "label": "재료 구조 설계",
        "page_key": "재료 등록",
        "params": {}
    },
    StrategyType.PORTFOLIO: {
        "label": "메뉴 포트폴리오 설계",
        "page_key": "메뉴 등록",
        "params": {}
    },
    StrategyType.ACQUISITION: {
        "label": "분석총평",
        "page_key": "분석총평",
        "params": {}
    },
    StrategyType.OPERATIONS: {
        "label": "건강검진 리포트",
        "page_key": "종합 건강검진",
        "params": {}
    }
}


def build_base_strategies(context: Dict) -> List[Dict]:
    """
    기본 전략 6개 후보 생성
    
    Args:
        context: {
            "store_state": {...},  # classify_store_state 결과 요약
            "overall_score": float,  # 또는 store_state에서 추출
            "break_even_gap_ratio": float,  # 손익분기점 대비 비율 (0.95 = 95%)
            "margin_menu_ratio": float,  # 마진 메뉴 비율
            "ingredient_concentration": float,  # 재료 집중도
            "visitors_trend": str,  # "up" | "down" | "stable" | "unknown"
            ...
        }
    
    Returns:
        [
            {
                "type": "MARGIN",
                "title": "...명령문...",
                "priority_score": 100,
                "success_prob": 0.55,
                "impact_estimate": {"won": 0, "direction": "up"},
                "reasons": [... 최대 3개 ...],
                "cta": {"label":"...", "page_key":"...", "params":{}}
            },
            ...
        ]
    """
    strategies = []
    
    store_state = context.get("store_state", {})
    overall_score = context.get("overall_score", store_state.get("scores", {}).get("overall", 50))
    break_even_gap_ratio = context.get("break_even_gap_ratio", 1.0)
    margin_menu_ratio = context.get("margin_menu_ratio", 0.0)
    ingredient_concentration = context.get("ingredient_concentration", 0.0)
    visitors_trend = context.get("visitors_trend", "unknown")
    
    # 1. SURVIVAL 전략
    if break_even_gap_ratio < 0.95 or overall_score < 40:
        strategies.append({
            "type": StrategyType.SURVIVAL.value,
            "title": "생존선부터 복구하기",
            "priority_score": 100,
            "success_prob": 0.50,
            "impact_estimate": {"won": 0, "direction": "up"},
            "reasons": [
                f"손익분기점 대비 {break_even_gap_ratio*100:.0f}%",
                "수익 구조 점수 낮음" if overall_score < 40 else "예상 매출 부족"
            ],
            "cta": STRATEGY_CTA_MAP[StrategyType.SURVIVAL]
        })
    
    # 2. MARGIN 전략
    if margin_menu_ratio < 0.2 or overall_score < 50:
        strategies.append({
            "type": StrategyType.MARGIN.value,
            "title": "마진 구조 복구하기",
            "priority_score": 100,
            "success_prob": 0.55,
            "impact_estimate": {"won": 0, "direction": "up"},
            "reasons": [
                f"마진 메뉴 비율 {margin_menu_ratio*100:.0f}%" if margin_menu_ratio < 0.2 else "마진 구조 점수 낮음",
                "수익 기여도 개선 필요"
            ],
            "cta": STRATEGY_CTA_MAP[StrategyType.MARGIN]
        })
    
    # 3. COST 전략
    if ingredient_concentration > 0.7 or overall_score < 50:
        strategies.append({
            "type": StrategyType.COST.value,
            "title": "원가 집중도 분산하기",
            "priority_score": 100,
            "success_prob": 0.60,
            "impact_estimate": {"won": 0, "direction": "up"},
            "reasons": [
                f"재료 집중도 {ingredient_concentration*100:.0f}%" if ingredient_concentration > 0.7 else "원가 구조 점수 낮음",
                "대체재 설계 필요"
            ],
            "cta": STRATEGY_CTA_MAP[StrategyType.COST]
        })
    
    # 4. PORTFOLIO 전략
    if margin_menu_ratio < 0.3:
        strategies.append({
            "type": StrategyType.PORTFOLIO.value,
            "title": "메뉴 포트폴리오 재배치",
            "priority_score": 100,
            "success_prob": 0.55,
            "impact_estimate": {"won": 0, "direction": "up"},
            "reasons": [
                f"마진 메뉴 비율 {margin_menu_ratio*100:.0f}%",
                "포트폴리오 균형 개선 필요"
            ],
            "cta": STRATEGY_CTA_MAP[StrategyType.PORTFOLIO]
        })
    
    # 5. ACQUISITION 전략
    if visitors_trend == "down" or overall_score < 50:
        strategies.append({
            "type": StrategyType.ACQUISITION.value,
            "title": "분석총평",
            "priority_score": 100,
            "success_prob": 0.60,
            "impact_estimate": {"won": 0, "direction": "up"},
            "reasons": [
                "방문자 추세 하락" if visitors_trend == "down" else "매출 점수 낮음",
                "원인 분석 필요"
            ],
            "cta": STRATEGY_CTA_MAP[StrategyType.ACQUISITION]
        })
    
    # 6. OPERATIONS 전략 (조건부 포함 - 검진 기반)
    # 주의: 이 카드는 health_diag가 있을 때만 우선순위가 높아짐
    # health_diag가 없으면 기본 우선순위로 포함
    strategies.append({
        "type": StrategyType.OPERATIONS.value,
        "title": "운영 품질(QSC) 복구부터 하세요",
        "priority_score": 50,  # 기본 우선순위 (health_diag로 가중치 추가)
        "success_prob": 0.65,
        "impact_estimate": {"won": 0, "direction": "up"},
        "reasons": [
            "운영 프로세스 개선",
            "표준화 필요"
        ],
        "cta": {
            "label": "체크결과 보기",
            "page_key": "체크결과",
            "params": {}
        }
    })
    
    # 6개 미만이면 기본 전략으로 채움
    while len(strategies) < 6:
        strategies.append({
            "type": StrategyType.OPERATIONS.value,
            "title": "가게 설계 센터에서 시작",
            "priority_score": 50,
            "success_prob": 0.50,
            "impact_estimate": {"won": 0, "direction": "up"},
            "reasons": ["데이터 부족", "설계부터 시작"],
            "cta": {
                "label": "가게 설계 센터",
                "page_key": "가게 설계 센터",
                "params": {}
            }
        })
    
    return strategies[:6]  # 최대 6개
