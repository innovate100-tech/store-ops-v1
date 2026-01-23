"""
대시보드 UI 섹션 렌더링
"""
import streamlit as st
import pandas as pd
import datetime as dt
from datetime import timedelta
import time
from src.ui_helpers import safe_get_value
from src.ui.aggrid_render import render_aggrid
from src.analytics import calculate_menu_cost, calculate_ingredient_usage
from src.utils.boot_perf import record_compute_call


def _render_breakeven_section(ctx, metrics, raw_data):
    """손익분기점 관련 UI 섹션 렌더링"""
    breakeven_sales = metrics['breakeven_sales']
    if breakeven_sales is None or breakeven_sales <= 0:
        st.info("손익분기 매출을 계산하려면 목표 비용구조 페이지에서 고정비와 변동비율을 입력해주세요.")
        return
    
    fixed_costs = metrics['fixed_costs']
    variable_cost_rate = metrics['variable_cost_rate']
    target_sales = metrics['target_sales']
    target_profit = metrics['target_profit']
    weekday_ratio = metrics['weekday_ratio']
    weekend_ratio = metrics['weekend_ratio']
    weekday_daily_breakeven = metrics['weekday_daily_breakeven']
    weekend_daily_breakeven = metrics['weekend_daily_breakeven']
    weekday_daily_target = metrics['weekday_daily_target']
    weekend_daily_target = metrics['weekend_daily_target']
    weekday_daily_target_profit = metrics['weekday_daily_target_profit']
    weekend_daily_target_profit = metrics['weekend_daily_target_profit']
    
    # 손익분기 매출 vs 목표 매출 비교 섹션
    st.markdown("""
    <div style="margin: 1rem 0 0.5rem 0;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
            📊 손익분기 매출 vs 목표 매출 비교
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    if breakeven_sales:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.75rem;">
            <span style="color: #ffffff; font-size: 0.85rem;">
                계산 공식: 고정비 ÷ (1 - 변동비율) = {int(fixed_costs):,}원 ÷ (1 - {variable_cost_rate:.1f}%)
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    # 월간 매출 비교
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
            <div style="font-size: 1.1rem; margin-bottom: 0.4rem; opacity: 0.9;">📊 손익분기 월매출</div>
            <div style="font-size: 1.5rem; font-weight: 700;">{int(breakeven_sales):,}원</div>
            <div style="font-size: 1.1rem; margin-top: 0.75rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.6rem;">
                💰 추정 영업이익
            </div>
            <div style="font-size: 1.1rem; font-weight: 600; margin-top: 0.2rem;">0원</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if target_sales > 0:
            profit_color = "#ffd700" if target_profit > 0 else "#ff6b6b"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                <div style="font-size: 1.1rem; margin-bottom: 0.4rem; opacity: 0.9;">🎯 목표 월매출</div>
                <div style="font-size: 1.5rem; font-weight: 700;">{int(target_sales):,}원</div>
                <div style="font-size: 1.1rem; margin-top: 0.75rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.6rem;">
                    💰 추정 영업이익
                </div>
                <div style="font-size: 1.1rem; font-weight: 600; margin-top: 0.2rem; color: {profit_color};">{int(target_profit):,}원</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; text-align: center; margin-top: 0.25rem; border: 2px dashed rgba(255,255,255,0.3);">
                <div style="font-size: 0.85rem; margin-bottom: 0.4rem; color: #ffffff;">🎯 목표 월매출</div>
                <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7);">목표 비용구조 페이지에서 목표 매출을 설정하세요</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
    
    # 일일 매출 비교 섹션
    st.markdown("""
    <div style="margin: 1rem 0 0.5rem 0;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
            📅 일일 매출 비교
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        weekday_profit_color = "#ffd700" if weekday_daily_target_profit > 0 else "#ff6b6b" if weekday_daily_target_profit < 0 else "white"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); padding: 1rem; border-radius: 8px; color: white; margin-top: 0.25rem; text-align: right;">
            <div style="font-size: 1.1rem; margin-bottom: 0.3rem; opacity: 0.9; text-align: center;">📅 평일 일일 매출</div>
            <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.1rem;">일일손익분기매출: {int(weekday_daily_breakeven):,}원</div>
            {f'<div style="font-size: 1.1rem; font-weight: 700;">일일목표매출: {int(weekday_daily_target):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7; margin-top: 0.2rem;">목표 매출 입력 필요</div>'}
            <div style="font-size: 1rem; margin-top: 0.7rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem; text-align: center;">
                💰 일일 영업이익
            </div>
            <div style="font-size: 0.85rem; font-weight: 600; margin-top: 0.2rem; margin-bottom: 0.2rem;">손익분기시 영업이익: 0원</div>
            {f'<div style="font-size: 0.85rem; font-weight: 600; color: {weekday_profit_color};">목표시 영업이익: {int(weekday_daily_target_profit):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
            <div style="font-size: 0.7rem; margin-top: 0.4rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.4rem;">
                (월매출 × {weekday_ratio:.1f}% ÷ 22일)
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        weekend_profit_color = "#ffd700" if weekend_daily_target_profit > 0 else "#ff6b6b" if weekend_daily_target_profit < 0 else "white"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); padding: 1rem; border-radius: 8px; color: white; margin-top: 0.25rem; text-align: right;">
            <div style="font-size: 1.1rem; margin-bottom: 0.3rem; opacity: 0.9; text-align: center;">🎉 주말 일일 매출</div>
            <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.1rem;">일일손익분기매출: {int(weekend_daily_breakeven):,}원</div>
            {f'<div style="font-size: 1.1rem; font-weight: 700;">일일목표매출: {int(weekend_daily_target):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7; margin-top: 0.2rem;">목표 매출 입력 필요</div>'}
            <div style="font-size: 1rem; margin-top: 0.7rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem; text-align: center;">
                💰 일일 영업이익
            </div>
            <div style="font-size: 0.85rem; font-weight: 600; margin-top: 0.2rem; margin-bottom: 0.2rem;">손익분기시 영업이익: 0원</div>
            {f'<div style="font-size: 0.85rem; font-weight: 600; color: {weekend_profit_color};">목표시 영업이익: {int(weekend_daily_target_profit):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
            <div style="font-size: 0.7rem; margin-top: 0.4rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.4rem;">
                (월매출 × {weekend_ratio:.1f}% ÷ 8일)
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
    
    # 매출 수준별 비용·영업이익 시뮬레이션
    if target_sales > 0:
        expense_df = raw_data['expense_df']
        # 5대 비용 세부 계산을 위한 카테고리별 데이터
        fixed_by_category = {
            '임차료': 0,
            '인건비': 0,
            '공과금': 0,
        }
        variable_rate_by_category = {
            '재료비': 0.0,
            '부가세&카드수수료': 0.0,
        }
        
        if not expense_df.empty:
            fixed_categories = ['임차료', '인건비', '공과금']
            for cat in fixed_categories:
                fixed_by_category[cat] = expense_df[expense_df['category'] == cat]['amount'].sum()
            
            variable_categories = ['재료비', '부가세&카드수수료']
            variable_df = expense_df[expense_df['category'].isin(variable_categories)]
            if not variable_df.empty:
                for cat in variable_categories:
                    variable_rate_by_category[cat] = variable_df[variable_df['category'] == cat]['amount'].sum()
        
        # 목표매출을 기준으로 다양한 시나리오 생성
        scenarios = [
            ("목표매출 - 1,000만원", max(target_sales - 10_000_000, 0)),
            ("목표매출 - 500만원", max(target_sales - 5_000_000, 0)),
            ("목표매출 (기준)", target_sales),
            ("목표매출 + 500만원", target_sales + 5_000_000),
            ("목표매출 + 1,000만원", target_sales + 10_000_000),
            ("목표매출 + 1,500만원", target_sales + 15_000_000),
        ]
        
        st.markdown("""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                📊 매출 수준별 비용·영업이익 시뮬레이션
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.75rem;">
            <span style="color: #ffffff; font-size: 0.85rem;">
                비용구조의 고정비와 변동비율, 목표 매출을 기준으로 다양한 매출 수준에서의 비용과 영업이익을 비교합니다.
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        
        for idx, (label, sales) in enumerate(scenarios):
            if sales <= 0:
                continue
            
            # 5대 비용 세부 계산
            rent_cost = fixed_by_category.get('임차료', 0)
            labor_cost = fixed_by_category.get('인건비', 0)
            utility_cost = fixed_by_category.get('공과금', 0)
            material_rate = variable_rate_by_category.get('재료비', 0.0) / 100
            fee_rate = variable_rate_by_category.get('부가세&카드수수료', 0.0) / 100
            material_cost = sales * material_rate
            fee_cost = sales * fee_rate
            
            total_cost = rent_cost + labor_cost + utility_cost + material_cost + fee_cost
            profit = sales - total_cost
            
            tile_col = cols[idx % 3]
            with tile_col:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 1rem; border-radius: 10px; margin-top: 0.5rem; color: #e5e7eb; box-shadow: 0 2px 6px rgba(0,0,0,0.35);">
                    <div style="font-size: 0.85rem; margin-bottom: 0.3rem; opacity: 0.9;">{label}</div>
                    <!-- 매출 영역: 선명한 흰색 -->
                    <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.25rem; color: #ffffff !important;">
                        매출: {int(sales):,}원
                    </div>
                    <!-- 비용 영역 제목: 더 진한 빨간색 -->
                    <div style="font-size: 0.85rem; margin-top: 0.4rem; border-top: 1px solid rgba(148,163,184,0.5); padding-top: 0.4rem; color: #ff4d4f !important;">
                        비용 합계 및 세부내역
                    </div>
                    <!-- 총 비용: 더 진한 빨간색 -->
                    <div style="font-size: 1rem; font-weight: 600; margin-bottom: 0.15rem; color: #ff4d4f !important;">
                        총 비용: {int(total_cost):,}원
                    </div>
                    <div style="font-size: 0.75rem; margin-top: 0.25rem; line-height: 1.3; color: #ff4d4f !important;">
                        임차료(고정비): {int(rent_cost):,}원<br>
                        인건비(고정비): {int(labor_cost):,}원<br>
                        공과금(고정비): {int(utility_cost):,}원<br>
                        재료비(변동비): {int(material_cost):,}원<br>
                        부가세·카드수수료(변동비): {int(fee_cost):,}원
                    </div>
                    <!-- 추정 영업이익 제목: 선명한 노란색 -->
                    <div style="font-size: 0.85rem; margin-top: 0.4rem; border-top: 1px solid rgba(148,163,184,0.5); padding-top: 0.4rem; color: #ffd700 !important;">
                        추정 영업이익
                    </div>
                    <!-- 추정 영업이익 값: 선명한 노란색 -->
                    <div style="font-size: 1rem; font-weight: 600; color: #ffd700 !important;">
                        {int(profit):,}원
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
    st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)


def _render_sales_sections(ctx, metrics, raw_data):
    """매출 관련 UI 섹션 렌더링"""
    merged_df = metrics['merged_df']
    month_data = metrics['month_data']
    month_total_sales = metrics['month_total_sales']
    month_total_visitors = metrics['month_total_visitors']
    monthly_summary = metrics['monthly_summary']
    targets_df = raw_data['targets_df']
    
    # 목표 매출 확인
    target_sales_dashboard = 0
    target_row_dashboard = targets_df[
        (targets_df['연도'] == ctx['year']) & 
        (targets_df['월'] == ctx['month'])
    ]
    if not target_row_dashboard.empty:
        target_sales_dashboard = float(safe_get_value(target_row_dashboard, '목표매출', 0))
    
    if not merged_df.empty:
        # 1. 이번달 요약
        st.markdown("""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                📊 이번달 요약
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not month_data.empty:
            # 미마감 배지 표시
            unofficial_days = metrics.get('unofficial_days', 0)
            if unofficial_days > 0:
                st.warning(f"⚠️ **미마감 데이터 포함 ({unofficial_days}일)**: 이번달 누적 매출에 마감되지 않은 날짜의 매출이 포함되어 있습니다.")
            
            month_avg_daily_sales = month_total_sales / len(month_data) if len(month_data) > 0 else 0
            month_avg_daily_visitors = month_total_visitors / len(month_data) if len(month_data) > 0 else 0
            avg_customer_value = month_total_sales / month_total_visitors if month_total_visitors > 0 else 0
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("이번달 누적 매출", f"{month_total_sales:,.0f}원")
            with col2:
                st.metric("평균 일일 매출", f"{month_avg_daily_sales:,.0f}원")
            with col3:
                st.metric("이번달 총 방문자", f"{int(month_total_visitors):,}명")
            with col4:
                st.metric("평균 객단가", f"{avg_customer_value:,.0f}원")
            with col5:
                target_achievement = (month_total_sales / target_sales_dashboard * 100) if target_sales_dashboard > 0 else None
                if target_achievement is not None:
                    st.metric("목표 달성률", f"{target_achievement:.1f}%", 
                            f"{target_achievement - 100:.1f}%p" if target_achievement != 100 else "0%p")
                else:
                    st.metric("목표 달성률", "-", help="목표 매출이 설정되지 않았습니다")
        
        st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
        
        # 2. 저장된 매출 내역
        st.markdown("""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                📋 저장된 매출 내역
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not merged_df.empty:
            # 통합 데이터 표시
            display_df_dashboard = merged_df.copy()
            
            # 표시할 컬럼만 선택
            display_columns = []
            if '날짜' in display_df_dashboard.columns:
                display_columns.append('날짜')
            if '매장' in display_df_dashboard.columns:
                display_columns.append('매장')
            if '카드매출' in display_df_dashboard.columns:
                display_columns.append('카드매출')
            if '현금매출' in display_df_dashboard.columns:
                display_columns.append('현금매출')
            if '총매출' in display_df_dashboard.columns:
                display_columns.append('총매출')
            if '방문자수' in display_df_dashboard.columns:
                display_columns.append('방문자수')
            
            # 필요한 컬럼만 선택
            if display_columns:
                display_df_dashboard = display_df_dashboard[display_columns]
                
                # 날짜를 문자열로 변환
                if '날짜' in display_df_dashboard.columns:
                    display_df_dashboard['날짜'] = pd.to_datetime(display_df_dashboard['날짜']).dt.strftime('%Y-%m-%d')
                
                # 숫자 포맷팅
                if '총매출' in display_df_dashboard.columns:
                    display_df_dashboard['총매출'] = display_df_dashboard['총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                if '카드매출' in display_df_dashboard.columns:
                    display_df_dashboard['카드매출'] = display_df_dashboard['카드매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                if '현금매출' in display_df_dashboard.columns:
                    display_df_dashboard['현금매출'] = display_df_dashboard['현금매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                if '방문자수' in display_df_dashboard.columns:
                    display_df_dashboard['방문자수'] = display_df_dashboard['방문자수'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
            
            # AgGrid로 렌더링 (다크 테마 적용 가능, 패키지 없으면 자동 fallback)
            render_aggrid(
                display_df_dashboard,
                key="dashboard_daily_table",
                height=300,
                sortable=True,
                filterable=True,
                resizable=True
            )
        
        st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
        
        # 3. 월별 요약 (최근 6개월)
        st.markdown("""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                📋 월별 요약 (최근 6개월)
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not monthly_summary.empty:
            display_monthly = monthly_summary.head(6).copy()
            display_monthly['월'] = display_monthly['월'].apply(lambda x: f"{int(x)}월")
            display_monthly['월총매출'] = display_monthly['월총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_monthly['일평균매출'] = display_monthly['일평균매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_monthly['월총방문자'] = display_monthly['월총방문자'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
            display_monthly['월별객단가'] = display_monthly['월별객단가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_monthly['전월대비'] = display_monthly['전월대비'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
            
            # AgGrid로 렌더링 (다크 테마 적용 가능, 패키지 없으면 자동 fallback)
            render_aggrid(
                display_monthly[['연도', '월', '영업일수', '월총매출', '일평균매출', '월총방문자', '월별객단가', '전월대비']],
                key="dashboard_monthly_table",
                height=350,
                sortable=True,
                filterable=True,
                resizable=True
            )
        
    st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)


def _render_menu_sections(ctx, metrics, raw_data):
    """메뉴/ABC 분석 관련 UI 섹션 렌더링"""
    menu_sales_summary = metrics['menu_sales_summary']
    daily_sales_df = raw_data['daily_sales_df']
    menu_df = raw_data['menu_df']
    recipe_df = raw_data['recipe_df']
    ingredient_df = raw_data['ingredient_df']
    
    # 판매 ABC 분석
    st.markdown("""
    <div style="margin: 1rem 0 0.5rem 0;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
            📊 판매 ABC 분석
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    if not daily_sales_df.empty and not menu_df.empty:
        daily_sales_df_copy = daily_sales_df.copy()
        daily_sales_df_copy['날짜'] = pd.to_datetime(daily_sales_df_copy['날짜'])
        
        start_of_month = dt.date(ctx['year'], ctx['month'], 1)
        if ctx['month'] < 12:
            next_month_first = dt.date(ctx['year'], ctx['month'] + 1, 1)
            days_in_month = (next_month_first - timedelta(days=1)).day
        else:
            days_in_month = 31
        end_of_month = dt.date(ctx['year'], ctx['month'], days_in_month)
        
        filtered_sales_df = daily_sales_df_copy[
            (daily_sales_df_copy['날짜'].dt.date >= start_of_month) & 
            (daily_sales_df_copy['날짜'].dt.date <= end_of_month)
        ].copy()
        
        if not filtered_sales_df.empty and not menu_sales_summary.empty:
            total_revenue = menu_sales_summary['매출'].sum()
            
            if total_revenue > 0:
                # ABC 분석
                summary_df = menu_sales_summary.sort_values('매출', ascending=False).copy()
                summary_df['비율(%)'] = (summary_df['매출'] / total_revenue * 100).round(2)
                summary_df['누계 비율(%)'] = summary_df['비율(%)'].cumsum().round(2)
                
                # ABC 등급 부여
                def assign_abc_grade(cumulative_ratio):
                    if cumulative_ratio <= 70:
                        return 'A'
                    elif cumulative_ratio <= 90:
                        return 'B'
                    else:
                        return 'C'
                
                t0 = time.perf_counter()
                summary_df['ABC 등급'] = summary_df['누계 비율(%)'].apply(assign_abc_grade)
                t1 = time.perf_counter()
                record_compute_call("dashboard: abc_grade_apply", (t1 - t0) * 1000,
                                  rows_in=len(summary_df), rows_out=len(summary_df))
                
                # ABC 등급별 통계
                t0 = time.perf_counter()
                abc_stats = summary_df.groupby('ABC 등급').agg({
                    '메뉴명': 'count',
                    '매출': 'sum',
                    '판매수량': 'sum'
                }).reset_index()
                t1 = time.perf_counter()
                record_compute_call("dashboard: abc_stats_groupby", (t1 - t0) * 1000,
                                  rows_in=len(summary_df), rows_out=len(abc_stats))
                abc_stats.columns = ['ABC 등급', '메뉴 수', '총 매출', '총 판매수량']
                abc_stats['매출 비율(%)'] = (abc_stats['총 매출'] / total_revenue * 100).round(2)
                
                # ABC 등급별 통계 카드
                col1, col2, col3 = st.columns(3)
                with col1:
                    a_count = abc_stats[abc_stats['ABC 등급'] == 'A']['메뉴 수'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'A'].empty else 0
                    a_revenue = abc_stats[abc_stats['ABC 등급'] == 'A']['총 매출'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'A'].empty else 0
                    a_ratio = abc_stats[abc_stats['ABC 등급'] == 'A']['매출 비율(%)'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'A'].empty else 0
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                        <div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🟢 A등급</div>
                        <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.25rem;">{int(a_count)}개 메뉴</div>
                        <div style="font-size: 1rem; margin-bottom: 0.25rem;">{int(a_revenue):,}원</div>
                        <div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {a_ratio:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    b_count = abc_stats[abc_stats['ABC 등급'] == 'B']['메뉴 수'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'B'].empty else 0
                    b_revenue = abc_stats[abc_stats['ABC 등급'] == 'B']['총 매출'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'B'].empty else 0
                    b_ratio = abc_stats[abc_stats['ABC 등급'] == 'B']['매출 비율(%)'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'B'].empty else 0
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                        <div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🟡 B등급</div>
                        <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.25rem;">{int(b_count)}개 메뉴</div>
                        <div style="font-size: 1rem; margin-bottom: 0.25rem;">{int(b_revenue):,}원</div>
                        <div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {b_ratio:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    c_count = abc_stats[abc_stats['ABC 등급'] == 'C']['메뉴 수'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'C'].empty else 0
                    c_revenue = abc_stats[abc_stats['ABC 등급'] == 'C']['총 매출'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'C'].empty else 0
                    c_ratio = abc_stats[abc_stats['ABC 등급'] == 'C']['매출 비율(%)'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'C'].empty else 0
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                        <div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🔴 C등급</div>
                        <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.25rem;">{int(c_count)}개 메뉴</div>
                        <div style="font-size: 1rem; margin-bottom: 0.25rem;">{int(c_revenue):,}원</div>
                        <div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {c_ratio:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # TOP 10 메뉴 표시
                st.markdown("""
                <div style="margin: 1rem 0 0.5rem 0;">
                    <h4 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.1rem;">
                        🏆 ABC 분석 TOP 10 메뉴
                    </h4>
                </div>
                """, unsafe_allow_html=True)
                
                top10_df = summary_df.head(10).copy()
                top10_df.insert(0, '순위', range(1, len(top10_df) + 1))
                
                # 표시용 포맷팅
                display_top10 = top10_df.copy()
                display_top10['판매수량'] = display_top10['판매수량'].apply(lambda x: f"{int(x):,}개")
                display_top10['매출'] = display_top10['매출'].apply(lambda x: f"{int(x):,}원")
                display_top10['비율(%)'] = display_top10['비율(%)'].apply(lambda x: f"{x:.2f}%")
                display_top10['누계 비율(%)'] = display_top10['누계 비율(%)'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(
                    display_top10[['순위', '메뉴명', '판매수량', '매출', '비율(%)', '누계 비율(%)', 'ABC 등급']],
                    use_container_width=True,
                    hide_index=True
                )
                    
                st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
                
                # 재료 사용량 TOP 10
                usage_df = calculate_ingredient_usage(filtered_sales_df, recipe_df)
                
                if not usage_df.empty and not ingredient_df.empty:
                    usage_df = pd.merge(
                        usage_df,
                        ingredient_df[['재료명', '단가']],
                        on='재료명',
                        how='left'
                    )
                    usage_df['단가'] = usage_df['단가'].fillna(0)
                    usage_df['총사용단가'] = usage_df['총사용량'] * usage_df['단가']
                    
                    t0 = time.perf_counter()
                    ingredient_summary = (
                        usage_df
                        .groupby('재료명')[['총사용량', '총사용단가']]
                        .sum()
                        .reset_index()
                    )
                    t1 = time.perf_counter()
                    record_compute_call("dashboard: ingredient_summary_groupby", (t1 - t0) * 1000,
                                      rows_in=len(usage_df), rows_out=len(ingredient_summary))
                    
                    ingredient_summary = ingredient_summary.sort_values('총사용단가', ascending=False)
                    total_cost = ingredient_summary['총사용단가'].sum()
                    
                    if total_cost > 0:
                        ingredient_summary['비율(%)'] = (ingredient_summary['총사용단가'] / total_cost * 100).round(2)
                        ingredient_summary['누적 비율(%)'] = ingredient_summary['비율(%)'].cumsum().round(2)
                        
                        def assign_abc_grade_ingredient(cumulative_ratio):
                            if cumulative_ratio <= 70:
                                return 'A'
                            elif cumulative_ratio <= 90:
                                return 'B'
                            else:
                                return 'C'
                        
                        ingredient_summary['ABC 등급'] = ingredient_summary['누적 비율(%)'].apply(assign_abc_grade_ingredient)
                        
                        st.markdown("""
                        <div style="margin: 1rem 0 0.5rem 0;">
                            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                                📦 재료 사용 단가 TOP 10
                            </h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        top10_ingredients = ingredient_summary.head(10).copy()
                        top10_ingredients.insert(0, '순위', range(1, len(top10_ingredients) + 1))
                        
                        display_top10_ingredients = top10_ingredients.copy()
                        display_top10_ingredients['총 사용량'] = display_top10_ingredients['총사용량'].apply(lambda x: f"{x:,.2f}")
                        display_top10_ingredients['총 사용단가'] = display_top10_ingredients['총사용단가'].apply(lambda x: f"{int(x):,}원")
                        display_top10_ingredients['비율(%)'] = display_top10_ingredients['비율(%)'].apply(lambda x: f"{x:.2f}%")
                        display_top10_ingredients['누적 비율(%)'] = display_top10_ingredients['누적 비율(%)'].apply(lambda x: f"{x:.2f}%")
                        
                        st.dataframe(
                            display_top10_ingredients[['순위', '재료명', '총 사용량', '총 사용단가', '비율(%)', '누적 비율(%)', 'ABC 등급']],
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        top10_total = top10_ingredients['총사용단가'].sum()
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin-top: 0.75rem;">
                            <span style="color: #ffffff; font-size: 0.9rem; font-weight: 600;">
                                💰 TOP 10 총 사용단가 합계: {int(top10_total):,}원
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
                
                # 레시피 검색 및 수정
                recipe_df_dashboard = raw_data['recipe_df']
                
                if not recipe_df_dashboard.empty:
                    # 레시피가 있는 메뉴 목록 추출
                    menus_with_recipes = recipe_df_dashboard['메뉴명'].unique().tolist()
                    
                    if menus_with_recipes:
                        st.markdown("""
                        <div style="margin: 1rem 0 0.5rem 0;">
                            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                                🔍 레시피 검색 및 수정
                            </h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 메뉴 선택
                        filter_menu = st.selectbox(
                            "메뉴 선택",
                            options=menus_with_recipes,
                            key="dashboard_recipe_filter_menu",
                            index=0 if menus_with_recipes else None
                        )
                        
                        # 선택한 메뉴의 레시피만 필터링
                        display_recipe_df = recipe_df_dashboard[recipe_df_dashboard['메뉴명'] == filter_menu].copy()
                        
                        if not display_recipe_df.empty:
                            # 재료 정보와 조인하여 단위 및 단가 표시
                            display_recipe_df = pd.merge(
                                display_recipe_df,
                                ingredient_df[['재료명', '단위', '단가']],
                                on='재료명',
                                how='left'
                            )
                            
                            # 원가 계산
                            menu_cost_df = calculate_menu_cost(menu_df, recipe_df_dashboard, ingredient_df)
                            menu_cost_info = menu_cost_df[menu_cost_df['메뉴명'] == filter_menu]
                            
                            # 메뉴 정보 가져오기
                            menu_info = menu_df[menu_df['메뉴명'] == filter_menu]
                            # Phase 1: 안전한 DataFrame 접근
                            menu_price = int(safe_get_value(menu_info, '판매가', 0)) if not menu_info.empty else 0
                            
                            # 조리방법 가져오기 (menu_master에서)
                            cooking_method_text = ""
                            try:
                                from src.auth import get_supabase_client
                                supabase = get_supabase_client()
                                store_id = ctx['store_id']
                                if supabase and store_id:
                                    menu_result = supabase.table("menu_master").select("cooking_method").eq("store_id", store_id).eq("name", filter_menu).execute()
                                    if menu_result.data and menu_result.data[0].get('cooking_method'):
                                        cooking_method_text = menu_result.data[0]['cooking_method']
                            except Exception as e:
                                import logging
                                logging.getLogger(__name__).warning(f"조리방법 조회 실패 (대시보드): {e}")
                            
                            # 원가 정보
                            cost = int(safe_get_value(menu_cost_info, '원가', 0)) if not menu_cost_info.empty else 0
                            cost_rate = float(safe_get_value(menu_cost_info, '원가율', 0)) if not menu_cost_info.empty else 0
                            
                            # 메뉴 정보 카드
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                                    <div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">판매가</div>
                                    <div style="font-size: 1.3rem; font-weight: 700;">{menu_price:,}원</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                                    <div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">원가</div>
                                    <div style="font-size: 1.3rem; font-weight: 700;">{cost:,}원</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with col3:
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                                    <div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">원가율</div>
                                    <div style="font-size: 1.3rem; font-weight: 700;">{cost_rate:.1f}%</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # 구성 재료 및 사용량 테이블
                            st.markdown("""
                            <div style="margin: 1rem 0 0.5rem 0;">
                                <h4 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.1rem;">
                                    📋 구성 재료 및 사용량
                                </h4>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 테이블 데이터 준비
                            table_data = []
                            for idx, row in display_recipe_df.iterrows():
                                ing_name = row['재료명']
                                unit = row['단위'] if pd.notna(row['단위']) else ""
                                current_qty = float(row['사용량'])
                                unit_price = float(row['단가']) if pd.notna(row['단가']) else 0
                                ingredient_cost = current_qty * unit_price
                                
                                table_data.append({
                                    '재료명': ing_name,
                                    '기준단위': unit,
                                    '사용량': f"{current_qty:.2f}",
                                    '1단위 단가': f"{unit_price:,.1f}원",
                                    '재료비': f"{ingredient_cost:,.1f}원"
                                })
                            
                            # 테이블 표시
                            ingredients_table_df = pd.DataFrame(table_data)
                            st.dataframe(ingredients_table_df, use_container_width=True, hide_index=True)
                            
                            # 조리방법 표시
                            st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
                            st.markdown("""
                            <div style="margin: 1rem 0 0.5rem 0;">
                                <h4 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.1rem;">
                                    👨‍🍳 조리방법
                                </h4>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if cooking_method_text:
                                st.markdown(f"""
                                <div style="background: rgba(30, 41, 59, 0.5); padding: 1rem; border-radius: 12px; 
                                            border-left: 4px solid #667eea; margin: 0.75rem 0;">
                                    <div style="color: #e5e7eb; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap;">
                                        {cooking_method_text.replace(chr(10), '<br>')}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.info("조리방법이 등록되지 않았습니다.")

