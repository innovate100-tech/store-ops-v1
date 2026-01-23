"""
목표 비용구조 페이지 (수익 구조 설계실)
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import time
from src.ui_helpers import render_page_header, render_section_header, render_section_divider, safe_get_value
from src.utils.time_utils import current_year_kst, current_month_kst
from src.storage_supabase import load_csv, load_expense_structure, save_expense_item, update_expense_item, delete_expense_item, copy_expense_structure_from_previous_month, save_targets, get_fixed_costs, get_variable_cost_ratio, calculate_break_even_sales, load_monthly_sales_total
from src.utils.crud_guard import run_write
from src.auth import get_current_store_id
from ui_pages.design_lab.design_lab_frame import (
    render_coach_board,
    render_structure_map_container,
    render_school_cards,
    render_design_tools_container,
)
from ui_pages.design_lab.design_lab_coach_data import get_revenue_structure_design_coach_data
import logging

# 공통 설정 적용
bootstrap(page_title="Target Cost Structure")


def render_target_cost_structure():
    """목표 비용구조 페이지 렌더링 (HOME v2 공통 프레임 적용)"""
    # 성능 측정 시작
    t0 = time.perf_counter()
    
    # 비용구조 페이지 전용 헤더 (화이트 모드에서도 항상 흰색 텍스트로 표시)
    header_color = "#ffffff"
    page_title = "수익 구조 설계실"
    st.markdown(f"""
    <div style="margin: 0 0 1.0rem 0;">
        <h2 style="color: {header_color}; font-weight: 700; margin: 0;">
            💳 {page_title}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # 임시 연결 안내 (수익 구조 설계실과 목표 비용 구조가 동일 페이지로 연결됨)
    st.info("💡 현재 '수익 구조 설계실'은 목표 비용 구조 페이지로 임시 연결되어 있습니다. 수익 구조 설계실 전용 페이지는 준비 중입니다.")
    
    store_id = get_current_store_id()
    current_year = current_year_kst()
    current_month = current_month_kst()
    
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # ZONE A: Coach Board
    monthly_sales = load_monthly_sales_total(store_id, current_year, current_month) or 0
    coach_data = get_revenue_structure_design_coach_data(store_id, current_year, current_month)
    render_coach_board(
        cards=coach_data["cards"],
        verdict_text=coach_data["verdict_text"],
        action_title=coach_data.get("action_title"),
        action_reason=coach_data.get("action_reason"),
        action_target_page=coach_data.get("action_target_page"),
        action_button_label=coach_data.get("action_button_label")
    )
    
    # ZONE B: Structure Map
    def _render_revenue_structure_map():
        fixed_costs = get_fixed_costs(store_id, current_year, current_month)
        variable_ratio = get_variable_cost_ratio(store_id, current_year, current_month)
        break_even = calculate_break_even_sales(store_id, current_year, current_month)
        
        if fixed_costs > 0 and break_even > 0:
            # 간단한 수익 구조 차트 (고정비/변동비/손익분기점)
            structure_data = pd.DataFrame({
                '항목': ['고정비', '손익분기점', '이번 달 매출'],
                '금액': [fixed_costs, break_even, monthly_sales]
            })
            st.bar_chart(structure_data.set_index('항목'))
        else:
            st.info("고정비와 변동비율을 입력하면 구조 맵이 표시됩니다.")
    
    render_structure_map_container(
        content_func=_render_revenue_structure_map,
        empty_message="고정비와 변동비율을 입력하면 구조 맵이 표시됩니다.",
        empty_action_label="비용 구조 입력하기",
        empty_action_page="목표 비용구조"
    )
    
    # ZONE C: Owner School
    school_cards = [
        {
            "title": "수익 구조 이해",
            "point1": "손익분기점은 목표가 아니라 생존선입니다",
            "point2": "고정비는 매출이 없어도 나가는 돈입니다"
        },
        {
            "title": "비용 구조 관리",
            "point1": "변동비율이 50% 이상이면 원가 관리가 시급합니다",
            "point2": "고정비가 월매출의 30% 이상이면 위험합니다"
        },
        {
            "title": "수익성 개선",
            "point1": "매출이 손익분기점보다 낮으면 구조 조정이 필요합니다",
            "point2": "변동비율을 낮추면 수익성이 향상됩니다"
        },
    ]
    render_school_cards(school_cards)
    
    # ZONE D: Design Tools (기존 기능)
    render_design_tools_container(lambda: _render_revenue_design_tools(current_year, current_month, store_id))


