"""
메뉴 수익 구조 설계실 (가격·마진)
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from src.ui_helpers import render_page_header, render_section_divider
from src.storage_supabase import load_csv
from src.analytics import calculate_menu_cost
from ui_pages.design_lab.design_lab_frame import (
    render_coach_board,
    render_structure_map_container,
    render_school_cards,
    render_design_tools_container,
)
from ui_pages.design_lab.design_lab_coach_data import get_menu_profit_design_coach_data
from src.auth import get_current_store_id

# 공통 설정 적용
bootstrap(page_title="Menu Profit Design Lab")


def render_menu_profit_design_lab():
    """메뉴 수익 구조 설계실 페이지 렌더링 (Design Lab 공통 프레임 적용)"""
    render_page_header("메뉴 수익 구조 설계실", "💰")
    
    # 공통 네비게이션 버튼
    from ui_pages.design_lab.design_lab_nav import render_back_to_design_center_button
    render_back_to_design_center_button()
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
    recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
    
    # 원가 계산
    cost_df = pd.DataFrame()
    if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
        cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
    
    # ZONE A: Coach Board
    coach_data = get_menu_profit_design_coach_data(store_id)
    
    # 평균 공헌이익 추가 (가능하면)
    if not cost_df.empty and '원가' in cost_df.columns and '판매가' in cost_df.columns:
        cost_df['공헌이익'] = cost_df['판매가'] - cost_df['원가']
        avg_contribution = cost_df['공헌이익'].mean()
        if 'cards' in coach_data and len(coach_data['cards']) < 4:
            coach_data['cards'].append({
                "title": "평균 공헌이익",
                "value": f"{int(avg_contribution):,}원",
                "subtitle": None
            })
    
    # 전략 브리핑 / 전략 실행 탭 분리
    tab1, tab2 = st.tabs(["📊 전략 브리핑", "🛠️ 전략 실행"])
    
    with tab1:
        # ZONE A: Coach Board
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
        if cost_df.empty:
            st.info("메뉴, 레시피, 재료 데이터가 모두 필요합니다.")
            return
        
        # 1) 메뉴별 원가율 분포
        st.markdown("#### 📊 메뉴별 원가율 분포")
        if '원가율' in cost_df.columns:
            # 상위 10개 메뉴의 원가율 차트
            top_10 = cost_df.head(10)
            st.bar_chart(top_10.set_index('메뉴명')['원가율'])
        
        # 2) 공헌이익 TOP/Bottom 5 표
        if '공헌이익' in cost_df.columns:
            st.markdown("#### 💰 공헌이익 TOP/Bottom 5")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**TOP 5**")
                top5 = cost_df.nlargest(5, '공헌이익')[['메뉴명', '판매가', '원가', '공헌이익']].copy()
                top5['공헌이익'] = top5['공헌이익'].apply(lambda x: f"{int(x):,}원")
                top5['판매가'] = top5['판매가'].apply(lambda x: f"{int(x):,}원")
                top5['원가'] = top5['원가'].apply(lambda x: f"{int(x):,}원")
                st.dataframe(top5, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**Bottom 5**")
                bottom5 = cost_df.nsmallest(5, '공헌이익')[['메뉴명', '판매가', '원가', '공헌이익']].copy()
                bottom5['공헌이익'] = bottom5['공헌이익'].apply(lambda x: f"{int(x):,}원")
                bottom5['판매가'] = bottom5['판매가'].apply(lambda x: f"{int(x):,}원")
                bottom5['원가'] = bottom5['원가'].apply(lambda x: f"{int(x):,}원")
                st.dataframe(bottom5, use_container_width=True, hide_index=True)
    
        render_structure_map_container(
            content_func=_render_menu_profit_structure_map,
            empty_message="원가를 계산하려면 메뉴, 레시피, 재료 데이터가 모두 필요합니다.",
            empty_action_label="데이터 입력하기",
            empty_action_page="메뉴 등록"
        )
        
        # ZONE C: Owner School
        school_cards = [
        {
            "title": "원가율과 공헌이익은 다르다",
            "point1": "원가율이 낮아도 판매가가 낮으면 공헌이익은 적습니다",
            "point2": "공헌이익 = 판매가 - 원가입니다. 두 값 모두 확인하세요"
        },
        {
            "title": "가격은 구조를 바꾼다",
            "point1": "가격을 올리면 원가율은 낮아지고 공헌이익은 증가합니다",
            "point2": "하지만 가격이 너무 높으면 판매량이 줄어들 수 있습니다"
        },
        {
            "title": "미끼/볼륨/마진 메뉴의 조합",
            "point1": "미끼 메뉴: 손님을 끌어들이는 저가 메뉴",
            "point2": "볼륨 메뉴: 판매량이 많은 메뉴, 마진 메뉴: 수익 기여도가 높은 메뉴"
        },
        ]
        render_school_cards(school_cards)
    
    with tab2:
        # ZONE D: Design Tools
        render_design_tools_container(lambda: _render_menu_profit_design_tools(cost_df, menu_df, recipe_df, ingredient_df))


def _render_menu_profit_design_tools(cost_df: pd.DataFrame, menu_df: pd.DataFrame, recipe_df: pd.DataFrame, ingredient_df: pd.DataFrame):
    """ZONE D: 메뉴 수익 구조 설계 도구"""
    
    if cost_df.empty:
        st.info("원가를 계산하려면 메뉴, 레시피, 재료 데이터가 모두 필요합니다.")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("메뉴 수", len(menu_df))
        with col2:
            st.metric("레시피 수", len(recipe_df))
        with col3:
            st.metric("재료 수", len(ingredient_df))
        return
    
    # 공헌이익 계산
    if '공헌이익' not in cost_df.columns:
        cost_df['공헌이익'] = cost_df['판매가'] - cost_df['원가']
    
    # 1) 위험 메뉴 테이블
    st.markdown("#### ⚠️ 위험 메뉴 분석")
    
    # 필터 옵션
    filter_option = st.radio(
        "필터 옵션",
        ["원가율 35% 이상", "공헌이익 하위", "판매가 낮은데 원가 높은 메뉴", "전체"],
        horizontal=True,
        key="menu_profit_risk_filter"
    )
    
    # 필터링
    if filter_option == "원가율 35% 이상":
        risk_df = cost_df[cost_df['원가율'] >= 35].copy()
        risk_reason = "원가율 35% 이상"
    elif filter_option == "공헌이익 하위":
        risk_df = cost_df.nsmallest(5, '공헌이익').copy()
        risk_reason = "공헌이익 하위 5개"
    elif filter_option == "판매가 낮은데 원가 높은 메뉴":
        # 판매가 대비 원가 비율이 높은 메뉴
        cost_df['원가_비율'] = (cost_df['원가'] / cost_df['판매가'] * 100)
        risk_df = cost_df[cost_df['원가_비율'] >= 40].copy()
        risk_df = risk_df.nsmallest(5, '판매가').copy()
        risk_reason = "판매가 낮은데 원가 비율 높은 메뉴"
    else:
        risk_df = cost_df.copy()
        risk_reason = "전체"
    
    if not risk_df.empty:
        # 위험 사유 추가
        risk_df['위험 사유'] = risk_df.apply(lambda row: _get_risk_reason(row), axis=1)
        
        # 표시용 DataFrame
        display_df = risk_df[['메뉴명', '판매가', '원가', '원가율', '공헌이익', '위험 사유']].copy()
        display_df['판매가'] = display_df['판매가'].apply(lambda x: f"{int(x):,}원")
        display_df['원가'] = display_df['원가'].apply(lambda x: f"{int(x):,}원")
        display_df['원가율'] = display_df['원가율'].apply(lambda x: f"{x:.1f}%")
        display_df['공헌이익'] = display_df['공헌이익'].apply(lambda x: f"{int(x):,}원")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.caption(f"총 {len(risk_df)}개 메뉴 ({risk_reason})")
    else:
        st.info("해당 조건의 위험 메뉴가 없습니다.")
    
    render_section_divider()
    
    # 2) 가격/마진 시뮬레이터
    st.markdown("#### 🎯 가격/마진 시뮬레이터")
    
    if not cost_df.empty:
        menu_list = cost_df['메뉴명'].tolist()
        selected_menu = st.selectbox("메뉴 선택", menu_list, key="menu_profit_simulator_menu")
        
        if selected_menu:
            menu_info = cost_df[cost_df['메뉴명'] == selected_menu].iloc[0]
            current_price = int(menu_info['판매가'])
            current_cost = float(menu_info['원가'])
            current_cost_rate = float(menu_info['원가율'])
            current_contribution = float(menu_info['공헌이익'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**현재 상태**")
                st.metric("판매가", f"{current_price:,}원")
                st.metric("원가", f"{int(current_cost):,}원")
                st.metric("원가율", f"{current_cost_rate:.1f}%")
                st.metric("공헌이익", f"{int(current_contribution):,}원")
            
            with col2:
                st.markdown("**새 가격 시뮬레이션**")
                new_price = st.number_input(
                    "새 판매가 (원)",
                    min_value=0,
                    value=current_price,
                    step=1000,
                    key="menu_profit_simulator_price"
                )
                
                if new_price > 0:
                    new_cost_rate = (current_cost / new_price * 100) if new_price > 0 else 0
                    new_contribution = new_price - current_cost
                    contribution_change = new_contribution - current_contribution
                    
                    st.metric("새 원가율", f"{new_cost_rate:.1f}%", delta=f"{new_cost_rate - current_cost_rate:.1f}%p")
                    st.metric("새 공헌이익", f"{int(new_contribution):,}원", delta=f"{int(contribution_change):,}원")
                    
                    if contribution_change > 0:
                        st.success(f"✅ 공헌이익이 {int(contribution_change):,}원 증가합니다!")
                    elif contribution_change < 0:
                        st.warning(f"⚠️ 공헌이익이 {abs(int(contribution_change)):,}원 감소합니다.")
                    else:
                        st.info("공헌이익 변화 없음")
    else:
        st.info("메뉴 데이터가 없습니다.")
    
    render_section_divider()
    
    # 3) 메뉴 역할 태그 (표시만, DB 저장 없음)
    st.markdown("#### 🏷️ 메뉴 역할 태그")
    st.info("💡 메뉴 역할 태그 저장 기능은 다음 단계에서 추가될 예정입니다. 현재는 표시만 가능합니다.")
    
    if not cost_df.empty:
        menu_list = cost_df['메뉴명'].tolist()
        selected_menu_for_tag = st.selectbox("메뉴 선택", menu_list, key="menu_profit_tag_menu")
        
        if selected_menu_for_tag:
            # session_state에서 역할 태그 가져오기 (저장 없이 표시만)
            tag_key = f"menu_role_tag_{selected_menu_for_tag}"
            current_tag = st.session_state.get(tag_key, "미설정")
            
            st.write(f"**선택된 메뉴**: {selected_menu_for_tag}")
            st.write(f"**현재 역할**: {current_tag}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🎣 미끼", key=f"tag_bait_{selected_menu_for_tag}", use_container_width=True):
                    st.session_state[tag_key] = "미끼"
                    st.rerun()
            with col2:
                if st.button("📦 볼륨", key=f"tag_volume_{selected_menu_for_tag}", use_container_width=True):
                    st.session_state[tag_key] = "볼륨"
                    st.rerun()
            with col3:
                if st.button("💰 마진", key=f"tag_margin_{selected_menu_for_tag}", use_container_width=True):
                    st.session_state[tag_key] = "마진"
                    st.rerun()
            
            if current_tag != "미설정":
                if st.button("🗑️ 태그 제거", key=f"tag_remove_{selected_menu_for_tag}"):
                    st.session_state[tag_key] = "미설정"
                    st.rerun()


def _get_risk_reason(row: pd.Series) -> str:
    """위험 사유 판단"""
    reasons = []
    
    if row.get('원가율', 0) >= 50:
        reasons.append("원가율 50% 이상")
    elif row.get('원가율', 0) >= 35:
        reasons.append("원가율 35% 이상")
    
    if row.get('공헌이익', 0) < 0:
        reasons.append("공헌이익 마이너스")
    elif row.get('공헌이익', 0) < 1000:
        reasons.append("공헌이익 1천원 미만")
    
    if row.get('판매가', 0) < 5000 and row.get('원가율', 0) >= 40:
        reasons.append("저가 고원가율")
    
    return ", ".join(reasons) if reasons else "정상 범위"
