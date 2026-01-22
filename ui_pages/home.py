"""
홈 (사장 계기판) 페이지
Phase 3 / STEP 1: 뼈대 + 데이터 단계 판별만 구현
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header, render_section_divider
from src.auth import get_current_store_id, get_supabase_client

# 공통 설정 적용
bootstrap(page_title="Home Dashboard")

# 로그인 체크
from src.auth import check_login, show_login_page
if not check_login():
    show_login_page()
    st.stop()


def detect_data_level(store_id: str) -> int:
    """
    현재 매장의 데이터 성숙도 단계를 판별
    
    LEVEL 0: 데이터 거의 없음 (sales 0건)
    LEVEL 1: 매출만 있음 (sales 존재, daily_close 거의 없음)
    LEVEL 2: 운영 데이터 있음 (daily_close 또는 daily_sales_items 존재)
    LEVEL 3: 재무 구조 있음 (expense_structure 또는 actual_settlement 존재)
    
    Returns:
        int: 0, 1, 2, 또는 3
    """
    if not store_id:
        return 0
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0
        
        # LEVEL 0 체크: sales 0건
        sales_check = supabase.table("sales")\
            .select("id", count="exact")\
            .eq("store_id", store_id)\
            .limit(1)\
            .execute()
        
        sales_count = sales_check.count if hasattr(sales_check, 'count') and sales_check.count is not None else (len(sales_check.data) if sales_check.data else 0)
        
        if sales_count == 0:
            return 0
        
        # LEVEL 1 체크: sales 존재, daily_close 거의 없음 (3건 이하)
        daily_close_check = supabase.table("daily_close")\
            .select("id", count="exact")\
            .eq("store_id", store_id)\
            .limit(1)\
            .execute()
        
        daily_close_count = daily_close_check.count if hasattr(daily_close_check, 'count') and daily_close_check.count is not None else (len(daily_close_check.data) if daily_close_check.data else 0)
        
        if daily_close_count <= 3:
            return 1
        
        # LEVEL 2 체크: daily_close 또는 daily_sales_items 존재
        # daily_close는 이미 체크했으므로, daily_sales_items도 확인
        daily_sales_check = supabase.table("v_daily_sales_items_effective")\
            .select("menu_id", count="exact")\
            .eq("store_id", store_id)\
            .limit(1)\
            .execute()
        
        daily_sales_count = daily_sales_check.count if hasattr(daily_sales_check, 'count') and daily_sales_check.count is not None else (len(daily_sales_check.data) if daily_sales_check.data else 0)
        
        if daily_close_count > 3 or daily_sales_count > 0:
            # LEVEL 3 체크: expense_structure 또는 actual_settlement 존재
            try:
                expense_check = supabase.table("expense_structure")\
                    .select("id", count="exact")\
                    .eq("store_id", store_id)\
                    .limit(1)\
                    .execute()
                
                expense_count = expense_check.count if hasattr(expense_check, 'count') and expense_check.count is not None else (len(expense_check.data) if expense_check.data else 0)
                
                if expense_count > 0:
                    return 3
            except Exception:
                pass
            
            try:
                settlement_check = supabase.table("actual_settlement")\
                    .select("id", count="exact")\
                    .eq("store_id", store_id)\
                    .limit(1)\
                    .execute()
                
                settlement_count = settlement_check.count if hasattr(settlement_check, 'count') and settlement_check.count is not None else (len(settlement_check.data) if settlement_check.data else 0)
                
                if settlement_count > 0:
                    return 3
            except Exception:
                pass
            
            return 2
        
        return 1
        
    except Exception as e:
        # 에러 발생 시 안전하게 0 리턴
        return 0


def render_home():
    """홈 (사장 계기판) 페이지 렌더링"""
    render_page_header("사장 계기판", "🏠")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다. 로그인 상태를 확인해주세요.")
        return
    
    # 데이터 단계 판별 (최초 1회만)
    if 'home_data_level' not in st.session_state:
        st.session_state.home_data_level = detect_data_level(store_id)
    
    data_level = st.session_state.home_data_level
    
    # 단계별 안내
    level_labels = {
        0: "LEVEL 0: 데이터 거의 없음",
        1: "LEVEL 1: 매출만 있음",
        2: "LEVEL 2: 운영 데이터 있음",
        3: "LEVEL 3: 재무 구조 있음",
    }
    
    st.info(f"📊 현재 데이터 단계: **{level_labels.get(data_level, '알 수 없음')}**")
    
    render_section_divider()
    
    # ========== 섹션 1: 상태판 ==========
    with st.container():
        st.markdown("### 📊 상태판")
        
        if data_level == 0:
            st.markdown("""
            <div style="padding: 2rem; background: #f8f9fa; border-radius: 12px; text-align: center; border: 2px dashed #dee2e6;">
                <h4 style="color: #6c757d; margin-bottom: 1rem;">아직 데이터가 없습니다</h4>
                <p style="color: #6c757d; margin-bottom: 1.5rem;">오늘 마감부터 시작하세요.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📋 오늘 마감하기", type="primary", use_container_width=True, key="home_btn_close"):
                st.session_state.current_page = "점장 마감"
                st.rerun()
        elif data_level == 1:
            st.markdown("""
            <div style="padding: 2rem; background: #fff3cd; border-radius: 12px; text-align: center; border: 2px solid #ffc107;">
                <h4 style="color: #856404; margin-bottom: 1rem;">매출 데이터가 있습니다</h4>
                <p style="color: #856404; margin-bottom: 1.5rem;">마감을 꾸준히 입력하면 더 많은 분석이 가능합니다.</p>
            </div>
            """, unsafe_allow_html=True)
        elif data_level == 2:
            st.markdown("""
            <div style="padding: 2rem; background: #d1ecf1; border-radius: 12px; text-align: center; border: 2px solid #17a2b8;">
                <h4 style="color: #0c5460; margin-bottom: 1rem;">운영 데이터가 쌓이고 있습니다</h4>
                <p style="color: #0c5460; margin-bottom: 1.5rem;">재무 구조를 입력하면 더 정확한 분석이 가능합니다.</p>
            </div>
            """, unsafe_allow_html=True)
        else:  # level 3
            st.markdown("""
            <div style="padding: 2rem; background: #d4edda; border-radius: 12px; text-align: center; border: 2px solid #28a745;">
                <h4 style="color: #155724; margin-bottom: 1rem;">완전한 데이터 구조가 갖춰졌습니다</h4>
                <p style="color: #155724; margin-bottom: 1.5rem;">모든 분석 기능을 사용할 수 있습니다.</p>
            </div>
            """, unsafe_allow_html=True)
    
    render_section_divider()
    
    # ========== 섹션 2: 핵심 숫자 카드 ==========
    with st.container():
        st.markdown("### 💰 핵심 숫자 카드")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if data_level == 0:
                st.markdown("""
                <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem;">오늘 매출</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">-</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; text-align: center; color: white;">
                    <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">오늘 매출</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">계산 예정</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if data_level == 0:
                st.markdown("""
                <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem;">이번 달 매출</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">-</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 8px; text-align: center; color: white;">
                    <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 매출</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">계산 예정</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            if data_level < 2:
                st.markdown("""
                <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem;">객단가</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">-</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 8px; text-align: center; color: white;">
                    <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">객단가</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">계산 예정</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            if data_level < 3:
                st.markdown("""
                <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem;">이번 달 이익</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">-</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 8px; text-align: center; color: white;">
                    <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 이익</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">계산 예정</div>
                </div>
                """, unsafe_allow_html=True)
    
    render_section_divider()
    
    # ========== 섹션 3: 오늘 하나만 ==========
    with st.container():
        st.markdown("### 🎯 오늘 하나만")
        
        if data_level == 0:
            st.markdown("""
            <div style="padding: 1.5rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                <h4 style="color: #856404; margin-bottom: 0.5rem;">오늘 마감을 입력하세요</h4>
                <p style="color: #856404; margin-bottom: 1rem;">첫 마감부터 시작하면 데이터가 쌓이기 시작합니다.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📋 오늘 마감하기", type="primary", use_container_width=True, key="home_btn_close_today"):
                st.session_state.current_page = "점장 마감"
                st.rerun()
        elif data_level == 1:
            st.markdown("""
            <div style="padding: 1.5rem; background: #d1ecf1; border-radius: 8px; border-left: 4px solid #17a2b8;">
                <h4 style="color: #0c5460; margin-bottom: 0.5rem;">이번 주는 매출만 꾸준히 입력해보세요</h4>
                <p style="color: #0c5460; margin-bottom: 1rem;">매출 데이터가 쌓이면 더 많은 분석이 가능합니다.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("💰 매출 등록", type="primary", use_container_width=True, key="home_btn_sales"):
                st.session_state.current_page = "매출 등록"
                st.rerun()
        elif data_level == 2:
            st.markdown("""
            <div style="padding: 1.5rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                <h4 style="color: #155724; margin-bottom: 0.5rem;">오늘 마감을 완료하세요</h4>
                <p style="color: #155724; margin-bottom: 1rem;">운영 데이터가 쌓이면 더 정확한 분석이 가능합니다.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📋 오늘 마감하기", type="primary", use_container_width=True, key="home_btn_close_level2"):
                st.session_state.current_page = "점장 마감"
                st.rerun()
        else:  # level 3
            st.markdown("""
            <div style="padding: 1.5rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                <h4 style="color: #155724; margin-bottom: 0.5rem;">오늘도 마감을 완료하세요</h4>
                <p style="color: #155724; margin-bottom: 1rem;">완전한 데이터 구조로 모든 분석을 활용할 수 있습니다.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📋 오늘 마감하기", type="primary", use_container_width=True, key="home_btn_close_level3"):
                st.session_state.current_page = "점장 마감"
                st.rerun()
    
    render_section_divider()
    
    # ========== 섹션 4: 문제 / 잘한 점 ==========
    with st.container():
        st.markdown("### ⚠️ 문제 / ✅ 잘한 점")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ⚠️ 문제")
            if data_level < 2:
                st.markdown("""
                <div style="padding: 1.5rem; background: #f8d7da; border-radius: 8px; border-left: 4px solid #dc3545;">
                    <p style="color: #721c24; margin: 0;">운영 데이터가 부족합니다. 마감을 꾸준히 입력해주세요.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: #f8d7da; border-radius: 8px; border-left: 4px solid #dc3545;">
                    <p style="color: #721c24; margin: 0;">문제 분석은 다음 단계에서 추가됩니다.</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### ✅ 잘한 점")
            if data_level == 0:
                st.markdown("""
                <div style="padding: 1.5rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                    <p style="color: #155724; margin: 0;">시스템을 시작하셨습니다. 첫 마감부터 시작하세요!</p>
                </div>
                """, unsafe_allow_html=True)
            elif data_level == 1:
                st.markdown("""
                <div style="padding: 1.5rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                    <p style="color: #155724; margin: 0;">매출 데이터를 꾸준히 입력하고 있습니다. 좋습니다!</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                    <p style="color: #155724; margin: 0;">잘한 점 분석은 다음 단계에서 추가됩니다.</p>
                </div>
                """, unsafe_allow_html=True)
    
    render_section_divider()
    
    # ========== 섹션 5: 이상 징후 ==========
    with st.container():
        st.markdown("### 🔍 이상 징후")
        
        if data_level < 2:
            st.markdown("""
            <div style="padding: 1.5rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                <p style="color: #856404; margin: 0;">이상 징후 분석을 위해서는 운영 데이터가 필요합니다. 마감을 꾸준히 입력해주세요.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding: 1.5rem; background: #d1ecf1; border-radius: 8px; border-left: 4px solid #17a2b8;">
                <p style="color: #0c5460; margin: 0;">이상 징후 분석은 다음 단계에서 추가됩니다.</p>
            </div>
            """, unsafe_allow_html=True)
    
    render_section_divider()
    
    # ========== 섹션 6: 미니 차트 ==========
    with st.container():
        st.markdown("### 📈 미니 차트")
        
        if data_level == 0:
            st.markdown("""
            <div style="padding: 2rem; background: #f8f9fa; border-radius: 8px; text-align: center; border: 2px dashed #dee2e6;">
                <p style="color: #6c757d; margin: 0;">차트를 표시하려면 데이터가 필요합니다. 마감을 입력해주세요.</p>
            </div>
            """, unsafe_allow_html=True)
        elif data_level == 1:
            st.markdown("""
            <div style="padding: 2rem; background: #fff3cd; border-radius: 8px; text-align: center; border: 2px solid #ffc107;">
                <p style="color: #856404; margin: 0;">더 많은 차트를 보려면 마감을 꾸준히 입력해주세요.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding: 2rem; background: #d1ecf1; border-radius: 8px; text-align: center; border: 2px solid #17a2b8;">
                <p style="color: #0c5460; margin: 0;">미니 차트는 다음 단계에서 추가됩니다.</p>
            </div>
            """, unsafe_allow_html=True)
    
    render_section_divider()
    
    # ========== 섹션 7: 우리 가게 숫자 구조 ==========
    with st.container():
        st.markdown("### 🏪 우리 가게 숫자 구조")
        
        if data_level < 3:
            st.markdown("""
            <div style="padding: 1.5rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                <h4 style="color: #856404; margin-bottom: 0.5rem;">재무 구조를 입력하세요</h4>
                <p style="color: #856404; margin-bottom: 1rem;">비용 구조와 실제 정산을 입력하면 우리 가게의 숫자 구조를 볼 수 있습니다.</p>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💳 목표 비용구조", use_container_width=True, key="home_btn_cost"):
                    st.session_state.current_page = "목표 비용구조"
                    st.rerun()
            with col2:
                if st.button("🧾 실제정산", use_container_width=True, key="home_btn_settlement"):
                    st.session_state.current_page = "실제정산"
                    st.rerun()
        else:
            st.markdown("""
            <div style="padding: 1.5rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                <h4 style="color: #155724; margin-bottom: 0.5rem;">우리 가게 숫자 구조가 여기에 표시됩니다</h4>
                <p style="color: #155724; margin: 0;">숫자 구조 분석은 다음 단계에서 추가됩니다.</p>
            </div>
            """, unsafe_allow_html=True)
    
    render_section_divider()
    
    # ========== 섹션 8: 이번 달 운영 메모 ==========
    with st.container():
        st.markdown("### 📝 이번 달 운영 메모")
        
        if data_level < 2:
            st.markdown("""
            <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #6c757d;">
                <p style="color: #495057; margin: 0;">운영 메모를 입력하려면 마감 데이터가 필요합니다. 마감을 꾸준히 입력해주세요.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding: 1.5rem; background: #d1ecf1; border-radius: 8px; border-left: 4px solid #17a2b8;">
                <p style="color: #0c5460; margin: 0;">이번 달 운영 메모는 다음 단계에서 추가됩니다.</p>
            </div>
            """, unsafe_allow_html=True)
