"""
건강검진 판독 · 경영 해석 엔진

역할:
- 기존 scoring 결과(축별 점수, raw answers)를 입력으로 받아
- 경영 관점 판독 결과를 생성
- HOME/전략 엔진에 넘길 구조화된 판독 데이터 생성
"""

import logging
from typing import Dict, List, Optional, Tuple
from src.health_check.questions_bank import CATEGORIES_ORDER

logger = logging.getLogger(__name__)


# ============================================
# 위험도 레벨 정의 (축별 공통 기준)
# ============================================

def get_risk_level(score: float) -> str:
    """
    점수에 따른 위험도 레벨 판정
    
    Args:
        score: 축별 점수 (0~100, 10점 만점 기준으로 변환 필요)
    
    Returns:
        'good' | 'mid' | 'high'
        - score >= 7.5  → "good"
        - 5.0 ~ 7.49   → "mid"
        - < 5.0        → "high"
    """
    # 점수를 10점 만점으로 변환 (100점 만점 → 10점 만점)
    score_10 = score / 10.0
    
    if score_10 >= 7.5:
        return "good"
    elif score_10 >= 5.0:
        return "mid"
    else:
        return "high"


# 축별 메타 정보 (의미 문구 딕셔너리)
AXIS_META = {
    "Q": {
        "name": "품질",
        "high": "품질 붕괴 위험",
        "mid": "품질 불안정",
        "good": "품질 안정"
    },
    "S": {
        "name": "서비스",
        "high": "재방문 붕괴 위험",
        "mid": "경험 일관성 부족",
        "good": "서비스 안정"
    },
    "C": {
        "name": "청결",
        "high": "위생 리스크",
        "mid": "관리 불안정",
        "good": "청결 안정"
    },
    "P1": {
        "name": "가격",
        "high": "가격 신뢰 붕괴",
        "mid": "가격 저항 가능성",
        "good": "가격 구조 안정"
    },
    "P2": {
        "name": "공간",
        "high": "공간 매력 상실",
        "mid": "체류 매력 약함",
        "good": "공간 경쟁력"
    },
    "P3": {
        "name": "입지",
        "high": "입지 활용 실패",
        "mid": "입지 대비 효율 낮음",
        "good": "입지 활용 양호"
    },
    "M": {
        "name": "마케팅",
        "high": "유입 구조 부재",
        "mid": "인지 약함",
        "good": "유입 구조 존재"
    },
    "H": {
        "name": "인적자원",
        "high": "운영 붕괴 신호",
        "mid": "교육/관리 미흡",
        "good": "운영 안정"
    },
    "F": {
        "name": "재무",
        "high": "수익 구조 위험",
        "mid": "이익 구조 불안",
        "good": "수익 구조 안정"
    }
}


# ============================================
# Top3 리스크 추출 로직
# ============================================

def extract_top3_risks(axis_scores: Dict[str, float]) -> List[Dict]:
    """
    Top3 리스크 추출
    
    Args:
        axis_scores: {"Q": 7.2, "S": 5.1, ...} (0~100 점수)
    
    Returns:
        [
            {"axis": "H", "score": 3.8, "level": "high", "reason": "인력/운영 붕괴 신호"},
            ...
        ]
        최대 3개, level == "high" 우선, 없으면 mid 중 하위부터
    """
    # 점수를 10점 만점으로 변환하여 레벨 계산
    risk_items = []
    
    for axis, score in axis_scores.items():
        if axis not in AXIS_META:
            continue
        
        score_10 = score / 10.0
        level = get_risk_level(score)
        meta = AXIS_META[axis]
        
        # reason 생성
        if level == "high":
            reason = meta["high"]
        elif level == "mid":
            reason = meta["mid"]
        else:
            reason = meta["good"]
        
        risk_items.append({
            "axis": axis,
            "score": round(score_10, 1),  # 10점 만점으로 변환
            "level": level,
            "reason": reason
        })
    
    # 정렬: level 우선 (high > mid > good), 같은 level 내에서는 점수 오름차순
    def sort_key(item):
        level_priority = {"high": 0, "mid": 1, "good": 2}
        return (level_priority.get(item["level"], 99), item["score"])
    
    risk_items.sort(key=sort_key)
    
    # 최대 3개 반환
    return risk_items[:3]


# ============================================
# 경영 패턴 엔진 (v1 패턴 6종)
# ============================================

