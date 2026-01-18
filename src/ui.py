"""
UI 컴포넌트 모듈
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime


# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows 기본 한글 폰트
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지


def render_sales_input():
    """매출 입력 폼 렌더링 (단일 입력)"""
    st.subheader("💰 매출 입력")
    
    col1, col2 = st.columns(2)
    
    with col1:
        date = st.date_input("날짜", value=datetime.now().date(), key="sales_date")
        store = st.text_input("매장", value="Plate&Share", key="sales_store")
    
    with col2:
        st.write("")  # 공간 맞추기
        st.write("")  # 공간 맞추기
    
    # 매출 입력 (카드/현금 분리)
    st.write("**매출 입력**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        card_sales = st.number_input(
            "💳 카드매출 (원)",
            min_value=0,
            value=0,
            step=1000,
            key="sales_card"
        )
    
    with col2:
        cash_sales = st.number_input(
            "💵 현금매출 (원)",
            min_value=0,
            value=0,
            step=1000,
            key="sales_cash"
        )
    
    with col3:
        total_sales = card_sales + cash_sales
        st.markdown(f"""
        <div style="padding: 1rem; background: #f0f2f6; border-radius: 8px; border: 2px solid #667eea;">
            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">💰 총매출 (자동계산)</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #1f4788;">{total_sales:,}원</div>
        </div>
        """, unsafe_allow_html=True)
    
    return date, store, card_sales, cash_sales, total_sales


def render_sales_batch_input():
    """매출 일괄 입력 폼 렌더링 (여러 날짜)"""
    st.subheader("💰 매출 일괄 입력")
    st.info("💡 여러 날짜의 매출을 한 번에 입력할 수 있습니다. 시작일부터 종료일까지 날짜별로 입력하세요.")
    
    from datetime import timedelta
    
    # 날짜 범위 선택
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "시작일",
            value=datetime.now().date() - timedelta(days=6),
            key="batch_sales_start_date"
        )
    with col2:
        end_date = st.date_input(
            "종료일",
            value=datetime.now().date(),
            key="batch_sales_end_date"
        )
    
    # 매장명
    store = st.text_input("매장", value="Plate&Share", key="batch_sales_store")
    
    # 날짜 유효성 검사
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦을 수 없습니다.")
        return []
    
    # 날짜 리스트 생성
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    st.markdown("---")
    st.write(f"**📅 총 {len(date_list)}일의 매출 입력**")
    
    # 각 날짜별 매출 입력 (카드/현금 분리)
    sales_data = []
    for i, date in enumerate(date_list):
        st.markdown(f"**{date.strftime('%Y-%m-%d (%a)')}**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            card_sales = st.number_input(
                f"💳 카드매출 (원)",
                min_value=0,
                value=0,
                step=1000,
                key=f"batch_sales_card_{i}"
            )
        
        with col2:
            cash_sales = st.number_input(
                f"💵 현금매출 (원)",
                min_value=0,
                value=0,
                step=1000,
                key=f"batch_sales_cash_{i}"
            )
        
        with col3:
            total_sales = card_sales + cash_sales
            st.markdown(f"""
            <div style="padding: 0.8rem; background: #f0f2f6; border-radius: 8px; margin-top: 0.5rem;">
                <div style="font-size: 0.8rem; color: #7f8c8d;">💰 총매출</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #1f4788;">{total_sales:,}원</div>
            </div>
            """, unsafe_allow_html=True)
        
        if total_sales > 0:
            sales_data.append((date, store, card_sales, cash_sales, total_sales))
        
        st.markdown("---")
    
    return sales_data


def render_visitor_batch_input():
    """방문자 일괄 입력 폼 렌더링 (여러 날짜)"""
    st.subheader("👥 방문자 일괄 입력")
    st.info("💡 여러 날짜의 방문자수를 한 번에 입력할 수 있습니다. 시작일부터 종료일까지 날짜별로 입력하세요.")
    
    from datetime import timedelta
    
    # 날짜 범위 선택
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "시작일",
            value=datetime.now().date() - timedelta(days=6),
            key="batch_visitor_start_date"
        )
    with col2:
        end_date = st.date_input(
            "종료일",
            value=datetime.now().date(),
            key="batch_visitor_end_date"
        )
    
    # 날짜 유효성 검사
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦을 수 없습니다.")
        return []
    
    # 날짜 리스트 생성
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    st.markdown("---")
    st.write(f"**📅 총 {len(date_list)}일의 방문자수 입력**")
    
    # 각 날짜별 방문자수 입력
    visitor_data = []
    for i, date in enumerate(date_list):
        col1, col2 = st.columns([2, 3])
        with col1:
            st.write(f"**{date.strftime('%Y-%m-%d (%a)')}**")
        with col2:
            visitors = st.number_input(
                f"방문자수 (명)",
                min_value=0,
                value=0,
                step=1,
                key=f"batch_visitor_{i}"
            )
            if visitors > 0:
                visitor_data.append((date, visitors))
    
    return visitor_data


def render_visitor_input():
    """방문자 입력 폼 렌더링"""
    st.subheader("👥 네이버 스마트플레이스 방문자 입력")
    
    col1, col2 = st.columns(2)
    
    with col1:
        date = st.date_input("날짜", value=datetime.now().date(), key="visitor_date")
    
    with col2:
        visitors = st.number_input(
            "방문자수",
            min_value=0,
            value=0,
            step=1,
            key="visitor_count"
        )
    
    return date, visitors


def render_menu_input():
    """메뉴 입력 폼 렌더링 (단일 입력)"""
    st.subheader("🍽️ 메뉴 마스터 등록")
    
    col1, col2 = st.columns(2)
    
    with col1:
        menu_name = st.text_input("메뉴명", key="menu_name")
    
    with col2:
        price = st.number_input(
            "판매가 (원)",
            min_value=0,
            value=0,
            step=1000,
            key="menu_price"
        )
    
    return menu_name, price


def render_menu_batch_input():
    """메뉴 일괄 입력 폼 렌더링 (여러 메뉴)"""
    st.subheader("🍽️ 메뉴 일괄 등록")
    st.info("💡 여러 메뉴를 한 번에 등록할 수 있습니다. 아래에 메뉴명과 판매가를 입력하세요.")
    
    # 입력할 메뉴 개수 선택
    menu_count = st.number_input(
        "등록할 메뉴 개수",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        key="batch_menu_count"
    )
    
    st.markdown("---")
    st.write(f"**📋 총 {menu_count}개 메뉴 입력**")
    
    # 각 메뉴별 입력 필드
    menu_data = []
    for i in range(menu_count):
        col1, col2 = st.columns([3, 2])
        with col1:
            menu_name = st.text_input(
                f"메뉴명 {i+1}",
                key=f"batch_menu_name_{i}"
            )
        with col2:
            price = st.number_input(
                f"판매가 (원) {i+1}",
                min_value=0,
                value=0,
                step=1000,
                key=f"batch_menu_price_{i}"
            )
        
        if menu_name and menu_name.strip() and price > 0:
            menu_data.append((menu_name.strip(), price))
    
    return menu_data


def render_sales_chart(sales_df):
    """매출 라인 차트 렌더링"""
    if sales_df.empty:
        st.info("매출 데이터가 없습니다.")
        return
    
    if '날짜' not in sales_df.columns or '총매출' not in sales_df.columns:
        st.warning("매출 데이터 형식이 올바르지 않습니다.")
        return
    
    # 날짜 기준 정렬
    chart_df = sales_df.sort_values('날짜').copy()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(chart_df['날짜'], chart_df['총매출'], marker='o', linewidth=2, markersize=6)
    ax.set_xlabel('날짜')
    ax.set_ylabel('총매출 (원)')
    ax.set_title('날짜별 매출 추이')
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig)


def render_correlation_info(correlation):
    """상관계수 정보 표시"""
    if correlation is None:
        st.info("상관계수를 계산할 수 없습니다. (데이터 부족)")
        return
    
    st.metric(
        "매출-방문자 상관계수",
        f"{correlation:.3f}",
        help="피어슨 상관계수: -1 ~ 1 사이 값. 1에 가까울수록 양의 상관관계가 강함"
    )
    
    if correlation > 0.7:
        st.success("강한 양의 상관관계가 있습니다. 방문자가 많을수록 매출이 높습니다.")
    elif correlation > 0.3:
        st.info("중간 정도의 양의 상관관계가 있습니다.")
    elif correlation > -0.3:
        st.warning("상관관계가 거의 없습니다.")
    else:
        st.error("음의 상관관계가 있습니다.")


def render_ingredient_input():
    """재료 입력 폼 렌더링"""
    st.subheader("🥬 재료 마스터 등록")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ingredient_name = st.text_input("재료명", key="ingredient_name")
    
    with col2:
        unit = st.selectbox(
            "단위",
            options=["g", "ml", "ea", "개", "kg", "L"],
            key="ingredient_unit"
        )
    
    with col3:
        unit_price = st.number_input(
            "단가 (원/단위)",
            min_value=0.0,
            value=0.0,
            step=100.0,
            format="%.2f",
            key="ingredient_unit_price"
        )
    
    return ingredient_name, unit, unit_price


def render_recipe_input(menu_list, ingredient_list):
    """레시피 입력 폼 렌더링"""
    st.subheader("📝 레시피 등록 (메뉴-재료 매핑)")
    
    if not menu_list:
        st.warning("먼저 메뉴를 등록해주세요.")
        return None, None, None
    
    if not ingredient_list:
        st.warning("먼저 재료를 등록해주세요.")
        return None, None, None
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        menu_name = st.selectbox(
            "메뉴 선택",
            options=menu_list,
            key="recipe_menu"
        )
    
    with col2:
        ingredient_name = st.selectbox(
            "재료 선택",
            options=ingredient_list,
            key="recipe_ingredient"
        )
    
    with col3:
        quantity = st.number_input(
            "1인분 사용량",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f",
            key="recipe_quantity"
        )
    
    return menu_name, ingredient_name, quantity


def render_cost_analysis(cost_df, warning_threshold=35.0):
    """원가/원가율 분석 표시"""
    if cost_df.empty:
        st.info("원가를 계산할 데이터가 없습니다. 메뉴, 레시피, 재료 데이터를 먼저 등록해주세요.")
        return
    
    st.subheader("💰 메뉴별 원가 분석")
    
    # 원가율 경고 표시를 위한 스타일링
    def highlight_high_cost_rate(row):
        """원가율이 높은 행에 경고 표시"""
        if row['원가율'] >= warning_threshold:
            return ['background-color: #ffcccc'] * len(row)
        return [''] * len(row)
    
    # 표시용 DataFrame 생성
    display_df = cost_df.copy()
    display_df['판매가'] = display_df['판매가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
    display_df['원가'] = display_df['원가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
    display_df['원가율'] = display_df['원가율'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
    
    # 원본 데이터로 스타일 적용
    styled_df = cost_df.style.apply(highlight_high_cost_rate, axis=1)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # 경고 메시지
    high_cost_count = len(cost_df[cost_df['원가율'] >= warning_threshold])
    if high_cost_count > 0:
        st.warning(f"⚠️ 원가율이 {warning_threshold}% 이상인 메뉴가 {high_cost_count}개 있습니다. 수익성을 검토해주세요.")
    
    # 통계 정보
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 메뉴 수", len(cost_df))
    with col2:
        avg_cost_rate = cost_df['원가율'].mean()
        st.metric("평균 원가율", f"{avg_cost_rate:.2f}%")
    with col3:
        max_cost_rate = cost_df['원가율'].max()
        st.metric("최고 원가율", f"{max_cost_rate:.2f}%")
    with col4:
        min_cost_rate = cost_df['원가율'].min()
        st.metric("최저 원가율", f"{min_cost_rate:.2f}%")


def render_daily_sales_input(menu_list):
    """일일 판매 입력 폼 렌더링"""
    st.subheader("📦 일일 판매 입력")
    
    if not menu_list:
        st.warning("먼저 메뉴를 등록해주세요.")
        return None, None, None
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        from datetime import datetime
        date = st.date_input("날짜", value=datetime.now().date(), key="daily_sales_date")
    
    with col2:
        menu_name = st.selectbox(
            "메뉴 선택",
            options=menu_list,
            key="daily_sales_menu"
        )
    
    with col3:
        quantity = st.number_input(
            "판매수량",
            min_value=0,
            value=0,
            step=1,
            key="daily_sales_quantity"
        )
    
    return date, menu_name, quantity


def render_inventory_input(ingredient_list):
    """재고 입력 폼 렌더링"""
    st.subheader("📦 재고 관리")
    
    if not ingredient_list:
        st.warning("먼저 재료를 등록해주세요.")
        return None, None, None
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ingredient_name = st.selectbox(
            "재료 선택",
            options=ingredient_list,
            key="inventory_ingredient"
        )
    
    with col2:
        current_stock = st.number_input(
            "현재고",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f",
            key="inventory_current"
        )
    
    with col3:
        safety_stock = st.number_input(
            "안전재고",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f",
            key="inventory_safety"
        )
    
    return ingredient_name, current_stock, safety_stock


def render_daily_closing_input(menu_list):
    """일일 마감 통합 입력 폼 렌더링"""
    st.subheader("📋 일일 마감 입력")
    
    from datetime import datetime
    
    # 날짜 선택 (기본 오늘)
    selected_date = st.date_input("날짜", value=datetime.now().date(), key="closing_date")
    
    st.markdown("---")
    
    # 매출 입력 (카드/현금 분리)
    st.write("**💰 매출 정보**")
    col1, col2 = st.columns(2)
    with col1:
        store = st.text_input("매장", value="Plate&Share", key="closing_store")
    with col2:
        st.write("")  # 공간 맞추기
    
    col1, col2, col3 = st.columns(3)
    with col1:
        card_sales = st.number_input(
            "💳 카드매출 (원)",
            min_value=0,
            value=0,
            step=1000,
            key="closing_card_sales"
        )
    with col2:
        cash_sales = st.number_input(
            "💵 현금매출 (원)",
            min_value=0,
            value=0,
            step=1000,
            key="closing_cash_sales"
        )
    with col3:
        total_sales = card_sales + cash_sales
        st.markdown(f"""
        <div style="padding: 1rem; background: #f0f2f6; border-radius: 8px; border: 2px solid #667eea; margin-top: 0.5rem;">
            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">💰 총매출 (자동계산)</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #1f4788;">{total_sales:,}원</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 방문자 입력
    st.write("**👥 방문자 정보**")
    visitors = st.number_input(
        "네이버 스마트플레이스 방문자수",
        min_value=0,
        value=0,
        step=1,
        key="closing_visitors"
    )
    
    st.markdown("---")
    
    # 일일 판매 내역 입력
    st.write("**📦 일일 판매 내역**")
    
    if not menu_list:
        st.warning("먼저 메뉴를 등록해주세요.")
        return selected_date, store, card_sales, cash_sales, total_sales, visitors, []
    
    # 동적 입력 필드 (최대 20개 메뉴)
    sales_items = []
    
    st.write("메뉴별 판매수량을 입력하세요 (판매한 메뉴만 입력):")
    
    # 세션 상태로 입력 필드 개수 관리
    if 'sales_item_count' not in st.session_state:
        st.session_state.sales_item_count = 3  # 기본 3개
    
    col1, col2 = st.columns([3, 1])
    with col1:
        item_count = st.number_input(
            "입력할 메뉴 개수",
            min_value=0,
            max_value=20,
            value=st.session_state.sales_item_count,
            step=1,
            key="item_count_input"
        )
        st.session_state.sales_item_count = item_count
    
    for i in range(item_count):
        col1, col2 = st.columns([3, 1])
        with col1:
            menu_name = st.selectbox(
                f"메뉴 {i+1}",
                options=["선택안함"] + menu_list,
                key=f"closing_menu_{i}"
            )
        with col2:
            quantity = st.number_input(
                "판매수량",
                min_value=0,
                value=0,
                step=1,
                key=f"closing_quantity_{i}"
            )
        
        if menu_name != "선택안함" and quantity > 0:
            sales_items.append((menu_name, quantity))
    
    return selected_date, store, card_sales, cash_sales, total_sales, visitors, sales_items


