"""
사장 루틴 상태 관리
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from src.storage_supabase import load_official_daily_sales
import streamlit as st


def get_routine_status(store_id: str) -> dict:
    """
    루틴 상태 조회
    
    Returns:
        {
            "daily_close_done": bool,
            "weekly_design_check_done": bool,
            "monthly_structure_review_done": bool,
            "messages": {
                "daily_close": str,
                "weekly_design": str,
                "monthly_review": str
            }
        }
    """
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    today = now.date()
    year = now.year
    month = now.month
    
    # 이번 주 계산 (ISO 주)
    week_num = now.isocalendar()[1]
    week_key = f"{year}-W{week_num:02d}"
    
    # 이번 달 키
    month_key = f"{year}-{month:02d}"
    
    # 1) 오늘 마감 완료 여부
    daily_close_done = False
    try:
        official_df = load_official_daily_sales(store_id=store_id)
        if not official_df.empty and 'date' in official_df.columns:
            today_str = today.isoformat()
            daily_close_done = today_str in official_df['date'].astype(str).values
    except Exception:
        pass
    
    # 2) 이번 주 구조 점검 완료 여부 (session_state)
    weekly_key = f"routine_weekly_checked::{store_id}::{week_key}"
    weekly_design_check_done = st.session_state.get(weekly_key, False)
    
    # 3) 이번 달 구조 판결 확인 완료 여부 (session_state)
    monthly_key = f"routine_monthly_reviewed::{store_id}::{month_key}"
    monthly_structure_review_done = st.session_state.get(monthly_key, False)
    
    # 메시지 생성
    messages = {
        "daily_close": "✅ 오늘 마감 완료" if daily_close_done else "⚠️ 오늘 마감 미완료",
        "weekly_design": "✅ 이번 주 구조 점검 완료" if weekly_design_check_done else "⚠️ 이번 주 구조 점검 미완료",
        "monthly_review": "✅ 이번 달 구조 판결 확인 완료" if monthly_structure_review_done else "⚠️ 이번 달 구조 판결 확인 미완료",
    }
    
    return {
        "daily_close_done": daily_close_done,
        "weekly_design_check_done": weekly_design_check_done,
        "monthly_structure_review_done": monthly_structure_review_done,
        "messages": messages
    }


def mark_weekly_check_done(store_id: str):
    """이번 주 구조 점검 완료 처리"""
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    year = now.year
    week_num = now.isocalendar()[1]
    week_key = f"{year}-W{week_num:02d}"
    
    key = f"routine_weekly_checked::{store_id}::{week_key}"
    st.session_state[key] = True


def mark_monthly_review_done(store_id: str):
    """이번 달 구조 판결 확인 완료 처리"""
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    year = now.year
    month = now.month
    month_key = f"{year}-{month:02d}"
    
    key = f"routine_monthly_reviewed::{store_id}::{month_key}"
    st.session_state[key] = True