PATTERN_DEFINITIONS = {
    "OPERATION_BREAKDOWN": {
        "title": "운영 붕괴형",
        "description": "인력·서비스·위생 축이 동시에 약화된 상태로, 숫자보다 현장 붕괴가 먼저 오는 유형",
        "condition": lambda scores: (
            (scores.get("H", 0) / 10.0 < 5.2) and
            (scores.get("S", 0) / 10.0 < 5.2) and
            (scores.get("C", 0) / 10.0 < 5.2)
        ),
        "weight": 3.0
    },
    "REVISIT_COLLAPSE": {
        "title": "재방문 붕괴형",
        "description": "품질과 서비스가 동시에 낮아 고객 재방문이 급격히 감소하는 패턴",
        "condition": lambda scores: (
            (scores.get("Q", 0) / 10.0 < 5.5) and
            (scores.get("S", 0) / 10.0 < 5.5)
        ),
        "weight": 2.5
    },
    "PRICE_STRUCTURE_RISK": {
        "title": "가격/마진 붕괴형",
        "description": "가격 신뢰도와 재무 구조가 동시에 약화되어 수익성이 위협받는 상태",
        "condition": lambda scores: (
            (scores.get("P1", 0) / 10.0 < 5.0) and
            (scores.get("F", 0) / 10.0 < 5.5)
        ),
        "weight": 2.5
    },
    "PRODUCT_STRUCTURE_WEAK": {
        "title": "상품·공간 매력 저하형",
        "description": "품질과 공간 매력이 동시에 낮아 고객 만족도가 급격히 하락하는 패턴",
        "condition": lambda scores: (
            (scores.get("Q", 0) / 10.0 < 6.0) and
            (scores.get("P2", 0) / 10.0 < 5.5)
        ),
        "weight": 2.0
    },
    "GROWTH_BLOCKED": {
        "title": "입지 대비 성장 실패형",
        "description": "입지는 좋지만 마케팅이 부재하여 성장 기회를 놓치고 있는 상태",
        "condition": lambda scores: (
            (scores.get("M", 0) / 10.0 < 5.0) and
            (scores.get("P3", 0) / 10.0 >= 6.0)
        ),
        "weight": 1.5
    },
    "FINANCIAL_DANGER": {
        "title": "생존선 위험형",
        "description": "재무 구조가 생존선 이하로 떨어져 즉각적인 구조 개선이 필요한 상태",
        "condition": lambda scores: (
            scores.get("F", 0) / 10.0 < 4.8
        ),
        "weight": 3.5
    }
}


def detect_primary_pattern(axis_scores: Dict[str, float]) -> Dict:
    """
    경영 패턴 감지
    
    Args:
        axis_scores: {"Q": 7.2, "S": 5.1, ...} (0~100 점수)
    
    Returns:
        {
            "code": "OPERATION_BREAKDOWN",
            "title": "운영 붕괴형",
            "description": "..."
        }
    """
    matched_patterns = []
    
    for pattern_code, pattern_def in PATTERN_DEFINITIONS.items():
        if pattern_def["condition"](axis_scores):
            matched_patterns.append({
                "code": pattern_code,
                "weight": pattern_def["weight"]
            })
    
    if not matched_patterns:
        # 패턴이 없으면 기본값 (모든 축이 양호한 상태)
        return {
            "code": "STABLE",
            "title": "안정형",
            "description": "모든 축이 안정적인 상태로, 현재 구조를 유지하면서 점진적 개선이 가능한 상태"
        }
    
    # 위험도 가중치 합으로 primary 선택
    matched_patterns.sort(key=lambda x: x["weight"], reverse=True)
    primary_code = matched_patterns[0]["code"]
    primary_def = PATTERN_DEFINITIONS[primary_code]
    
    return {
        "code": primary_code,
        "title": primary_def["title"],
        "description": primary_def["description"]
    }


# ============================================
# 경영 판독 문장 생성기
# ============================================

