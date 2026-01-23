"""
건강검진 가중치/확률/근거 보정 레이어
건강검진 결과를 전략 우선순위에 반영
"""
from typing import Dict, List
from src.health_check.questions_bank import CATEGORY_NAMES

# 가중치 규칙: {카테고리: {전략타입: 가중치}}
WEIGHT_RULES = {
    'F': {  # 재무 red
        'SURVIVAL': +35,
        'COST': +10,
        'MARGIN': +5,
        'ACQUISITION': -10
    },
    'H': {  # 인력 red
        'OPERATIONS': +35,
        'ACQUISITION': -5,
        'MARGIN': -5
    },
    'Q': {  # 품질 red
        'MARGIN': +30,
        'PORTFOLIO': +10
    },
    'M': {  # 마케팅 red
        'ACQUISITION': +30
    },
    'P1': {  # 가격1 red
        'PORTFOLIO': +15,
        'ACQUISITION': +10
    },
    'S': {  # 서비스 red
        'OPERATIONS': +20,
        'ACQUISITION': -5
    },
    'C': {  # 청결 red
        'OPERATIONS': +15
    },
    'P3': {  # 가격3(수익성) red
        'ACQUISITION': +15
    }
}


def apply_health_weighting(strategies: List[Dict], health_profile: Dict) -> List[Dict]:
    """
    건강검진 결과를 전략에 반영
    
    Args:
        strategies: 기본 전략 리스트
        health_profile: load_latest_health_profile 결과
    
    Returns:
        가중치 적용 및 정렬된 전략 리스트 (상위 6개)
    """
    if not health_profile.get("exists", False):
        return strategies
    
    # age_days가 30일 넘으면 효과 70%만 적용
    age_days = health_profile.get("age_days", 999)
    age_factor = 0.7 if age_days > 30 else 1.0
    
    risk_levels = health_profile.get("risk_levels", {})
    category_scores = health_profile.get("category_scores", {})
    main_bottleneck = health_profile.get("main_bottleneck")
    
    # 각 전략에 가중치 적용
    for strategy in strategies:
        strategy_type = strategy.get("type", "")
        original_priority = strategy.get("priority_score", 100)
        original_prob = strategy.get("success_prob", 0.55)
        
        priority_delta = 0
        prob_delta = 0
        
        # red 리스크 카테고리별 가중치 적용
        for category, risk_level in risk_levels.items():
            if risk_level == "red":
                rules = WEIGHT_RULES.get(category, {})
                weight = rules.get(strategy_type, 0)
                if weight != 0:
                    priority_delta += weight * age_factor
        
        # 병목 관련 전략은 확률 약간 감소 (필요하지만 난이도↑)
        if main_bottleneck and strategy_type in ["SURVIVAL", "MARGIN", "COST"]:
            bottleneck_rules = WEIGHT_RULES.get(main_bottleneck, {})
            if strategy_type in bottleneck_rules:
                prob_delta -= 0.05 * age_factor
        
        # 강점 영역 관련 전략은 확률 증가
        strength_top = health_profile.get("strength_top", [])
        for strength_cat in strength_top:
            if strategy_type == "OPERATIONS" and strength_cat in ["C", "S"]:
                prob_delta += 0.05 * age_factor
            elif strategy_type == "MARGIN" and strength_cat in ["P2", "P3"]:
                prob_delta += 0.05 * age_factor
        
        # 가중치/확률 적용
        strategy["priority_score"] = max(0, original_priority + int(priority_delta))
        strategy["success_prob"] = max(0.25, min(0.80, original_prob + prob_delta))
        
        # 근거 추가 (최대 3개 유지)
        reasons = strategy.get("reasons", [])
        
        # 건강검진 근거 추가
        health_reason = _build_health_reason(category_scores, risk_levels, main_bottleneck)
        if health_reason:
            # 기존 reasons에 추가 (최대 3개)
            if len(reasons) < 3:
                reasons.append(health_reason)
            else:
                # 마지막 항목 교체
                reasons[-1] = health_reason
        
        strategy["reasons"] = reasons[:3]  # 최대 3개 유지
    
    # priority_score 기준 내림차순 정렬
    strategies_sorted = sorted(
        strategies,
        key=lambda x: x.get("priority_score", 0),
        reverse=True
    )
    
    return strategies_sorted[:6]  # 상위 6개만 반환


def _build_health_reason(category_scores: Dict, risk_levels: Dict, main_bottleneck: Optional[str]) -> str:
    """
    건강검진 근거 문구 생성
    
    Returns:
        "최근 건강검진: F 🔴 (45점)" 같은 형식
    """
    if not main_bottleneck:
        return ""
    
    score = category_scores.get(main_bottleneck, 0)
    risk_level = risk_levels.get(main_bottleneck, "unknown")
    category_name = CATEGORY_NAMES.get(main_bottleneck, main_bottleneck)
    
    risk_emoji = {
        "red": "🔴",
        "yellow": "🟡",
        "green": "🟢"
    }.get(risk_level, "⚪")
    
    return f"최근 건강검진: {main_bottleneck}({category_name}) {risk_emoji} ({score:.0f}점)"
