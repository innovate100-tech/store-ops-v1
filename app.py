"""
매장 운영 시스템 v1 - 메인 앱 (Supabase 기반)
"""
import streamlit as st
from datetime import datetime
import pandas as pd

# 페이지 설정은 최상단에 위치 (다른 st.* 호출 전에)
st.set_page_config(
    page_title="매장 운영 시스템 v1",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"  # 사이드바 항상 열림
)

# 로그인 체크
from src.auth import check_login, show_login_page, get_current_store_name, logout

# 로그인이 안 되어 있으면 로그인 화면 표시
if not check_login():
    show_login_page()
    st.stop()

# Supabase 기반 storage 사용
from src.storage_supabase import (
    load_csv,
    save_sales,
    save_visitor,
    save_menu,
    update_menu,
    delete_menu,
    save_ingredient,
    update_ingredient,
    delete_ingredient,
    save_recipe,
    delete_recipe,
    save_daily_sales_item,
    save_inventory,
    save_targets,
    save_abc_history,
    delete_sales,
    delete_visitor,
    create_backup,
    save_daily_close
)
from src.analytics import (
    calculate_correlation,
    merge_sales_visitors,
    calculate_menu_cost,
    calculate_ingredient_usage,
    calculate_order_recommendation,
    abc_analysis,
    target_gap_analysis
)
from src.ui import (
    render_sales_input,
    render_sales_batch_input,
    render_visitor_input,
    render_visitor_batch_input,
    render_menu_input,
    render_menu_batch_input,
    render_sales_chart,
    render_correlation_info,
    render_ingredient_input,
    render_recipe_input,
    render_cost_analysis,
    render_daily_sales_input,
    render_inventory_input,
    render_report_input,
    render_target_input,
    render_target_dashboard,
    render_abc_analysis,
    render_manager_closing_input
)
from src.reporting import generate_weekly_report
from src.ui_helpers import render_page_header, render_section_header, render_section_divider