def render_report_input():
    """리포트 생성 입력 폼 렌더링"""
    st.subheader("📄 주간 리포트 생성")
    
    from datetime import datetime, timedelta
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 기본값: 최근 7일
        default_end = datetime.now().date()
        default_start = default_end - timedelta(days=6)
        start_date = st.date_input("시작일", value=default_start, key="report_start_date")
    
    with col2:
        end_date = st.date_input("종료일", value=default_end, key="report_end_date")
    
    return start_date, end_date


def render_target_input():
    """목표 매출/비용 구조 입력 폼 렌더링"""
    from datetime import datetime
    
    st.subheader("🎯 목표 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        year = st.number_input("연도", min_value=2020, max_value=2100, value=datetime.now().year, key="target_year")
        month = st.number_input("월", min_value=1, max_value=12, value=datetime.now().month, key="target_month")
        target_sales = st.number_input(
            "월 목표 매출 (원)",
            min_value=0,
            value=0,
            step=100000,
            key="target_sales"
        )
    
    with col2:
        target_cost_rate = st.number_input(
            "목표 원가율 (%)",
            min_value=0.0,
            max_value=100.0,
            value=30.0,
            step=0.5,
            format="%.1f",
            key="target_cost_rate"
        )
        target_labor_rate = st.number_input(
            "목표 인건비율 (%)",
            min_value=0.0,
            max_value=100.0,
            value=25.0,
            step=0.5,
            format="%.1f",
            key="target_labor_rate"
        )
        target_rent_rate = st.number_input(
            "목표 임대료율 (%)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=0.5,
            format="%.1f",
            key="target_rent_rate"
        )
        target_other_rate = st.number_input(
            "목표 기타비용율 (%)",
            min_value=0.0,
            max_value=100.0,
            value=5.0,
            step=0.5,
            format="%.1f",
            key="target_other_rate"
        )
        target_profit_rate = st.number_input(
            "목표 순이익률 (%)",
            min_value=0.0,
            max_value=100.0,
            value=30.0,
            step=0.5,
            format="%.1f",
            key="target_profit_rate"
        )
    
    # 비율 합계 검증
    total_rate = target_cost_rate + target_labor_rate + target_rent_rate + target_other_rate + target_profit_rate
    if abs(total_rate - 100.0) > 0.1:
        st.warning(f"⚠️ 비율 합계가 100%가 아닙니다. (현재: {total_rate:.1f}%)")
    
    return year, month, target_sales, target_cost_rate, target_labor_rate, target_rent_rate, target_other_rate, target_profit_rate


def render_target_dashboard(analysis_result):
    """목표 대비 대시보드 렌더링 (신호등 포함)"""
    if analysis_result is None:
        st.info("목표 데이터를 먼저 설정해주세요.")
        return
    
    st.subheader("📊 목표 대비 현황")
    
    # 신호등 표시
    status = analysis_result['status']
    indicator = analysis_result['indicator']
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 12px; margin: 1rem 0;">
            <h2 style="margin: 0; font-size: 3rem;">{indicator}</h2>
            <h3 style="margin: 0.5rem 0 0 0; color: #2c3e50;">{status}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # 주요 지표
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        progress = analysis_result['progress_rate']
        progress_color = "#28a745" if progress >= 100 else "#ffc107" if progress >= 80 else "#dc3545"
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">목표 진행률</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {progress_color};">{progress:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        current = analysis_result['current_sales']
        target = analysis_result['target_sales']
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">현재 누적 매출</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #1f4788;">{current:,.0f}원</div>
            <div style="font-size: 0.8rem; color: #7f8c8d; margin-top: 0.3rem;">목표: {target:,.0f}원</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        daily_target = analysis_result['daily_target']
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">하루 목표 매출</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #17a2b8;">{daily_target:,.0f}원</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        forecast = analysis_result['forecast_sales']
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">예상 월 매출</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #667eea;">{forecast:,.0f}원</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 원가율 비교
    st.markdown("---")
    st.write("**💰 원가율 비교**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        target_cost = analysis_result['target_cost_rate']
        st.metric("목표 원가율", f"{target_cost:.1f}%")
    
    with col2:
        current_cost = analysis_result['current_cost_rate']
        st.metric("현재 원가율", f"{current_cost:.1f}%")
    
    with col3:
        gap = analysis_result['cost_rate_gap']
        gap_color = "#dc3545" if gap > 5 else "#ffc107" if gap > 0 else "#28a745"
        st.markdown(f"""
        <div style="padding: 1rem; background: white; border-radius: 8px; border: 1px solid #e0e0e0;">
            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">원가율 차이</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {gap_color};">{gap:+.1f}%p</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 예상 이익
    st.markdown("---")
    forecast_profit = analysis_result['forecast_profit']
    st.metric("예상 순이익", f"{forecast_profit:,.0f}원")


def render_abc_analysis(abc_df, cost_df, a_threshold=70, b_threshold=20, c_threshold=10):
    """ABC 분석 결과 렌더링"""
    if abc_df.empty:
        st.info("ABC 분석을 수행할 데이터가 없습니다.")
        return
    
    st.subheader("📊 ABC 분석 결과")
    
    # ABC 등급별 통계
    st.write("**ABC 등급별 집계**")
    
    abc_summary = abc_df.groupby('ABC등급').agg({
        '매출': 'sum',
        '공헌이익': 'sum',
        '메뉴명': 'count'
    }).reset_index()
    abc_summary.columns = ['ABC등급', '총매출', '총공헌이익', '메뉴수']
    
    # 비중 계산
    total_sales = abc_summary['총매출'].sum()
    total_profit = abc_summary['총공헌이익'].sum()
    
    if total_sales > 0:
        abc_summary['매출비중'] = (abc_summary['총매출'] / total_sales * 100).round(1)
    else:
        abc_summary['매출비중'] = 0
    
    if total_profit > 0:
        abc_summary['이익비중'] = (abc_summary['총공헌이익'] / total_profit * 100).round(1)
    else:
        abc_summary['이익비중'] = 0
    
    # 표시용 포맷팅
    display_summary = abc_summary.copy()
    display_summary['총매출'] = display_summary['총매출'].apply(lambda x: f"{int(x):,}원")
    display_summary['총공헌이익'] = display_summary['총공헌이익'].apply(lambda x: f"{int(x):,}원")
    display_summary['매출비중'] = display_summary['매출비중'].apply(lambda x: f"{x:.1f}%")
    display_summary['이익비중'] = display_summary['이익비중'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(display_summary, use_container_width=True, hide_index=True)
    
    # 상세 메뉴별 ABC 등급
    st.markdown("---")
    st.write("**📋 메뉴별 ABC 등급**")
    
    # 표시용 DataFrame
    display_abc = abc_df.copy()
    display_abc['판매량'] = display_abc['판매량'].apply(lambda x: f"{int(x):,}")
    display_abc['매출'] = display_abc['매출'].apply(lambda x: f"{int(x):,}원")
    display_abc['공헌이익'] = display_abc['공헌이익'].apply(lambda x: f"{int(x):,}원")
    display_abc['판매량비중'] = display_abc['판매량비중'].apply(lambda x: f"{x:.1f}%")
    display_abc['매출비중'] = display_abc['매출비중'].apply(lambda x: f"{x:.1f}%")
    display_abc['공헌이익비중'] = display_abc['공헌이익비중'].apply(lambda x: f"{x:.1f}%")
    
    # ABC 등급별 색상 구분
    def highlight_abc_grade(row):
        grade = row['ABC등급']
        if grade == 'A':
            return ['background-color: #d4edda'] * len(row)
        elif grade == 'B':
            return ['background-color: #fff3cd'] * len(row)
        else:
            return ['background-color: #f8d7da'] * len(row)
    
    st.dataframe(display_abc, use_container_width=True, hide_index=True)
    
    # 경고 메시지
    st.markdown("---")
    
    # A인데 원가율 위험 메뉴
    if not cost_df.empty:
        abc_with_cost = pd.merge(
            abc_df[['메뉴명', 'ABC등급']],
            cost_df[['메뉴명', '원가율']],
            on='메뉴명',
            how='left'
        )
        
        high_cost_a = abc_with_cost[
            (abc_with_cost['ABC등급'] == 'A') & (abc_with_cost['원가율'] >= 35)
        ]
        
        if not high_cost_a.empty:
            st.warning(f"⚠️ A등급인데 원가율이 35% 이상인 메뉴: {', '.join(high_cost_a['메뉴명'].tolist())}")
        
        # C인데 작업복잡도 높은 메뉴 (수동 체크용 안내)
        st.info("💡 C등급 메뉴 중 작업복잡도가 높은 메뉴는 수동으로 검토해주세요.")
