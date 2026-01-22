"""
매출 관리 페이지 (분석 전용)
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from datetime import timedelta
from calendar import monthrange
from src.ui_helpers import render_page_header, render_section_divider, safe_get_value
from src.utils.time_utils import current_year_kst, current_month_kst, today_kst
from src.storage_supabase import load_csv, load_monthly_sales_total
from src.analytics import merge_sales_visitors, calculate_correlation
from src.auth import get_current_store_id

# 공통 설정 적용
bootstrap(page_title="Sales Management")

# 로그인 체크
from src.auth import check_login, show_login_page
if not check_login():
    show_login_page()
    st.stop()


def render_sales_management():
    """매출 관리 페이지 렌더링"""
    render_page_header("매출 관리", "📊")
    
    # store_id 초기화 (UnboundLocalError 방지)
    store_id = None
    try:
        store_id = get_current_store_id()
    except Exception:
        store_id = None
    
    # 매출 새로고침 버튼 (캐시 무효화)
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 매출 새로고침", key="sales_refresh", use_container_width=True):
            # load_csv 캐시 무효화
            load_csv.clear()
            # load_monthly_sales_total 캐시도 무효화
            try:
                from src.storage_supabase import load_monthly_sales_total
                load_monthly_sales_total.clear()
            except Exception:
                pass
            st.success("✅ 매출 데이터를 새로고침했습니다.")
            st.rerun()
    
    # 데이터 로드
    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
    targets_df = load_csv('targets.csv', default_columns=[
        '연도', '월', '목표매출', '목표원가율', '목표인건비율',
        '목표임대료율', '목표기타비용율', '목표순이익률'
    ])
    
    # 매출과 방문자 데이터 통합
    try:
        merged_df = merge_sales_visitors(sales_df, visitors_df)
    except Exception:
        merged_df = pd.DataFrame()
    
    # 날짜 컬럼을 datetime으로 변환
    if not merged_df.empty and '날짜' in merged_df.columns:
        try:
            merged_df['날짜'] = pd.to_datetime(merged_df['날짜'])
        except Exception:
            pass
    if not sales_df.empty and '날짜' in sales_df.columns:
        try:
            sales_df['날짜'] = pd.to_datetime(sales_df['날짜'])
        except Exception:
            pass
    if not visitors_df.empty and '날짜' in visitors_df.columns:
        try:
            visitors_df['날짜'] = pd.to_datetime(visitors_df['날짜'])
        except Exception:
            pass
    
    current_year = current_year_kst()
    current_month = current_month_kst()
    today = today_kst()
    
    # 목표 매출 확인 (전역 사용)
    target_sales = 0
    target_row = targets_df[
        (targets_df['연도'] == current_year) & 
        (targets_df['월'] == current_month)
    ]
    # Phase 1: 안전한 DataFrame 접근
    target_sales = safe_get_value(target_row, '목표매출', 0.0)
    if target_sales is None:
        target_sales = 0.0
    else:
        target_sales = float(target_sales)
    
    # 이번달 데이터 필터링 및 기본 변수 계산 (전역 사용)
    if not merged_df.empty and '날짜' in merged_df.columns and pd.api.types.is_datetime64_any_dtype(merged_df['날짜']):
        month_data = merged_df[
            (merged_df['날짜'].dt.year == current_year) & 
            (merged_df['날짜'].dt.month == current_month)
        ].copy()
    else:
        month_data = pd.DataFrame()
    
    # 월매출: SSOT 함수 사용 (헌법 준수)
    month_total_sales = load_monthly_sales_total(store_id, current_year, current_month) if store_id else 0
    month_total_visitors = month_data['방문자수'].sum() if not month_data.empty and '방문자수' in month_data.columns else 0
    
    if not merged_df.empty:
        # ========== 1. 핵심 요약 지표 (KPI 카드) ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📊 이번달 요약
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not month_data.empty:
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
                # 목표 달성률 계산
                target_achievement = (month_total_sales / target_sales * 100) if target_sales > 0 else None
                if target_achievement is not None:
                    st.metric("목표 달성률", f"{target_achievement:.1f}%", 
                            f"{target_achievement - 100:.1f}%p" if target_achievement != 100 else "0%p")
                else:
                    st.metric("목표 달성률", "-", help="목표 매출이 설정되지 않았습니다")
        
        render_section_divider()
        
        # ========== 2. 기간별 비교 분석 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📈 기간별 비교 분석
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 전월 데이터
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year
        
        prev_month_data = merged_df[
            (merged_df['날짜'].dt.year == prev_year) & 
            (merged_df['날짜'].dt.month == prev_month)
        ].copy()
        
        # 작년 동월 데이터
        last_year_month_data = merged_df[
            (merged_df['날짜'].dt.year == current_year - 1) & 
            (merged_df['날짜'].dt.month == current_month)
        ].copy()
        
        # 주간 비교 (이번 주 vs 지난 주)
        week_start = today - timedelta(days=today.weekday())
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_start - timedelta(days=1)
        
        this_week_data = merged_df[
            (merged_df['날짜'].dt.date >= week_start) & 
            (merged_df['날짜'].dt.date <= today)
        ].copy()
        
        last_week_data = merged_df[
            (merged_df['날짜'].dt.date >= last_week_start) & 
            (merged_df['날짜'].dt.date <= last_week_end)
        ].copy()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**전월 대비**")
            if not prev_month_data.empty and not month_data.empty:
                # 전월 매출: SSOT 함수 사용
                prev_year = current_year if current_month > 1 else current_year - 1
                prev_month = current_month - 1 if current_month > 1 else 12
                prev_sales = load_monthly_sales_total(store_id, prev_year, prev_month) if store_id else 0
                prev_visitors = prev_month_data['방문자수'].sum() if '방문자수' in prev_month_data.columns else 0
                
                sales_change = month_total_sales - prev_sales
                sales_change_pct = (sales_change / prev_sales * 100) if prev_sales > 0 else 0
                visitors_change = month_total_visitors - prev_visitors
                visitors_change_pct = (visitors_change / prev_visitors * 100) if prev_visitors > 0 else 0
                
                st.metric("매출", f"{month_total_sales:,.0f}원", f"{sales_change:+,.0f}원 ({sales_change_pct:+.1f}%)")
                st.metric("방문자", f"{int(month_total_visitors):,}명", f"{visitors_change:+,.0f}명 ({visitors_change_pct:+.1f}%)")
            else:
                st.info("전월 데이터 없음")
        
        with col2:
            st.write("**작년 동월 대비**")
            if not last_year_month_data.empty and not month_data.empty:
                # 작년 동월 매출: SSOT 함수 사용
                last_year_sales = load_monthly_sales_total(store_id, current_year - 1, current_month) if store_id else 0
                last_year_visitors = last_year_month_data['방문자수'].sum() if '방문자수' in last_year_month_data.columns else 0
                
                sales_change = month_total_sales - last_year_sales
                sales_change_pct = (sales_change / last_year_sales * 100) if last_year_sales > 0 else 0
                visitors_change = month_total_visitors - last_year_visitors
                visitors_change_pct = (visitors_change / last_year_visitors * 100) if last_year_visitors > 0 else 0
                
                st.metric("매출", f"{month_total_sales:,.0f}원", f"{sales_change:+,.0f}원 ({sales_change_pct:+.1f}%)")
                st.metric("방문자", f"{int(month_total_visitors):,}명", f"{visitors_change:+,.0f}명 ({visitors_change_pct:+.1f}%)")
            else:
                st.info("작년 동월 데이터 없음")
        
        with col3:
            st.write("**주간 비교 (이번 주 vs 지난 주)**")
            if not this_week_data.empty and not last_week_data.empty:
                this_week_sales = this_week_data['총매출'].sum() if '총매출' in this_week_data.columns else 0
                last_week_sales = last_week_data['총매출'].sum() if '총매출' in last_week_data.columns else 0
                this_week_visitors = this_week_data['방문자수'].sum() if '방문자수' in this_week_data.columns else 0
                last_week_visitors = last_week_data['방문자수'].sum() if '방문자수' in last_week_data.columns else 0
                
                sales_change = this_week_sales - last_week_sales
                sales_change_pct = (sales_change / last_week_sales * 100) if last_week_sales > 0 else 0
                visitors_change = this_week_visitors - last_week_visitors
                visitors_change_pct = (visitors_change / last_week_visitors * 100) if last_week_visitors > 0 else 0
                
                st.metric("매출", f"{this_week_sales:,.0f}원", f"{sales_change:+,.0f}원 ({sales_change_pct:+.1f}%)")
                st.metric("방문자", f"{int(this_week_visitors):,}명", f"{visitors_change:+,.0f}명 ({visitors_change_pct:+.1f}%)")
            else:
                st.info("주간 데이터 부족")
        
        render_section_divider()
        
        # ========== 3. 요일별 분석 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📅 요일별 패턴 분석
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not month_data.empty:
            month_data['요일'] = month_data['날짜'].dt.day_name()
            day_names_kr = {
                'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
                'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
            }
            month_data['요일한글'] = month_data['요일'].map(day_names_kr)
            
            day_analysis = month_data.groupby('요일한글').agg({
                '총매출': ['mean', 'sum', 'count'],
                '방문자수': ['mean', 'sum']
            }).reset_index()
            day_analysis.columns = ['요일', '평균매출', '총매출', '일수', '평균방문자', '총방문자']
            day_analysis['객단가'] = day_analysis['평균매출'] / day_analysis['평균방문자']
            day_analysis = day_analysis.sort_values('평균매출', ascending=False)
            
            # 요일 순서 정렬
            day_order = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
            day_analysis['요일순서'] = day_analysis['요일'].map({day: i for i, day in enumerate(day_order)})
            day_analysis = day_analysis.sort_values('요일순서')
            
            display_day = day_analysis.copy()
            display_day['평균매출'] = display_day['평균매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_day['총매출'] = display_day['총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_day['평균방문자'] = display_day['평균방문자'].apply(lambda x: f"{int(x):,.1f}명" if pd.notna(x) else "-")
            display_day['객단가'] = display_day['객단가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            
            st.dataframe(
                display_day[['요일', '일수', '평균매출', '총매출', '평균방문자', '객단가']],
                use_container_width=True,
                hide_index=True
            )
            
            # 가장 좋은/나쁜 요일
            best_day = day_analysis.loc[day_analysis['평균매출'].idxmax()]
            worst_day = day_analysis.loc[day_analysis['평균매출'].idxmin()]
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ **최고 요일**: {best_day['요일']} (평균 {int(best_day['평균매출']):,}원)")
            with col2:
                st.warning(f"⚠️ **최저 요일**: {worst_day['요일']} (평균 {int(worst_day['평균매출']):,}원)")
        
        render_section_divider()
        
        # 목표 관련 변수 초기화 (전역 사용)
        days_in_month = monthrange(current_year, current_month)[1]
        current_day = today.day if today.year == current_year and today.month == current_month else days_in_month
        remaining_days = days_in_month - current_day
        
        # 예상 매출 및 달성률 계산 (목표가 있는 경우)
        daily_actual = month_total_sales / current_day if current_day > 0 else 0
        forecast_sales = month_total_sales + (daily_actual * remaining_days) if current_day > 0 else 0
        forecast_achievement = (forecast_sales / target_sales * 100) if not target_row.empty and target_sales > 0 else None
        
        # ========== 4. 목표 대비 실적 ==========
        if not target_row.empty:
            st.markdown("""
            <div style="margin: 2rem 0 1rem 0;">
                <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                    🎯 목표 달성 현황
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            daily_target = target_sales / days_in_month if days_in_month > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("목표 매출", f"{target_sales:,.0f}원")
            with col2:
                st.metric("현재 누적 매출", f"{month_total_sales:,.0f}원", 
                        f"{month_total_sales - target_sales:+,.0f}원")
            with col3:
                st.metric("일평균 목표", f"{daily_target:,.0f}원")
            with col4:
                st.metric("일평균 실적", f"{daily_actual:,.0f}원", 
                        f"{daily_actual - daily_target:+,.0f}원")
            
            # 예상 매출 및 달성 가능성
            col1, col2 = st.columns(2)
            with col1:
                st.metric("예상 월 매출", f"{forecast_sales:,.0f}원")
            with col2:
                achievement_status = "✅ 달성 가능" if forecast_achievement >= 100 else "⚠️ 달성 위험"
                st.metric("예상 달성률", f"{forecast_achievement:.1f}%", achievement_status)
            
            # 남은 일수 기준 필요 일평균
            if remaining_days > 0:
                required_daily = (target_sales - month_total_sales) / remaining_days
                if required_daily > 0:
                    st.info(f"📌 목표 달성을 위해 남은 {remaining_days}일 동안 일평균 **{required_daily:,.0f}원**이 필요합니다.")
            
            render_section_divider()
        
        # ========== 5. 트렌드 분석 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📊 매출 트렌드
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 최근 7일 vs 최근 30일
        recent_7_days = merged_df[merged_df['날짜'].dt.date >= (today - timedelta(days=7))].copy()
        recent_30_days = merged_df[merged_df['날짜'].dt.date >= (today - timedelta(days=30))].copy()
        
        if not recent_7_days.empty and not recent_30_days.empty:
            avg_7d = recent_7_days['총매출'].mean() if '총매출' in recent_7_days.columns else 0
            avg_30d = recent_30_days['총매출'].mean() if '총매출' in recent_30_days.columns else 0
            trend_change = avg_7d - avg_30d
            trend_pct = (trend_change / avg_30d * 100) if avg_30d > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("최근 7일 평균", f"{avg_7d:,.0f}원")
            with col2:
                st.metric("최근 30일 평균", f"{avg_30d:,.0f}원")
            with col3:
                trend_status = "📈 상승" if trend_change > 0 else "📉 하락" if trend_change < 0 else "➡️ 유지"
                st.metric("트렌드", f"{trend_pct:+.1f}%", trend_status)
        
        render_section_divider()
        
        # ========== 6. 경고/알림 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                ⚠️ 알림 및 경고
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        alerts = []
        
        # 목표 대비 저조한 날짜
        if not target_row.empty and not month_data.empty:
            daily_target = target_sales / days_in_month if days_in_month > 0 else 0
            low_days = month_data[month_data['총매출'] < daily_target * 0.8] if '총매출' in month_data.columns else pd.DataFrame()
            if not low_days.empty:
                low_days_count = len(low_days)
                alerts.append(f"🔴 목표 대비 저조한 날짜: {low_days_count}일 (목표의 80% 미만)")
        
        # 전일 대비 급락
        if len(month_data) >= 2:
            recent_days = month_data.sort_values('날짜').tail(2)
            if len(recent_days) == 2:
                # Phase 1: 안전한 DataFrame 접근
                prev_sales = safe_get_value(recent_days.iloc[[0]], '총매출', 0) if len(recent_days) > 0 else 0
                curr_sales = safe_get_value(recent_days.iloc[[1]], '총매출', 0) if len(recent_days) > 1 else 0
                if prev_sales > 0:
                    drop_pct = ((curr_sales - prev_sales) / prev_sales * 100)
                    if drop_pct < -20:
                        alerts.append(f"🔴 전일 대비 급락: {drop_pct:.1f}% 감소")
        
        # 연속 저조일
        if not month_data.empty and '총매출' in month_data.columns:
            month_data_sorted = month_data.sort_values('날짜')
            daily_target = target_sales / days_in_month if not target_row.empty and days_in_month > 0 else month_data_sorted['총매출'].mean() * 0.8
            low_days_series = month_data_sorted['총매출'] < daily_target
            consecutive_low = 0
            max_consecutive = 0
            for is_low in low_days_series:
                if is_low:
                    consecutive_low += 1
                    max_consecutive = max(max_consecutive, consecutive_low)
                else:
                    consecutive_low = 0
            if max_consecutive >= 3:
                alerts.append(f"🟡 연속 저조일: {max_consecutive}일 연속 목표 미달")
        
        # 월말 목표 달성 위험
        if not target_row.empty and forecast_achievement is not None:
            if forecast_achievement < 90 and remaining_days <= 7:
                alerts.append(f"🔴 월말 목표 달성 위험: 현재 달성률 {target_achievement:.1f}%, 예상 달성률 {forecast_achievement:.1f}%")
        
        if alerts:
            for alert in alerts:
                if "🔴" in alert:
                    st.error(alert)
                elif "🟡" in alert:
                    st.warning(alert)
                else:
                    st.info(alert)
        else:
            st.success("✅ 특별한 알림이 없습니다. 매출이 정상적으로 진행되고 있습니다.")
        
        render_section_divider()
        
        # ========== 7. 월별 요약 테이블 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📋 월별 요약 (최근 6개월)
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 최근 6개월 데이터
        six_months_ago = today - timedelta(days=180)
        recent_6m_data = merged_df[merged_df['날짜'].dt.date >= six_months_ago].copy()
        
        if not recent_6m_data.empty:
            recent_6m_data['연도'] = recent_6m_data['날짜'].dt.year
            recent_6m_data['월'] = recent_6m_data['날짜'].dt.month
            
            # 방문자 데이터는 CSV 기반 집계 유지
            visitors_summary = recent_6m_data.groupby(['연도', '월']).agg({
                '방문자수': ['sum', 'mean', 'count']
            }).reset_index()
            visitors_summary.columns = ['연도', '월', '월총방문자', '일평균방문자', '영업일수']
            
            # 월매출: SSOT 함수로 각 월별 조회
            unique_months = recent_6m_data[['연도', '월']].drop_duplicates().sort_values(['연도', '월'], ascending=[False, False])
            monthly_sales_list = []
            for _, row in unique_months.iterrows():
                year = int(row['연도'])
                month = int(row['월'])
                sales_total = load_monthly_sales_total(store_id, year, month) if store_id else 0
                # 일평균 매출 계산을 위해 영업일수 필요 (visitors_summary에서 가져옴)
                visitors_row = visitors_summary[(visitors_summary['연도'] == year) & (visitors_summary['월'] == month)]
                days_count = int(visitors_row['영업일수'].iloc[0]) if not visitors_row.empty else 0
                avg_daily_sales = sales_total / days_count if days_count > 0 else 0
                monthly_sales_list.append({
                    '연도': year,
                    '월': month,
                    '월총매출': sales_total,
                    '일평균매출': avg_daily_sales
                })
            
            sales_summary = pd.DataFrame(monthly_sales_list)
            
            # 방문자와 매출 데이터 병합
            monthly_summary = pd.merge(visitors_summary, sales_summary, on=['연도', '월'], how='outer')
            monthly_summary['월별객단가'] = monthly_summary['월총매출'] / monthly_summary['월총방문자']
            monthly_summary = monthly_summary.sort_values(['연도', '월'], ascending=[False, False])
            
            # 성장률 계산
            monthly_summary['전월대비'] = monthly_summary['월총매출'].pct_change() * 100
            
            display_monthly = monthly_summary.head(6).copy()
            display_monthly['월'] = display_monthly['월'].apply(lambda x: f"{int(x)}월")
            display_monthly['월총매출'] = display_monthly['월총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_monthly['일평균매출'] = display_monthly['일평균매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_monthly['월총방문자'] = display_monthly['월총방문자'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
            display_monthly['월별객단가'] = display_monthly['월별객단가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_monthly['전월대비'] = display_monthly['전월대비'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
            
            st.dataframe(
                display_monthly[['연도', '월', '영업일수', '월총매출', '일평균매출', '월총방문자', '월별객단가', '전월대비']],
                use_container_width=True,
                hide_index=True
            )
        
        render_section_divider()
        
        # ========== 8. 예측/예상 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                🔮 예상 매출 및 목표 달성 가능성
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not month_data.empty:
            # 현재 추세 기반 예상 (위에서 이미 계산된 forecast_sales 사용)
            if current_day > 0:
                
                # 필요 일평균 (목표가 있는 경우만)
                if not target_row.empty and target_sales > 0:
                    required_daily = (target_sales - month_total_sales) / remaining_days if remaining_days > 0 and target_sales > month_total_sales else 0
                else:
                    required_daily = 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("이번달 예상 총 매출", f"{forecast_sales:,.0f}원")
                with col2:
                    if forecast_achievement is not None:
                        st.metric("예상 목표 달성률", f"{forecast_achievement:.1f}%")
                    else:
                        st.info("목표 매출 미설정")
                with col3:
                    if required_daily > 0:
                        st.warning(f"필요 일평균: {required_daily:,.0f}원")
                    elif not target_row.empty:
                        st.success("목표 달성 가능")
                    else:
                        st.info("목표 미설정")
        
        render_section_divider()
        
        # ========== 저장된 매출 내역 ==========
        # 저장된 매출 내역 (매출 + 네이버 스마트플레이스 방문자 통합)
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📋 저장된 매출 내역
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not merged_df.empty:
            # 통합 데이터 표시 (입력값만 표시)
            display_df = merged_df.copy()
            
            # 표시할 컬럼만 선택 (기술적 컬럼 제외)
            display_columns = []
            if '날짜' in display_df.columns:
                display_columns.append('날짜')
            if '매장' in display_df.columns:
                display_columns.append('매장')
            if '카드매출' in display_df.columns:
                display_columns.append('카드매출')
            if '현금매출' in display_df.columns:
                display_columns.append('현금매출')
            if '총매출' in display_df.columns:
                display_columns.append('총매출')
            if '방문자수' in display_df.columns:
                display_columns.append('방문자수')
            
            # 필요한 컬럼만 선택
            if display_columns:
                display_df = display_df[display_columns]
                
                # 날짜를 문자열로 변환
                if '날짜' in display_df.columns:
                    display_df['날짜'] = pd.to_datetime(display_df['날짜']).dt.strftime('%Y-%m-%d')
                
                # 숫자 포맷팅
                if '총매출' in display_df.columns:
                    display_df['총매출'] = display_df['총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                if '카드매출' in display_df.columns:
                    display_df['카드매출'] = display_df['카드매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                if '현금매출' in display_df.columns:
                    display_df['현금매출'] = display_df['현금매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                if '방문자수' in display_df.columns:
                    display_df['방문자수'] = display_df['방문자수'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # ========== 이달 일일 매출과 방문자 사이의 연관성 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📈 이달 일일 매출과 방문자 사이의 연관성
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 이번달 데이터 사용 (위에서 이미 필터링됨)
        chart_df = month_data.copy() if not month_data.empty else pd.DataFrame()
        
        if not chart_df.empty and '총매출' in chart_df.columns and '방문자수' in chart_df.columns:
            # 연관성 지표 계산
            month_sales_df = chart_df[['날짜', '총매출']].copy()
            month_visitors_df = chart_df[['날짜', '방문자수']].copy()
            correlation = calculate_correlation(month_sales_df, month_visitors_df)
            
            # 연관성 지표 표시
            if correlation is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "상관계수",
                        f"{correlation:.3f}",
                        help="피어슨 상관계수: -1 ~ 1 사이 값. 1에 가까울수록 양의 상관관계가 강함"
                    )
                with col2:
                    if correlation > 0.7:
                        st.success("✅ 강한 양의 상관관계\n방문자가 많을수록 매출이 높습니다.")
                    elif correlation > 0.3:
                        st.info("ℹ️ 중간 정도의 양의 상관관계")
                    elif correlation > -0.3:
                        st.warning("⚠️ 상관관계가 거의 없음")
                    else:
                        st.error("❌ 음의 상관관계")
                with col3:
                    # 평균 일일 매출
                    avg_sales = chart_df['총매출'].mean()
                    st.metric("평균 일일 매출", f"{avg_sales:,.0f}원")
            
            render_section_divider()
            
            # 표로 표시
            display_chart_df = chart_df.copy()
            display_chart_df['날짜'] = display_chart_df['날짜'].dt.strftime('%Y-%m-%d')
            display_chart_df['일일 매출'] = display_chart_df['총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_chart_df['일일 방문자수'] = display_chart_df['방문자수'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
            
            # 표시할 컬럼만 선택
            table_df = display_chart_df[['날짜', '일일 매출', '일일 방문자수']].copy()
            
            st.dataframe(table_df, use_container_width=True, hide_index=True)
        elif not chart_df.empty:
            st.info("이번달 매출 또는 방문자 데이터가 없습니다.")
        else:
            st.info("이번달 데이터가 없습니다.")
    else:
        st.info("저장된 매출 데이터가 없습니다.")


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_sales_management()