def _render_revenue_design_tools(year: int, month: int, store_id: str):
    """ZONE D: 수익 구조 설계 도구 (기존 기능)"""
    # 기존 코드는 그대로 유지하되, selected_year, selected_month를 파라미터로 받음
    selected_year = year
    selected_month = month
    
    # 기간 선택 및 전월 데이터 복사
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        selected_year = st.number_input(
            "연도",
            min_value=2020,
            max_value=2100,
            value=year,
            key="target_cost_structure_expense_year"
        )
    with col2:
        selected_month = st.number_input(
            "월",
            min_value=1,
            max_value=12,
            value=month,
            key="target_cost_structure_expense_month"
        )
    with col3:
        st.write("")
        st.write("")
        if st.button("📋 전월 데이터 복사", key="target_cost_structure_copy_prev_month", use_container_width=True):
            try:
                success, message = copy_expense_structure_from_previous_month(selected_year, selected_month)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.warning(message)
            except Exception as e:
                st.error(f"복사 중 오류: {e}")
    
    render_section_divider()
    
    # ========== 손익분기점 계산 및 상단 표시 ==========
    # 공식 엔진 함수 사용 (헌법 준수)
    # expense_df 로드
    expense_df = load_expense_structure(selected_year, selected_month, store_id)
    
    fixed_costs = get_fixed_costs(store_id, selected_year, selected_month) if store_id else 0.0
    variable_cost_ratio = get_variable_cost_ratio(store_id, selected_year, selected_month) if store_id else 0.0
    breakeven_sales = calculate_break_even_sales(store_id, selected_year, selected_month) if store_id else 0.0
    monthly_sales = load_monthly_sales_total(store_id, selected_year, selected_month) or 0
    
    # 변동비율을 % 단위로 변환 (UI 표시용)
    variable_cost_rate = variable_cost_ratio * 100.0  # % 단위
    variable_rate_decimal = variable_cost_ratio  # 소수 형태
    
    # breakeven_sales가 0이면 None으로 변환 (기존 로직 호환)
    if breakeven_sales <= 0:
        breakeven_sales = None
    
    # 목표 매출 로드
    targets_df = load_csv('targets.csv', default_columns=[
        '연도', '월', '목표매출', '목표원가율', '목표인건비율',
        '목표임대료율', '목표기타비용율', '목표순이익률'
    ])
    
    # 원본 데이터 로드 완료 시점
    t1 = time.perf_counter()
    
    # targets 필터링 (실제 사용되는 부분)
    target_sales = 0
    target_row = pd.DataFrame()
    if not targets_df.empty:
        target_row = targets_df[(targets_df['연도'] == selected_year) & (targets_df['월'] == selected_month)]
        # Phase 1: 안전한 DataFrame 접근
        target_sales = float(safe_get_value(target_row, '목표매출', 0)) if not target_row.empty else 0.0
    
    # 중간 계산 단계들
    fixed_categories_df = pd.DataFrame()
    variable_df = pd.DataFrame()
    if not expense_df.empty:
        fixed_categories_df = expense_df[expense_df['category'].isin(['임차료', '인건비', '공과금'])]
        variable_df = expense_df[expense_df['category'].isin(['재료비', '부가세&카드수수료'])]
    
    # 데이터 가공 완료 시점 (필터링, 계산 등 완료 후)
    t2 = time.perf_counter()
    
    # 최종 표시용 DataFrame들 (나중에 생성됨)
    analysis_df = pd.DataFrame()
    summary_df = pd.DataFrame()
    
    # 개발모드 디버그 정보 표시
    try:
        from src.auth import is_dev_mode, get_current_store_id
        if is_dev_mode():
            with st.expander("🔍 DEBUG: target cost structure", expanded=False):
                current_store_id = get_current_store_id()
                st.write(f"**CURRENT STORE ID:** {current_store_id}")
                st.write(f"**선택된 기간:** {selected_year}년 {selected_month}월")
                
                # A) 원본 데이터 로드 직후
                st.markdown("---")
                st.write("### A) 원본 데이터 로드 직후")
                
                st.write("**expense_structure (load_expense_structure):**")
                st.write(f"  - row_count: {len(expense_df)}")
                if not expense_df.empty:
                    st.write(f"  - 주요 컬럼: {list(expense_df.columns)[:5]}")
                    st.dataframe(expense_df.head(5), use_container_width=True)
                else:
                    st.caption("  (데이터 없음)")
                
                st.write("**targets (load_csv):**")
                st.write(f"  - row_count: {len(targets_df)}")
                if not targets_df.empty:
                    st.write(f"  - 주요 컬럼: {list(targets_df.columns)[:5]}")
                    st.dataframe(targets_df.head(5), use_container_width=True)
                else:
                    st.caption("  (데이터 없음)")
                
                # B) 중간 처리 단계
                st.markdown("---")
                st.write("### B) 중간 처리 단계")
                
                st.write("**expense_df → fixed_categories_df (필터: 임차료/인건비/공과금):**")
                st.write(f"  - row_count: {len(fixed_categories_df)}")
                if not fixed_categories_df.empty:
                    st.dataframe(fixed_categories_df.head(5), use_container_width=True)
                
                st.write("**expense_df → variable_df (필터: 재료비/부가세&카드수수료):**")
                st.write(f"  - row_count: {len(variable_df)}")
                if not variable_df.empty:
                    st.dataframe(variable_df.head(5), use_container_width=True)
                
                st.write("**targets_df → target_row (필터: 연도={}, 월={}):**".format(selected_year, selected_month))
                st.write(f"  - row_count: {len(target_row)}")
                if not target_row.empty:
                    st.dataframe(target_row.head(5), use_container_width=True)
                else:
                    st.caption("  ⚠️ 필터 후 데이터 없음 (targets는 {}건인데 필터 후 0건)".format(len(targets_df)))
                
                st.write("**target_sales (target_row에서 추출한 값):**")
                st.write(f"  - 값: {target_sales}")
                if target_sales == 0:
                    st.caption("  ⚠️ target_sales가 0입니다 (target_row가 비어있거나 목표매출 컬럼이 없음)")
                
                # C) 최종 표시용 DataFrame (조건부 생성되므로 나중에 업데이트)
                st.markdown("---")
                st.write("### C) 최종 표시용 DataFrame")
                st.caption("(아래는 조건부로 생성되므로 실제 화면 표시 시점에 확인 필요)")
                
                # analysis_df는 조건부 생성되므로 여기서는 확인 불가
                # summary_df도 조건부 생성되므로 여기서는 확인 불가
                # 실제 화면에서 st.caption으로 표시됨
    except Exception:
        pass  # 디버그 실패해도 페이지는 계속 동작
    
    
    # 손익분기점 상단 공지 표시
    if breakeven_sales is not None and breakeven_sales > 0:
        # 평일/주말 비율 입력 - 공통 info-box 스타일 사용
        st.markdown("""
        <div class="info-box">
            <strong>📅 평일/주말 매출 비율 설정</strong>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            weekday_ratio = st.number_input(
                "평일 매출 비율 (%)",
                min_value=0.0,
                max_value=100.0,
                value=70.0,
                step=1.0,
                format="%.1f",
                key="target_cost_structure_weekday_ratio",
                help="평일(22일) 매출이 차지하는 비율"
            )
        with col2:
            weekend_ratio = st.number_input(
                "주말 매출 비율 (%)",
                min_value=0.0,
                max_value=100.0,
                value=30.0,
                step=1.0,
                format="%.1f",
                key="target_cost_structure_weekend_ratio",
                help="주말(8일) 매출이 차지하는 비율"
            )
        with col3:
            st.write("")
            st.write("")
            total_ratio = weekday_ratio + weekend_ratio
            if abs(total_ratio - 100.0) > 0.1:
                st.warning(f"⚠️ 합계: {total_ratio:.1f}% (100%가 되어야 합니다)")
            else:
                st.success(f"✓ 합계: {total_ratio:.1f}%")
        
        # 목표 월매출 입력 - 공통 info-box 스타일 사용
        st.markdown("""
        <div class="info-box">
            <strong>🎯 목표 월매출 설정</strong>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            target_sales_input = st.number_input(
                "목표 월매출 (원)",
                min_value=0,
                value=int(target_sales) if target_sales > 0 else 0,
                step=100000,
                key="target_cost_structure_target_sales_input",
                help="이번 달 목표 매출을 입력하세요"
            )
        with col2:
            st.write("")
            st.write("")
            if st.button("💾 목표 저장", key="target_cost_structure_save_target_sales", use_container_width=True):
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
        
        # 손익분기 매출과 목표 매출 비교 표시
        if abs(total_ratio - 100.0) <= 0.1:
            # 일일 손익분기 매출 계산
            weekday_daily_breakeven = (breakeven_sales * weekday_ratio / 100) / 22
            weekend_daily_breakeven = (breakeven_sales * weekend_ratio / 100) / 8
            
            # 일일 목표 매출 계산 (목표 매출이 있을 때만)
            weekday_daily_target = 0
            weekend_daily_target = 0
            if target_sales_input > 0:
                weekday_daily_target = (target_sales_input * weekday_ratio / 100) / 22
                weekend_daily_target = (target_sales_input * weekend_ratio / 100) / 8
            
            # 일일 고정비 계산 개선 (평일/주말 비율 반영)
            # 평일 고정비 = 고정비 × (평일 일수 / 총 일수) / 평일 일수
            weekday_monthly_fixed = fixed_costs * (22 / 30)
            weekend_monthly_fixed = fixed_costs * (8 / 30)
            weekday_daily_fixed = weekday_monthly_fixed / 22
            weekend_daily_fixed = weekend_monthly_fixed / 8
            
            # 일일 영업이익 계산
            # 일일 영업이익 = 일일 매출 × (1 - 변동비율) - 일일 고정비
            weekday_daily_breakeven_profit = 0  # 손익분기점이므로 0원
            weekend_daily_breakeven_profit = 0  # 손익분기점이므로 0원
            
            weekday_daily_target_profit = 0
            weekend_daily_target_profit = 0
            if target_sales_input > 0:
                weekday_daily_target_profit = (weekday_daily_target * (1 - variable_rate_decimal)) - weekday_daily_fixed
                weekend_daily_target_profit = (weekend_daily_target * (1 - variable_rate_decimal)) - weekend_daily_fixed
            
            # 손익분기 매출과 목표 매출 비교 - 공통 info-box 스타일 사용 + 계산 공식 안내
            st.markdown(f"""
            <div class="info-box">
                <strong>📊 손익분기 매출 vs 목표 매출 비교</strong><br>
                <span style="font-size: 0.85rem; opacity: 0.95;">
                    계산 공식: 고정비 ÷ (1 - 변동비율) = {int(fixed_costs):,}원 ÷ (1 - {variable_cost_rate:.1f}%)
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # 추정 영업이익 계산
            # 영업이익 = 매출 × (1 - 변동비율) - 고정비
            variable_rate_decimal = variable_cost_rate / 100
            
            # 손익분기 매출의 추정 영업이익 (0원)
            breakeven_profit = 0
            
            # 목표 매출의 추정 영업이익
            target_profit = 0
            if target_sales_input > 0:
                target_profit = (target_sales_input * (1 - variable_rate_decimal)) - fixed_costs
            
            # 월간 매출 비교
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.5rem;">
                    <div style="font-size: 1.35rem; margin-bottom: 0.5rem; opacity: 0.9;">📊 손익분기 월매출</div>
                    <div style="font-size: 1.8rem; font-weight: 700;">{int(breakeven_sales):,}원</div>
                    <div style="font-size: 1.35rem; margin-top: 1rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.8rem;">
                        💰 추정 영업이익
                    </div>
                    <div style="font-size: 1.3rem; font-weight: 600; margin-top: 0.3rem;">0원</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if target_sales_input > 0:
                    gap = target_sales_input - breakeven_sales
                    gap_percent = (gap / breakeven_sales * 100) if breakeven_sales > 0 else 0
                    gap_color = "#28a745" if gap > 0 else "#dc3545"
                    profit_color = "#ffd700" if target_profit > 0 else "#ff6b6b"
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 1.5rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.5rem;">
                    <div style="font-size: 1.35rem; margin-bottom: 0.5rem; opacity: 0.9;">🎯 목표 월매출</div>
                        <div style="font-size: 1.8rem; font-weight: 700;">{int(target_sales_input):,}원</div>
                    <div style="font-size: 1.35rem; margin-top: 1rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.8rem;">
                        💰 추정 영업이익
                    </div>
                        <div style="font-size: 1.3rem; font-weight: 600; margin-top: 0.3rem; color: {profit_color};">{int(target_profit):,}원</div>
                        <!-- 차이(원, %) 표시는 제거하여 박스를 더 단순하게 유지 -->
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; text-align: center; margin-top: 0.5rem; border: 2px dashed #dee2e6;">
                        <div style="font-size: 0.9rem; margin-bottom: 0.5rem; color: #6c757d;">🎯 목표 월매출</div>
                        <div style="font-size: 0.85rem; color: #6c757d;">위에서 목표 매출을 입력하세요</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 일일 매출 비교 - 공통 info-box 스타일 사용
            st.markdown("""
            <div class="info-box">
                <strong>📅 일일 매출 비교</strong>
            </div>
            """, unsafe_allow_html=True)
            
            # 평일 일일 매출
            col1, col2 = st.columns(2)
            with col1:
                weekday_profit_color = "#ffd700" if weekday_daily_target_profit > 0 else "#ff6b6b" if weekday_daily_target_profit < 0 else "white"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); padding: 1.5rem; border-radius: 8px; color: white; margin-top: 0.5rem; text-align: right;">
                    <div style="font-size: 1.3rem; margin-bottom: 0.4rem; opacity: 0.9; text-align: center;">📅 평일 일일 매출</div>
                    <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.1rem;">일일손익분기매출: {int(weekday_daily_breakeven):,}원</div>
                    {f'<div style="font-size: 1.3rem; font-weight: 700;">일일목표매출: {int(weekday_daily_target):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.2rem;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 1.275rem; margin-top: 0.9rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.7rem; text-align: center;">
                        💰 일일 영업이익
                    </div>
                    <div style="font-size: 0.95rem; font-weight: 600; margin-top: 0.25rem; margin-bottom: 0.25rem;">손익분기시 영업이익: 0원</div>
                    {f'<div style="font-size: 0.95rem; font-weight: 600; color: {weekday_profit_color};">목표시 영업이익: {int(weekday_daily_target_profit):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.8rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem;">
                        (월매출 × {weekday_ratio:.1f}% ÷ 22일)
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                weekend_profit_color = "#ffd700" if weekend_daily_target_profit > 0 else "#ff6b6b" if weekend_daily_target_profit < 0 else "white"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); padding: 1.5rem; border-radius: 8px; color: white; margin-top: 0.5rem; text-align: right;">
                    <div style="font-size: 1.3rem; margin-bottom: 0.4rem; opacity: 0.9; text-align: center;">🎉 주말 일일 매출</div>
                    <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.1rem;">일일손익분기매출: {int(weekend_daily_breakeven):,}원</div>
                    {f'<div style="font-size: 1.3rem; font-weight: 700;">일일목표매출: {int(weekend_daily_target):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.2rem;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 1.275rem; margin-top: 1rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.7rem; text-align: center;">
                        💰 일일 영업이익
                    </div>
                    <div style="font-size: 0.95rem; font-weight: 600; margin-top: 0.25rem; margin-bottom: 0.25rem;">손익분기시 영업이익: 0원</div>
                    {f'<div style="font-size: 0.95rem; font-weight: 600; color: {weekend_profit_color};">목표시 영업이익: {int(weekend_daily_target_profit):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.8rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem;">
                        (월매출 × {weekend_ratio:.1f}% ÷ 8일)
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("평일과 주말 비율의 합이 100%가 되어야 일일 매출을 계산할 수 있습니다.")
    else:
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; text-align: center; border-left: 4px solid #667eea;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem; font-weight: 600;">📊 손익분기 매출 계산</div>
            <div style="font-size: 0.9rem; color: #666;">고정비와 변동비율을 모두 입력해야 손익분기 매출이 계산됩니다.</div>
            <div style="font-size: 0.85rem; color: #888; margin-top: 0.3rem;">고정비: 임차료, 인건비, 공과금 / 변동비: 재료비, 부가세&카드수수료</div>
        </div>
        """, unsafe_allow_html=True)
    
    render_section_divider()
    
    # ========== 비용 구조 입력 ==========
    # 5개 카테고리별 입력
    expense_categories = {
        '임차료': {'type': 'fixed', 'icon': '🏢', 'description': '고정비 (금액 직접 입력)'},
        '인건비': {'type': 'fixed', 'icon': '👥', 'description': '고정비 (금액 직접 입력)'},
        '재료비': {'type': 'variable', 'icon': '🥬', 'description': '변동비 (매출 대비 비율)'},
        '공과금': {'type': 'fixed', 'icon': '💡', 'description': '고정비 (금액 직접 입력)'},
        '부가세&카드수수료': {'type': 'variable', 'icon': '💳', 'description': '변동비 (매출 대비 비율)'}
    }
    
    # 기존 데이터 로드
    existing_items = {}
    if not expense_df.empty:
        for _, row in expense_df.iterrows():
            cat = row['category']
            if cat not in existing_items:
                existing_items[cat] = []
            existing_items[cat].append({
                'id': row.get('id'),
                'item_name': row.get('item_name'),
                'amount': row.get('amount'),
                'notes': row.get('notes')
            })
    
    # 한글 원화 변환 함수
    def format_korean_currency(amount):
        """숫자를 한글 원화로 변환 (예: 10000 -> 1만원, 15000000 -> 1천5백만원)"""
        if amount == 0:
            return "0원"
        
        # 억 단위
        eok = amount // 100000000
        remainder = amount % 100000000
        
        # 만 단위
        man = remainder // 10000
        remainder = remainder % 10000
        
        parts = []
        if eok > 0:
            parts.append(f"{eok}억")
        if man > 0:
            parts.append(f"{man}만")
        if remainder > 0:
            parts.append(f"{remainder:,}".replace(",", ""))
        
        if not parts:
            return "0원"
        
        return "".join(parts) + "원"
    
    # 각 카테고리별 입력 섹션
    for category, info in expense_categories.items():
        # 카테고리별 총액 계산
        category_total = 0
        category_items = existing_items.get(category, [])
        if category_items:
            if info['type'] == 'fixed':
                category_total = sum(item['amount'] for item in category_items)
            else:
                # 변동비는 비율 합계
                category_total = sum(item['amount'] for item in category_items)
        
        # 섹션 헤더와 총액 표시
        col1, col2 = st.columns([3, 1])
        with col1:
            # 화이트 테마일 때도 비용구조 카테고리 텍스트는 흰색으로 보이도록 색상 분기
            header_color = "#ffffff" if st.session_state.get("theme", "light") == "light" else "#ffffff"
            st.markdown(f"""
            <div style="margin: 1.5rem 0 0.5rem 0;">
                <h3 style="color: {header_color}; font-weight: 600; margin: 0;">
                    {info['icon']} {category}
                </h3>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"{info['description']}")
        with col2:
            if category_items:
                if info['type'] == 'fixed':
                    st.markdown(f"""
                    <div style="text-align: right; margin-top: 0.5rem; padding-top: 0.5rem;">
                        <strong style="color: #667eea; font-size: 1.1rem;">
                            총액: {format_korean_currency(int(category_total))}
                        </strong>
                        <div style="font-size: 0.85rem; color: #666;">
                            ({category_total:,.0f}원)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="text-align: right; margin-top: 0.5rem;">
                        <strong style="color: #667eea; font-size: 1.1rem;">
                            총 비율: {category_total:.2f}%
                        </strong>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 기존 항목 표시 - Expander 제거하고 직접 표시 (중첩 문제 해결)
        if category in existing_items and existing_items[category]:
            # 기존 항목은 기본적으로 펼쳐 두고, 필요시 사용자가 접을 수 있게 처리
            with st.expander(f"📋 기존 입력된 항목 ({len(existing_items[category])}개)", expanded=True):
                for item in existing_items[category]:
                    # 수정 모드 체크
                    edit_key = f"edit_{category}_{item['id']}"
                    is_editing = st.session_state.get(edit_key, False)
                    
                    if is_editing:
                        # 수정 모드
                        with st.container():
                            st.markdown("---")
                            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                            with col1:
                                edit_name = st.text_input(
                                    "항목명",
                                    value=item['item_name'],
                                    key=f"edit_name_{category}_{item['id']}"
                                )
                            with col2:
                                if info['type'] == 'fixed':
                                    edit_amount = st.number_input(
                                        "금액 (원)",
                                        min_value=0,
                                        value=int(item['amount']),
                                        step=10000,
                                        key=f"edit_amount_{category}_{item['id']}"
                                    )
                                else:
                                    edit_amount = st.number_input(
                                        "매출 대비 비율 (%)",
                                        min_value=0.0,
                                        max_value=100.0,
                                        value=float(item['amount']),
                                        step=0.1,
                                        format="%.2f",
                                        key=f"edit_rate_{category}_{item['id']}"
                                    )
                            with col3:
                                st.write("")
                                st.write("")
                                if st.button("💾 저장", key=f"save_edit_{category}_{item['id']}"):
                                    try:
                                        # 변동비율 검증 (변동비인 경우)
                                        if info['type'] == 'variable':
                                            existing_variable_total = sum(
                                                other_item['amount'] 
                                                for other_item in category_items 
                                                if other_item['id'] != item['id']
                                            )
                                            total_variable_rate = existing_variable_total + edit_amount
                                            
                                            # 모든 변동비 카테고리 합계 검증
                                            all_variable_categories = ['재료비', '부가세&카드수수료']
                                            all_variable_total = 0
                                            for var_cat in all_variable_categories:
                                                var_items = existing_items.get(var_cat, [])
                                                if var_cat == category:
                                                    all_variable_total += total_variable_rate
                                                else:
                                                    all_variable_total += sum(
                                                        other_item['amount'] 
                                                        for other_item in var_items
                                                    )
                                            
                                            if all_variable_total > 100:
                                                st.error(f"⚠️ 변동비율 합계가 100%를 초과할 수 없습니다. (합계: {all_variable_total:.2f}%)")
                                                st.stop()
                                        
                                        # run_write로 통일
                                        run_write(
                                            "update_expense_item",
                                            lambda: update_expense_item(item['id'], edit_name.strip(), edit_amount, item.get('notes')),
                                            targets=["cost", "expense_structure"],
                                            extra={"id": item['id'], "category": category},
                                            success_message="수정되었습니다!"
                                        )
                                        st.session_state[edit_key] = False
                                    except Exception as e:
                                        st.error(f"수정 중 오류: {e}")
                            with col4:
                                st.write("")
                                st.write("")
                                if st.button("❌ 취소", key=f"cancel_edit_{category}_{item['id']}"):
                                    st.session_state[edit_key] = False
                                    st.rerun()
                    else:
                        # 일반 표시 모드
                        # 마지막 두 컬럼(✏️, 🗑️ 버튼) 간격이 화면이 넓어져도 너무 벌어지지 않도록
                        # 버튼 컬럼 자체의 비율을 줄여 간격을 일정하게 보이게 조정
                        col1, col2, col3, col4, col5 = st.columns([6, 4, 1.2, 0.6, 0.6])
                        with col1:
                            st.write(f"**{item['item_name']}**")
                        with col2:
                            if info['type'] == 'fixed':
                                st.write(f"{format_korean_currency(int(item['amount']))} ({int(item['amount']):,}원)")
                            else:
                                st.write(f"{item['amount']:.2f}%")
                        with col3:
                            if item.get('notes'):
                                st.write(f"📝 {item['notes']}")
                        with col4:
                            if st.button("✏️", key=f"edit_btn_{category}_{item['id']}", help="수정"):
                                st.session_state[edit_key] = True
                                st.rerun()
                        with col5:
                            if st.button("🗑️", key=f"del_{category}_{item['id']}", help="삭제"):
                                # run_write로 통일
                                run_write(
                                    "delete_expense_item",
                                    lambda: delete_expense_item(item['id']),
                                    targets=["cost", "expense_structure"],
                                    extra={"id": item['id'], "category": category},
                                    success_message="삭제되었습니다!"
                                )
        
        # 새 항목 입력
        if info['type'] == 'fixed':
            # 고정비: 금액 직접 입력
            # 입력 필드 초기화를 위한 카운터 사용
            reset_key = f"reset_count_{category}"
            if reset_key not in st.session_state:
                st.session_state[reset_key] = 0
            
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    # value 파라미터로 초기값 설정
                    default_name = "" if st.session_state[reset_key] == 0 else ""
                    new_item_name = st.text_input(
                        "항목명",
                        value=default_name,
                        key=f"new_item_name_{category}_{st.session_state[reset_key]}",
                        placeholder="예: 본점 임차료, 메인 요리사 급여 등"
                    )
                with col2:
                    default_amount = 0 if st.session_state[reset_key] == 0 else 0
                    new_amount = st.number_input(
                        "금액 (원)",
                        min_value=0,
                        value=default_amount,
                        step=10000,
                        key=f"new_amount_{category}_{st.session_state[reset_key]}"
                    )
                    # 한글 원화 표시
                    if new_amount > 0:
                        st.caption(f"💬 {format_korean_currency(int(new_amount))}")
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("➕ 추가", key=f"add_{category}"):
                        if new_item_name and new_item_name.strip() and new_amount > 0:
                            # 항목명 중복 체크
                            existing_names = [item['item_name'] for item in category_items]
                            if new_item_name.strip() in existing_names:
                                st.warning("⚠️ 동일한 항목명이 이미 존재합니다.")
                            else:
                                # run_write로 통일
                                run_write(
                                    "save_expense_item",
                                    lambda: save_expense_item(selected_year, selected_month, category, new_item_name.strip(), new_amount),
                                    targets=["cost", "expense_structure"],
                                    extra={"year": selected_year, "month": selected_month, "category": category},
                                    success_message=f"{category} 항목이 추가되었습니다!"
                                )
                                # 입력 필드 초기화를 위해 카운터 증가
                                st.session_state[reset_key] += 1
                        else:
                            st.error("항목명과 금액을 모두 입력해주세요.")
        else:
            # 변동비: 매출 대비 비율 입력
            # 입력 필드 초기화를 위한 카운터 사용
            reset_key = f"reset_count_{category}"
            if reset_key not in st.session_state:
                st.session_state[reset_key] = 0
            
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    # value 파라미터로 초기값 설정
                    default_name = "" if st.session_state[reset_key] == 0 else ""
                    new_item_name = st.text_input(
                        "항목명",
                        value=default_name,
                        key=f"new_item_name_{category}_{st.session_state[reset_key]}",
                        placeholder="예: 식자재 구매비, 카드사 수수료 등"
                    )
                with col2:
                    default_rate = 0.0 if st.session_state[reset_key] == 0 else 0.0
                    new_rate = st.number_input(
                        "매출 대비 비율 (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=default_rate,
                        step=0.1,
                        format="%.2f",
                        key=f"new_rate_{category}_{st.session_state[reset_key]}"
                    )
                    # 비율을 금액으로 저장 (나중에 계산 시 사용)
                    # 실제로는 비율(%)로 저장하되, amount 필드에 비율 값을 저장
                    # 하지만 DB 스키마상 amount는 NUMERIC이므로 비율도 저장 가능
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("➕ 추가", key=f"add_{category}"):
                        if new_item_name and new_item_name.strip() and new_rate > 0:
                            # 변동비율 합계 검증
                            existing_variable_total = sum(item['amount'] for item in category_items)
                            total_variable_rate = existing_variable_total + new_rate
                            
                            # 모든 변동비 카테고리 합계 검증
                            all_variable_categories = ['재료비', '부가세&카드수수료']
                            all_variable_total = 0
                            for var_cat in all_variable_categories:
                                var_items = existing_items.get(var_cat, [])
                                if var_cat == category:
                                    all_variable_total += total_variable_rate
                                else:
                                    all_variable_total += sum(item['amount'] for item in var_items)
                            
                            if all_variable_total > 100:
                                st.error(f"⚠️ 변동비율 합계가 100%를 초과할 수 없습니다. (현재 합계: {all_variable_total:.2f}%)")
                            elif new_item_name.strip() in [item['item_name'] for item in category_items]:
                                st.warning("⚠️ 동일한 항목명이 이미 존재합니다.")
                            else:
                                # run_write로 통일
                                run_write(
                                    "save_expense_item",
                                    lambda: save_expense_item(selected_year, selected_month, category, new_item_name.strip(), new_rate),
                                    targets=["cost", "expense_structure"],
                                    extra={"year": selected_year, "month": selected_month, "category": category},
                                    success_message=f"{category} 항목이 추가되었습니다!"
                                )
                                # 입력 필드 초기화를 위해 카운터 증가
                                st.session_state[reset_key] += 1
                        else:
                            st.error("항목명과 비율을 모두 입력해주세요.")
        
        render_section_divider()
    
    # ========== 목표매출 달성시 비용구조 분석 ==========
    if breakeven_sales is not None and breakeven_sales > 0 and target_sales_input > 0:
        render_section_header("목표매출 달성시 비용구조 분석", "💰")
        
        if not expense_df.empty:
            # 목표매출 달성시 각 비용 카테고리별 월매출 대비 비율 계산
            analysis_data = []
            
            for category in expense_categories.keys():
                cat_df = expense_df[expense_df['category'] == category]
                if not cat_df.empty:
                    if expense_categories[category]['type'] == 'fixed':
                        # 고정비: 금액을 월매출 대비 비율로 계산
                        category_amount = cat_df['amount'].sum()
                        category_ratio = (category_amount / target_sales_input * 100) if target_sales_input > 0 else 0
                        analysis_data.append({
                            '비용 카테고리': category,
                            '비용 금액': f"{int(category_amount):,}원",
                            '월매출 대비 비율': f"{category_ratio:.2f}%"
                        })
                    else:
                        # 변동비: 이미 비율로 저장되어 있음
                        category_rate = cat_df['amount'].sum()
                        category_amount = target_sales_input * (category_rate / 100)
                        analysis_data.append({
                            '비용 카테고리': category,
                            '비용 금액': f"{int(category_amount):,}원",
                            '월매출 대비 비율': f"{category_rate:.2f}%"
                        })
            
            # 분석 데이터프레임 생성
            if analysis_data:
                analysis_df = pd.DataFrame(analysis_data)
                
                # 개발모드: 최종 DataFrame 디버그
                try:
                    from src.auth import is_dev_mode
                    if is_dev_mode():
                        st.caption(f"🔍 DEBUG: analysis_df row_count = {len(analysis_df)}")
                except Exception:
                    pass
                
                st.dataframe(analysis_df, use_container_width=True, hide_index=True)
                
                # 총 비용 및 이익률 계산
                total_expenses = fixed_costs + (target_sales_input * variable_cost_rate / 100)
                expense_ratio = (total_expenses / target_sales_input * 100) if target_sales_input > 0 else 0
                profit_margin = 100 - expense_ratio
                
                st.markdown("---")
                
                # 요약 지표
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("목표 월매출", f"{int(target_sales_input):,}원")
                with col2:
                    st.metric("총 비용", f"{int(total_expenses):,}원")
                with col3:
                    st.metric("총 비용률", f"{expense_ratio:.2f}%")
                with col4:
                    st.metric("이익률", f"{profit_margin:.2f}%")
                
                # 알림 시스템
                st.markdown("#### ⚠️ 알림")
                alerts = []
                
                # 변동비율 기준 (위험: 50% 이상, 주의: 40-50%, 정상: 40% 미만)
                if variable_cost_rate >= 50:
                    alerts.append("🔴 변동비율이 50% 이상입니다. 원가 관리가 시급합니다.")
                elif variable_cost_rate >= 40:
                    alerts.append("🟡 변동비율이 40% 이상입니다. 주의가 필요합니다.")
                else:
                    alerts.append("✅ 변동비율이 정상 범위입니다.")
                
                # 고정비 기준 (위험: 목표 매출의 30% 이상, 주의: 20-30%, 정상: 20% 미만)
                fixed_cost_ratio = (fixed_costs / target_sales_input * 100) if target_sales_input > 0 else 0
                if fixed_cost_ratio >= 30:
                    alerts.append("🔴 고정비가 목표 매출의 30% 이상입니다. 고정비 절감이 필요합니다.")
                elif fixed_cost_ratio >= 20:
                    alerts.append("🟡 고정비가 목표 매출의 20% 이상입니다. 주의가 필요합니다.")
                else:
                    alerts.append("✅ 고정비가 정상 범위입니다.")
                
                # 총 비용률 기준 (위험: 90% 이상, 주의: 80-90%, 정상: 80% 미만)
                if expense_ratio >= 90:
                    alerts.append("🔴 총 비용률이 90% 이상입니다. 수익성이 매우 낮습니다.")
                elif expense_ratio >= 80:
                    alerts.append("🟡 총 비용률이 80% 이상입니다. 비용 절감이 필요합니다.")
                else:
                    alerts.append("✅ 총 비용률이 정상 범위입니다.")
                
                # 알림 표시
                for alert in alerts:
                    if "🔴" in alert:
                        st.error(alert)
                    elif "🟡" in alert:
                        st.warning(alert)
                    else:
                        st.success(alert)
            else:
                st.info("비용 데이터가 없습니다.")
        else:
            st.info("목표 매출을 입력하고 비용 데이터를 입력해주세요.")
    
    # ========== 월간 집계 표시 ==========
    render_section_header("월간 비용 집계", "📊")
    
    if not expense_df.empty:
        # 카테고리별 집계
        summary_data = []
        total_amount = 0
        
        for category in expense_categories.keys():
            cat_df = expense_df[expense_df['category'] == category]
            if not cat_df.empty:
                if expense_categories[category]['type'] == 'fixed':
                    # 고정비: 합계
                    cat_total = cat_df['amount'].sum()
                    summary_data.append({
                        '카테고리': category,
                        '유형': '고정비',
                        '항목수': len(cat_df),
                        '합계': f"{int(cat_total):,}원"
                    })
                    total_amount += cat_total
                else:
                    # 변동비: 비율 표시 (평균 또는 합계)
                    # 실제로는 각 항목이 비율이므로, 가장 큰 비율 또는 합계를 표시
                    cat_max_rate = cat_df['amount'].max()
                    summary_data.append({
                        '카테고리': category,
                        '유형': '변동비',
                        '항목수': len(cat_df),
                        '합계': f"{cat_max_rate:.2f}% (최대 비율)"
                    })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            
            # 개발모드: 최종 DataFrame 디버그
            try:
                from src.auth import is_dev_mode
                if is_dev_mode():
                    st.caption(f"🔍 DEBUG: summary_df row_count = {len(summary_df)}")
            except Exception:
                pass
            
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                <strong>총 고정비: {int(total_amount):,}원</strong>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"{selected_year}년 {selected_month}월의 비용 데이터가 없습니다. 위에서 비용 항목을 입력해주세요.")
    
    # UI 출력 완료 시점
    t3 = time.perf_counter()
    
    # 개발모드 성능 측정 표시
    try:
        from src.auth import is_dev_mode
        if is_dev_mode():
            total_sec = round(t3 - t0, 3)
            load_sec = round(t1 - t0, 3)
            transform_sec = round(t2 - t1, 3)
            ui_sec = round(t3 - t2, 3)
            
            with st.expander("🔍 DEBUG: performance", expanded=False):
                st.write("**렌더 성능 측정:**")
                st.write(f"  - **총 시간:** {total_sec}초")
                st.write(f"  - **데이터 로드:** {load_sec}초")
                st.write(f"  - **데이터 가공:** {transform_sec}초")
                st.write(f"  - **UI 출력:** {ui_sec}초")
                
                # 병목 지점 표시
                if load_sec > 5:
                    st.warning(f"⚠️ 데이터 로드가 느립니다 ({load_sec}초)")
                if transform_sec > 2:
                    st.warning(f"⚠️ 데이터 가공이 느립니다 ({transform_sec}초)")
                if ui_sec > 2:
                    st.warning(f"⚠️ UI 출력이 느립니다 ({ui_sec}초)")
    except Exception:
        pass  # 성능 측정 실패해도 페이지는 계속 동작


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_target_cost_structure()