def generate_insight_summary(
    axis_scores: Dict[str, float],
    primary_pattern: Dict,
    top3_risks: List[Dict]
) -> List[str]:
    """
    경영 판독 문장 생성
    
    Returns:
        [
            "핵심 판결 문장",
            "위험 구조 문장",
            "경영 경고 문장"
        ]
    """
    insights = []
    
    # A) 핵심 판결
    pattern_title = primary_pattern.get("title", "안정형")
    insights.append(f"이번 검진 기준, 이 가게는 '{pattern_title}' 패턴이 감지됩니다.")
    
    # B) 위험 구조
    high_risks = [r for r in top3_risks if r["level"] == "high"]
    mid_risks = [r for r in top3_risks if r["level"] == "mid"]
    
    if high_risks:
        risk_axes = [AXIS_META[r["axis"]]["name"] for r in high_risks[:2]]
        if len(risk_axes) == 2:
            insights.append(f"{risk_axes[0]}({high_risks[0]['axis']}), {risk_axes[1]}({high_risks[1]['axis']}) 축이 동시에 낮아 현장 운영 리스크가 큽니다.")
        elif len(risk_axes) == 1:
            insights.append(f"{risk_axes[0]}({high_risks[0]['axis']}) 축이 매우 낮아 즉각적인 개선이 필요합니다.")
        else:
            insights.append("여러 축에서 높은 위험도가 감지되었습니다.")
    elif mid_risks:
        risk_axes = [AXIS_META[r["axis"]]["name"] for r in mid_risks[:2]]
        if len(risk_axes) >= 1:
            insights.append(f"{risk_axes[0]}({mid_risks[0]['axis']}) 축이 불안정하여 지속적인 모니터링이 필요합니다.")
        else:
            insights.append("일부 축에서 불안정한 신호가 감지되었습니다.")
    else:
        insights.append("현재 모든 축이 안정적인 상태입니다.")
    
    # C) 경영 경고
    pattern_code = primary_pattern.get("code", "")
    if pattern_code == "OPERATION_BREAKDOWN":
        insights.append("이 상태에서 가격·메뉴 개편을 먼저 시도하면 실패 확률이 높습니다. 운영 안정화를 최우선으로 해야 합니다.")
    elif pattern_code == "REVISIT_COLLAPSE":
        insights.append("품질과 서비스 개선 없이는 마케팅 투자 효과가 제한적입니다.")
    elif pattern_code == "PRICE_STRUCTURE_RISK":
        insights.append("가격 구조와 재무 구조를 동시에 개선해야 지속 가능한 수익 구조를 만들 수 있습니다.")
    elif pattern_code == "FINANCIAL_DANGER":
        insights.append("즉각적인 재무 구조 개선이 필요합니다. 생존선 이하 상태입니다.")
    elif pattern_code == "GROWTH_BLOCKED":
        insights.append("입지 대비 마케팅이 부재하여 성장 기회를 놓치고 있습니다.")
    else:
        insights.append("현재 구조를 유지하면서 점진적 개선을 추진하세요.")
    
    return insights


# ============================================
# 전략 가중치 출력
# ============================================

def calculate_strategy_bias(primary_pattern: Dict, axis_scores: Dict[str, float]) -> Dict[str, float]:
    """
    패턴/리스크에 따라 strategy_bias 생성
    
    Returns:
        {
            "operation_fix": 0.82,
            "menu_structure": 0.21,
            "pricing": 0.18,
            "marketing": 0.12,
            "finance_control": 0.33
        }
    """
    pattern_code = primary_pattern.get("code", "STABLE")
    
    # 기본 가중치 (모든 전략 균등)
    base_bias = {
        "operation_fix": 0.2,
        "menu_structure": 0.2,
        "pricing": 0.2,
        "marketing": 0.2,
        "finance_control": 0.2
    }
    
    # 패턴별 가중치 조정
    if pattern_code == "OPERATION_BREAKDOWN":
        base_bias["operation_fix"] = 0.85
        base_bias["menu_structure"] = 0.15
        base_bias["pricing"] = 0.10
        base_bias["marketing"] = 0.05
        base_bias["finance_control"] = 0.25
    elif pattern_code == "REVISIT_COLLAPSE":
        base_bias["operation_fix"] = 0.70
        base_bias["menu_structure"] = 0.30
        base_bias["pricing"] = 0.15
        base_bias["marketing"] = 0.20
        base_bias["finance_control"] = 0.20
    elif pattern_code == "PRICE_STRUCTURE_RISK":
        base_bias["operation_fix"] = 0.30
        base_bias["menu_structure"] = 0.25
        base_bias["pricing"] = 0.80
        base_bias["marketing"] = 0.15
        base_bias["finance_control"] = 0.70
    elif pattern_code == "PRODUCT_STRUCTURE_WEAK":
        base_bias["operation_fix"] = 0.40
        base_bias["menu_structure"] = 0.75
        base_bias["pricing"] = 0.30
        base_bias["marketing"] = 0.25
        base_bias["finance_control"] = 0.30
    elif pattern_code == "GROWTH_BLOCKED":
        base_bias["operation_fix"] = 0.25
        base_bias["menu_structure"] = 0.20
        base_bias["pricing"] = 0.15
        base_bias["marketing"] = 0.85
        base_bias["finance_control"] = 0.20
    elif pattern_code == "FINANCIAL_DANGER":
        base_bias["operation_fix"] = 0.35
        base_bias["menu_structure"] = 0.20
        base_bias["pricing"] = 0.70
        base_bias["marketing"] = 0.10
        base_bias["finance_control"] = 0.90
    
    # 재무 축이 낮으면 finance_control 가중치 추가
    if axis_scores.get("F", 0) / 10.0 < 5.0:
        base_bias["finance_control"] = min(1.0, base_bias["finance_control"] + 0.2)
    
    # 정규화 (합이 1이 되도록)
    total = sum(base_bias.values())
    if total > 0:
        normalized = {k: round(v / total, 2) for k, v in base_bias.items()}
    else:
        normalized = base_bias
    
    return normalized


