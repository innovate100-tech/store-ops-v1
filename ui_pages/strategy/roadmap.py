"""
이번 주 실행 로드맵 생성
- 전략 카드 기반으로 실행 가능한 작업 3개 생성
"""
from __future__ import annotations

from typing import Dict, List


def build_weekly_roadmap(cards_payload: Dict) -> List[Dict]:
    """
    이번 주 실행 로드맵 TOP3 생성
    
    Args:
        cards_payload: build_strategy_cards() 결과
    
    Returns:
        [
            {
                "rank": 1,
                "task": "...",
                "estimate": "10m" | "30m" | "60m",
                "cta": {"label": "...", "page": "...", "params": {}}
            },
            ...
        ]
    """
    if not cards_payload or not cards_payload.get("cards"):
        return _get_default_roadmap()
    
    cards = cards_payload.get("cards", [])[:3]
    roadmap = []
    
    for card in cards:
        task = _extract_task_from_card(card)
        estimate = _estimate_task_time(card)
        cta = card.get("cta", {})
        
        roadmap.append({
            "rank": card.get("rank", len(roadmap) + 1),
            "task": task,
            "estimate": estimate,
            "cta": cta
        })
    
    # 3개 미만이면 기본 작업으로 채움
    while len(roadmap) < 3:
        default_task = _get_default_roadmap()[len(roadmap)]
        roadmap.append(default_task)
    
    return roadmap[:3]


def _extract_task_from_card(card: Dict) -> str:
    """카드에서 실행형 작업 문구 추출"""
    title = card.get("title", "")
    goal = card.get("goal", "")
    
    # title이 명령형이면 그대로 사용
    if title:
        return title
    
    # goal에서 실행형 추출
    if "점검" in goal:
        return "구조 점검하기"
    elif "설계" in goal:
        return "구조 설계하기"
    elif "정리" in goal:
        return "데이터 정리하기"
    elif "찾기" in goal:
        return "원인 찾기"
    else:
        return "전략 실행하기"


def _estimate_task_time(card: Dict) -> str:
    """
    작업 시간 추정
    
    규칙:
    - revenue/ingredient 구조 작업 => 60m
    - portfolio 정리 => 30m
    - 매출 원인 찾기 => 10m
    - 데이터 채우기 => 30m
    """
    cta_page = card.get("cta", {}).get("page", "")
    title = card.get("title", "").lower()
    
    # 수익 구조 / 재료 구조
    if "수익 구조" in cta_page or "재료" in cta_page:
        return "60m"
    
    # 포트폴리오 / 메뉴 등록
    if "포트폴리오" in cta_page or "메뉴 등록" in cta_page:
        return "30m"
    
    # 매출 하락 원인 찾기
    if "매출 하락" in cta_page or "원인 찾기" in title:
        return "10m"
    
    # 데이터 채우기 / 설계 센터
    if "설계 센터" in cta_page or "데이터" in title:
        return "30m"
    
    # 메뉴 수익 구조
    if "메뉴 수익" in cta_page:
        return "30m"
    
    # 기본값
    return "30m"


def _get_default_roadmap() -> List[Dict]:
    """기본 로드맵 (데이터 부족 시)"""
    return [
        {
            "rank": 1,
            "task": "설계 데이터 채우기",
            "estimate": "30m",
            "cta": {
                "label": "가게 설계 센터로 이동",
                "page": "가게 설계 센터",
                "params": {}
            }
        },
        {
            "rank": 2,
            "task": "오늘 입력 완료하기",
            "estimate": "10m",
            "cta": {
                "label": "점장 마감으로 이동",
                "page": "점장 마감",
                "params": {}
            }
        },
        {
            "rank": 3,
            "task": "매출 하락 원인 찾기",
            "estimate": "10m",
            "cta": {
                "label": "원인 찾기",
                "page": "매출 하락 원인 찾기",
                "params": {}
            }
        }
    ]