# 커스텀 CSS 적용
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Noto Sans KR', sans-serif !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white !important;
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .info-box {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-left: 4px solid #667eea;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: 1px solid #e0e0e0;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 2rem 0;
        border: none;
    }
    
    /* 입력 폼 컨테이너 */
    .form-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
    }
    
    /* 데이터프레임 스타일 개선 */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* 버튼 그룹 스타일 */
    .button-group {
        display: flex;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    /* 카드 스타일 섹션 */
    .card-section {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    /* 사이드바 카테고리별 메뉴 구분 스타일 */
    [data-testid="stSidebar"] .stRadio {
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* 라디오 버튼 항목 그룹핑을 위한 스타일 */
    [data-testid="stSidebar"] .stRadio > label {
        position: relative;
    }
    
    /* 카테고리 구분선 효과 */
    .category-separator {
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀 (개선된 디자인)
st.markdown("""
<div class="main-header">
    <h1>🏪 매장 운영 시스템 v1</h1>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">효율적인 매장 운영을 위한 통합 관리 시스템</p>
</div>
""", unsafe_allow_html=True)

# 사이드바 상단: 매장명 및 로그아웃
with st.sidebar:
    store_name = get_current_store_name()
    
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <div style="font-size: 0.9rem; color: rgba(255,255,255,0.7); margin-bottom: 0.3rem;">🏪 현재 매장</div>
        <div style="font-size: 1.1rem; font-weight: 600; color: white;">{store_name}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 로그아웃", use_container_width=True, type="secondary"):
        logout()
        st.rerun()
    
    st.markdown("---")
    
    # 백업 기능
    if st.button("💾 데이터 백업 생성", use_container_width=True):
        try:
            success, message = create_backup()
            if success:
                st.success(f"백업이 생성되었습니다!\n{message}")
            else:
                st.error(f"백업 생성 실패: {message}")
        except Exception as e:
            st.error(f"백업 중 오류: {e}")

# 사이드바 네비게이션 - 카테고리별로 구분
# 메뉴 항목들을 카테고리별로 정의
menu_categories = {
    "매출": [
        ("점장 마감", "📋"),
        ("매출 관리", "📊"),
        ("판매 관리", "📦"),
        ("발주 관리", "🛒"),
    ],
    "비용": [
        ("메뉴 관리", "🍽️"),
        ("재료 관리", "🥬"),
        ("레시피 관리", "📝"),
        ("원가 분석", "💰"),
    ],
    "기타": [
        ("주간 리포트", "📄"),
        ("통합 대시보드", "📊"),
        ("사장 설계", "👔")
    ]
}

# 선택된 페이지 확인
if 'current_page' not in st.session_state:
    st.session_state.current_page = "점장 마감"

# 모든 메뉴 항목 추출 (순서 유지)
all_menu_items = []
all_menu_options = []

for category_name, items in menu_categories.items():
    for menu_name, icon in items:
        all_menu_items.append((menu_name, icon))
        all_menu_options.append(f"{icon} {menu_name}")

# 카테고리별로 헤더와 메뉴를 함께 표시
# 각 카테고리의 메뉴를 버튼으로 표시하여 카테고리별 구분이 명확하게 보이도록 함
selected_menu_text = st.session_state.current_page

for category_name, items in menu_categories.items():
    # 카테고리 헤더
    st.sidebar.markdown(f"""
    <div style="margin-top: 1.5rem; margin-bottom: 0.5rem;">
        <div style="font-size: 0.85rem; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 1px; font-weight: 600; padding-left: 0.5rem;">
            {category_name}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 카테고리 내 각 메뉴를 버튼으로 표시
    for menu_name, icon in items:
        # 현재 선택된 메뉴인지 확인
        is_selected = (selected_menu_text == menu_name)
        button_type = "primary" if is_selected else "secondary"
        
        if st.sidebar.button(
            f"{icon} {menu_name}",
            key=f"menu_btn_{menu_name}",
            use_container_width=True,
            type=button_type
        ):
            st.session_state.current_page = menu_name
            st.rerun()

page = st.session_state.current_page

# 점장 마감 페이지
if page == "점장 마감":
    render_page_header("점장 마감", "📋")
    
    st.markdown("""
    <div class="info-box">
        <strong>⏱️ 목표:</strong> 하루 1번, 1분 안에 입력하고 끝내는 간단한 마감 입력 화면입니다.
    </div>
    """, unsafe_allow_html=True)
    
    # 전체 메뉴 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    # 점장 마감 입력 폼
    date, store, card_sales, cash_sales, total_sales, visitors, sales_items, issues, memo = render_manager_closing_input(menu_list)
    
    st.markdown("---")
    
    # 마감 완료 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ 마감 완료", type="primary", use_container_width=True, key="manager_close_btn"):
            errors = []
            
            if not store or store.strip() == "":
                errors.append("매장명을 입력해주세요.")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    # daily_close에 저장
                    result = save_daily_close(
                        date, store, card_sales, cash_sales, total_sales,
                        visitors, sales_items, issues, memo
                    )
                    
                    # 저장 결과에 따라 메시지 표시
                    if result:
                        st.success("✅ 마감이 완료되었습니다! 데이터가 저장되었습니다.")
                    else:
                        # DEV MODE 등에서 저장되지 않은 경우
                        st.warning("⚠️ DEV MODE: 마감 정보는 표시되지만 실제 데이터는 저장되지 않았습니다.")
                        st.info("💡 실제 저장을 원하시면 Supabase를 설정하고 DEV MODE를 비활성화하세요.")
                    
                    # 저장 성공 여부와 관계없이 풍선 애니메이션 및 마감 완료 메시지 표시
                    st.balloons()  # 항상 풍선 애니메이션 표시
                    st.info("💡 **마감 수정 방법**: 같은 날짜로 다시 마감을 입력하시면 기존 데이터가 자동으로 업데이트됩니다.")
                    
                    # 오늘 요약 카드 표시
                    st.markdown("---")
                    st.markdown("### 📊 오늘 요약")
                    
                    # 객단가 계산
                    avg_price = (total_sales / visitors) if visitors > 0 else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">총매출</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #28a745;">{total_sales:,}원</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">방문자수</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #17a2b8;">{visitors}명</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">객단가</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #ffc107;">{avg_price:,.0f}원</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        menu_count = len([q for _, q in sales_items if q > 0])
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">판매 메뉴 수</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #667eea;">{menu_count}개</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 판매량 TOP 3
                    if sales_items:
                        st.markdown("---")
                        st.markdown("### 🔝 판매량 TOP 3")
                        
                        sorted_items = sorted([(m, q) for m, q in sales_items if q > 0], key=lambda x: x[1], reverse=True)
                        top3_items = sorted_items[:3]
                        
                        if top3_items:
                            top3_cols = st.columns(len(top3_items))
                            for idx, (menu_name, quantity) in enumerate(top3_items):
                                with top3_cols[idx]:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">{menu_name}</div>
                                        <div style="font-size: 1.5rem; font-weight: 700; color: #667eea;">{quantity}개</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")

# 매출 관리 페이지 (매출 + 방문자 통합)
elif page == "매출 관리":
    render_page_header("매출 관리", "📊")
    
    # 카테고리 선택 (매출 / 방문자)
    category = st.radio(
        "카테고리",
        ["💰 매출", "👥 방문자"],
        horizontal=True,
        key="sales_category"
    )
    
    render_section_divider()
    
    # ========== 매출 입력 섹션 ==========
    if category == "💰 매출":
        # 입력 모드 선택 (단일 / 일괄)
        input_mode = st.radio(
            "입력 모드",
            ["단일 입력", "일괄 입력 (여러 날짜)"],
            horizontal=True,
            key="sales_input_mode"
        )
        
        render_section_divider()
        
        if input_mode == "단일 입력":
            # 단일 입력 폼
            date, store, card_sales, cash_sales, total_sales = render_sales_input()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 저장", type="primary", use_container_width=True):
                    if not store or store.strip() == "":
                        st.error("매장명을 입력해주세요.")
                    elif total_sales <= 0:
                        st.error("매출은 0보다 큰 값이어야 합니다.")
                    else:
                        try:
                            save_sales(date, store, card_sales, cash_sales, total_sales)
                            st.success(f"매출이 저장되었습니다! ({date}, {store}, 총매출: {total_sales:,}원)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"저장 중 오류가 발생했습니다: {e}")
        
        else:
            # 일괄 입력 폼
            sales_data = render_sales_batch_input()
            
            if sales_data:
                render_section_divider()
                
                # 입력 요약 표시
                st.write("**📊 입력 요약**")
                summary_df = pd.DataFrame(
                    [(d.strftime('%Y-%m-%d'), s, f"{card:,}원", f"{cash:,}원", f"{total:,}원") 
                     for d, s, card, cash, total in sales_data],
                    columns=['날짜', '매장', '카드매출', '현금매출', '총매출']
                )
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                total_card = sum(card for _, _, card, _, _ in sales_data)
                total_cash = sum(cash for _, _, _, cash, _ in sales_data)
                total_all = sum(total for _, _, _, _, total in sales_data)
                
                st.markdown(f"**총 {len(sales_data)}일, 카드매출: {total_card:,}원, 현금매출: {total_cash:,}원, 총 매출: {total_all:,}원**")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 일괄 저장", type="primary", use_container_width=True):
                        errors = []
                        success_count = 0
                        
                        for date, store, card_sales, cash_sales, total_sales in sales_data:
                            if not store or store.strip() == "":
                                errors.append(f"{date}: 매장명이 없습니다.")
                            else:
                                try:
                                    save_sales(date, store, card_sales, cash_sales, total_sales)
                                    success_count += 1
                                except Exception as e:
                                    errors.append(f"{date}: {e}")
                        
                        if errors:
                            for error in errors:
                                st.error(error)
                        
                        if success_count > 0:
                            st.success(f"✅ {success_count}일의 매출이 저장되었습니다!")
                            st.balloons()
                            st.rerun()
    
    # ========== 방문자 입력 섹션 ==========
    else:
        # 입력 모드 선택 (단일 / 일괄)
        input_mode = st.radio(
            "입력 모드",
            ["단일 입력", "일괄 입력 (여러 날짜)"],
            horizontal=True,
            key="visitor_input_mode"
        )
        
        render_section_divider()
        
        if input_mode == "단일 입력":
            # 단일 입력 폼
            date, visitors = render_visitor_input()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 저장", type="primary", use_container_width=True):
                    if visitors <= 0:
                        st.error("방문자수는 0보다 큰 값이어야 합니다.")
                    else:
                        try:
                            save_visitor(date, visitors)
                            st.success(f"방문자수가 저장되었습니다! ({date}, {visitors}명)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"저장 중 오류가 발생했습니다: {e}")
        
        else:
            # 일괄 입력 폼
            visitor_data = render_visitor_batch_input()
            
            if visitor_data:
                render_section_divider()
                
                # 입력 요약 표시
                st.write("**📊 입력 요약**")
                summary_df = pd.DataFrame(
                    [(d.strftime('%Y-%m-%d'), f"{v}명") for d, v in visitor_data],
                    columns=['날짜', '방문자수']
                )
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                st.markdown(f"**총 {len(visitor_data)}일, 총 방문자수: {sum(v for _, v in visitor_data):,}명**")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 일괄 저장", type="primary", use_container_width=True):
                        errors = []
                        success_count = 0
                        
                        for date, visitors in visitor_data:
                            try:
                                save_visitor(date, visitors)
                                success_count += 1
                            except Exception as e:
                                errors.append(f"{date}: {e}")
                        
                        if errors:
                            for error in errors:
                                st.error(error)
                        
                        if success_count > 0:
                            st.success(f"✅ {success_count}일의 방문자수가 저장되었습니다!")
                            st.balloons()
                            st.rerun()
    
    render_section_divider()
    
    # ========== 저장된 데이터 표시 ==========
    if category == "💰 매출":
        # 저장된 매출 표시 및 삭제
        render_section_header("저장된 매출 내역", "📋")
        sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
        
        if not sales_df.empty:
            # 삭제 기능
            st.write("**🗑️ 매출 데이터 삭제**")
            col1, col2, col3 = st.columns(3)
            with col1:
                delete_date = st.date_input("삭제할 날짜", key="sales_delete_date")
            with col2:
                delete_store_list = sales_df['매장'].unique().tolist()
                delete_store = st.selectbox(
                    "매장 선택 (전체 삭제 시 '전체' 선택)",
                    ["전체"] + delete_store_list,
                    key="sales_delete_store"
                )
            with col3:
                st.write("")
                st.write("")
                if st.button("🗑️ 삭제", key="sales_delete_btn", type="primary"):
                    try:
                        if delete_store == "전체":
                            success, message = delete_sales(delete_date, None)
                        else:
                            success, message = delete_sales(delete_date, delete_store)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"삭제 중 오류: {e}")
            
            render_section_divider()
            
            # 실제 입력값만 표시 (기술적 컬럼 제거)
            display_df = sales_df.copy()
            
            # 표시할 컬럼만 선택
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
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # 차트 표시
            render_section_header("날짜별 매출 추이", "📈")
            render_sales_chart(sales_df)
        else:
            st.info("저장된 매출 데이터가 없습니다.")
    
    else:
        # 저장된 방문자 표시 및 삭제
        render_section_header("저장된 방문자 내역", "📋")
        visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
        
        if not visitors_df.empty:
            # 삭제 기능
            st.write("**🗑️ 방문자 데이터 삭제**")
            col1, col2 = st.columns([2, 1])
            with col1:
                delete_date = st.date_input("삭제할 날짜", key="visitor_delete_date")
            with col2:
                st.write("")
                st.write("")
                if st.button("🗑️ 삭제", key="visitor_delete_btn", type="primary"):
                    try:
                        success, message = delete_visitor(delete_date)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"삭제 중 오류: {e}")
            
            render_section_divider()
            
            # 실제 입력값만 표시 (기술적 컬럼 제거)
            display_df = visitors_df.copy()
            
            # 표시할 컬럼만 선택
            display_columns = []
            if '날짜' in display_df.columns:
                display_columns.append('날짜')
            if '방문자수' in display_df.columns:
                display_columns.append('방문자수')
            
            # 필요한 컬럼만 선택
            if display_columns:
                display_df = display_df[display_columns]
                
                # 날짜를 문자열로 변환
                if '날짜' in display_df.columns:
                    display_df['날짜'] = pd.to_datetime(display_df['날짜']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("저장된 방문자 데이터가 없습니다.")

# 메뉴 관리 페이지
elif page == "메뉴 관리":
    render_page_header("메뉴 관리", "🍽️")
    
    # 입력 모드 선택 (단일 / 일괄)
    input_mode = st.radio(
        "입력 모드",
        ["단일 입력", "일괄 입력 (여러 메뉴)"],
        horizontal=True,
        key="menu_input_mode"
    )
    
    render_section_divider()
    
    if input_mode == "단일 입력":
        # 단일 입력 폼
        menu_name, price = render_menu_input()
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 저장", type="primary", use_container_width=True):
                if not menu_name or menu_name.strip() == "":
                    st.error("메뉴명을 입력해주세요.")
                elif price <= 0:
                    st.error("판매가는 0보다 큰 값이어야 합니다.")
                else:
                    try:
                        success, message = save_menu(menu_name, price)
                        if success:
                            st.success(f"메뉴가 저장되었습니다! ({menu_name}, {price:,}원)")
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    else:
        # 일괄 입력 폼
        menu_data = render_menu_batch_input()
        
        if menu_data:
            render_section_divider()
            
            # 입력 요약 표시
            st.write("**📊 입력 요약**")
            summary_df = pd.DataFrame(
                [(name, f"{price:,}원") for name, price in menu_data],
                columns=['메뉴명', '판매가']
            )
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            st.markdown(f"**총 {len(menu_data)}개 메뉴**")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 일괄 저장", type="primary", use_container_width=True):
                    errors = []
                    success_count = 0
                    
                    for menu_name, price in menu_data:
                        try:
                            success, message = save_menu(menu_name, price)
                            if success:
                                success_count += 1
                            else:
                                errors.append(f"{menu_name}: {message}")
                        except Exception as e:
                            errors.append(f"{menu_name}: {e}")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    
                    if success_count > 0:
                        st.success(f"✅ {success_count}개 메뉴가 저장되었습니다!")
                        st.balloons()
                        st.rerun()
    
    render_section_divider()
    
    # 저장된 메뉴 표시 및 수정/삭제
    render_section_header("등록된 메뉴 리스트", "📋")
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    
    if not menu_df.empty:
        display_df = menu_df.copy()
        if '판매가' in display_df.columns:
            display_df['판매가'] = display_df['판매가'].apply(lambda x: f"{int(x):,}원")
        
        # 수정/삭제 기능
        st.write("**📝 메뉴 수정/삭제**")
        menu_list = menu_df['메뉴명'].tolist()
        selected_menu = st.selectbox(
            "수정/삭제할 메뉴 선택",
            ["선택하세요"] + menu_list,
            key="menu_edit_select"
        )
        
        if selected_menu != "선택하세요":
            menu_info = menu_df[menu_df['메뉴명'] == selected_menu].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**수정**")
                new_menu_name = st.text_input("메뉴명", value=menu_info['메뉴명'], key="menu_edit_name")
                new_price = st.number_input("판매가 (원)", min_value=0, value=int(menu_info['판매가']), step=1000, key="menu_edit_price")
                if st.button("✅ 수정", key="menu_edit_btn"):
                    try:
                        success, message = update_menu(menu_info['메뉴명'], new_menu_name, new_price)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"수정 중 오류: {e}")
            
            with col2:
                st.write("**삭제**")
                st.warning(f"⚠️ '{selected_menu}' 메뉴를 삭제하시겠습니까?")
                if st.button("🗑️ 삭제", key="menu_delete_btn", type="primary"):
                    try:
                        success, message, refs = delete_menu(selected_menu)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                            if refs:
                                st.info(f"**참조 정보:** {', '.join([f'{k}: {v}개' for k, v in refs.items()])}")
                    except Exception as e:
                        st.error(f"삭제 중 오류: {e}")
        
        render_section_divider()
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("등록된 메뉴가 없습니다.")

# 재료 관리 페이지
elif page == "재료 관리":
    render_page_header("재료 관리", "🥬")
    
    # 재료 입력 폼
    ingredient_name, unit, unit_price = render_ingredient_input()
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 저장", type="primary", use_container_width=True):
            if not ingredient_name or ingredient_name.strip() == "":
                st.error("재료명을 입력해주세요.")
            elif unit_price <= 0:
                st.error("단가는 0보다 큰 값이어야 합니다.")
            else:
                try:
                    success, message = save_ingredient(ingredient_name, unit, unit_price)
                    if success:
                        st.success(f"재료가 저장되었습니다! ({ingredient_name}, {unit_price:,.2f}원/{unit})")
                        st.rerun()
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    render_section_divider()
    
    # 저장된 재료 표시 및 수정/삭제
    render_section_header("등록된 재료 리스트", "📋")
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    if not ingredient_df.empty:
        display_df = ingredient_df.copy()
        # 단가 표시 포맷팅
        display_df['단가'] = display_df.apply(
            lambda x: f"{x['단가']:,.2f}원/{x['단위']}",
            axis=1
        )
        
        # 수정/삭제 기능
        st.write("**📝 재료 수정/삭제**")
        ingredient_list = ingredient_df['재료명'].tolist()
        selected_ingredient = st.selectbox(
            "수정/삭제할 재료 선택",
            ["선택하세요"] + ingredient_list,
            key="ingredient_edit_select"
        )
        
        if selected_ingredient != "선택하세요":
            ingredient_info = ingredient_df[ingredient_df['재료명'] == selected_ingredient].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**수정**")
                new_ingredient_name = st.text_input("재료명", value=ingredient_info['재료명'], key="ingredient_edit_name")
                new_unit = st.text_input("단위", value=ingredient_info['단위'], key="ingredient_edit_unit")
                new_unit_price = st.number_input("단가 (원)", min_value=0.0, value=float(ingredient_info['단가']), step=100.0, key="ingredient_edit_price")
                if st.button("✅ 수정", key="ingredient_edit_btn"):
                    try:
                        success, message = update_ingredient(ingredient_info['재료명'], new_ingredient_name, new_unit, new_unit_price)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"수정 중 오류: {e}")
            
            with col2:
                st.write("**삭제**")
                st.warning(f"⚠️ '{selected_ingredient}' 재료를 삭제하시겠습니까?")
                if st.button("🗑️ 삭제", key="ingredient_delete_btn", type="primary"):
                    try:
                        success, message, refs = delete_ingredient(selected_ingredient)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                            if refs:
                                st.info(f"**참조 정보:** {', '.join([f'{k}: {v}개' for k, v in refs.items()])}")
                    except Exception as e:
                        st.error(f"삭제 중 오류: {e}")
        
        render_section_divider()
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("등록된 재료가 없습니다.")

# 레시피 관리 페이지
elif page == "레시피 관리":
    render_page_header("레시피 관리", "📝")
    
    # 메뉴 및 재료 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    ingredient_list = ingredient_df['재료명'].tolist() if not ingredient_df.empty else []
    
    # 레시피 입력 폼
    recipe_result = render_recipe_input(menu_list, ingredient_list)
    
    if recipe_result[0] is not None:
        menu_name, ingredient_name, quantity = recipe_result
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 저장", type="primary", use_container_width=True):
                if quantity <= 0:
                    st.error("사용량은 0보다 큰 값이어야 합니다.")
                else:
                    try:
                        save_recipe(menu_name, ingredient_name, quantity)
                        st.success(f"레시피가 저장되었습니다! ({menu_name} - {ingredient_name}: {quantity})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    render_section_divider()
    
    # 저장된 레시피 표시
    render_section_header("등록된 레시피", "📋")
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    
    if not recipe_df.empty:
        # 메뉴 필터
        render_section_header("레시피 검색", "🔍")
        filter_menu = st.selectbox(
            "메뉴 필터",
            options=["전체"] + menu_list,
            key="recipe_filter_menu"
        )
        
        display_recipe_df = recipe_df.copy()
        if filter_menu != "전체":
            display_recipe_df = display_recipe_df[display_recipe_df['메뉴명'] == filter_menu]
        
        if not display_recipe_df.empty:
            # 재료 정보와 조인하여 단위 표시
            display_recipe_df = pd.merge(
                display_recipe_df,
                ingredient_df[['재료명', '단위']],
                on='재료명',
                how='left'
            )
            display_recipe_df['사용량'] = display_recipe_df.apply(
                lambda x: f"{x['사용량']:.2f}{x['단위']}" if pd.notna(x['단위']) else f"{x['사용량']:.2f}",
                axis=1
            )
            display_recipe_df = display_recipe_df[['메뉴명', '재료명', '사용량']]
            
            st.dataframe(display_recipe_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"'{filter_menu}' 메뉴에 대한 레시피가 없습니다.")
    else:
        st.info("등록된 레시피가 없습니다.")

# 원가 분석 페이지
elif page == "원가 분석":
    render_page_header("원가 분석", "💰")
    
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

# 판매 관리 페이지
elif page == "판매 관리":
    render_page_header("판매 관리", "📦")
    
    # 메뉴 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    # 일일 판매 입력 폼
    sales_result = render_daily_sales_input(menu_list)
    
    if sales_result[0] is not None:
        date, menu_name, quantity = sales_result
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 저장", type="primary", use_container_width=True):
                if quantity <= 0:
                    st.error("판매수량은 0보다 큰 값이어야 합니다.")
                else:
                    try:
                        save_daily_sales_item(date, menu_name, quantity)
                        st.success(f"판매 내역이 저장되었습니다! ({date}, {menu_name}: {quantity}개)")
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    render_section_divider()
    
    # 저장된 판매 내역 표시
    render_section_header("일일 판매 내역", "📋")
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    
    if not daily_sales_df.empty:
        # 날짜 필터
        date_list = sorted(daily_sales_df['날짜'].unique(), reverse=True)
        selected_date = st.selectbox("날짜 필터", options=["전체"] + [str(d.date()) if hasattr(d, 'date') else str(d) for d in date_list], key="sales_date_filter")
        
        display_df = daily_sales_df.copy()
        if selected_date != "전체":
            display_df = display_df[display_df['날짜'].astype(str).str.startswith(selected_date)]
        
        if not display_df.empty:
            # 날짜를 문자열로 변환
            display_df['날짜'] = pd.to_datetime(display_df['날짜']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # 집계 정보
            render_section_divider()
            render_section_header("판매 집계", "📊")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**날짜별 판매량**")
                date_summary = display_df.groupby('날짜')['판매수량'].sum().reset_index()
                date_summary.columns = ['날짜', '총 판매수량']
                st.dataframe(date_summary, use_container_width=True, hide_index=True)
            
            with col2:
                st.write("**메뉴별 판매량**")
                menu_summary = display_df.groupby('메뉴명')['판매수량'].sum().reset_index()
                menu_summary.columns = ['메뉴명', '총 판매수량']
                menu_summary = menu_summary.sort_values('총 판매수량', ascending=False)
                st.dataframe(menu_summary, use_container_width=True, hide_index=True)
        else:
            st.info(f"'{selected_date}' 날짜의 판매 내역이 없습니다.")
    else:
        st.info("저장된 판매 내역이 없습니다.")
    
    # 재료 사용량 집계
    render_section_divider()
    render_section_header("재료 사용량 집계", "🥬")
    
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    
    if not daily_sales_df.empty and not recipe_df.empty:
        usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
        
        if not usage_df.empty:
            # 날짜 필터
            usage_date_list = sorted(usage_df['날짜'].unique(), reverse=True)
            selected_usage_date = st.selectbox(
                "날짜 필터 (재료 사용량)",
                options=["전체"] + [str(d.date()) if hasattr(d, 'date') else str(d) for d in usage_date_list],
                key="usage_date_filter"
            )
            
            display_usage_df = usage_df.copy()
            if selected_usage_date != "전체":
                display_usage_df = display_usage_df[display_usage_df['날짜'].astype(str).str.startswith(selected_usage_date)]
            
            if not display_usage_df.empty:
                display_usage_df['날짜'] = pd.to_datetime(display_usage_df['날짜']).dt.strftime('%Y-%m-%d')
                
                # 재료별 총 사용량 표시
                st.write("**재료별 사용량**")
                st.dataframe(display_usage_df, use_container_width=True, hide_index=True)
                
                # 오늘 사용한 재료 TOP (선택된 날짜가 오늘이거나 전체일 때)
                if selected_usage_date == "전체" or selected_usage_date == str(pd.Timestamp.now().date()):
                    ingredient_summary = display_usage_df.groupby('재료명')['총사용량'].sum().reset_index()
                    ingredient_summary = ingredient_summary.sort_values('총사용량', ascending=False).head(10)
                    ingredient_summary.columns = ['재료명', '총 사용량']
                    
                    st.write("**🔝 사용량 TOP 10 재료**")
                    st.dataframe(ingredient_summary, use_container_width=True, hide_index=True)
        else:
            st.info("재료 사용량을 계산할 데이터가 없습니다.")
    else:
        st.info("판매 내역과 레시피 데이터가 필요합니다.")

# 발주 관리 페이지
elif page == "발주 관리":
    render_page_header("발주 관리", "🛒")
    
    # 재료 목록 로드
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    ingredient_list = ingredient_df['재료명'].tolist() if not ingredient_df.empty else []
    
    # 재고 입력 폼
    inventory_result = render_inventory_input(ingredient_list)
    
    if inventory_result[0] is not None:
        ingredient_name, current_stock, safety_stock = inventory_result
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 저장", type="primary", use_container_width=True):
                try:
                    save_inventory(ingredient_name, current_stock, safety_stock)
                    st.success(f"재고 정보가 저장되었습니다! ({ingredient_name}: 현재고 {current_stock}, 안전재고 {safety_stock})")
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    render_section_divider()
    
    # 저장된 재고 정보 표시
    render_section_header("재고 현황", "📦")
    inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
    
    if not inventory_df.empty:
        # 재료 정보와 조인하여 단위 표시
        display_inventory_df = pd.merge(
            inventory_df,
            ingredient_df[['재료명', '단위']],
            on='재료명',
            how='left'
        )
        
        st.dataframe(display_inventory_df, use_container_width=True, hide_index=True)
    else:
        st.info("등록된 재고 정보가 없습니다.")
    
    # 발주 추천
    render_section_divider()
    render_section_header("발주 추천", "🛒")
    
    if not inventory_df.empty:
        # 재료 사용량 계산을 위한 데이터 로드
        daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        
        # 발주 추천 파라미터 설정
        col1, col2 = st.columns(2)
        with col1:
            days_for_avg = st.number_input("평균 사용량 계산 기간 (일)", min_value=1, value=7, step=1, key="days_for_avg")
        with col2:
            forecast_days = st.number_input("예측일수", min_value=1, value=3, step=1, key="forecast_days")
        
        if not daily_sales_df.empty and not recipe_df.empty:
            # 재료 사용량 계산
            usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
            
            if not usage_df.empty:
                # 발주 추천 계산
                order_df = calculate_order_recommendation(
                    ingredient_df,
                    inventory_df,
                    usage_df,
                    days_for_avg=int(days_for_avg),
                    forecast_days=int(forecast_days)
                )
                
                if not order_df.empty:
                    st.write("**📋 발주 추천 리스트**")
                    
                    # 표시용 DataFrame 생성
                    display_order_df = order_df.copy()
                    display_order_df['현재고'] = display_order_df['현재고'].apply(lambda x: f"{x:,.2f}")
                    display_order_df['안전재고'] = display_order_df['안전재고'].apply(lambda x: f"{x:,.2f}")
                    display_order_df['최근평균사용량'] = display_order_df['최근평균사용량'].apply(lambda x: f"{x:,.2f}")
                    display_order_df['예상소요량'] = display_order_df['예상소요량'].apply(lambda x: f"{x:,.2f}")
                    display_order_df['발주필요량'] = display_order_df['발주필요량'].apply(lambda x: f"{x:,.2f}")
                    display_order_df['예상금액'] = display_order_df['예상금액'].apply(lambda x: f"{int(x):,}원")
                    
                    st.dataframe(display_order_df, use_container_width=True, hide_index=True)
                    
                    # 총 예상 금액
                    total_amount = order_df['예상금액'].sum()
                    st.metric("총 예상 발주 금액", f"{int(total_amount):,}원")
                    
                    # 엑셀 다운로드
                    render_section_divider()
                    render_section_header("발주 리스트 다운로드", "📥")
                    
                    # CSV 형식으로 변환
                    csv_data = order_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 발주 리스트 다운로드 (CSV)",
                        data=csv_data,
                        file_name=f"발주리스트_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.success("✅ 현재 발주가 필요한 재료가 없습니다.")
            else:
                st.info("재료 사용량 데이터가 없습니다. 판매 내역을 입력해주세요.")
        else:
            st.info("발주 추천을 계산하려면 판매 내역과 레시피 데이터가 필요합니다.")
    else:
        st.info("발주 추천을 계산하려면 재고 정보를 먼저 등록해주세요.")

# 주간 리포트 페이지
elif page == "주간 리포트":
    render_page_header("주간 리포트 생성", "📄")
    
    # 리포트 입력 폼
    start_date, end_date = render_report_input()
    
    # 날짜 유효성 검사
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦을 수 없습니다.")
    else:
        st.markdown("---")
        
        # 리포트 생성 버튼
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("📄 리포트 생성", type="primary", use_container_width=True):
                try:
                    # 필요한 데이터 로드
                    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
                    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
                    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
                    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
                    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
                    inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
                    
                    # 재료 사용량 계산
                    from src.analytics import calculate_ingredient_usage
                    usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
                    
                    # 리포트 생성
                    with st.spinner("리포트 생성 중..."):
                        pdf_path = generate_weekly_report(
                            sales_df,
                            visitors_df,
                            daily_sales_df,
                            recipe_df,
                            ingredient_df,
                            inventory_df,
                            usage_df,
                            start_date,
                            end_date
                        )
                    
                    st.success(f"리포트가 생성되었습니다! 📄")
                    
                    # PDF 다운로드 버튼
                    with open(pdf_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    st.download_button(
                        label="📥 PDF 다운로드",
                        data=pdf_data,
                        file_name=f"주간리포트_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                    
                    # 리포트 미리보기 정보
                    render_section_divider()
                    render_section_header("리포트 포함 내용", "📋")
                    st.info("""
                    - 총매출 및 일평균 매출
                    - 방문자수 총합 및 일평균
                    - 매출 vs 방문자 추세 차트
                    - 메뉴별 판매 TOP 10
                    - 재료 사용량 TOP 10
                    - 발주 추천 TOP 10
                    """)
                    
                except Exception as e:
                    st.error(f"리포트 생성 중 오류가 발생했습니다: {e}")
                    st.exception(e)
        
        # 기존 리포트 목록 표시
        render_section_divider()
        render_section_header("생성된 리포트 목록", "📁")
        
        from pathlib import Path
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        pdf_files = list(reports_dir.glob("*.pdf"))
        if pdf_files:
            pdf_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for pdf_file in pdf_files[:10]:  # 최근 10개만 표시
                with open(pdf_file, 'rb') as f:
                    pdf_data = f.read()
                
                file_size = len(pdf_data) / 1024  # KB
                file_date = datetime.fromtimestamp(pdf_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"📄 {pdf_file.name}")
                with col2:
                    st.write(f"{file_size:.1f} KB ({file_date})")
                with col3:
                    st.download_button(
                        label="다운로드",
                        data=pdf_data,
                        file_name=pdf_file.name,
                        mime="application/pdf",
                        key=f"download_{pdf_file.name}"
                    )
        else:
            st.info("생성된 리포트가 없습니다.")

# 통합 대시보드 페이지
elif page == "통합 대시보드":
    st.header("📊 통합 대시보드")
    
    # 데이터 로드
    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
    
    # 조인된 데이터 표시
    render_section_header("매출 & 방문자 통합 데이터", "📋")
    merged_df = merge_sales_visitors(sales_df, visitors_df)
    
    if not merged_df.empty:
        display_df = merged_df.copy()
        if '날짜' in display_df.columns:
            display_df['날짜'] = pd.to_datetime(display_df['날짜']).dt.strftime('%Y-%m-%d')
        if '총매출' in display_df.columns:
            display_df['총매출'] = display_df['총매출'].apply(
                lambda x: f"{int(x):,}원" if pd.notna(x) else "-"
            )
        if '방문자수' in display_df.columns:
            display_df['방문자수'] = display_df['방문자수'].apply(
                lambda x: f"{int(x):,}명" if pd.notna(x) else "-"
            )
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # 상관계수 계산 및 표시
        render_section_divider()
        render_section_header("매출-방문자 상관관계 분석", "📈")
        correlation = calculate_correlation(sales_df, visitors_df)
        render_correlation_info(correlation)
    else:
        st.info("통합할 데이터가 없습니다. 매출과 방문자 데이터를 먼저 입력해주세요.")

# 사장 설계 페이지
elif page == "사장 설계":
    render_page_header("사장 설계 영역", "👔")
    
    st.markdown("""
    <div class="info-box">
        <strong>💼 사장님 전용:</strong> 목표 설정 및 메뉴 ABC 분석을 통해 전략적 의사결정을 지원합니다.
    </div>
    """, unsafe_allow_html=True)
    
    # 하위 메뉴 선택
    submenu = st.radio(
        "기능 선택",
        ["목표 매출/비용 구조", "메뉴 ABC 분석"],
        horizontal=True,
        key="owner_submenu"
    )
    
    render_section_divider()
    
    # 목표 매출/비용 구조
    if submenu == "목표 매출/비용 구조":
        render_section_header("목표 매출/비용 구조 설정", "🎯")
        
        # 목표 입력
        year, month, target_sales, target_cost_rate, target_labor_rate, \
        target_rent_rate, target_other_rate, target_profit_rate = render_target_input()
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 목표 저장", type="primary", use_container_width=True):
                try:
                    save_targets(
                        year, month, target_sales, target_cost_rate,
                        target_labor_rate, target_rent_rate,
                        target_other_rate, target_profit_rate
                    )
                    st.success(f"{year}년 {month}월 목표가 저장되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")
        
        render_section_divider()
        
        # 목표 대비 분석 대시보드
        targets_df = load_csv('targets.csv', default_columns=[
            '연도', '월', '목표매출', '목표원가율', '목표인건비율',
            '목표임대료율', '목표기타비용율', '목표순이익률'
        ])
        
        if not targets_df.empty:
            # 현재 월 목표 데이터 확인
            from datetime import datetime
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            # 분석할 연도/월 선택
            col1, col2 = st.columns(2)
            with col1:
                analysis_year = st.number_input(
                    "분석 연도",
                    min_value=2020,
                    max_value=2100,
                    value=current_year,
                    key="analysis_year"
                )
            with col2:
                analysis_month = st.number_input(
                    "분석 월",
                    min_value=1,
                    max_value=12,
                    value=current_month,
                    key="analysis_month"
                )
            
            # 매출 및 원가 데이터 로드
            sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
            menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
            recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
            ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
            daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
            
            # 원가 계산
            cost_df = pd.DataFrame()
            if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
                from src.analytics import calculate_menu_cost
                cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
            
            # 목표 대비 분석 (판매 비중 반영)
            analysis_result = target_gap_analysis(
                sales_df, targets_df, cost_df, analysis_year, analysis_month,
                daily_sales_df=daily_sales_df, menu_df=menu_df
            )
            
            if analysis_result:
                render_target_dashboard(analysis_result)
            else:
                st.info(f"{analysis_year}년 {analysis_month}월의 목표 데이터가 없습니다.")
        else:
            st.info("목표 데이터를 먼저 설정해주세요.")
    
    # 메뉴 ABC 분석
    elif submenu == "메뉴 ABC 분석":
        render_section_header("메뉴 ABC 분석", "📊")
        
        # 기간 선택
        from datetime import datetime
        col1, col2, col3 = st.columns(3)
        
        with col1:
            analysis_year = st.number_input(
                "분석 연도",
                min_value=2020,
                max_value=2100,
                value=datetime.now().year,
                key="abc_year"
            )
        with col2:
            analysis_month = st.number_input(
                "분석 월",
                min_value=1,
                max_value=12,
                value=datetime.now().month,
                key="abc_month"
            )
        with col3:
            a_threshold = st.number_input(
                "A 등급 비중 (%)",
                min_value=0,
                max_value=100,
                value=70,
                step=5,
                key="abc_a_threshold"
            )
            b_threshold = st.number_input(
                "B 등급 비중 (%)",
                min_value=0,
                max_value=100,
                value=20,
                step=5,
                key="abc_b_threshold"
            )
            c_threshold = 100 - a_threshold - b_threshold
            if c_threshold < 0:
                st.warning("A + B 비중이 100%를 초과합니다.")
                c_threshold = 10
        
        # 데이터 로드
        daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
        menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
        
        # 해당 월 데이터 필터링
        if not daily_sales_df.empty:
            daily_sales_df['날짜'] = pd.to_datetime(daily_sales_df['날짜'])
            monthly_sales = daily_sales_df[
                (daily_sales_df['날짜'].dt.year == analysis_year) &
                (daily_sales_df['날짜'].dt.month == analysis_month)
            ]
        else:
            monthly_sales = pd.DataFrame()
        
        # 원가 계산
        cost_df = pd.DataFrame()
        if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
            from src.analytics import calculate_menu_cost
            cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
        
        # ABC 분석 실행
        if not monthly_sales.empty and not menu_df.empty:
            abc_result = abc_analysis(
                monthly_sales, menu_df, cost_df,
                a_threshold=a_threshold,
                b_threshold=b_threshold,
                c_threshold=c_threshold
            )
            
            if not abc_result.empty:
                render_abc_analysis(abc_result, cost_df, a_threshold, b_threshold, c_threshold)
                
                # ABC 히스토리 저장 버튼
                render_section_divider()
                if st.button("💾 ABC 분석 결과 저장", type="primary"):
                    try:
                        save_abc_history(analysis_year, analysis_month, abc_result)
                        st.success(f"{analysis_year}년 {analysis_month}월 ABC 분석 결과가 저장되었습니다!")
                    except Exception as e:
                        st.error(f"저장 중 오류가 발생했습니다: {e}")
            else:
                st.info("ABC 분석 결과가 없습니다.")
        else:
            st.info("ABC 분석을 수행하려면 판매 데이터와 메뉴 데이터가 필요합니다.")
