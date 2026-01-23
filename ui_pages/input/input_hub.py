"""
입력 허브 페이지
입력 관련 모든 페이지로의 네비게이션 허브
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header
from src.auth import get_current_store_id, get_supabase_client
from src.storage_supabase import get_day_record_status, load_actual_settlement_items
from src.utils.time_utils import today_kst
from datetime import timedelta

# 공통 설정 적용
bootstrap(page_title="Input Hub")


def _count_completed_checklists_last_7_days(store_id: str) -> int:
    """
    최근 7일 내 완료된 체크리스트 개수 조회
    
    Args:
        store_id: 매장 ID
    
    Returns:
        int: 완료된 체크리스트 개수 (에러 시 0)
    """
    if not store_id:
        return 0
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0
        
        today = today_kst()
        cutoff_date = (today - timedelta(days=6)).isoformat()  # 총 7일 (오늘 포함)
        
        result = supabase.table("health_check_sessions").select("id", count="exact").eq(
            "store_id", store_id
        ).not_.is_("completed_at", "null").gte("completed_at", cutoff_date).execute()
        
        return result.count if result.count is not None else 0
    
    except Exception as e:
        # 에러 발생 시 조용히 0 반환 (페이지 크래시 방지)
        return 0


def _is_monthly_settlement_done_for_prev_month(store_id: str) -> bool:
    """
    지난달 실제정산 완료 여부 확인
    
    Args:
        store_id: 매장 ID
    
    Returns:
        bool: 완료 여부 (에러/판단 불가 시 False)
    """
    if not store_id:
        return False
    
    try:
        today = today_kst()
        prev_month = today.month - 1
        prev_year = today.year
        
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
        
        # actual_settlement_items 조회
        items = load_actual_settlement_items(store_id, prev_year, prev_month)
        
        # 항목이 1개 이상 있으면 완료로 간주
        return len(items) > 0
    
    except Exception as e:
        # 에러 발생 시 False 반환 (추천 로직에서 P4 건너뛰도록)
        return False


def _get_today_recommendation(store_id: str) -> dict:
    """
    오늘 추천 액션 결정 (규칙 v2)
    
    우선순위:
    P1. 오늘 입력(통합)이 "매출도 없고 기록도 없음" → "📝 오늘 입력(통합)"
    P2. 오늘 매출/기록은 있는데 "마감 없음" → "📋 점장 마감"
    P3. 오늘 마감까지 완료했는데, 최근 7일 내 체크리스트 완료가 0회 → "📋 매장 체크리스트"
    P4. 월초(1~3일)이고 지난달 실제정산 미완료 → "📅 월간 정산(실제 입력)"
    Fallback. 예외 발생/판단 불가 → "📝 오늘 입력(통합)"
    
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
        has_visitors = status.get("has_visitors", False)
        # 기록 있음 = 매출 또는 방문자 또는 마감 중 하나라도 있으면 True
        has_any = has_sales or has_visitors or has_close
        
        # P1: 오늘 매출도 없고 기록도 없음 → 오늘 입력 추천
        if not has_sales and not has_any:
            return {
                "message": "📝 오늘 입력을 시작하세요",
                "button_label": "📝 오늘 입력(통합)",
                "page_key": "일일 입력(통합)"
            }
        
        # P2: 오늘 매출/기록은 있는데 마감 없음 → 점장 마감 추천
        if not has_close:
            return {
                "message": "📋 오늘 마감을 완료하세요",
                "button_label": "📋 점장 마감",
                "page_key": "점장 마감"
            }
        
        # P3: 오늘 마감까지 완료했는데, 최근 7일 내 체크리스트 완료가 0회 → 매장 체크리스트 추천
        try:
            checklist_count = _count_completed_checklists_last_7_days(store_id)
            if checklist_count == 0:
                return {
                    "message": "📋 이번 주 점검을 한번 해보세요",
                    "button_label": "📋 매장 체크리스트",
                    "page_key": "건강검진 실시"
                }
        except Exception:
            # 체크리스트 조회 실패 시 P3 건너뛰고 P4로 진행
            pass
        
        # P4: 월초(1~3일)이고 지난달 실제정산 미완료 → 월간 정산 추천
        if today.day <= 3:
            try:
                is_settlement_done = _is_monthly_settlement_done_for_prev_month(store_id)
                if not is_settlement_done:
                    return {
                        "message": "📅 월초입니다. 지난달 정산을 마무리하세요",
                        "button_label": "📅 월간 정산(실제 입력)",
                        "page_key": "실제정산"
                    }
            except Exception:
                # 월간 정산 조회 실패 시 P4 건너뛰고 fallback으로
                pass
        
        # 모든 조건을 통과했으면 기본값 (오늘 입력 추천)
        return {
            "message": "📝 오늘 입력을 시작하세요",
            "button_label": "📝 오늘 입력(통합)",
            "page_key": "일일 입력(통합)"
        }
    
    except Exception:
        # Fallback: 예외 발생 시 기본값 반환
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