# ============================================
# 메인 진단 함수
# ============================================

def diagnose_health_check(
    session_id: str,
    store_id: str,
    axis_scores: Dict[str, float],
    axis_raw: Optional[Dict[str, List[str]]] = None,
    meta: Optional[Dict] = None
) -> Dict:
    """
    건강검진 판독 실행
    
    Args:
        session_id: 세션 ID
        store_id: 매장 ID
        axis_scores: {"Q": 75.2, "S": 51.0, ...} (0~100 점수)
        axis_raw: {"Q": ["yes", "no", ...], ...} (선택, raw answers)
        meta: (선택, 이전 검진, 날짜 등)
    
    Returns:
        {
            "risk_axes": [...],
            "primary_pattern": {...},
            "insight_summary": [...],
            "strategy_bias": {...}
        }
    """
    try:
        # 1. Top3 리스크 추출
        risk_axes = extract_top3_risks(axis_scores)
        
        # 2. 경영 패턴 감지
        primary_pattern = detect_primary_pattern(axis_scores)
        
        # 3. 경영 판독 문장 생성
        insight_summary = generate_insight_summary(axis_scores, primary_pattern, risk_axes)
        
        # 4. 전략 가중치 계산
        strategy_bias = calculate_strategy_bias(primary_pattern, axis_scores)
        
        return {
            "risk_axes": risk_axes,
            "primary_pattern": primary_pattern,
            "insight_summary": insight_summary,
            "strategy_bias": strategy_bias
        }
    
    except Exception as e:
        logger.error(f"diagnose_health_check: Error - {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # 에러 시 기본값 반환
        return {
            "risk_axes": [],
            "primary_pattern": {
                "code": "UNKNOWN",
                "title": "판독 불가",
                "description": "판독 중 오류가 발생했습니다."
            },
            "insight_summary": ["판독 결과를 생성할 수 없습니다."],
            "strategy_bias": {
                "operation_fix": 0.2,
                "menu_structure": 0.2,
                "pricing": 0.2,
                "marketing": 0.2,
                "finance_control": 0.2
            }
        }


# ============================================
# DEV 검증 함수
# ============================================

def dev_test_diagnosis():
    """
    DEV 검증 함수: 임의 점수 dict로 판독 리포트 출력
    """
    print("=" * 60)
    print("건강검진 판독 엔진 DEV 테스트")
    print("=" * 60)
    
    # 테스트 케이스 1: 운영 붕괴형
    test_scores_1 = {
        "Q": 60.0,  # 6.0
        "S": 45.0,  # 4.5
        "C": 40.0,  # 4.0
        "P1": 70.0,
        "P2": 65.0,
        "P3": 75.0,
        "M": 50.0,
        "H": 35.0,  # 3.5
        "F": 55.0
    }
    
    print("\n[테스트 케이스 1] 운영 붕괴형")
    print("-" * 60)
    result_1 = diagnose_health_check("test-1", "test-store", test_scores_1)
    print(f"패턴: {result_1['primary_pattern']['title']}")
    print(f"Top3 리스크:")
    for risk in result_1['risk_axes']:
        print(f"  - {risk['axis']}: {risk['score']}/10 ({risk['level']}) - {risk['reason']}")
    print(f"\n판독 요약:")
    for insight in result_1['insight_summary']:
        print(f"  - {insight}")
    print(f"\n전략 가중치:")
    for strategy, weight in result_1['strategy_bias'].items():
        print(f"  - {strategy}: {weight}")
    
    # 테스트 케이스 2: 재방문 붕괴형
    test_scores_2 = {
        "Q": 50.0,  # 5.0
        "S": 48.0,  # 4.8
        "C": 70.0,
        "P1": 75.0,
        "P2": 65.0,
        "P3": 80.0,
        "M": 60.0,
        "H": 70.0,
        "F": 65.0
    }
    
    print("\n\n[테스트 케이스 2] 재방문 붕괴형")
    print("-" * 60)
    result_2 = diagnose_health_check("test-2", "test-store", test_scores_2)
    print(f"패턴: {result_2['primary_pattern']['title']}")
    print(f"Top3 리스크:")
    for risk in result_2['risk_axes']:
        print(f"  - {risk['axis']}: {risk['score']}/10 ({risk['level']}) - {risk['reason']}")
    print(f"\n판독 요약:")
    for insight in result_2['insight_summary']:
        print(f"  - {insight}")
    print(f"\n전략 가중치:")
    for strategy, weight in result_2['strategy_bias'].items():
        print(f"  - {strategy}: {weight}")
    
    print("\n" + "=" * 60)
    print("DEV 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    dev_test_diagnosis()
