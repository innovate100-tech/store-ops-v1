"""
전략 미션 결과 기반 다음 개입 결정 엔진
"""
from __future__ import annotations

from typing import Dict, Optional


def decide_next_intervention(mission: Dict, result: Dict) -> Optional[Dict]:
    """
    미션 결과 기반 다음 개입 결정
    
    Args:
        mission: 미션 dict (cause_type 포함)
        result: 평가 결과 dict (result_type, coach_comment 포함)
    
    Returns:
        {
            "next_cause_type": str,  # 다음 추천 원인 타입
            "next_cta_page": str,  # 다음 CTA 페이지
            "next_strategy_title": str,  # 다음 전략 카드 제목
            "next_reason_bullets": List[str],  # 다음 근거
            "intervention_type": str,  # "maintain" | "escalate" | "pivot" | "wait"
        } 또는 None
    """
    if not mission or not result:
        return None
    
    cause_type = mission.get("cause_type", "")
    result_type = result.get("result_type", "")
    
    intervention = {
        "next_cause_type": "",
        "next_cta_page": "",
        "next_strategy_title": "",
        "next_reason_bullets": [],
        "intervention_type": "",
    }
    
    # improved: 유지 전략
    if result_type == "improved":
        intervention["intervention_type"] = "maintain"
        intervention["next_strategy_title"] = "현재 전략 유지 + 메뉴/구조 최적화"
        intervention["next_reason_bullets"] = [
            "이전 전략이 효과를 보였습니다",
            "지속적인 최적화가 필요합니다",
        ]
        intervention["next_cta_page"] = "가게 설계 센터"
        intervention["next_cause_type"] = cause_type  # 동일 유지
    
    # no_change: 다음 원인 후보
    elif result_type == "no_change":
        intervention["intervention_type"] = "pivot"
        
        # 원인 타입별 다음 후보
        next_cause_map = {
            "유입 감소형": "객단가 하락형",
            "객단가 하락형": "판매량 하락형",
            "판매량 하락형": "주력메뉴 붕괴형",
            "주력메뉴 붕괴형": "원가율 악화형",
            "원가율 악화형": "구조 리스크형",
            "구조 리스크형": "유입 감소형",
        }
        
        next_cause = next_cause_map.get(cause_type, "판매량 하락형")
        intervention["next_cause_type"] = next_cause
        intervention["next_strategy_title"] = f"{next_cause} 대응 전략"
        intervention["next_reason_bullets"] = [
            "이전 전략의 효과가 제한적이었습니다",
            "다른 원인을 점검해야 합니다",
        ]
        
        # CTA 페이지 매핑
        cta_map = {
            "유입 감소형": "메뉴 등록",
            "객단가 하락형": "메뉴 수익 구조 설계실",
            "판매량 하락형": "판매 관리",
            "주력메뉴 붕괴형": "메뉴 수익 구조 설계실",
            "원가율 악화형": "메뉴 수익 구조 설계실",
            "구조 리스크형": "수익 구조 설계실",
        }
        intervention["next_cta_page"] = cta_map.get(next_cause, "가게 설계 센터")
    
    # worsened: 상위 구조로 격상
    elif result_type == "worsened":
        intervention["intervention_type"] = "escalate"
        
        # 상위 구조로 격상
        escalation_map = {
            "유입 감소형": "구조 리스크형",
            "객단가 하락형": "구조 리스크형",
            "판매량 하락형": "구조 리스크형",
            "주력메뉴 붕괴형": "구조 리스크형",
            "원가율 악화형": "구조 리스크형",
            "구조 리스크형": "구조 리스크형",  # 이미 최상위
        }
        
        escalated_cause = escalation_map.get(cause_type, "구조 리스크형")
        intervention["next_cause_type"] = escalated_cause
        intervention["next_strategy_title"] = "상위 구조 점검 (수익 구조 설계실)"
        intervention["next_reason_bullets"] = [
            "이전 전략으로는 해결되지 않았습니다",
            "고정비/변동비 구조부터 점검이 필요합니다",
        ]
        intervention["next_cta_page"] = "수익 구조 설계실"
    
    # data_insufficient: 감시 유지
    else:  # data_insufficient
        intervention["intervention_type"] = "wait"
        intervention["next_strategy_title"] = "데이터 수집 중"
        intervention["next_reason_bullets"] = [
            "아직 7일이 지나지 않았습니다",
            "데이터가 더 쌓이면 자동으로 평가합니다",
        ]
        intervention["next_cta_page"] = "홈"
        intervention["next_cause_type"] = cause_type  # 동일 유지
    
    return intervention
