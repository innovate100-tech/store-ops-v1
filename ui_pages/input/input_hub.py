"""
입력 허브 페이지
입력 관련 모든 페이지로의 네비게이션 허브
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header
from src.auth import get_current_store_id
from src.storage_supabase import get_day_record_status
from src.utils.time_utils import today_kst

# 공통 설정 적용
bootstrap(page_title="Input Hub")


def _get_today_recommendation(store_id: str) -> dict:
    """
    오늘 추천 액션 결정 (규칙 v1)
    
    Returns:
        {
            "message": "추천 메시지",
            "button_label": "버튼 라벨",
            "page_key": "페이지 키"
        }
    """
    if not store_id:
        return {
            "message": "📝 오늘 입력을 시작하세요",
            "button_label": "📝 오늘 입력(통합)",
            "page_key": "일일 입력(통합)"
        }
    
    try:
        today = today_kst()
        status = get_day_record_status(store_id, today)
        has_close = status.get("has_close", False)
        has_sales = status.get("has_sales", False)
        
        # 오늘 데이터가 없으면: 오늘 입력 추천
        if not has_close and not has_sales:
            return {
                "message": "📝 오늘 입력을 시작하세요",
                "button_label": "📝 오늘 입력(통합)",
                "page_key": "일일 입력(통합)"
            }
        
        # 오늘 데이터가 있으면: 점장 마감 추천
        # TODO: 주간 리포트는 요일이 월요일이면 추천 (향후 구현)
        return {
            "message": "📋 오늘 마감을 완료하세요",
            "button_label": "📋 점장 마감",
            "page_key": "점장 마감"
        }
    except Exception:
        # 에러 발생 시 기본값 반환
        return {
            "message": "📝 오늘 입력을 시작하세요",
            "button_label": "📝 오늘 입력(통합)",
            "page_key": "일일 입력(통합)"
        }


def render_input_hub():
    """입력 허브 페이지 렌더링"""
    render_page_header("✍ 입력 허브", "✍")
    
    store_id = get_current_store_id()
    
    # 오늘 추천 액션 (최상단)
    recommendation = _get_today_recommendation(store_id)
    st.markdown(f"""
    <div style="padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 12px; color: white; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">🎯 오늘 추천</div>
        <div style="font-size: 0.95rem; margin-bottom: 0.8rem;">{recommendation['message']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(recommendation['button_label'], type="primary", use_container_width=True, key="input_hub_today_recommendation"):
        st.session_state["current_page"] = recommendation['page_key']
        st.rerun()
    
    st.markdown("---")
    
    # 안내 문구
    st.info("""
    💡 **입력은 기준(원본)을 만드는 곳입니다.**  
    🧠 **설계는 기준을 업그레이드/변형하는 곳입니다.**
    """)
    
    st.markdown("---")
    
    # A) 매일 입력
    st.markdown("### 📅 매일 입력")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 오늘 입력(통합)", use_container_width=True, type="primary", key="input_hub_daily_input"):
            st.session_state["current_page"] = "일일 입력(통합)"
            st.rerun()
    
    with col2:
        if st.button("📋 점장 마감", use_container_width=True, type="primary", key="input_hub_manager_close"):
            st.session_state["current_page"] = "점장 마감"
            st.rerun()
    
    st.markdown("---")
    
    # B) 월 1회 입력
    st.markdown("### 📆 월 1회 입력")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📅 월간 정산(실제 입력)", use_container_width=True, type="secondary", key="input_hub_settlement"):
            st.session_state["current_page"] = "실제정산"
            st.rerun()
        st.caption("페이지 키: 실제정산 (기존 유지)")
    
    with col2:
        if st.button("🎯 목표 매출 구조(기준 입력)", use_container_width=True, type="secondary", key="input_hub_target_sales"):
            st.session_state["current_page"] = "목표 매출구조"
            st.rerun()
    
    with col3:
        if st.button("🧾 목표 비용 구조(기준 입력)", use_container_width=True, type="secondary", key="input_hub_target_cost"):
            st.session_state["current_page"] = "목표 비용구조"
            st.rerun()
    
    st.markdown("---")
    
    # C) 주간·불시
    st.markdown("### 📊 주간·불시")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📈 주간 리포트", use_container_width=True, type="secondary", key="input_hub_weekly_report"):
            st.session_state["current_page"] = "주간 리포트"
            st.rerun()
    
    with col2:
        if st.button("📋 매장 체크리스트", use_container_width=True, type="secondary", key="input_hub_health_check"):
            st.session_state["current_page"] = "건강검진 실시"
            st.rerun()
    
    st.markdown("---")
    
    # D) 보정/과거 입력(필요할 때만)
    st.markdown("### 🔧 보정/과거 입력 (필요할 때만)")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧮 매출 등록(보정)", use_container_width=True, type="secondary", key="input_hub_sales_entry"):
            st.session_state["current_page"] = "매출 등록"
            st.rerun()
    
    with col2:
        if st.button("📦 판매량 등록(보정)", use_container_width=True, type="secondary", key="input_hub_sales_volume"):
            st.session_state["current_page"] = "판매량 등록"
            st.rerun()
