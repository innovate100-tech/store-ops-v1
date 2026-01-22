"""
한국 시간(KST) 기준 시간 유틸리티
앱 전체에서 "현재 시각/오늘/이번달" 기준을 KST로 통일하기 위한 공통 함수
"""
from datetime import datetime, date
from zoneinfo import ZoneInfo


def now_kst():
    """
    현재 시각을 한국 시간(KST)으로 반환
    
    Returns:
        datetime: KST 기준 현재 시각
    """
    return datetime.now(ZoneInfo("Asia/Seoul"))


def today_kst():
    """
    오늘 날짜를 한국 시간(KST) 기준으로 반환
    
    Returns:
        date: KST 기준 오늘 날짜
    """
    return now_kst().date()


def current_year_kst():
    """
    현재 연도를 한국 시간(KST) 기준으로 반환
    
    Returns:
        int: KST 기준 현재 연도
    """
    return now_kst().year


def current_month_kst():
    """
    현재 월을 한국 시간(KST) 기준으로 반환
    
    Returns:
        int: KST 기준 현재 월 (1-12)
    """
    return now_kst().month
