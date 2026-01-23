"""
메뉴 포트폴리오 설계실 헬퍼 함수
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple


def get_menu_portfolio_tags(store_id: str) -> Dict[str, str]:
    """메뉴별 역할 태그 조회 (session_state)"""
    key = f"menu_portfolio_tags::{store_id}"
    return st.session_state.get(key, {})


def set_menu_portfolio_tag(store_id: str, menu_name: str, role: str):
    """메뉴 역할 태그 저장 (session_state)"""
    key = f"menu_portfolio_tags::{store_id}"
    if key not in st.session_state:
        st.session_state[key] = {}
    st.session_state[key][menu_name] = role


def get_menu_portfolio_categories(store_id: str) -> Dict[str, str]:
    """메뉴별 카테고리 조회 (session_state, DB에서도 로드)"""
    # DB에서 먼저 로드
    from src.storage_supabase import load_csv
    menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
    
    categories = {}
    if not menu_df.empty:
        if 'category' in menu_df.columns:
            for _, row in menu_df.iterrows():
                menu_name = row.get('메뉴명', '')
                category = row.get('category', '기타메뉴')
                if menu_name:
                    categories[menu_name] = category
        elif '카테고리' in menu_df.columns:
            for _, row in menu_df.iterrows():
                menu_name = row.get('메뉴명', '')
                category = row.get('카테고리', '기타메뉴')
                if menu_name:
                    categories[menu_name] = category
    
    # session_state에서도 로드 (포트폴리오 분류용)
    key = f"menu_portfolio_categories::{store_id}"
    session_categories = st.session_state.get(key, {})
    
    # session_state 우선 (포트폴리오 분류가 최신)
    for menu_name, category in session_categories.items():
        categories[menu_name] = category
    
    return categories


def set_menu_portfolio_category(store_id: str, menu_name: str, category: str):
    """메뉴 카테고리 저장 (session_state, DB도 업데이트)"""
    # session_state 저장
    key = f"menu_portfolio_categories::{store_id}"
    if key not in st.session_state:
        st.session_state[key] = {}
    st.session_state[key][menu_name] = category
    
    # DB도 업데이트 (기존 함수 사용)
    from src.storage_supabase import update_menu_category
    try:
        update_menu_category(menu_name, category)
    except Exception:
        pass  # DB 업데이트 실패해도 session_state는 저장됨


def calculate_portfolio_balance_score(menu_df: pd.DataFrame, roles: Dict[str, str], categories: Dict[str, str]) -> Tuple[int, str]:
    """
    포트폴리오 균형 점수 계산 (0~100)
    
    Returns:
        (score: int, status: str)
        status: "균형" | "주의" | "위험"
    """
    if menu_df.empty:
        return 0, "위험"
    
    # 역할 분포
    role_counts = {"미끼": 0, "볼륨": 0, "마진": 0, "미분류": 0}
    for menu_name in menu_df['메뉴명'].tolist():
        role = roles.get(menu_name, "미분류")
        if role in role_counts:
            role_counts[role] += 1
        else:
            role_counts["미분류"] += 1
    
    # 카테고리 분포
    category_counts = {"대표메뉴": 0, "주력메뉴": 0, "유인메뉴": 0, "보조메뉴": 0, "기타메뉴": 0, "미분류": 0}
    for menu_name in menu_df['메뉴명'].tolist():
        category = categories.get(menu_name, "미분류")
        if category in category_counts:
            category_counts[category] += 1
        else:
            category_counts["미분류"] += 1
    
    total_menus = len(menu_df)
    if total_menus == 0:
        return 0, "위험"
    
    score = 100
    issues = []
    
    # 역할 균형 체크
    role_classified = total_menus - role_counts["미분류"]
    if role_classified < total_menus * 0.5:  # 50% 미만 분류
        score -= 30
        issues.append("역할 미분류 과다")
    
    # 역할 편중 체크
    if role_counts["미끼"] > total_menus * 0.5:  # 미끼 메뉴가 50% 초과
        score -= 20
        issues.append("미끼 메뉴 과다")
    if role_counts["볼륨"] > total_menus * 0.6:  # 볼륨 메뉴가 60% 초과
        score -= 15
        issues.append("볼륨 메뉴 과다")
    if role_counts["마진"] == 0 and total_menus >= 3:  # 마진 메뉴 없음
        score -= 20
        issues.append("마진 메뉴 부족")
    
    # 카테고리 균형 체크
    if category_counts["대표메뉴"] == 0 and total_menus >= 3:
        score -= 15
        issues.append("대표메뉴 부족")
    if category_counts["유인메뉴"] == 0 and total_menus >= 5:
        score -= 10
        issues.append("유인메뉴 부족")
    if category_counts["주력메뉴"] == 0 and total_menus >= 5:
        score -= 10
        issues.append("주력메뉴 부족")
    
    # 카테고리 편중 체크
    max_category_count = max(category_counts.values())
    if max_category_count > total_menus * 0.7:  # 한 카테고리가 70% 초과
        score -= 15
        issues.append("카테고리 편중")
    
    score = max(0, min(100, score))
    
    if score >= 70:
        status = "균형"
    elif score >= 40:
        status = "주의"
    else:
        status = "위험"
    
    return score, status


def get_portfolio_verdict(menu_df: pd.DataFrame, roles: Dict[str, str], categories: Dict[str, str], avg_price: float) -> Tuple[str, str, str]:
    """
    포트폴리오 판결문 생성
    
    Returns:
        (verdict_text: str, action_title: str, action_target_page: str)
    """
    if menu_df.empty:
        return "메뉴가 등록되지 않았습니다. 메뉴를 등록하면 포트폴리오 분석이 시작됩니다.", "메뉴 등록 시작하기", "메뉴 등록"
    
    total_menus = len(menu_df)
    role_counts = {"미끼": 0, "볼륨": 0, "마진": 0, "미분류": 0}
    for menu_name in menu_df['메뉴명'].tolist():
        role = roles.get(menu_name, "미분류")
        if role in role_counts:
            role_counts[role] += 1
        else:
            role_counts["미분류"] += 1
    
    category_counts = {"대표메뉴": 0, "주력메뉴": 0, "유인메뉴": 0, "보조메뉴": 0, "기타메뉴": 0}
    for menu_name in menu_df['메뉴명'].tolist():
        category = categories.get(menu_name, "기타메뉴")
        if category in category_counts:
            category_counts[category] += 1
    
    # 판결 우선순위
    if category_counts["유인메뉴"] == 0 and total_menus >= 5:
        return "유인메뉴가 부족해 객단가 상승 장치가 약합니다.", "메뉴 수익 구조 설계실", "메뉴 수익 구조 설계실"
    
    if role_counts["마진"] == 0 and total_menus >= 3:
        return "마진 메뉴가 없어 수익 기여도가 낮을 수 있습니다.", "메뉴 수익 구조 설계실", "메뉴 수익 구조 설계실"
    
    if role_counts["미끼"] > total_menus * 0.5:
        return f"미끼 메뉴가 {role_counts['미끼']}개로 과다합니다. 볼륨/마진 메뉴 비율을 늘리세요.", "메뉴 수익 구조 설계실", "메뉴 수익 구조 설계실"
    
    if role_counts["미분류"] > total_menus * 0.3:
        return f"역할이 분류되지 않은 메뉴가 {role_counts['미분류']}개 있습니다. 포트폴리오 분류를 완료하세요.", "메뉴 포트폴리오 설계", "메뉴 등록"
    
    # 원가율 위험 체크 (간단 버전)
    if avg_price > 0:
        # 평균 가격이 낮은데 메뉴가 많으면 원가율 위험 가능성
        if avg_price < 10000 and total_menus >= 5:
            return "평균 가격이 낮은 편입니다. 원가율 관리가 중요합니다.", "메뉴 수익 구조 설계실", "메뉴 수익 구조 설계실"
    
    return "메뉴 포트폴리오가 균형 잡힌 상태입니다.", None, None
