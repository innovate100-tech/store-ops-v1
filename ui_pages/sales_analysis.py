"""
판매 관리 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from datetime import timedelta
from src.ui_helpers import render_page_header, render_section_divider
from src.utils.time_utils import today_kst
from src.storage_supabase import load_csv
from src.analytics import calculate_menu_cost

# 공통 설정 적용
bootstrap(page_title="Sales Analysis")


def render_sales_analysis():
    """판매 관리 페이지 렌더링"""
    render_page_header("판매 관리", "📦")
    
    # 메뉴 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    if daily_sales_df.empty or menu_df.empty:
        st.info("판매 분석을 위해서는 메뉴와 일일 판매 데이터가 필요합니다.")
    else:
        # 날짜를 datetime으로 변환
        daily_sales_df['날짜'] = pd.to_datetime(daily_sales_df['날짜'])
        
        # 사용 가능한 날짜 범위
        min_date = daily_sales_df['날짜'].min().date()
        max_date = daily_sales_df['날짜'].max().date()
        
        # 기간 선택 필터 (전역 사용)
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📅 분석 기간 선택
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            analysis_start_date = st.date_input(
                "시작일",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key="sales_mgmt_start_date"
            )
        with col2:
            analysis_end_date = st.date_input(
                "종료일",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="sales_analysis_sales_mgmt_end_date"
            )
        
        # 기간 유효성 검사
        if analysis_start_date > analysis_end_date:
            st.error("⚠️ 시작일은 종료일보다 이전이어야 합니다.")
        else:
            # 기간 필터링
            filtered_sales_df = daily_sales_df[
                (daily_sales_df['날짜'].dt.date >= analysis_start_date) & 
                (daily_sales_df['날짜'].dt.date <= analysis_end_date)
            ].copy()
            
            if filtered_sales_df.empty:
                st.info(f"선택한 기간({analysis_start_date.strftime('%Y년 %m월 %d일')} ~ {analysis_end_date.strftime('%Y년 %m월 %d일')})에 해당하는 판매 데이터가 없습니다.")
            else:
                # 메뉴별 총 판매수량 집계
                sales_summary = (
                    filtered_sales_df.groupby('메뉴명')['판매수량']
                    .sum()
                    .reset_index()
                )
                sales_summary.columns = ['메뉴명', '판매수량']
                
                # 메뉴 마스터와 조인하여 판매가 가져오기
                summary_df = pd.merge(
                    sales_summary,
                    menu_df[['메뉴명', '판매가']],
                    on='메뉴명',
                    how='left',
                )
                
                # 매출 금액 계산
                summary_df['매출'] = summary_df['판매수량'] * summary_df['판매가']
                
                # 원가 정보 계산
                if not recipe_df.empty and not ingredient_df.empty:
                    cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
                    summary_df = pd.merge(
                        summary_df,
                        cost_df[['메뉴명', '원가']],
                        on='메뉴명',
                        how='left',
                    )
                    summary_df['원가'] = summary_df['원가'].fillna(0)
                    summary_df['총판매원가'] = summary_df['판매수량'] * summary_df['원가']
                    summary_df['이익'] = summary_df['매출'] - summary_df['총판매원가']
                    summary_df['이익률'] = (summary_df['이익'] / summary_df['매출'] * 100).round(2)
                    summary_df['원가율'] = (summary_df['원가'] / summary_df['판매가'] * 100).round(2)
                else:
                    summary_df['원가'] = 0
                    summary_df['총판매원가'] = 0
                    summary_df['이익'] = summary_df['매출']
                    summary_df['이익률'] = 0
                    summary_df['원가율'] = 0
                
                # 총합계 계산
                total_revenue = summary_df['매출'].sum()
                total_cost = summary_df['총판매원가'].sum()
                total_profit = summary_df['이익'].sum()
                total_quantity = summary_df['판매수량'].sum()
                days_count = (analysis_end_date - analysis_start_date).days + 1
                
                # ========== 1. 핵심 요약 지표 (KPI 카드) ==========
                st.markdown("""
                <div style="margin: 2rem 0 1rem 0;">
                    <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                        📊 기간 내 요약
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("총 판매량", f"{int(total_quantity):,}개")
                with col2:
                    st.metric("총 매출", f"{total_revenue:,.0f}원")
                with col3:
                    st.metric("총 원가", f"{total_cost:,.0f}원")
                with col4:
                    st.metric("총 이익", f"{total_profit:,.0f}원")
                with col5:
                    avg_daily_quantity = total_quantity / days_count if days_count > 0 else 0
                    st.metric("일평균 판매량", f"{avg_daily_quantity:,.1f}개")
                
                render_section_divider()
                
                # ========== 2. ABC 분석 ==========
                st.markdown("""
                <div style="margin: 2rem 0 1rem 0;">
                    <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                        📊 판매 ABC 분석
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                if total_revenue <= 0:
                    st.info("매출 데이터가 충분하지 않아 ABC 분석을 할 수 없습니다.")
                else:
                    # ABC 분석 테이블
                    summary_df = summary_df.sort_values('매출', ascending=False)
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
                    
                    summary_df['ABC 등급'] = summary_df['누계 비율(%)'].apply(assign_abc_grade)
                    
                    # 표시용 데이터프레임 구성
                    display_df = summary_df.copy()
                    display_df['판매가'] = display_df['판매가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    display_df['매출'] = display_df['매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    display_df['원가'] = display_df['원가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    display_df['총판매원가'] = display_df['총판매원가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    
                    # 이익 컬럼이 있는지 확인 후 포맷팅
                    if '이익' in display_df.columns:
                        display_df['이익'] = display_df['이익'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    if '이익률' in display_df.columns:
                        display_df['이익률'] = display_df['이익률'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
                    if '원가율' in display_df.columns:
                        display_df['원가율'] = display_df['원가율'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
                    
                    # 표시할 컬럼 선택 (존재하는 컬럼만)
                    available_columns = []
                    column_order = ['메뉴명', '판매가', '판매수량', '매출', '비율(%)', '누계 비율(%)', 'ABC 등급', 
                                   '원가', '총판매원가', '이익', '이익률', '원가율']
                    for col in column_order:
                        if col in display_df.columns:
                            available_columns.append(col)
                    
                    display_df = display_df[available_columns]
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    render_section_divider()
                    
                    # ========== 3. 인기 메뉴 TOP 10 ==========
                    st.markdown("""
                    <div style="margin: 2rem 0 1rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                            🏆 인기 메뉴 TOP 10
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    top10_df = summary_df.head(10).copy()
                    top10_df.insert(0, '순위', range(1, len(top10_df) + 1))
                    
                    display_top10 = top10_df.copy()
                    display_top10['판매수량'] = display_top10['판매수량'].apply(lambda x: f"{int(x):,}개")
                    display_top10['매출'] = display_top10['매출'].apply(lambda x: f"{int(x):,}원")
                    
                    st.dataframe(
                        display_top10[['순위', '메뉴명', '판매수량', '매출', '비율(%)', 'ABC 등급']],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    render_section_divider()
                    
                    # ========== 4. 수익성 분석 ==========
                    st.markdown("""
                    <div style="margin: 2rem 0 1rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                            💰 수익성 분석
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 이익률 기준 정렬
                    profitability_df = summary_df.sort_values('이익률', ascending=False).copy()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**✅ 최고 수익성 메뉴 (이익률 기준)**")
                        top_profit_df = profitability_df.head(5).copy()
                        top_profit_df['이익률'] = top_profit_df['이익률'].apply(lambda x: f"{x:.1f}%")
                        top_profit_df['이익'] = top_profit_df['이익'].apply(lambda x: f"{int(x):,}원")
                        st.dataframe(
                            top_profit_df[['메뉴명', '이익', '이익률', '원가율']],
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        st.write("**⚠️ 저수익성 메뉴 (이익률 기준)**")
                        low_profit_df = profitability_df.tail(5).copy()
                        low_profit_df = low_profit_df[low_profit_df['이익률'] < 30].copy()  # 이익률 30% 미만만 표시
                        if not low_profit_df.empty:
                            low_profit_df['이익률'] = low_profit_df['이익률'].apply(lambda x: f"{x:.1f}%")
                            low_profit_df['이익'] = low_profit_df['이익'].apply(lambda x: f"{int(x):,}원")
                            st.dataframe(
                                low_profit_df[['메뉴명', '이익', '이익률', '원가율']],
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.info("저수익성 메뉴가 없습니다.")
                    
                    render_section_divider()
                    
                    # ========== 5. 판매 트렌드 분석 ==========
                    st.markdown("""
                    <div style="margin: 2rem 0 1rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                            📈 판매 트렌드 분석
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 일별 판매량 집계
                    daily_summary = filtered_sales_df.groupby('날짜')['판매수량'].sum().reset_index()
                    daily_summary = daily_summary.sort_values('날짜')
                    
                    # 최근 7일 vs 최근 30일 비교
                    today_date = today_kst()
                    recent_7_days = filtered_sales_df[
                        filtered_sales_df['날짜'].dt.date >= (today_date - timedelta(days=7))
                    ]
                    recent_30_days = filtered_sales_df[
                        filtered_sales_df['날짜'].dt.date >= (today_date - timedelta(days=30))
                    ]
                    
                    if not recent_7_days.empty and not recent_30_days.empty:
                        avg_7d = recent_7_days['판매수량'].sum() / 7
                        avg_30d = recent_30_days['판매수량'].sum() / 30
                        trend_change = avg_7d - avg_30d
                        trend_pct = (trend_change / avg_30d * 100) if avg_30d > 0 else 0
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("최근 7일 평균 판매량", f"{avg_7d:,.1f}개")
                        with col2:
                            st.metric("최근 30일 평균 판매량", f"{avg_30d:,.1f}개")
                        with col3:
                            trend_status = "📈 상승" if trend_change > 0 else "📉 하락" if trend_change < 0 else "➡️ 유지"
                            st.metric("트렌드", f"{trend_pct:+.1f}%", trend_status)
                    
                    # 일별 판매량 표
                    if not daily_summary.empty:
                        st.write("**📅 일별 판매량 추이**")
                        display_daily = daily_summary.copy()
                        display_daily['날짜'] = display_daily['날짜'].dt.strftime('%Y-%m-%d')
                        display_daily['판매수량'] = display_daily['판매수량'].apply(lambda x: f"{int(x):,}개")
                        st.dataframe(display_daily, use_container_width=True, hide_index=True)
                    
                    render_section_divider()
                    
                    # ========== 6. 요일별 인기 메뉴 ==========
                    st.markdown("""
                    <div style="margin: 2rem 0 1rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                            📅 요일별 인기 메뉴
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    filtered_sales_df['요일'] = filtered_sales_df['날짜'].dt.day_name()
                    day_names_kr = {
                        'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
                        'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
                    }
                    filtered_sales_df['요일한글'] = filtered_sales_df['요일'].map(day_names_kr)
                    
                    day_menu_summary = filtered_sales_df.groupby(['요일한글', '메뉴명'])['판매수량'].sum().reset_index()
                    day_menu_summary = day_menu_summary.sort_values(['요일한글', '판매수량'], ascending=[True, False])
                    
                    # 요일별 TOP 3 메뉴
                    day_order = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
                    for day in day_order:
                        day_data = day_menu_summary[day_menu_summary['요일한글'] == day].head(3)
                        if not day_data.empty:
                            st.write(f"**{day} TOP 3**")
                            display_day = day_data.copy()
                            display_day['판매수량'] = display_day['판매수량'].apply(lambda x: f"{int(x):,}개")
                            st.dataframe(display_day[['메뉴명', '판매수량']], use_container_width=True, hide_index=True)
                    
                    render_section_divider()
                    
                    # ========== 7. 메뉴별 성장률 분석 ==========
                    st.markdown("""
                    <div style="margin: 2rem 0 1rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                            📊 메뉴별 성장률 분석
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 기간을 반으로 나눠서 비교
                    mid_date = analysis_start_date + (analysis_end_date - analysis_start_date) / 2
                    first_half = filtered_sales_df[filtered_sales_df['날짜'].dt.date <= mid_date]
                    second_half = filtered_sales_df[filtered_sales_df['날짜'].dt.date > mid_date]
                    
                    if not first_half.empty and not second_half.empty:
                        first_half_summary = first_half.groupby('메뉴명')['판매수량'].sum().reset_index()
                        first_half_summary.columns = ['메뉴명', '전반기 판매량']
                        second_half_summary = second_half.groupby('메뉴명')['판매수량'].sum().reset_index()
                        second_half_summary.columns = ['메뉴명', '후반기 판매량']
                        
                        growth_df = pd.merge(first_half_summary, second_half_summary, on='메뉴명', how='outer')
                        growth_df = growth_df.fillna(0)
                        growth_df['성장률(%)'] = ((growth_df['후반기 판매량'] - growth_df['전반기 판매량']) / 
                                                 growth_df['전반기 판매량'] * 100).round(1)
                        growth_df = growth_df.replace([float('inf'), float('-inf')], 0)
                        growth_df = growth_df.sort_values('성장률(%)', ascending=False)
                        
                        st.write("**📈 성장률 TOP 10 메뉴**")
                        top_growth_df = growth_df.head(10).copy()
                        top_growth_df['전반기 판매량'] = top_growth_df['전반기 판매량'].apply(lambda x: f"{int(x):,}개")
                        top_growth_df['후반기 판매량'] = top_growth_df['후반기 판매량'].apply(lambda x: f"{int(x):,}개")
                        top_growth_df['성장률(%)'] = top_growth_df['성장률(%)'].apply(lambda x: f"{x:+.1f}%")
                        st.dataframe(
                            top_growth_df[['메뉴명', '전반기 판매량', '후반기 판매량', '성장률(%)']],
                            use_container_width=True,
                            hide_index=True
                        )


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_sales_analysis()
