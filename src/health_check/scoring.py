"""
건강검진 점수/리스크/병목 계산 엔진
"""

from typing import Dict, List, Optional
from src.health_check.questions_bank import CATEGORIES_ORDER


def score_from_raw(raw_value: str) -> int:
    """
    raw_value를 점수로 변환
    
    Args:
        raw_value: 'yes' | 'maybe' | 'no'
    
    Returns:
        점수: yes=3, maybe=1, no=0
    
    Raises:
        ValueError: raw_value가 유효하지 않은 경우
    """
    mapping = {
        'yes': 3,
        'maybe': 1,
        'no': 0
    }
    
    if raw_value not in mapping:
        raise ValueError(f"Invalid raw_value: {raw_value}. Must be 'yes', 'maybe', or 'no'")
    
    return mapping[raw_value]


def calc_category_score(answers: List[int]) -> float:
    """
    카테고리별 평균 점수 계산 (0~100)
    
    Args:
        answers: 점수 리스트 (각 문항의 점수: 0, 1, 3)
    
    Returns:
        평균 점수 (0~100): (sum(answers) / (len(answers) * 3)) * 100
    
    Note:
        - 답변이 없으면 0 반환
        - 최대 점수는 문항 수 * 3
    """
    if not answers or len(answers) == 0:
        return 0.0
    
    total_score = sum(answers)
    max_possible_score = len(answers) * 3
    
    if max_possible_score == 0:
        return 0.0
    
    return (total_score / max_possible_score) * 100.0


def risk_level(score: float) -> str:
    """
    점수에 따른 리스크 레벨 판정
    
    Args:
        score: 카테고리 점수 (0~100)
    
    Returns:
        'green' | 'yellow' | 'red'
        - >= 75: green
        - >= 45: yellow
        - < 45: red
    """
    if score >= 75:
        return 'green'
    elif score >= 45:
        return 'yellow'
    else:
        return 'red'


def overall_grade(overall_score: float) -> str:
    """
    전체 점수에 따른 등급 계산
    
    Args:
        overall_score: 전체 평균 점수 (0~100)
    
    Returns:
        'A' | 'B' | 'C' | 'D' | 'E'
        - >= 85: A
        - >= 70: B
        - >= 55: C
        - >= 40: D
        - < 40: E
    """
    if overall_score >= 85:
        return 'A'
    elif overall_score >= 70:
        return 'B'
    elif overall_score >= 55:
        return 'C'
    elif overall_score >= 40:
        return 'D'
    else:
        return 'E'


def compute_session_results(answers_by_category: Dict[str, List[int]]) -> Dict:
    """
    세션 전체 결과 계산
    
    Args:
        answers_by_category: {category: [score1, score2, ...]}
            예: {'Q': [3, 1, 0, ...], 'S': [3, 3, 1, ...]}
    
    Returns:
        {
            'per_category': {
                'Q': {'score_avg': 75.5, 'risk_level': 'green'},
                'S': {'score_avg': 60.0, 'risk_level': 'yellow'},
                ...
            },
            'overall_score': 65.2,
            'overall_grade': 'C',
            'main_bottleneck': 'C'  # 가장 낮은 점수 카테고리
        }
    
    Note:
        - 답변이 없는 카테고리는 제외
        - main_bottleneck은 점수가 가장 낮은 카테고리 (동점 시 첫 번째)
    """
    per_category = {}
    category_scores = []
    
    # 카테고리별 점수 계산
    for category in CATEGORIES_ORDER:
        if category in answers_by_category and answers_by_category[category]:
            answers = answers_by_category[category]
            score_avg = calc_category_score(answers)
            risk = risk_level(score_avg)
            
            per_category[category] = {
                'score_avg': round(score_avg, 2),
                'risk_level': risk
            }
            category_scores.append((category, score_avg))
    
    # 전체 점수 계산 (카테고리별 평균의 평균)
    if category_scores:
        overall_score = sum(score for _, score in category_scores) / len(category_scores)
        overall_grade_val = overall_grade(overall_score)
    else:
        overall_score = 0.0
        overall_grade_val = 'E'
    
    # 병목 찾기 (가장 낮은 점수 카테고리)
    main_bottleneck = None
    if category_scores:
        # 점수가 낮은 순으로 정렬
        category_scores_sorted = sorted(category_scores, key=lambda x: x[1])
        main_bottleneck = category_scores_sorted[0][0]
    
    return {
        'per_category': per_category,
        'overall_score': round(overall_score, 2),
        'overall_grade': overall_grade_val,
        'main_bottleneck': main_bottleneck
    }


def compute_strength_flags(answers: List[int], category: str) -> List[str]:
    """
    강점 플래그 계산 (점수가 높은 문항들)
    
    Args:
        answers: 점수 리스트
        category: 카테고리 코드
    
    Returns:
        강점 플래그 리스트 (예: ['Q1', 'Q3'])
    
    Note:
        - 점수가 3인 문항만 강점으로 표시
    """
    from src.health_check.questions_bank import QUESTIONS
    
    flags = []
    category_questions = QUESTIONS.get(category, [])
    for idx, score in enumerate(answers):
        if score == 3 and idx < len(category_questions):
            question_code = category_questions[idx].get("code", "")
            if question_code:
                flags.append(question_code)
    
    return flags


def compute_risk_flags(answers: List[int], category: str) -> List[str]:
    """
    리스크 플래그 계산 (점수가 낮은 문항들)
    
    Args:
        answers: 점수 리스트
        category: 카테고리 코드
    
    Returns:
        리스크 플래그 리스트 (예: ['Q5', 'Q7'])
    
    Note:
        - 점수가 0인 문항만 리스크로 표시
    """
    from src.health_check.questions_bank import QUESTIONS
    
    flags = []
    category_questions = QUESTIONS.get(category, [])
    for idx, score in enumerate(answers):
        if score == 0 and idx < len(category_questions):
            question_code = category_questions[idx].get("code", "")
            if question_code:
                flags.append(question_code)
    
    return flags
