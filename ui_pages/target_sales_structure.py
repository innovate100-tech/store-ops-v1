"""
목표 매출 구조 입력 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import time
from src.ui_helpers import render_section_header, render_section_divider, safe_get_value
from src.ui.layouts.input_layouts import render_form_layout
from src.storage_supabase import load_expense_structure
from src.utils.time_utils import current_year_kst, current_month_kst
from src.storage_supabase import load_csv, save_targets
from src.auth import get_current_store_id

# 공통 설정 제거 (app.py에서 이미 실행됨)
# bootstrap(page_title="Target Sales Structure")


def render_target_sales_structure():
    """목표 매출 구조 입력 페이지 렌더링 (FORM형 레이아웃 적용)"""
    # 성능 측정 시작
    t0 = time.perf_counter()
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    current_year = current_year_kst()
    current_month = current_month_kst()
    
    # 비용구조 페이지에서 사용한 연/월을 우선 사용하고, 없으면 현재 연/월 사용
    selected_year = st.session_state.get("expense_year")
    if selected_year is None: selected_year = current_year
    
    selected_month = st.session_state.get("expense_month")
    if selected_month is None: selected_month = current_month
    
    selected_year = int(selected_year)
    selected_month = int(selected_month)
    
    # 세션 상태 업데이트
    st.session_state["expense_year"] = selected_year
    st.session_state["expense_month"] = selected_month
    
    # 목표 매출 로드 (SummaryStrip용)
    targets_df = load_csv('targets.csv', default_columns=[
        '연도', '월', '목표매출', '목표원가율', '목표인건비율',
        '목표임대료율', '목표기타비용율', '목표순이익률'
    ])
    target_sales = 0
    if not targets_df.empty:
        target_row = targets_df[(targets_df['연도'] == selected_year) & (targets_df['월'] == selected_month)]
        target_sales = float(safe_get_value(target_row, '목표매출', 0)) if not target_row.empty else 0.0
    
    # 비용 구조 입력 완료 여부 확인 (SummaryStrip용)
    expense_df = load_expense_structure(selected_year, selected_month, store_id)
    has_cost_structure = not expense_df.empty
    
    # SummaryStrip 항목 구성 (기존 값 사용)
    summary_items = [
        {
            "label": "목표 기간",
            "value": f"{selected_year}년 {selected_month}월",
            "badge": None
        },
        {
            "label": "목표 매출",
            "value": f"{int(target_sales):,}원" if target_sales > 0 else "미입력",
            "badge": "success" if target_sales > 0 else "warning"
        },
        {
            "label": "비용 구조",
            "value": "입력 완료" if has_cost_structure else "미입력",
            "badge": "success" if has_cost_structure else "warning"
        }
    ]
    
    def render_main_content():
        """Main Card 내용: 목표 매출 구조 입력 UI"""
        # ========== ZONE A: 기간 선택 ==========
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.number_input(
            "연도",
            min_value=2020,
            max_value=2100,
            value=selected_year,
            key="target_sales_structure_year"
        )
    with col2:
        selected_month = st.number_input(
            "월",
            min_value=1,
            max_value=12,
            value=selected_month,
            key="target_sales_structure_month"
        )
    
    # 세션 상태 업데이트
    st.session_state["expense_year"] = selected_year
    st.session_state["expense_month"] = selected_month
    
        render_section_divider()
        
        # ========== ZONE B: 목표 매출 입력 ==========
        render_section_header("목표 매출 입력", "🎯")
        
        # 목표 매출 로드
        targets_df = load_csv('targets.csv', default_columns=[
            '연도', '월', '목표매출', '목표원가율', '목표인건비율',
            '목표임대료율', '목표기타비용율', '목표순이익률'
        ])
        
        target_sales = 0
        if not targets_df.empty:
            target_row = targets_df[(targets_df['연도'] == selected_year) & (targets_df['월'] == selected_month)]
            target_sales = float(safe_get_value(target_row, '목표매출', 0)) if not target_row.empty else 0.0
    
    col1, col2 = st.columns([3, 1])
    with col1:
        target_sales_input = st.number_input(
            "목표 월매출 (원)",
            min_value=0,
            value=int(target_sales) if target_sales > 0 else 0,
            step=100000,
            key="target_sales_structure_target_sales_input",
            help="이번 달 목표 매출을 입력하세요"
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("💾 목표 저장", key="target_sales_structure_save_target_sales", use_container_width=True):
            try:
                # 목표 매출만 저장 (나머지는 0으로 설정)
                save_targets(
                    selected_year, selected_month, 
                    target_sales_input, 0, 0, 0, 0, 0
                )
                st.success("목표 매출이 저장되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류: {e}")
    
    render_section_divider()
    
    # ========== ZONE B-2: 목표 매출 구조 입력 (신규) ==========
    render_section_header("목표 매출 구조 입력", "📊")
    
    st.info("목표 매출을 달성하기 위한 매출 구조를 입력하세요.")
    
    # 메뉴 카테고리별 목표 매출 비율
    st.markdown("### 메뉴 카테고리별 목표 매출 비율")
    
    menu_categories = {
        "메인 메뉴": 0.0,
        "사이드 메뉴": 0.0,
        "음료": 0.0,
        "기타": 0.0
    }
    
    # 기존 데이터 로드 (향후 구현)
    # TODO: target_sales_structure 테이블에서 로드
    
    menu_ratios = {}
    menu_total = 0.0
    
    col1, col2 = st.columns(2)
    with col1:
        for category in ["메인 메뉴", "사이드 메뉴"]:
            menu_ratios[category] = st.number_input(
                f"{category} (%)",
                min_value=0.0,
                max_value=100.0,
                value=menu_categories.get(category, 0.0),
                step=0.1,
                format="%.1f",
                key=f"menu_ratio_{category}"
            )
            menu_total += menu_ratios[category]
    
    with col2:
        for category in ["음료", "기타"]:
            menu_ratios[category] = st.number_input(
                f"{category} (%)",
                min_value=0.0,
                max_value=100.0,
                value=menu_categories.get(category, 0.0),
                step=0.1,
                format="%.1f",
                key=f"menu_ratio_{category}"
            )
            menu_total += menu_ratios[category]
    
    if abs(menu_total - 100.0) > 0.1:
        st.warning(f"⚠️ 합계: {menu_total:.1f}% (100%가 되어야 합니다)")
    else:
        st.success(f"✓ 합계: {menu_total:.1f}%")
    
    # 시간대별 목표 매출 비율
    st.markdown("### 시간대별 목표 매출 비율")
    
    time_periods = {
        "점심": 0.0,
        "저녁": 0.0,
        "기타": 0.0
    }
    
    # 기존 데이터 로드 (향후 구현)
    # TODO: target_sales_structure 테이블에서 로드
    
    time_ratios = {}
    time_total = 0.0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        time_ratios["점심"] = st.number_input(
            "점심 (%)",
            min_value=0.0,
            max_value=100.0,
            value=time_periods.get("점심", 0.0),
            step=0.1,
            format="%.1f",
            key="time_ratio_점심"
        )
        time_total += time_ratios["점심"]
    
    with col2:
        time_ratios["저녁"] = st.number_input(
            "저녁 (%)",
            min_value=0.0,
            max_value=100.0,
            value=time_periods.get("저녁", 0.0),
            step=0.1,
            format="%.1f",
            key="time_ratio_저녁"
        )
        time_total += time_ratios["저녁"]
    
    with col3:
        time_ratios["기타"] = st.number_input(
            "기타 (%)",
            min_value=0.0,
            max_value=100.0,
            value=time_periods.get("기타", 0.0),
            step=0.1,
            format="%.1f",
            key="time_ratio_기타"
        )
        time_total += time_ratios["기타"]
    
    if abs(time_total - 100.0) > 0.1:
        st.warning(f"⚠️ 합계: {time_total:.1f}% (100%가 되어야 합니다)")
    else:
        st.success(f"✓ 합계: {time_total:.1f}%")
    
    # 저장 버튼
    if st.button("💾 매출 구조 저장", key="target_sales_structure_save_structure", use_container_width=True):
        if abs(menu_total - 100.0) > 0.1:
            st.error("메뉴 카테고리별 비율의 합이 100%가 되어야 합니다.")
        elif abs(time_total - 100.0) > 0.1:
            st.error("시간대별 비율의 합이 100%가 되어야 합니다.")
        else:
            # TODO: target_sales_structure 테이블에 저장
            st.info("매출 구조 저장 기능은 향후 구현 예정입니다.")
            # st.success("매출 구조가 저장되었습니다!")
            # st.rerun()
    
        render_section_divider()
        
        # ========== ZONE C: 입력 현황 요약 ==========
        render_section_header("입력 현황", "📋")
        
        # 비용 구조 입력 완료 여부 확인
        expense_df = load_expense_structure(selected_year, selected_month, store_id)
        has_cost_structure = not expense_df.empty
        
        # 매출 구조 입력 완료 여부 확인
        # TODO: target_sales_structure 테이블에서 확인
        has_sales_structure = False  # 향후 구현
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("목표 매출", f"{int(target_sales_input):,}원" if target_sales_input > 0 else "미입력")
        with col2:
            status_icon = "✅" if has_cost_structure else "⚠️"
            st.metric("비용 구조 입력", status_icon)
        with col3:
            status_icon = "✅" if has_sales_structure else "⚠️"
            st.metric("매출 구조 입력", status_icon)
        
        # UI 출력 완료 시점
        t3 = time.perf_counter()
        
        # 개발모드 성능 측정 표시
        try:
            from src.auth import is_dev_mode
            if is_dev_mode():
                total_sec = round(t3 - t0, 3)
                
                with st.expander("🔍 DEBUG: performance", expanded=False):
                    st.write("**렌더 성능 측정:**")
                    st.write(f"  - **총 시간:** {total_sec}초")
        except Exception:
            pass  # 성능 측정 실패해도 페이지는 계속 동작
    
    # FORM형 레이아웃 적용
    render_form_layout(
        title="매출 목표 입력",
        icon="📈",
        status_badge=None,
        guide_kind="G3",
        guide_conclusion=None,  # 기본값 사용
        guide_bullets=None,  # 기본값 사용
        guide_next_action=None,  # 기본값 사용
        summary_items=summary_items,
        mini_progress_items=None,  # Mini Progress Panel 사용 안 함
        action_primary=None,  # ActionBar 사용 안 함 (기존 버튼 유지)
        action_secondary=None,
        main_content=render_main_content
    )


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_target_sales_structure()
