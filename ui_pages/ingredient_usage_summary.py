"""
재료 사용량 집계 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from src.ui_helpers import render_page_header, render_section_divider
from src.storage_supabase import load_csv
from src.analytics import calculate_ingredient_usage

# 공통 설정 적용
bootstrap(page_title="Ingredient Usage Summary")


def render_ingredient_usage_summary():
    """재료 사용량 집계 페이지 렌더링"""
    render_page_header("재료 사용량 집계", "📈")

    # 데이터 로드
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])

    if not daily_sales_df.empty and not recipe_df.empty:
        usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)

        if not usage_df.empty:
            # 날짜를 datetime으로 변환
            usage_df['날짜'] = pd.to_datetime(usage_df['날짜'])
            
            # 사용 가능한 날짜 범위
            min_date = usage_df['날짜'].min().date()
            max_date = usage_df['날짜'].max().date()
            
            # 기간 선택 필터
            st.markdown("**📅 기간 선택**")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "시작일",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="ingredient_usage_summary_usage_start_date"
                )
            with col2:
                end_date = st.date_input(
                    "종료일",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="ingredient_usage_summary_usage_end_date"
                )
            
            # 기간 유효성 검사
            if start_date > end_date:
                st.error("⚠️ 시작일은 종료일보다 이전이어야 합니다.")
            else:
                # 기간 필터링
                display_usage_df = usage_df[
                    (usage_df['날짜'].dt.date >= start_date) & 
                    (usage_df['날짜'].dt.date <= end_date)
                ].copy()
                
                if not display_usage_df.empty:
                    # 재료 단가와 조인하여 총 사용 단가 계산
                    if not ingredient_df.empty:
                        display_usage_df = pd.merge(
                            display_usage_df,
                            ingredient_df[['재료명', '단가']],
                            on='재료명',
                            how='left'
                        )
                        display_usage_df['단가'] = display_usage_df['단가'].fillna(0)
                    else:
                        display_usage_df['단가'] = 0.0

                    display_usage_df['총사용단가'] = display_usage_df['총사용량'] * display_usage_df['단가']
                    
                    # 기간 표시
                    st.markdown(f"**📊 조회 기간: {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}**")
                    
                    render_section_divider()
                    
                    # 재료별 총 사용량/총 사용 단가 집계 (기간 전체 합계)
                    ingredient_summary = (
                        display_usage_df
                        .groupby('재료명')[['총사용량', '총사용단가']]
                        .sum()
                        .reset_index()
                    )

                    # 사용 단가 기준으로 정렬
                    ingredient_summary = ingredient_summary.sort_values('총사용단가', ascending=False)
                    
                    # 총 사용단가 합계 계산
                    total_cost = ingredient_summary['총사용단가'].sum()
                    
                    # 비율 및 누적 비율 계산
                    ingredient_summary['비율(%)'] = (ingredient_summary['총사용단가'] / total_cost * 100).round(2)
                    ingredient_summary['누적 비율(%)'] = ingredient_summary['비율(%)'].cumsum().round(2)
                    
                    # ABC 등급 부여
                    def assign_abc_grade(cumulative_ratio):
                        if cumulative_ratio <= 70:
                            return 'A'
                        elif cumulative_ratio <= 90:
                            return 'B'
                        else:
                            return 'C'
                    
                    ingredient_summary['ABC 등급'] = ingredient_summary['누적 비율(%)'].apply(assign_abc_grade)
                    
                    # TOP 10 재료
                    st.markdown("**💰 사용 단가 TOP 10 재료**")
                    top10_df = ingredient_summary.head(10).copy()
                    top10_df.insert(0, '순위', range(1, len(top10_df) + 1))
                    top10_df['총 사용량'] = top10_df['총사용량']
                    top10_df['총 사용단가'] = top10_df['총사용단가']
                    top10_df = top10_df[['순위', '재료명', '총 사용량', '총 사용단가', '비율(%)', '누적 비율(%)', 'ABC 등급']]
                    st.dataframe(top10_df, use_container_width=True, hide_index=True)
                    # TOP 10 총합계
                    top10_total = top10_df['총 사용단가'].sum()
                    st.markdown(f"**💰 TOP 10 총 사용단가 합계: {top10_total:,.0f}원**")
                    
                    render_section_divider()
                    
                    # 전체 재료 사용 단가 순위표 (1위부터 끝까지, ABC 분석 포함)
                    st.markdown("**📊 전체 재료 사용 단가 순위 (ABC 분석)**")
                    full_ranking_df = ingredient_summary.copy()
                    full_ranking_df.insert(0, '순위', range(1, len(full_ranking_df) + 1))
                    full_ranking_df['총 사용량'] = full_ranking_df['총사용량']
                    full_ranking_df['총 사용단가'] = full_ranking_df['총사용단가']
                    full_ranking_df = full_ranking_df[['순위', '재료명', '총 사용량', '총 사용단가', '비율(%)', '누적 비율(%)', 'ABC 등급']]
                    st.dataframe(full_ranking_df, use_container_width=True, hide_index=True)
                    # 전체 총합계
                    full_total = full_ranking_df['총 사용단가'].sum()
                    st.markdown(f"**📊 전체 총 사용단가 합계: {full_total:,.0f}원**")
                    
                    # ABC 등급별 통계
                    abc_stats = full_ranking_df.groupby('ABC 등급').agg({
                        '재료명': 'count',
                        '총 사용단가': 'sum',
                        '비율(%)': 'sum'
                    }).reset_index()
                    abc_stats.columns = ['ABC 등급', '재료 수', '총 사용단가', '비율 합계(%)']
                    
                    render_section_divider()
                    st.markdown("**📈 ABC 등급별 통계**")
                    st.dataframe(abc_stats, use_container_width=True, hide_index=True)
                    
                    # 통계 정보
                    st.markdown(
                        f"**총 {len(full_ranking_df)}개 재료**"
                        f" | **총 사용량: {full_ranking_df['총 사용량'].sum():,.2f}**"
                        f" | **총 사용 단가: {full_ranking_df['총 사용단가'].sum():,.0f}원**"
                    )
                else:
                    st.warning(f"선택한 기간({start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')})에 해당하는 데이터가 없습니다.")
        else:
            st.info("재료 사용량을 계산할 데이터가 없습니다.")
    else:
        st.info("판매 내역과 레시피 데이터가 필요합니다.")


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_ingredient_usage_summary()
