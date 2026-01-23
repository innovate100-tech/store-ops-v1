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


def _is_current_month_settlement_done(store_id: str) -> bool:
    """
    이번달 실제정산 완료 여부 확인
    
    Args:
        store_id: 매장 ID
    
    Returns:
        bool: 완료 여부 (에러/판단 불가 시 False)
    """
    if not store_id:
        return False
    
    try:
        today = today_kst()
        current_year = today.year
        current_month = today.month
        
        # actual_settlement_items 조회
        items = load_actual_settlement_items(store_id, current_year, current_month)
        
        # 항목이 1개 이상 있으면 완료로 간주
        return len(items) > 0
    
    except Exception as e:
        # 에러 발생 시 False 반환
        return False


def _get_today_recommendation(store_id: str) -> dict:
    """
    오늘 추천 액션 결정 (규칙 v2 - 요구사항 반영)
    
    우선순위:
    P1. 오늘 아무 데이터 없으면 → 오늘 입력(통합)
    P2. 오늘 매출만 있고 마감 없으면 → 오늘 입력(통합)
    P3. 오늘 입력 있고 마감 없으면 → 점장 마감(오늘 입력 페이지)
    P4. 7일간 체크리스트 없으면 → 매장 체크리스트
    P5. 월초 + 이번달 정산 없으면 → 월간 정산
    Fallback. 예외 발생/판단 불가 → 오늘 입력(통합)
    
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
        
        # P1: 오늘 아무 데이터 없으면 → 오늘 입력 추천
        if not has_any:
            return {
                "message": "📝 오늘 입력을 시작하세요",
                "button_label": "📝 오늘 입력(통합)",
                "page_key": "일일 입력(통합)"
            }
        
        # P2: 오늘 매출만 있고 마감 없으면 → 오늘 입력 추천
        if has_sales and not has_close:
            return {
            "message": "📝 오늘 입력을 완료하세요",
            "button_label": "📝 오늘 입력(통합)",
            "page_key": "일일 입력(통합)"
            }
        
        # P3: 오늘 입력 있고 마감 없으면 → 점장 마감(오늘 입력 페이지)
        if has_any and not has_close:
            return {
                "message": "📋 오늘 마감을 완료하세요",
                "button_label": "📝 오늘 입력(통합)",
                "page_key": "일일 입력(통합)"  # 오늘 입력 페이지로 이동
            }
        
        # P4: 7일간 체크리스트 없으면 → 매장 체크리스트 추천
        try:
            checklist_count = _count_completed_checklists_last_7_days(store_id)
            if checklist_count == 0:
                return {
                    "message": "📋 이번 주 점검을 한번 해보세요",
                    "button_label": "📋 매장 체크리스트",
                    "page_key": "건강검진 실시"
                }
        except Exception:
            # 체크리스트 조회 실패 시 P4 건너뛰고 P5로 진행
            pass
        
        # P5: 월초 + 이번달 정산 없으면 → 월간 정산 추천
        if today.day <= 3:
            try:
                is_settlement_done = _is_current_month_settlement_done(store_id)
                if not is_settlement_done:
                    return {
                        "message": "📅 월초입니다. 이번달 정산을 시작하세요",
                        "button_label": "📅 월간 정산",
                        "page_key": "실제정산"
                    }
            except Exception:
                # 월간 정산 조회 실패 시 P5 건너뛰고 fallback으로
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
    """입력 허브 페이지 렌더링 - 입력 시스템 홈"""
    render_page_header("✍ 입력 허브", "✍")
    
    store_id = get_current_store_id()
    
    # ============================================
    # A. 오늘 추천 (최상단 고정)
    # ============================================
    recommendation = _get_today_recommendation(store_id)
    st.markdown(f"""
    <div style="padding: 1.2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 12px; color: white; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">🎯 오늘 추천</div>
        <div style="font-size: 1rem; margin-bottom: 1rem;">{recommendation['message']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(recommendation['button_label'], type="primary", use_container_width=True, key="input_hub_today_recommendation"):
        st.session_state["current_page"] = recommendation['page_key']
        st.rerun()
    
    st.markdown("---")
    
    # ============================================
    # 핵심 문구
    # ============================================
    st.markdown("""
    <div style="padding: 1rem; background: #f0f9ff; border-left: 4px solid #3b82f6; border-radius: 8px; margin-bottom: 2rem;">
        <p style="margin: 0; font-size: 1rem; line-height: 1.6;">
            <strong>입력은 가게의 현실을 만드는 일입니다.</strong><br>
            분석은 해석, 설계는 실험입니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================
    # B. 오늘/운영 입력 (장사하면서 쓰는 입력)
    # ============================================
    st.markdown("### 📊 오늘/운영 입력")
    st.caption("장사하면서 쓰는 입력 - 흘러가는 데이터를 기록합니다")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📝 오늘 입력(통합)**")
        st.caption("매일: 매출, 방문자, 판매량, 메모를 기록합니다")
        if st.button("📝 오늘 입력(통합)", use_container_width=True, type="primary", key="input_hub_daily_input"):
            st.session_state["current_page"] = "일일 입력(통합)"  # page key 유지
            st.rerun()
    
    with col2:
        st.markdown("**📋 매장 체크리스트**")
        st.caption("주 1-2회: 운영 전반을 점검하고 개선점을 찾습니다")
        if st.button("📋 매장 체크리스트", use_container_width=True, type="primary", key="input_hub_health_check"):
            st.session_state["current_page"] = "건강검진 실시"  # page key 유지
            st.rerun()
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("**📈 주간 리포트**")
        st.caption("주 1회: 이번 주 운영 상황을 정리합니다")
        if st.button("📈 주간 리포트", use_container_width=True, type="primary", key="input_hub_weekly_report"):
            st.session_state["current_page"] = "주간 리포트"  # page key 유지
            st.rerun()
    
    with col4:
        st.markdown("**📅 월간 정산**")
        st.caption("월 1회: 실제 성적을 확정하고 정산합니다")
        if st.button("📅 월간 정산", use_container_width=True, type="primary", key="input_hub_settlement"):
            st.session_state["current_page"] = "실제정산"  # page key 유지
            st.rerun()
    
    st.markdown("---")
    
    # ============================================
    # C. 매장 기준 입력 (설계의 원본 데이터)
    # ============================================
    st.markdown("### 🎯 매장 기준 입력")
    st.caption("설계가 가져다 쓰는 기준 데이터 - 목표와 기준을 설정합니다")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 목표 매출 구조**")
        st.caption("설계의 기준 데이터입니다. 설계 메뉴에서 업그레이드/시뮬레이션됩니다")
        if st.button("🎯 목표 매출 구조", use_container_width=True, type="secondary", key="input_hub_target_sales"):
            st.session_state["current_page"] = "목표 매출구조"  # page key 유지
            st.rerun()
    
    with col2:
        st.markdown("**🧾 목표 비용 구조**")
        st.caption("설계의 기준 데이터입니다. 설계 메뉴에서 업그레이드/시뮬레이션됩니다")
        if st.button("🧾 목표 비용 구조", use_container_width=True, type="secondary", key="input_hub_target_cost"):
            st.session_state["current_page"] = "목표 비용구조"  # page key 유지
            st.rerun()
    
    st.markdown("---")
    
    # ============================================
    # D. 매장 자산 입력 (가장 큰 섹션)
    # ============================================
    st.markdown("### 🏗️ 매장 자산 입력")
    st.markdown("""
    <div style="padding: 0.8rem; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px; margin-bottom: 1rem;">
        <p style="margin: 0; font-size: 0.95rem; line-height: 1.5;">
            <strong>이 앱의 뼈대는 여기서 만들어진다</strong><br>
            이 가게가 무엇으로 이루어져 있는가를 정의합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📘 메뉴 입력**")
        st.caption("가게의 모든 메뉴를 등록합니다")
        if st.button("📘 메뉴 입력", use_container_width=True, type="primary", key="input_hub_menu_input"):
            st.session_state["current_page"] = "메뉴 입력"  # page key 변경
            st.rerun()
    
    with col2:
        st.markdown("**🧺 재료 입력**")
        st.caption("사용하는 모든 재료를 등록합니다")
        if st.button("🧺 재료 입력", use_container_width=True, type="primary", key="input_hub_ingredient_input"):
            st.session_state["current_page"] = "재료 입력"  # page key 변경
            st.rerun()
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("**🧑‍🍳 레시피 입력**")
        st.caption("메뉴별 레시피와 원가를 등록합니다")
        if st.button("🧑‍🍳 레시피 입력", use_container_width=True, type="primary", key="input_hub_recipe_input"):
            st.session_state["current_page"] = "레시피 입력"  # page key 변경
            st.rerun()
    
    # 재고 관리는 향후 추가 예정 (현재 라우팅 없음)
    # with col4:
    #     st.markdown("**📦 재고 관리**")
    #     st.caption("재고 현황과 입출고를 관리합니다")
    #     if st.button("📦 재고 관리", use_container_width=True, type="primary", key="input_hub_inventory_management"):
    #         st.session_state["current_page"] = "재고 관리"  # page key 유지
    #         st.rerun()
    
    st.markdown("---")
    
    # ============================================
    # E. 보정·특수 입력
    # ============================================
    st.markdown("### 🔧 보정·특수 입력")
    st.caption("필요할 때만 사용 - 과거 데이터 수정이나 보정이 필요할 때")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🧮 매출 등록(과거/수정)**")
        st.caption("과거/수정: 특정 날짜의 매출을 보정하거나 추가 입력합니다")
        if st.button("🧮 매출 등록(과거/수정)", use_container_width=True, type="secondary", key="input_hub_sales_entry"):
            st.session_state["current_page"] = "매출 등록"  # page key 유지
            st.rerun()
    
    with col2:
        st.markdown("**📦 판매량 등록(과거/수정)**")
        st.caption("과거/수정: 특정 날짜의 판매량을 보정하거나 추가 입력합니다")
        if st.button("📦 판매량 등록(과거/수정)", use_container_width=True, type="secondary", key="input_hub_sales_volume"):
            st.session_state["current_page"] = "판매량 등록"  # page key 유지
            st.rerun()
