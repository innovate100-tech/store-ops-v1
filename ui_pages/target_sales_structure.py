"""
목표 매출 구조 입력 페이지
FormKit v2 + 블록 리듬 적용 (settlement_actual 기준)
"""
import streamlit as st
import pandas as pd
import time
from src.ui_helpers import safe_get_value, ui_flash_success, ui_flash_error, ui_flash_warning
from src.ui.layouts.input_layouts import render_form_layout
from src.ui.components.form_kit import inject_form_kit_css
from src.ui.components.form_kit_v2 import (
    inject_form_kit_v2_css,
    ps_input_block,
    ps_primary_money_input,
    ps_primary_ratio_input,
    ps_inline_feedback,
)
from src.storage_supabase import load_expense_structure
from src.utils.time_utils import current_year_kst, current_month_kst
from src.storage_supabase import load_csv, save_targets
from src.auth import get_current_store_id

# 공통 설정 제거 (app.py에서 이미 실행됨)
# bootstrap(page_title="Target Sales Structure")


def render_target_sales_structure():
    """목표 매출 구조 입력 (FormKit v2 + 블록 리듬, FORM형 레이아웃)"""
    inject_form_kit_css()
    inject_form_kit_v2_css("target_sales_structure")
    
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
        """Main Card: FormKit v2 + 블록 리듬"""
        cy, cm = current_year_kst(), current_month_kst()
        iy = int(st.session_state.get("expense_year", cy))
        im = int(st.session_state.get("expense_month", cm))
        
        # Block 1: 기간 선택 (Secondary)
        def _body_period():
            c1, c2 = st.columns(2)
            with c1:
                st.number_input("연도", min_value=2020, max_value=2100, value=iy, step=1, format="%d", key="target_sales_structure_year")
            with c2:
                st.number_input("월", min_value=1, max_value=12, value=im, step=1, format="%d", key="target_sales_structure_month")
        
        ps_input_block(title="기간 선택", description="목표 매출을 입력할 연·월을 선택하세요", level="secondary", body_fn=_body_period)
        selected_year = int(st.session_state.get("target_sales_structure_year", iy))
        selected_month = int(st.session_state.get("target_sales_structure_month", im))
        st.session_state["expense_year"] = selected_year
        st.session_state["expense_month"] = selected_month
        
        # 목표 매출 로드
        targets_df = load_csv('targets.csv', default_columns=[
            '연도', '월', '목표매출', '목표원가율', '목표인건비율',
            '목표임대료율', '목표기타비용율', '목표순이익률'
        ])
        target_sales = 0.0
        if not targets_df.empty:
            tr = targets_df[(targets_df['연도'] == selected_year) & (targets_df['월'] == selected_month)]
            target_sales = float(safe_get_value(tr, '목표매출', 0)) if not tr.empty else 0.0
        _tv = int(target_sales) if target_sales > 0 else 0
        
        # Block 2: Primary 1개 — 목표 월매출
        def _body_target():
            ps_primary_money_input(
                label="목표 월매출 (원)",
                key="target_sales_structure_target_sales_input",
                value=_tv,
                min_value=0,
                step=100000,
                unit="원"
            )
        ps_input_block(title="목표 월매출", description="이번 달 목표 매출을 입력하세요", level="primary", body_fn=_body_target)
        
        def handle_save_target_sales():
            try:
                v = st.session_state.get("target_sales_structure_target_sales_input", 0)
                if isinstance(v, float) and v.is_integer():
                    v = int(v)
                save_targets(selected_year, selected_month, v, 0, 0, 0, 0, 0)
                ui_flash_success("목표 매출이 저장되었습니다!")
                st.rerun()
            except Exception as e:
                ui_flash_error(f"저장 중 오류: {e}")
        st.session_state["_target_sales_save_target_sales"] = handle_save_target_sales
        
        # Block 3: 비율 입력 (메뉴/시간대) — compact ratio, 합계 검증은 ps_inline_feedback만
        menu_cats = {"메인 메뉴": 0.0, "사이드 메뉴": 0.0, "음료": 0.0, "기타": 0.0}
        
        def _body_menu_ratios():
            c1, c2 = st.columns(2)
            with c1:
                for cat in ["메인 메뉴", "사이드 메뉴"]:
                    ps_primary_ratio_input(
                        label=f"{cat} (%)",
                        key=f"menu_ratio_{cat}",
                        value=menu_cats.get(cat, 0.0),
                        min_value=0.0,
                        max_value=100.0,
                        step=0.1,
                        compact=True,
                        unit="%"
                    )
            with c2:
                for cat in ["음료", "기타"]:
                    ps_primary_ratio_input(
                        label=f"{cat} (%)",
                        key=f"menu_ratio_{cat}",
                        value=menu_cats.get(cat, 0.0),
                        min_value=0.0,
                        max_value=100.0,
                        step=0.1,
                        compact=True,
                        unit="%"
                    )
        
        ps_input_block(title="메뉴 카테고리별 목표 매출 비율", description="합계 100%", level="secondary", body_fn=_body_menu_ratios)
        menu_total = sum(float(st.session_state.get(f"menu_ratio_{c}", 0) or 0) for c in ["메인 메뉴", "사이드 메뉴", "음료", "기타"])
        ps_inline_feedback(label="메뉴 비율 합계", value=f"{menu_total:.1f}%", status="ok" if abs(menu_total - 100.0) <= 0.1 else "warn")
        
        def _body_time_ratios():
            c1, c2, c3 = st.columns(3)
            with c1:
                ps_primary_ratio_input(label="점심 (%)", key="time_ratio_점심", value=0.0, min_value=0.0, max_value=100.0, step=0.1, compact=True, unit="%")
            with c2:
                ps_primary_ratio_input(label="저녁 (%)", key="time_ratio_저녁", value=0.0, min_value=0.0, max_value=100.0, step=0.1, compact=True, unit="%")
            with c3:
                ps_primary_ratio_input(label="기타 (%)", key="time_ratio_기타", value=0.0, min_value=0.0, max_value=100.0, step=0.1, compact=True, unit="%")
        
        ps_input_block(title="시간대별 목표 매출 비율", description="합계 100%", level="secondary", body_fn=_body_time_ratios)
        time_total = sum(float(st.session_state.get(k, 0) or 0) for k in ["time_ratio_점심", "time_ratio_저녁", "time_ratio_기타"])
        ps_inline_feedback(label="시간대 비율 합계", value=f"{time_total:.1f}%", status="ok" if abs(time_total - 100.0) <= 0.1 else "warn")
        
        def handle_save_structure():
            mt = sum(float(st.session_state.get(f"menu_ratio_{c}", 0) or 0) for c in ["메인 메뉴", "사이드 메뉴", "음료", "기타"])
            tt = sum(float(st.session_state.get(k, 0) or 0) for k in ["time_ratio_점심", "time_ratio_저녁", "time_ratio_기타"])
            if abs(mt - 100.0) > 0.1:
                ui_flash_error("메뉴 카테고리별 비율의 합이 100%가 되어야 합니다.")
            elif abs(tt - 100.0) > 0.1:
                ui_flash_error("시간대별 비율의 합이 100%가 되어야 합니다.")
            else:
                ui_flash_warning("매출 구조 저장 기능은 향후 구현 예정입니다.")
        st.session_state["_target_sales_save_structure"] = handle_save_structure
        
        t3 = time.perf_counter()
        try:
            from src.auth import is_dev_mode
            if is_dev_mode():
                with st.expander("🔍 DEBUG: performance", expanded=False):
                    st.write("**총 시간:**", f"{round(t3 - t0, 3)}초")
        except Exception:
            pass
    
    # Action Bar 설정
    action_primary = None
    action_secondary = None
    
    # Primary 액션 설정
    if "_target_sales_save_target_sales" in st.session_state:
        action_primary = {
            "label": "💾 목표 저장",
            "key": "target_sales_primary_save",
            "action": st.session_state["_target_sales_save_target_sales"]
        }
        del st.session_state["_target_sales_save_target_sales"]
    
    # Secondary 액션 설정
    secondary_actions = []
    if "_target_sales_save_structure" in st.session_state:
        secondary_actions.append({
            "label": "💾 매출 구조 저장",
            "key": "target_sales_save_structure",
            "action": st.session_state["_target_sales_save_structure"]
        })
        del st.session_state["_target_sales_save_structure"]
    
    if secondary_actions:
        action_secondary = secondary_actions
    
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
        action_primary=action_primary,
        action_secondary=action_secondary,
        main_content=render_main_content
    )


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_target_sales_structure()
