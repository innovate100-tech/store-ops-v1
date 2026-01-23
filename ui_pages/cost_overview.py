"""
원가 파악 페이지 (메뉴 수익 구조 설계실)
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header
from src.storage_supabase import load_csv
from src.analytics import calculate_menu_cost
from src.ui import render_cost_analysis
from ui_pages.design_lab.design_lab_frame import (
    render_coach_board,
    render_structure_map_container,
    render_school_cards,
    render_design_tools_container,
)
from ui_pages.design_lab.design_lab_coach_data import get_menu_profit_design_coach_data
from src.auth import get_current_store_id

# 공통 설정 적용
bootstrap(page_title="Cost Overview")


def render_cost_overview():
    """원가 파악 페이지 렌더링 (HOME v2 공통 프레임 적용)"""
    render_page_header("메뉴 수익 구조 설계실", "💰")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # ZONE A: Coach Board
    coach_data = get_menu_profit_design_coach_data(store_id)
    render_coach_board(
        cards=coach_data["cards"],
        verdict_text=coach_data["verdict_text"],
        action_title=coach_data.get("action_title"),
        action_reason=coach_data.get("action_reason"),
        action_target_page=coach_data.get("action_target_page"),
        action_button_label=coach_data.get("action_button_label")
    )
    
    # ZONE B: Structure Map
    def _render_menu_profit_structure_map():
        menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
        
        if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
            cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
            if not cost_df.empty and '원가율' in cost_df.columns:
                # 원가율 분포 차트
                st.bar_chart(cost_df.set_index('메뉴명')['원가율'].head(10))
            else:
                st.info("원가 데이터를 계산할 수 없습니다.")
        else:
            st.info("메뉴, 레시피, 재료 데이터가 모두 필요합니다.")
    
    render_structure_map_container(
        content_func=_render_menu_profit_structure_map,
        empty_message="원가를 계산하려면 메뉴, 레시피, 재료 데이터가 모두 필요합니다.",
        empty_action_label="데이터 입력하기",
        empty_action_page="메뉴 등록"
    )
    
    # ZONE C: Owner School
    school_cards = [
        {
            "title": "메뉴 수익 구조",
            "point1": "원가율이 50%를 넘으면 그 메뉴는 수익에 거의 기여하지 않습니다",
            "point2": "저마진 메뉴는 가격 조정 또는 메뉴 교체를 고려하세요"
        },
        {
            "title": "원가율 관리",
            "point1": "평균 원가율 35% 이하를 목표로 하세요",
            "point2": "고원가율 메뉴는 대표메뉴로 삼지 마세요"
        },
        {
            "title": "공헌이익",
            "point1": "공헌이익 = 판매가 - 원가입니다",
            "point2": "공헌이익이 높은 메뉴를 주력으로 하세요"
        },
    ]
    render_school_cards(school_cards)
    
    # ZONE D: Design Tools (기존 기능)
    render_design_tools_container(_render_menu_profit_design_tools)


def _render_menu_profit_design_tools():
    """ZONE D: 메뉴 수익 구조 설계 도구 (기존 기능)"""
    # 데이터 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    # 원가 계산
    if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
        cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
        render_cost_analysis(cost_df, warning_threshold=35.0)
    else:
        st.info("원가를 계산하려면 메뉴, 레시피, 재료 데이터가 모두 필요합니다.")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("메뉴 수", len(menu_df))
        with col2:
            st.metric("레시피 수", len(recipe_df))
        with col3:
            st.metric("재료 수", len(ingredient_df))


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_cost_overview()
