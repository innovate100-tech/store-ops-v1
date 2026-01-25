"""
데이터 입력 센터 페이지 (v5 - Control Board 구조)
매장을 시스템으로 구축하는 '운영 OS 조종석(Control Board)'

역할:
1. 가이드 박스 (헌법 영역)
2. System Snapshot (초압축 진단)
3. INPUT CONTROL BOARD (페이지 본체 - 입력 네비게이션 중심화)
4. System Panels (접힘 영역 - 상세 현황)
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header
from src.auth import get_current_store_id, get_supabase_client, get_read_client
from src.storage_supabase import get_day_record_status, load_actual_settlement_items, load_csv
from src.utils.time_utils import today_kst, current_year_kst, current_month_kst
from datetime import timedelta
import pandas as pd

try:
    from src.debug.nav_trace import push_render_step
except ImportError:
    def push_render_step(*args, **kwargs):
        pass

from src.ui.css_manager import inject_fx


def inject_input_hub_animations_css():
    """입력허브 애니메이션 CSS 주입 (1회만 실행)"""
    # 1회 주입 가드 (css_manager 내부에서 처리)
    if st.session_state.get("_ps_input_hub_anim_css_injected", False):
        return
    
    animations_css = """
    <style id="ps-input-hub-animations">
    /* 입력허브 애니메이션 keyframes (실패해도 기본은 보이게 설계) */
    @keyframes fadeInUp { 
        from { opacity: 0; transform: translateY(20px); } 
        to { opacity: 1; transform: translateY(0); } 
    }
    @keyframes shimmer-bg { 
        0% { background-position: 0% 50%; } 
        50% { background-position: 100% 50%; } 
        100% { background-position: 0% 50%; } 
    }
    @keyframes wave-move { 
        0% { transform: translateX(-100%); } 
        100% { transform: translateX(100%); } 
    }
    @keyframes pulse-ring { 
        0% { transform: scale(0.9); opacity: 0.7; } 
        50% { transform: scale(1.1); opacity: 1; } 
        100% { transform: scale(0.9); opacity: 0.7; } 
    }
    /* 기본 상태: 항상 보이게 */
    .guide-card-animated,
    .animate-in {
        opacity: 1 !important;
        transform: none !important;
        animation-fill-mode: both;
    }
    
    /* 애니메이션 적용 (장식용) */
    .guide-card-animated { 
        animation: fadeInUp 0.8s ease-out forwards; 
    }
    .shimmer-overlay { 
        position: absolute; 
        top: 0; 
        left: 0; 
        width: 100%; 
        height: 100%; 
        background: linear-gradient(-45deg, rgba(59, 130, 246, 0.05), rgba(30, 41, 59, 0), rgba(96, 165, 250, 0.05));
        background-size: 400% 400%; 
        animation: shimmer-bg 10s ease infinite; 
    }
    
    /* 시작 필요 상태 강조 스타일 - JavaScript로 동적 적용 (CSS는 보조용) */
    /* 주의: Streamlit이 클래스와 속성을 제거할 수 있으므로 JavaScript가 주로 담당 */
    
    /* 버튼 강조 - JavaScript로 동적 적용 (애니메이션 제거) */
    [data-ps-scope="input_hub"] button[kind="primary"]:has-text("🚀"),
    [data-ps-scope="input_hub"] .stButton button:contains("🚀") {
        background: linear-gradient(135deg, #F59E0B 0%, #EF4444 100%) !important;
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.6),
                    0 0 40px rgba(245, 158, 11, 0.4) !important;
        border: 2px solid rgba(245, 158, 11, 0.8) !important;
        font-weight: 700 !important;
    }
    
    /* prefers-reduced-motion 지원 */
    @media (prefers-reduced-motion: reduce) {
        [data-ps-scope="input_hub"] *,
        .guide-card-animated,
        .animate-in,
        .shimmer-overlay,
        [data-ps-scope="input_hub"] .ps-start-needed-card,
        [data-ps-scope="input_hub"] .ps-start-needed-button {
            animation: none !important;
            transition: none !important;
        }
    }
    </style>
    """
    inject_fx(animations_css, "input_hub_animations")
    st.session_state["_ps_input_hub_anim_css_injected"] = True


def inject_input_hub_ultra_premium_css():
    """입력허브 Ultra Premium CSS 주입 (배경 레이어 + FX, 1회만 실행)"""
    # 토글 확인
    if st.session_state.get("_ps_disable_ultra_css", False):
        return
    
    # 1회 주입 가드
    if st.session_state.get("_ps_ultra_css_injected", False):
        return
    
    scope_id = "input_hub"
    
    ultra_css = f"""
    <style>
    /* ============================================
       입력허브 Ultra Premium 배경 레이어 (안정화)
       ============================================ */
    
    /* 배경 레이어 wrapper (컨텐츠를 감싸지 않음, 독립 배경만) */
    [data-ps-scope="{scope_id}"].ps-hub-bg {{
        position: relative !important;
        z-index: 1 !important;
        visibility: visible !important;
        display: block !important;
        transform: none !important;
        filter: none !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
    }}
    
    /* 배경 레이어 ::before (상단 Neon Bar) - 항상 뒤에 */
    [data-ps-scope="{scope_id}"].ps-hub-bg::before {{
        content: "" !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 4px !important;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(59, 130, 246, 0.6) 20%, 
            rgba(96, 165, 250, 0.8) 50%, 
            rgba(59, 130, 246, 0.6) 80%, 
            transparent 100%
        ) !important;
        z-index: 0 !important;
        pointer-events: none !important;
        animation: slowDrift 24s ease infinite !important;
    }}
    
    /* 배경 레이어 ::after (배경 메시/그리드) - 항상 뒤에 */
    [data-ps-scope="{scope_id}"].ps-hub-bg::after {{
        content: "" !important;
        position: fixed !important;
        inset: 0 !important;
        background: 
            radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(96, 165, 250, 0.06) 0%, transparent 50%),
            linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%) !important;
        z-index: 0 !important;
        pointer-events: none !important;
        animation: slowDrift 24s ease infinite !important;
    }}
    
    @keyframes slowDrift {{
        0%, 100% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
    }}
    
    /* 컨텐츠 wrapper는 항상 앞에 */
    [data-ps-scope="{scope_id}"].ps-hub-content {{
        position: relative !important;
        z-index: 10 !important;
    }}
    
    /* TIER 카드 기본 스타일 */
    [data-ps-scope="{scope_id}"] .tier-1-wrapper,
    [data-ps-scope="{scope_id}"] .hub-tier-1 {{
        position: relative !important;
        z-index: 5 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }}
    
    /* prefers-reduced-motion 지원 (입력허브 전체) */
    @media (prefers-reduced-motion: reduce) {{
        [data-ps-scope="{scope_id}"] *,
        [data-ps-scope="{scope_id}"].ps-hub-bg::before,
        [data-ps-scope="{scope_id}"].ps-hub-bg::after {{
            animation: none !important;
            transition: none !important;
        }}
    }}
    </style>
    """
    inject_fx(ultra_css, "input_hub_ultra")
    st.session_state["_ps_ultra_css_injected"] = True


def inject_input_hub_controlboard_compact_css():
    """입력허브 Control Board 컴팩트 레이아웃 CSS 주입 (1회만 실행)"""
    # 1회 주입 가드
    if st.session_state.get("_ps_input_hub_controlboard_compact_css_injected", False):
        return
    
    scope_id = "input_hub"
    
    compact_css = f"""
    <style>
    /* ============================================
       입력허브 Control Board 컴팩트 레이아웃 CSS
       ============================================ */
    
    /* Control Board 카드 통일 높이 (프리미엄 스타일) */
    [data-ps-scope="{scope_id}"] .ps-control-card-struct {{
        height: 120px !important;
        min-height: 120px !important;
        max-height: 120px !important;
        padding: 0.9rem !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-control-card-op {{
        height: 115px !important;
        min-height: 115px !important;
        max-height: 115px !important;
        padding: 0.9rem !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-control-card-target {{
        height: 110px !important;
        min-height: 110px !important;
        max-height: 110px !important;
        padding: 0.9rem !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
    }}
    
    /* Control Board 버튼 통일 높이 - 프리미엄 컨트롤 패널 스타일 */
    [data-ps-scope="{scope_id}"] button[kind="primary"],
    [data-ps-scope="{scope_id}"] button[kind="secondary"] {{
        height: 48px !important;
        min-height: 48px !important;
        line-height: 1.2 !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.01em !important;
    }}
    
    /* Primary 버튼 - 핵심 CTA만 글로우 */
    [data-ps-scope="{scope_id}"] button[kind="primary"] {{
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.3) !important;
    }}
    
    [data-ps-scope="{scope_id}"] button[kind="primary"]:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.4) !important;
    }}
    
    /* Secondary 버튼 - 입력 전용 컨트롤 패널 스타일 */
    [data-ps-scope="{scope_id}"] button[kind="secondary"] {{
        border: 1px solid rgba(148, 163, 184, 0.25) !important;
        background: rgba(30, 41, 59, 0.6) !important;
    }}
    
    [data-ps-scope="{scope_id}"] button[kind="secondary"]:hover {{
        border-color: rgba(59, 130, 246, 0.4) !important;
        background-color: rgba(59, 130, 246, 0.08) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }}
    
    /* 페이지 헤더 - 레이어드 카드 스타일 (옵션 4) - 전역 선택자 추가 */
    .ps-page-header-layered,
    [data-ps-scope="{scope_id}"] .ps-page-header-layered,
    div[data-ps-scope="input_hub"].ps-page-header-layered {{
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px !important;
        padding: 0 !important;
        margin-bottom: 2rem !important;
        margin-top: 0 !important;
        box-shadow: 
            0 2px 8px rgba(0, 0, 0, 0.1),
            0 0 20px rgba(59, 130, 246, 0.15) !important;
        overflow: hidden !important;
        position: relative !important;
    }}
    
    .ps-page-header-layered::before,
    [data-ps-scope="{scope_id}"] .ps-page-header-layered::before,
    div[data-ps-scope="input_hub"].ps-page-header-layered::before {{
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 6px !important;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(59, 130, 246, 0.6) 20%, 
            rgba(96, 165, 250, 0.9) 50%, 
            rgba(59, 130, 246, 0.6) 80%, 
            transparent 100%
        ) !important;
        z-index: 1 !important;
    }}
    
    .ps-page-header-content,
    [data-ps-scope="{scope_id}"] .ps-page-header-content {{
        padding: 1.8rem 2rem 1.5rem 2rem !important;
        position: relative !important;
        z-index: 2 !important;
    }}
    
    .ps-page-header-title-row,
    [data-ps-scope="{scope_id}"] .ps-page-header-title-row {{
        display: flex !important;
        align-items: center !important;
        gap: 1rem !important;
        margin-bottom: 0.5rem !important;
    }}
    
    .ps-page-header-icon,
    [data-ps-scope="{scope_id}"] .ps-page-header-icon {{
        font-size: 2.2rem !important;
        filter: drop-shadow(0 0 8px rgba(96, 165, 250, 0.5)) !important;
        line-height: 1 !important;
    }}
    
    .ps-page-header-title,
    [data-ps-scope="{scope_id}"] .ps-page-header-title,
    h1.ps-page-header-title {{
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #F8FAFC !important;
        margin: 0 !important;
        letter-spacing: -0.02em !important;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3) !important;
        line-height: 1.2 !important;
    }}
    
    .ps-page-header-subtitle,
    [data-ps-scope="{scope_id}"] .ps-page-header-subtitle {{
        font-size: 0.9rem !important;
        color: #94A3B8 !important;
        margin: 0 !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
        margin-left: 3.2rem !important;
    }}
    
    .ps-page-header-divider,
    [data-ps-scope="{scope_id}"] .ps-page-header-divider {{
        height: 4px !important;
        width: 60px !important;
        background: linear-gradient(90deg, #3B82F6 0%, transparent 100%) !important;
        border-radius: 2px !important;
        margin-top: 1.2rem !important;
        margin-left: 3.2rem !important;
    }}
    
    /* 반응형 대응 */
    @media (max-width: 768px) {{
        .ps-page-header-content,
        [data-ps-scope="{scope_id}"] .ps-page-header-content {{
            padding: 1.4rem 1.5rem 1.2rem 1.5rem !important;
        }}
        
        .ps-page-header-icon,
        [data-ps-scope="{scope_id}"] .ps-page-header-icon {{
            font-size: 1.8rem !important;
        }}
        
        .ps-page-header-title,
        [data-ps-scope="{scope_id}"] .ps-page-header-title,
        h1.ps-page-header-title {{
            font-size: 1.8rem !important;
        }}
        
        .ps-page-header-subtitle,
        [data-ps-scope="{scope_id}"] .ps-page-header-subtitle {{
            font-size: 0.85rem !important;
            margin-left: 2.8rem !important;
        }}
        
        .ps-page-header-divider,
        [data-ps-scope="{scope_id}"] .ps-page-header-divider {{
            margin-left: 2.8rem !important;
        }}
    }}
    
    /* 레이어 간 간격 축소 (프리미엄 레이아웃) */
    [data-ps-scope="{scope_id}"] .ps-layer-section {{
        margin-bottom: 18px !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-layer-title {{
        margin-bottom: 10px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: #E2E8F0 !important;
    }}
    
    /* 액션 바 스타일 */
    [data-ps-scope="{scope_id}"] .ps-action-bar-wrapper {{
        margin-top: 10px !important;
        margin-bottom: 0 !important;
    }}
    
    /* 카드 그리드 간격 */
    [data-ps-scope="{scope_id}"] .ps-card-grid {{
        gap: 14px !important;
        margin-bottom: 12px !important;
    }}
    
    /* 버튼 바 간격 */
    [data-ps-scope="{scope_id}"] .ps-action-bar {{
        margin-top: 12px !important;
        margin-bottom: 0 !important;
    }}
    
    /* 프리미엄 카드 스타일 - 상태 표시기 */
    [data-ps-scope="{scope_id}"] .ps-status-card {{
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(148, 163, 184, 0.15) !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-status-card:hover {{
        border-color: rgba(148, 163, 184, 0.25) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }}
    
    /* 카드 내부 계층 */
    [data-ps-scope="{scope_id}"] .ps-card-title {{
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        margin-bottom: 0.6rem !important;
        letter-spacing: 0.02em !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.4rem !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-card-status-badge {{
        display: inline-block !important;
        padding: 0.25rem 0.6rem !important;
        border-radius: 6px !important;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 0.5rem !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-card-status-badge.active {{
        background: rgba(16, 185, 129, 0.15) !important;
        color: #10B981 !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-card-status-badge.incomplete {{
        background: rgba(245, 158, 11, 0.15) !important;
        color: #F59E0B !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-card-status-badge.missing {{
        background: rgba(100, 116, 139, 0.15) !important;
        color: #64748B !important;
        border: 1px solid rgba(100, 116, 139, 0.3) !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-card-status-badge.start-needed {{
        background: rgba(245, 158, 11, 0.2) !important;
        color: #F59E0B !important;
        border: 1px solid rgba(245, 158, 11, 0.5) !important;
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.3) !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-card-status-badge.optional {{
        background: rgba(148, 163, 184, 0.1) !important;
        color: #94A3B8 !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-card-value {{
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #F8FAFC !important;
        line-height: 1.2 !important;
        margin-top: auto !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-card-value-sub {{
        font-size: 0.7rem !important;
        color: #64748B !important;
        margin-top: 0.25rem !important;
        font-weight: 500 !important;
    }}
    
    
    /* System Panels expander 여백 축소 */
    [data-ps-scope="{scope_id}"] .ps-system-panels {{
        margin-top: 16px !important;
    }}
    
    /* 자산 패널 스타일 */
    [data-ps-scope="{scope_id}"] .ps-asset-panel {{
        background: rgba(30, 41, 59, 0.5) !important;
        border-radius: 10px !important;
        border-left: 3px solid !important;
        padding: 0.8rem 1rem !important;
        margin-bottom: 1rem !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-asset-progress {{
        display: flex !important;
        align-items: center !important;
        gap: 0.8rem !important;
        margin-top: 0.8rem !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-asset-progress-bar {{
        flex: 1 !important;
        background: rgba(255,255,255,0.05) !important;
        border-radius: 4px !important;
        height: 6px !important;
        overflow: hidden !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-asset-progress-fill {{
        height: 100% !important;
        border-radius: 4px !important;
    }}
    
    /* 자산 상태 스트립 */
    [data-ps-scope="{scope_id}"] .ps-asset-strip {{
        display: grid !important;
        gap: 0.6rem !important;
        margin-bottom: 1rem !important;
    }}
    
    [data-ps-scope="{scope_id}"] .ps-asset-strip-item {{
        padding: 0.6rem !important;
        background: rgba(30, 41, 59, 0.4) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(148, 163, 184, 0.15) !important;
    }}
    
    /* prefers-reduced-motion 지원 */
    @media (prefers-reduced-motion: reduce) {{
        [data-ps-scope="{scope_id}"] button[kind="primary"],
        [data-ps-scope="{scope_id}"] button[kind="secondary"] {{
            transition: none !important;
        }}
        [data-ps-scope="{scope_id}"] button[kind="primary"]:hover,
        [data-ps-scope="{scope_id}"] button[kind="secondary"]:hover {{
            transform: none !important;
        }}
    }}
    </style>
    """
    inject_fx(compact_css, "input_hub_controlboard_compact")
    st.session_state["_ps_input_hub_controlboard_compact_css_injected"] = True


def _count_completed_checklists_last_n_days(store_id: str, days: int = 14) -> int:
    if not store_id: return 0
    try:
        supabase = get_read_client()
        if not supabase: return 0
        today = today_kst()
        cutoff_date = (today - timedelta(days=days-1)).isoformat()
        result = supabase.table("health_check_sessions").select("id", count="exact").eq(
            "store_id", store_id
        ).not_.is_("completed_at", "null").gte("completed_at", cutoff_date).execute()
        return result.count if result.count is not None else 0
    except Exception: return 0

def _is_current_month_settlement_done(store_id: str) -> bool:
    if not store_id: return False
    try:
        today = today_kst()
        items = load_actual_settlement_items(store_id, today.year, today.month)
        return len(items) > 0
    except Exception: return False

def _get_today_recommendations(store_id: str) -> list:
    recommendations = []
    if not store_id: return []
    try:
        today = today_kst()
        status = get_day_record_status(store_id, today)
        has_close = status.get("has_close", False)
        has_any = status.get("has_sales", False) or status.get("has_visitors", False) or has_close
        sales_val = status.get("best_total_sales") or 0
        visitors_val = status.get("visitors_best") or 0
        
        if not has_close:
            msg = "📝 오늘 마감 필요" if not has_any else "📝 오늘 마감 미완료"
            recommendations.append({"status": "pending", "message": msg, "button_label": "📝 일일 마감", "page_key": "일일 입력(통합)", "priority": 1, "summary": f"{int(sales_val):,}원 / {int(visitors_val)}명" if has_any else "데이터 없음"})
        else:
            recommendations.append({"status": "completed", "message": "✅ 오늘 마감 완료", "button_label": "📝 일일 마감", "page_key": "일일 입력(통합)", "priority": 1, "summary": f"{int(sales_val):,}원 / {int(visitors_val)}명"})
        
        checklist_count = _count_completed_checklists_last_n_days(store_id, days=14)
        last_date_str = "기록 없음"
        try:
            supabase = get_read_client()
            res = supabase.table("health_check_sessions").select("completed_at").eq("store_id", store_id).not_.is_("completed_at", "null").order("completed_at", desc=True).limit(1).execute()
            if res.data: last_date_str = res.data[0]["completed_at"][:10]
        except Exception: pass

        recommendations.append({"status": "completed" if checklist_count > 0 else "pending", "message": f"🩺 QSC 완료 ({checklist_count}회)" if checklist_count > 0 else "🩺 QSC 점검 권장", "button_label": "🩺 QSC 입력", "page_key": "건강검진 실시", "priority": 4, "summary": f"최근: {last_date_str}"})
        is_done = _is_current_month_settlement_done(store_id)
        recommendations.append({"status": "completed" if is_done else "pending", "message": "📅 월간 정산", "button_label": "📅 정산 입력", "page_key": "실제정산", "priority": 5, "summary": f"{current_month_kst()}월"})
        return recommendations
    except Exception: return []

def detect_system_stage(assets: dict, has_daily_close: bool) -> dict:
    """
    시스템 단계 감지 (LEVEL 1-4)
    
    Args:
        assets: _get_asset_readiness() 반환값
        has_daily_close: 오늘 마감 여부
    
    Returns:
        {
            "level": 1-4,
            "name": "기록 단계" | "구조 단계" | "수익 단계" | "전략 단계",
            "description": "이 매장은..."
        }
    """
    menu_ready = assets.get('menu_count', 0) > 0 and assets.get('missing_price', 0) == 0
    ing_ready = assets.get('ing_count', 0) > 0 and assets.get('missing_cost', 0) == 0
    recipe_ready = assets.get('recipe_rate', 0) >= 80
    has_target = assets.get('has_target', False)
    
    if not has_daily_close:
        return {
            "level": 1,
            "name": "기록 단계",
            "description": "이 매장은 아직 일일 마감 기록이 없습니다.\n매출이 기록되기 시작하면 시스템이 작동합니다."
        }
    elif not menu_ready or not ing_ready:
        return {
            "level": 1,
            "name": "기록 단계",
            "description": "이 매장은 매출은 기록되고 있으나,\n메뉴와 재료 구조가 아직 정립되지 않았습니다."
        }
    elif not recipe_ready:
        return {
            "level": 2,
            "name": "구조 단계",
            "description": "이 매장은 매출은 기록되고 있으나,\n왜 돈이 남는지는 아직 숫자로 보이지 않습니다."
        }
    elif not has_target:
        return {
            "level": 3,
            "name": "수익 단계",
            "description": "이 매장은 메뉴 수익성을 분석할 수 있는 단계입니다.\n목표를 설정하면 전략 보드가 활성화됩니다."
        }
    else:
        return {
            "level": 4,
            "name": "전략 단계",
            "description": "이 매장은 모든 데이터 자산이 구축되어 있습니다.\n정밀 리포트와 전략 기능이 모두 활성화되었습니다."
        }


def detect_system_bottleneck(assets: dict, has_daily_close: bool, system_stage: dict) -> dict:
    """
    시스템 병목 감지
    
    Args:
        assets: _get_asset_readiness() 반환값
        has_daily_close: 오늘 마감 여부
        system_stage: detect_system_stage() 반환값
    
    Returns:
        {
            "bottleneck": "일일 마감" | "메뉴/재료" | "레시피" | "목표" | None,
            "message": "병목 메시지",
            "details": ["상세 1", "상세 2", ...],
            "impact": "이 상태에서는..."
        }
    """
    level = system_stage.get("level", 1)
    
    if level == 1:
        if not has_daily_close:
            return {
                "bottleneck": "일일 마감",
                "message": "일일 마감 기록 없음",
                "details": ["매출 기록이 없으면 분석이 시작되지 않습니다"],
                "impact": "일일 마감을 입력해야 매출 추이 분석이 가능합니다."
            }
        else:
            menu_ready = assets.get('menu_count', 0) > 0 and assets.get('missing_price', 0) == 0
            ing_ready = assets.get('ing_count', 0) > 0 and assets.get('missing_cost', 0) == 0
            if not menu_ready:
                return {
                    "bottleneck": "메뉴/재료",
                    "message": "메뉴 데이터 미완성",
                    "details": [
                        f"메뉴 {assets.get('menu_count', 0)}개 있음" if assets.get('menu_count', 0) > 0 else "메뉴 없음",
                        f"가격 누락 {assets.get('missing_price', 0)}개" if assets.get('missing_price', 0) > 0 else "가격 완성"
                    ],
                    "impact": "이 상태에서는 메뉴 수익 구조 분석이 제한됩니다."
                }
            elif not ing_ready:
                return {
                    "bottleneck": "메뉴/재료",
                    "message": "재료 데이터 미완성",
                    "details": [
                        f"재료 {assets.get('ing_count', 0)}개 있음" if assets.get('ing_count', 0) > 0 else "재료 없음",
                        f"단가 누락 {assets.get('missing_cost', 0)}개" if assets.get('missing_cost', 0) > 0 else "단가 완성"
                    ],
                    "impact": "이 상태에서는 원가 분석이 제한됩니다."
                }
    
    if level == 2:
        recipe_rate = assets.get('recipe_rate', 0)
        return {
            "bottleneck": "레시피",
            "message": "레시피 데이터 미완성",
            "details": [
                f"메뉴 있음",
                f"재료 있음",
                f"레시피 완성도 {recipe_rate:.0f}%"
            ],
            "impact": "이 상태에서는 메뉴 수익성 분석 / 구조 비교 / 전략 보드가 제한됩니다."
        }
    
    if level == 3:
        return {
            "bottleneck": "목표",
            "message": "목표 데이터 미설정",
            "details": [
                "메뉴/재료/레시피 완성",
                "목표 미설정"
            ],
            "impact": "이 상태에서는 목표 대비 성과 분석과 전략 보드가 제한됩니다."
        }
    
    return {
        "bottleneck": None,
        "message": "병목 없음",
        "details": ["모든 데이터 자산이 구축되었습니다"],
        "impact": "모든 분석 기능이 활성화되었습니다."
    }


def get_system_recommendation(bottleneck: dict, assets: dict) -> dict:
    """
    시스템 추천 액션 생성
    
    Args:
        bottleneck: detect_system_bottleneck() 반환값
        assets: _get_asset_readiness() 반환값
    
    Returns:
        {
            "primary": {
                "label": "액션 라벨",
                "page_key": "페이지 키",
                "description": "설명",
                "button_text": "버튼 텍스트"
            },
            "secondary": {...} | None,
            "relief": ["지금은 안 해도 되는 입력", ...]
        }
    """
    bn = bottleneck.get("bottleneck")
    
    if bn == "일일 마감":
        return {
            "primary": {
                "label": "일일 마감 입력",
                "page_key": "일일 입력(통합)",
                "description": "일일 마감은 '오늘 매장이 어떻게 돌아갔는지'를 기록하는 데이터입니다.",
                "button_text": "👉 일일 마감 입력으로 이동"
            },
            "secondary": None,
            "relief": ["재고", "과거 판매량"]
        }
    elif bn == "메뉴/재료":
        missing_price = assets.get('missing_price', 0)
        missing_cost = assets.get('missing_cost', 0)
        if missing_price > 0:
            return {
                "primary": {
                    "label": "메뉴 입력 보완",
                    "page_key": "메뉴 입력",
                    "description": "메뉴는 '우리 매장이 무엇을 파는지'를 정의하는 데이터입니다.",
                    "button_text": "👉 메뉴 입력으로 이동"
                },
                "secondary": {
                    "label": "재료 입력",
                    "page_key": "재료 입력",
                    "description": "재료는 '메뉴의 원가를 계산하는' 기준 데이터입니다."
                },
                "relief": ["재고", "과거 판매량", "레시피"]
            }
        else:
            return {
                "primary": {
                    "label": "재료 입력 보완",
                    "page_key": "재료 입력",
                    "description": "재료는 '메뉴의 원가를 계산하는' 기준 데이터입니다.",
                    "button_text": "👉 재료 입력으로 이동"
                },
                "secondary": None,
                "relief": ["재고", "과거 판매량", "레시피"]
            }
    elif bn == "레시피":
        return {
            "primary": {
                "label": "레시피 입력 보완",
                "page_key": "레시피 등록",
                "description": "레시피는 '이 메뉴가 왜 돈이 되는지'를 증명하는 데이터입니다.",
                "button_text": "👉 레시피 입력으로 이동"
            },
            "secondary": {
                "label": "목표 입력",
                "page_key": "목표 매출구조",
                "description": "목표는 '우리가 어디로 가야 하는지'를 정의하는 기준입니다."
            },
            "relief": ["재고", "과거 판매량"]
        }
    elif bn == "목표":
        return {
            "primary": {
                "label": "목표 입력",
                "page_key": "목표 매출구조",
                "description": "목표는 '우리가 어디로 가야 하는지'를 정의하는 기준입니다.",
                "button_text": "👉 목표 입력으로 이동"
            },
            "secondary": {
                "label": "월간 정산",
                "page_key": "실제정산",
                "description": "정산은 '목표 대비 실제 성과'를 비교하는 데이터입니다."
            },
            "relief": ["재고", "과거 판매량"]
        }
    else:
        return {
            "primary": None,
            "secondary": None,
            "relief": []
        }


def _get_asset_readiness(store_id: str) -> dict:
    if not store_id: return {}
    try:
        menu_df = load_csv("menu_master.csv", store_id=store_id)
        menu_count = len(menu_df) if not menu_df.empty else 0
        missing_price = 0
        if not menu_df.empty and "판매가" in menu_df.columns:
            missing_price = menu_df["판매가"].isna().sum() + (menu_df["판매가"] == 0).sum()
        
        ing_df = load_csv("ingredient_master.csv", store_id=store_id)
        ing_count = len(ing_df) if not ing_df.empty else 0
        missing_cost = 0
        if not ing_df.empty and "단가" in ing_df.columns:
            missing_cost = ing_df["단가"].isna().sum() + (ing_df["단가"] == 0).sum()
        
        recipe_df = load_csv("recipes.csv", store_id=store_id)
        recipe_ready = 0
        if not menu_df.empty and not recipe_df.empty:
            recipe_ready = len([m for m in menu_df["메뉴명"].unique() if m in recipe_df["메뉴명"].unique()])
        recipe_rate = (recipe_ready / menu_count * 100) if menu_count > 0 else 0
        
        targets_df = load_csv("targets.csv", store_id=store_id)
        has_target = False
        if not targets_df.empty:
            target_row = targets_df[(targets_df["연도"] == current_year_kst()) & (targets_df["월"] == current_month_kst())]
            has_target = not target_row.empty and (target_row.iloc[0].get("목표매출", 0) or 0) > 0
        
        # 비용 목표 체크 (expense_structure 테이블)
        has_cost_target = False
        try:
            expense_df = load_csv("expense_structure.csv", store_id=store_id)
            if not expense_df.empty:
                expense_row = expense_df[(expense_df["연도"] == current_year_kst()) & (expense_df["월"] == current_month_kst())]
                has_cost_target = not expense_row.empty and len(expense_row) > 0
        except Exception:
            # expense_structure.csv가 없거나 로드 실패 시 Supabase에서 직접 조회
            try:
                from src.storage_supabase import get_read_client
                supabase = get_read_client()
                if supabase:
                    expense_res = supabase.table("expense_structure").select("id").eq("store_id", store_id).eq("year", current_year_kst()).eq("month", current_month_kst()).limit(1).execute()
                    has_cost_target = expense_res.data and len(expense_res.data) > 0
            except Exception:
                pass
        
        # 재고 안전재고 설정 비율 체크
        # 총 재료 중 안전재고를 설정한 재료의 비율로 판단
        inventory_safety_rate = 0
        try:
            inventory_df = load_csv("inventory.csv", store_id=store_id)
            if not inventory_df.empty and ing_count > 0:
                # 안전재고가 설정된 재료 수 (안전재고 > 0)
                if "안전재고" in inventory_df.columns:
                    safety_set_count = (inventory_df["안전재고"] > 0).sum()
                else:
                    # Supabase에서 직접 조회
                    try:
                        supabase = get_read_client()
                        if supabase:
                            inventory_res = supabase.table("inventory").select("ingredient_id").eq("store_id", store_id).gt("safety_stock", 0).execute()
                            safety_set_count = len(inventory_res.data) if inventory_res.data else 0
                    except Exception:
                        safety_set_count = 0
                inventory_safety_rate = (safety_set_count / ing_count * 100) if ing_count > 0 else 0
        except Exception:
            # inventory.csv가 없거나 로드 실패 시 Supabase에서 직접 조회
            try:
                supabase = get_read_client()
                if supabase:
                    # 총 재료 수
                    ing_res = supabase.table("ingredients").select("id").eq("store_id", store_id).execute()
                    total_ing_count = len(ing_res.data) if ing_res.data else ing_count
                    
                    # 안전재고가 설정된 재료 수
                    inventory_res = supabase.table("inventory").select("ingredient_id").eq("store_id", store_id).gt("safety_stock", 0).execute()
                    safety_set_count = len(inventory_res.data) if inventory_res.data else 0
                    
                    inventory_safety_rate = (safety_set_count / total_ing_count * 100) if total_ing_count > 0 else 0
            except Exception:
                pass
                
        return {
            "menu_count": menu_count, "missing_price": int(missing_price),
            "ing_count": ing_count, "missing_cost": int(missing_cost),
            "recipe_rate": recipe_rate, "has_target": has_target,
            "has_cost_target": has_cost_target, "inventory_safety_rate": inventory_safety_rate
        }
    except Exception: return {"menu_count": 0, "missing_price": 0, "ing_count": 0, "missing_cost": 0, "recipe_rate": 0, "has_target": False, "has_cost_target": False, "inventory_safety_rate": 0}

def _hub_status_card(title: str, value: str, sub: str, status: str = "pending", delay_class: str = ""):
    bg = "rgba(30, 41, 59, 0.5)"
    border = "rgba(148, 163, 184, 0.1)"
    glow = ""
    if status == "completed": 
        border = "rgba(16, 185, 129, 0.3)"
        text_color = "#10B981"
    elif status == "warning": 
        border = "rgba(245, 158, 11, 0.4)"
        text_color = "#F59E0B"
        glow = "box-shadow: 0 0 15px rgba(245, 158, 11, 0.1);"
    else:
        text_color = "#94A3B8"
    
    # backdrop-filter는 토글로 옵션화
    blur_style = ""
    if st.session_state.get("_ps_fx_blur_on", False):
        blur_style = "backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);"
    else:
        blur_style = "background: rgba(30, 41, 59, 0.6);"  # 배경색으로 대체

    st.markdown(f"""
    <div class="animate-in {delay_class}" style="padding: 1.5rem; background: {bg}; border-radius: 16px; border: 1px solid {border}; {glow} {blur_style} min-height: 150px; transition: all 0.3s ease; position: relative; overflow: hidden;">
        <div style="font-size: 0.8rem; font-weight: 600; color: #94A3B8; margin-bottom: 1rem; letter-spacing: 0.05em;">{title.upper()}</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: {text_color}; margin-bottom: 0.5rem;">{value}</div>
        <div style="font-size: 0.85rem; color: #64748B; line-height: 1.4;">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def _hub_asset_card(title: str, value: str, icon: str, delay_class: str = ""):
    card_style = "padding: 1.2rem; background: rgba(30, 41, 59, 0.4); border-radius: 14px; border: 1px solid rgba(255, 255, 255, 0.05); display: flex; align-items: center; gap: 1rem; min-height: 100px; transition: transform 0.2s ease;"
    title_style = "font-size: 0.75rem; color: #94A3B8; font-weight: 500; margin-bottom: 0.3rem; letter-spacing: 0.02em;"
    value_style = "font-size: 1.2rem; font-weight: 700; color: #F8FAFC; line-height: 1.2;"
    html_content = f"""
    <div class="animate-in {delay_class}" style="{card_style}">
        <div style="font-size: 2rem; background: rgba(59, 130, 246, 0.1); width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; border-radius: 10px;">{icon}</div>
        <div style="display: flex; flex-direction: column; justify-content: center;">
            <div style="{title_style}">{title}</div>
            <div style="{value_style}">{value}</div>
        </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

def render_input_hub_v3():
    """
    데이터 입력 센터 페이지 렌더링 (v5 - Control Board 구조)
    
    역할: 외식업 사장용 운영 OS의 Control Board (조종석)
    
    구조:
    - ZONE 0: 데이터 자산 가이드 (헌법 영역 - 절대 유지)
    - ZONE 1: System Snapshot (초압축 시스템 진단)
    - ZONE 2: INPUT CONTROL BOARD (3개 레이어 입력 모듈)
      - 구조 데이터 (설계 레이어): 메뉴, 재료, 레시피, 재고
      - 운영 데이터 (기록 레이어): 일일 마감, QSC, 월간 정산
      - 기준 데이터 (판단 레이어): 매출 목표, 비용 목표
    - ZONE 3: System Panels (접힘 영역 - 상세 현황)
    
    정체성: 입력 페이지 모음 ❌ → 시스템 조종석 ✅
    """
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다."); return

    # Ultra Premium CSS 주입 (1회만)
    inject_input_hub_ultra_premium_css()
    
    # 애니메이션 CSS 주입 (1회만)
    inject_input_hub_animations_css()
    
    # Control Board 컴팩트 레이아웃 CSS 주입 (1회만) - 헤더 스타일 포함
    inject_input_hub_controlboard_compact_css()
    
    # 프리미엄 레이어드 카드 스타일 헤더 렌더링 (CSS 직접 주입 + 간단한 HTML)
    header_css = """
    <style>
    #ps-input-hub-header {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px !important;
        padding: 0 !important;
        margin-bottom: 2rem !important;
        margin-top: 0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1), 0 0 20px rgba(59, 130, 246, 0.15) !important;
        overflow: hidden !important;
        position: relative !important;
    }
    #ps-header-neon-bar {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 6px !important;
        background: linear-gradient(90deg, transparent 0%, rgba(59, 130, 246, 0.6) 20%, rgba(96, 165, 250, 0.9) 50%, rgba(59, 130, 246, 0.6) 80%, transparent 100%) !important;
        z-index: 1 !important;
    }
    #ps-header-content {
        padding: 1.8rem 2rem 1.5rem 2rem !important;
        position: relative !important;
        z-index: 2 !important;
    }
    #ps-header-title-row {
        display: flex !important;
        align-items: center !important;
        gap: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    #ps-header-icon {
        font-size: 2.2rem !important;
        filter: drop-shadow(0 0 8px rgba(96, 165, 250, 0.5)) !important;
        line-height: 1 !important;
    }
    #ps-header-title {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #F8FAFC !important;
        margin: 0 !important;
        letter-spacing: -0.02em !important;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3) !important;
        line-height: 1.2 !important;
    }
    #ps-header-subtitle {
        font-size: 0.9rem !important;
        color: #94A3B8 !important;
        margin: 0 !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
        margin-left: 3.2rem !important;
    }
    #ps-header-divider {
        height: 4px !important;
        width: 60px !important;
        background: linear-gradient(90deg, #3B82F6 0%, transparent 100%) !important;
        border-radius: 2px !important;
        margin-top: 1.2rem !important;
        margin-left: 3.2rem !important;
    }
    </style>
    """
    st.markdown(header_css, unsafe_allow_html=True)
    
    st.markdown("""
    <div id="ps-input-hub-header" data-ps-scope="input_hub">
        <div id="ps-header-neon-bar"></div>
        <div id="ps-header-content">
            <div id="ps-header-title-row">
                <div id="ps-header-icon">✍</div>
                <h1 id="ps-header-title">데이터 입력 센터</h1>
            </div>
            <div id="ps-header-subtitle">매장 운영 OS 조종석</div>
            <div id="ps-header-divider"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 개발모드에서만 DB CLIENT MODE 표시 (기존 기능 유지)
    try:
        from src.storage_supabase import get_client_mode
        from src.auth import is_dev_mode
        
        if is_dev_mode():
            client_mode = get_client_mode()
            if client_mode == "service_role_dev":
                st.info(f"🔧 **DB CLIENT MODE: service_role_dev** (DEV MODE 전용, RLS 우회)")
            elif client_mode == "anon":
                st.caption(f"🔧 **DB CLIENT MODE: anon** (일반 모드)")
            else:
                st.caption(f"🔧 **DB CLIENT MODE: {client_mode}**")
    except Exception:
        pass  # 표시 실패해도 페이지는 계속 동작
    
    # 시작 필요 상태 강조 JavaScript 제거 (애니메이션만 제거, 스타일은 Python에서 처리)
    # 애니메이션 관련 JavaScript 코드 완전 제거
    
    # 컨텐츠 wrapper 시작
    st.markdown('<div data-ps-scope="input_hub" class="ps-hub-bg"><div class="ps-hub-content">', unsafe_allow_html=True)

    # 데이터 로드
    recs = _get_today_recommendations(store_id)
    assets = _get_asset_readiness(store_id)
    
    # 오늘 마감 여부 확인
    today = today_kst()
    today_status = get_day_record_status(store_id, today)
    has_daily_close = today_status.get("has_close", False)

    # 디지털 성숙도 점수 계산
    score = 0
    if assets.get('menu_count', 0) > 0 and assets.get('missing_price', 0) == 0: score += 25
    if assets.get('ing_count', 0) > 0 and assets.get('missing_cost', 0) == 0: score += 25
    if assets.get('recipe_rate', 0) >= 80: score += 25
    if assets.get('has_target'): score += 25
    
    # 시스템 진단
    system_stage = detect_system_stage(assets, has_daily_close)
    bottleneck = detect_system_bottleneck(assets, has_daily_close, system_stage)
    recommendation = get_system_recommendation(bottleneck, assets)

    # ============================================================
    # ZONE 0: 데이터 자산 가이드 (헌법 영역 - 절대 유지)
    # ============================================================
    # 이 블록은 입력센터의 정체성을 선언하는 헌법 영역입니다.
    # 크기/스타일/위치를 절대 변경하지 않습니다.
    status_color = "#10B981" if score == 100 else "#3B82F6"
    
    guide_html = f"""
<div class="guide-card-animated" style="padding: 1.8rem; background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.2); margin-bottom: 2.5rem; box-shadow: 0 10px 25px rgba(0,0,0,0.4); position: relative; overflow: hidden;">
    <div class="shimmer-overlay"></div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; position: relative;">
        <div>
            <h4 style="margin: 0 0 0.6rem 0; color: #F8FAFC; font-size: 1.2rem; font-weight: 700;">💡 데이터 자산 가이드</h4>
            <p style="margin: 0; color: #94A3B8; font-size: 0.95rem; line-height: 1.6;">
                이 앱은 '감'이 아니라 데이터 자산으로 매장을 운영하게 만듭니다.<br>
                아래 항목들이 채워질수록, 매장 운영이 시스템이 됩니다.
            </p>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.3rem; font-weight: 600;">MATURITY LEVEL</div>
            <div style="color: #3B82F6; font-weight: 800; font-size: 2rem; line-height: 1;">{score}<span style="font-size: 1rem; margin-left: 2px;">%</span></div>
        </div>
    </div>
    <div style="background-color: rgba(255,255,255,0.05); border-radius: 20px; height: 12px; margin-bottom: 1.2rem; overflow: hidden; border: 1px solid rgba(255,255,255,0.05); position: relative;">
        <div style="background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%); width: {score}%; height: 100%; border-radius: 20px; box-shadow: 0 0 10px rgba(59, 130, 246, 0.4); position: relative; overflow: hidden;">
            <div style="position: absolute; top: 0; left: 0; width: 200%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); animation: wave-move 2s infinite linear;"></div>
        </div>
    </div>
    <div style="display: flex; align-items: center; gap: 0.5rem; position: relative;">
        <div style="width: 8px; height: 8px; border-radius: 50%; background: {status_color}; animation: pulse-ring 2s infinite;"></div>
        <p style="margin: 0; color: {status_color}; font-size: 0.85rem; font-weight: 600; letter-spacing: 0.02em;">
            🚩 비어 있는 데이터를 채우면 정밀 리포트/전략 기능이 단계적으로 열립니다.<br>
            입력은 일이 아니라, 매장의 운영 시스템을 만드는 과정입니다.
        </p>
    </div>
    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(148, 163, 184, 0.1);">
        <p style="margin: 0; color: #94A3B8; font-size: 0.85rem; font-style: italic;">
            아래 패널들은 현재 매장이 보유한 '데이터 자산' 상태입니다.
        </p>
    </div>
</div>"""
    st.markdown(guide_html, unsafe_allow_html=True)

    # ============================================================
    # ZONE 1: System Snapshot (초압축 시스템 진단) - 사장 언어 버전
    # ============================================================
    # 할 일 목록이 아니라 매장 운영 상태판입니다.
    # 사장이 이해하기 쉬운 언어로 현재 상태, 막히는 것, 다음 행동만 표시합니다.
    st.markdown("### 🧠 매장 운영 상태")
    st.markdown("<div style='margin-bottom: 0.3rem;'></div>", unsafe_allow_html=True)
    
    # 시스템이 못하는 것 계산 (사장 언어)
    system_blocked = []
    if not has_daily_close:
        system_blocked.append("매출 흐름 파악")
    if assets.get('recipe_rate', 0) < 80:
        system_blocked.append("메뉴별 수익 확인")
        system_blocked.append("전략 수립")
    elif not assets.get('has_target'):
        system_blocked.append("전략 수립")
    
    stage_level = system_stage.get("level", 1)
    stage_name = system_stage.get("name", "기록 단계")
    bn_msg = bottleneck.get("message", "병목 없음") if bottleneck.get("bottleneck") else "병목 없음"
    blocked_text_full = ", ".join(system_blocked) if system_blocked else "없음 (모든 기능 활성화)"
    primary = recommendation.get("primary")
    
    # 사장 언어로 단계/병목 변환
    stage_display = {
        1: "기록 시작 단계",
        2: "구조 정리 단계",
        3: "수익 분석 단계",
        4: "전략 운영 단계"
    }.get(stage_level, f"단계 {stage_level}")
    
    # 병목 메시지를 사장 언어로 변환
    bn_display = bn_msg
    if "일일 마감" in bn_msg or "마감" in bn_msg:
        bn_display = "오늘 매장 기록이 없습니다"
    elif "레시피" in bn_msg:
        bn_display = "레시피 정리가 부족합니다"
    elif "메뉴" in bn_msg:
        bn_display = "메뉴 정보가 부족합니다"
    elif "재료" in bn_msg:
        bn_display = "재료 정보가 부족합니다"
    elif "목표" in bn_msg:
        bn_display = "이번 달 목표가 없습니다"
    
    # 잠김 기능 요약 (사장 언어, 최대 3개만 노출)
    blocked_display = []
    if system_blocked:
        blocked_display = system_blocked[:3]
        if len(system_blocked) > 3:
            blocked_display.append(f"외 {len(system_blocked) - 3}개")
        blocked_summary = " · ".join(blocked_display)
    else:
        blocked_summary = "없음"
    
    # 기본 카드 (압축형 - 사장 언어)
    snapshot_html = f"""
    <div class="animate-in delay-1" style="padding: 0.8rem 1rem; background: rgba(30, 41, 59, 0.6); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.3); margin-bottom: 0.8rem;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-bottom: 0.6rem;">
            <div>
                <div style="font-size: 0.7rem; color: #94A3B8; margin-bottom: 0.2rem; font-weight: 600; letter-spacing: 0.05em;">현재 상태</div>
                <div style="font-size: 0.85rem; font-weight: 700; color: #3B82F6;">{stage_display}</div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #94A3B8; margin-bottom: 0.2rem; font-weight: 600; letter-spacing: 0.05em;">지금 막히는 것</div>
                <div style="font-size: 0.85rem; font-weight: 700; color: #F59E0B;">{bn_display}</div>
            </div>
        </div>
        <div style="font-size: 0.75rem; color: #94A3B8; line-height: 1.3;">
            사용 불가: {blocked_summary}
        </div>
    </div>
    """
    st.markdown(snapshot_html, unsafe_allow_html=True)
    
    # 상세 정보 expander (사장 언어)
    with st.expander("자세히 보기", expanded=False):
        st.markdown("**현재 매장 운영 상태**")
        st.markdown(f"{stage_display}")
        st.markdown("---")
        
        st.markdown("**지금 막히는 것**")
        st.markdown(f"{bn_display}")
        st.markdown("---")
        
        st.markdown("**지금 사용할 수 없는 기능**")
        st.markdown(f"{blocked_text_full}")
        
        if primary:
            next_step_text = primary.get('description', '')
            if next_step_text:
                st.markdown("---")
                st.markdown("**다음 행동**")
                st.markdown(next_step_text)
    
    # PRIMARY ACTION 버튼 (항상 보완 기준)
    if primary:
        button_text = primary.get('button_text', '이동')
        # 버튼 텍스트를 보완 기준으로 변경
        if "입력" in button_text:
            button_text = button_text.replace("입력", "보완")
        elif "등록" in button_text:
            button_text = button_text.replace("등록", "보완")
        elif "설정" in button_text:
            button_text = button_text.replace("설정", "보완")
        
        if st.button(button_text, use_container_width=True, type="primary", key="btn_primary_action"):
            st.session_state.current_page = primary.get('page_key', '홈')
            st.rerun()
    
    st.markdown('<div class="ps-layer-section"></div>', unsafe_allow_html=True)

    # ============================================================
    # ZONE 2: DATA ASSET CONTROL BOARD (페이지 본체)
    # ============================================================
    # 데이터 자산 구축 현황판입니다.
    # 3개 자산 패널로 구성: 구조 자산 → 운영 기록 자산 → 판단 기준 자산
    st.markdown("## 🕹 DATA ASSET CONTROL BOARD")
    st.markdown("**매장 데이터 자산 구축 현황판**")
    st.markdown("아래 항목들은 모두 '매장을 시스템으로 만드는 데이터 자산'입니다.")
    st.markdown('<div class="ps-layer-section"></div>', unsafe_allow_html=True)
    
    # 최근 입력일 조회
    last_close_date = "기록 없음"
    try:
        supabase = get_read_client()
        if supabase:
            close_res = supabase.table("daily_close").select("date").eq("store_id", store_id).order("date", desc=True).limit(1).execute()
            if close_res.data:
                last_close_date = close_res.data[0]["date"][:10]
    except Exception:
        pass
    
    r1 = next((r for r in recs if r["priority"] == 1), {"status": "pending", "summary": "확인 불가"})
    r4 = next((r for r in recs if r["priority"] == 4), {"status": "pending", "summary": "확인 불가"})
    r5 = next((r for r in recs if r["priority"] == 5), {"status": "pending", "summary": "확인 불가"})
    
    # ────────────────────────────────────────────────────────────
    # A. 🧱 매장 구조 자산 패널
    # ────────────────────────────────────────────────────────────
    # 매장의 구조를 정의하는 데이터 자산입니다.
    st.markdown("""
    <h3 class="ps-layer-title">
        🧱 매장 구조 자산
        <span style="
            font-size: 0.7rem;
            font-weight: 400;
            color: #64748B;
            margin-left: 0.5rem;
        ">(메뉴·재료·레시피)</span>
    </h3>
    """, unsafe_allow_html=True)
    
    # 구조 자산 전체 요약 상태 계산 (운영 가능 기준)
    # '존재'가 아니라 '운영 가능' 기준으로 판단
    menu_operable = assets.get('menu_count', 0) > 0 and assets.get('missing_price', 0) == 0
    ing_operable = assets.get('ing_count', 0) > 0 and assets.get('missing_cost', 0) == 0
    recipe_operable = assets.get('recipe_rate', 0) >= 80
    
    if menu_operable and ing_operable and recipe_operable:
        struct_summary = "구조 자산: 정상 운영 중"
        struct_summary_color = "#10B981"
    elif (assets.get('menu_count', 0) > 0 or assets.get('ing_count', 0) > 0) and assets.get('recipe_rate', 0) > 0:
        struct_summary = "구조 자산: 부분 운영 가능 / 레시피 정리 필요"
        struct_summary_color = "#F59E0B"
    elif assets.get('menu_count', 0) > 0 or assets.get('ing_count', 0) > 0:
        struct_summary = "구조 자산: 보완 필요 / 메뉴와 재료 정보 보완 필요"
        struct_summary_color = "#F59E0B"
    else:
        struct_summary = "구조 자산: 시작 필요 / 메뉴와 재료부터 시작하세요"
        struct_summary_color = "#F59E0B"  # 회색 → 주황색으로 변경
    
    # 구조 자산 진행률 계산 (운영 가능 기준, MATURITY LEVEL 연결)
    # 재고는 선택 입력이므로 게이지에 반영하지 않음 (정보만 표시)
    struct_score = 0
    if menu_operable: struct_score += 33
    if ing_operable: struct_score += 33
    if recipe_operable: struct_score += 34
    
    # 게이지 0%일 때 특별 처리
    if struct_score == 0:
        gauge_text = "시작 필요"
        gauge_color = "#F59E0B"
    else:
        gauge_text = f"{struct_score}%"
        gauge_color = struct_summary_color
    
    # 구조 자산 진행률 상세 정보 계산
    struct_completed = sum([menu_operable, ing_operable, recipe_operable])
    struct_total = 3
    struct_remaining = struct_total - struct_completed
    if struct_remaining > 0:
        struct_progress_html = f'<div style="font-size: 0.8rem; color: #F59E0B; margin-top: 0.5rem;">⚠️ {struct_remaining}개 항목 남음</div>'
    else:
        struct_progress_html = '<div style="font-size: 0.8rem; color: #10B981; margin-top: 0.5rem;">✅ 모든 항목 완료!</div>'
    
    # 구조 자산 게이지 HTML을 문자열 연결로 구성
    struct_gauge_html = f'<div style="padding: 0.8rem 1rem; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border-left: 3px solid {struct_summary_color}; margin-bottom: 1rem;">'
    struct_gauge_html += f'<div style="font-size: 0.9rem; color: {struct_summary_color}; font-weight: 600; margin-bottom: 0.5rem;">{struct_summary}</div>'
    struct_gauge_html += '<div style="display: flex; align-items: center; gap: 0.8rem;">'
    struct_gauge_html += '<div style="font-size: 0.75rem; color: #94A3B8;">구조 자산</div>'
    struct_gauge_html += f'<div style="flex: 1; background: rgba(255,255,255,0.05); border-radius: 4px; height: 6px; overflow: hidden;">'
    struct_gauge_html += f'<div style="background: linear-gradient(90deg, {gauge_color} 0%, {gauge_color} 100%); width: {max(struct_score, 5)}%; height: 100%;"></div>'
    struct_gauge_html += '</div>'
    struct_gauge_html += f'<div style="font-size: 0.75rem; color: {gauge_color}; font-weight: 600;">{gauge_text}</div>'
    struct_gauge_html += '</div>'
    struct_gauge_html += struct_progress_html
    struct_gauge_html += '</div>'
    st.markdown(struct_gauge_html, unsafe_allow_html=True)
    
    # 하위 항목 상태 스트립 (4개) - 운영 체감 언어 + 색상
    # '구축됨'이 아니라 '운영 가능' 기준
    if menu_operable:
        menu_status_text = "정상 운영"
        menu_status_color = "#10B981"
        menu_card_class = ""
    elif assets.get('menu_count', 0) > 0:
        menu_status_text = "보완 필요"
        menu_status_color = "#F59E0B"
        menu_card_class = ""
    else:
        menu_status_text = "🚨 지금 시작하세요"
        menu_status_color = "#F59E0B"
        menu_card_class = "ps-start-needed-card"
    
    if ing_operable:
        ing_status_text = "정상 운영"
        ing_status_color = "#10B981"
        ing_card_class = ""
    elif assets.get('ing_count', 0) > 0:
        ing_status_text = "보완 필요"
        ing_status_color = "#F59E0B"
        ing_card_class = ""
    else:
        ing_status_text = "🚨 지금 시작하세요"
        ing_status_color = "#F59E0B"
        ing_card_class = "ps-start-needed-card"
    
    # 레시피 운영 체감 언어 + 색상
    recipe_rate = assets.get('recipe_rate', 0)
    if recipe_rate >= 80:
        recipe_status_text = "정상 운영"
        recipe_status_color = "#10B981"
        recipe_card_class = ""
    elif recipe_rate > 0:
        recipe_status_text = f"보완 필요 ({recipe_rate:.0f}%)"
        recipe_status_color = "#F59E0B"
        recipe_card_class = ""
    else:
        recipe_status_text = "🚨 지금 시작하세요"
        recipe_status_color = "#F59E0B"
        recipe_card_class = "ps-start-needed-card"
    
    # 재고 안전재고 설정 비율 운영 체감 언어 + 색상
    inventory_safety_rate = assets.get('inventory_safety_rate', 0)
    if inventory_safety_rate >= 80:
        inventory_status_text = "정상 운영"
        inventory_status_color = "#10B981"
        inventory_card_class = ""
    elif inventory_safety_rate > 0:
        inventory_status_text = f"보완 필요 ({inventory_safety_rate:.0f}%)"
        inventory_status_color = "#F59E0B"
        inventory_card_class = ""
    else:
        inventory_status_text = "🚨 지금 시작하세요"
        inventory_status_color = "#F59E0B"
        inventory_card_class = "ps-start-needed-card"
    
    # 시작 필요 카드는 기본 스타일은 유지하되 애니메이션을 위해 data 속성 추가 (Streamlit이 클래스를 제거할 수 있으므로)
    menu_card_style = "padding: 0.6rem; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border: 2px solid rgba(245, 158, 11, 0.6);" if menu_card_class else f"padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);"
    ing_card_style = "padding: 0.6rem; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border: 2px solid rgba(245, 158, 11, 0.6);" if ing_card_class else f"padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);"
    recipe_card_style = "padding: 0.6rem; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border: 2px solid rgba(245, 158, 11, 0.6);" if recipe_card_class else f"padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);"
    inventory_card_style = "padding: 0.6rem; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border: 2px solid rgba(245, 158, 11, 0.6);" if inventory_card_class else f"padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);"
    
    # data 속성 추가
    menu_card_data = 'data-ps-start-needed="true"' if menu_card_class else ''
    ing_card_data = 'data-ps-start-needed="true"' if ing_card_class else ''
    recipe_card_data = 'data-ps-start-needed="true"' if recipe_card_class else ''
    inventory_card_data = 'data-ps-start-needed="true"' if inventory_card_class else ''
    
    # STEP 배지 추가 (시작 필요 항목에만)
    menu_step_badge = '<div style="display: inline-block; background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); color: white; font-size: 0.65rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 10px; margin-bottom: 0.3rem; box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);">STEP 1</div>' if menu_card_class else ""
    ing_step_badge = '<div style="display: inline-block; background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); color: white; font-size: 0.65rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 10px; margin-bottom: 0.3rem; box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);">STEP 2</div>' if ing_card_class else ""
    recipe_step_badge = '<div style="display: inline-block; background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); color: white; font-size: 0.65rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 10px; margin-bottom: 0.3rem; box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);">STEP 3</div>' if recipe_card_class else ""
    inventory_step_badge = '<div style="display: inline-block; background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); color: white; font-size: 0.65rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 10px; margin-bottom: 0.3rem; box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);">STEP 4</div>' if inventory_card_class else ""
    
    # HTML을 문자열 연결로 구성 (f-string 문제 회피)
    cards_html = f'<div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 0.6rem; margin-bottom: 1rem;">'
    cards_html += f'<div class="{menu_card_class}" {menu_card_data} style="{menu_card_style}">'
    cards_html += menu_step_badge
    cards_html += f'<div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">📘 메뉴</div>'
    cards_html += f'<div style="font-size: 0.85rem; font-weight: 600; color: {menu_status_color};">{menu_status_text}</div>'
    cards_html += f'<div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{assets.get("menu_count", 0)}개</div>'
    cards_html += '</div>'
    cards_html += f'<div class="{ing_card_class}" {ing_card_data} style="{ing_card_style}">'
    cards_html += ing_step_badge
    cards_html += f'<div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">🧺 재료</div>'
    cards_html += f'<div style="font-size: 0.85rem; font-weight: 600; color: {ing_status_color};">{ing_status_text}</div>'
    cards_html += f'<div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{assets.get("ing_count", 0)}개</div>'
    cards_html += '</div>'
    cards_html += f'<div class="{recipe_card_class}" {recipe_card_data} style="{recipe_card_style}">'
    cards_html += recipe_step_badge
    cards_html += f'<div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">🍳 레시피</div>'
    cards_html += f'<div style="font-size: 0.85rem; font-weight: 600; color: {recipe_status_color};">{recipe_status_text}</div>'
    cards_html += f'<div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">완성도 {recipe_rate:.0f}%</div>'
    cards_html += '</div>'
    cards_html += f'<div class="{inventory_card_class}" {inventory_card_data} style="{inventory_card_style}">'
    cards_html += inventory_step_badge
    cards_html += f'<div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">📦 재고</div>'
    cards_html += f'<div style="font-size: 0.85rem; font-weight: 600; color: {inventory_status_color};">{inventory_status_text}</div>'
    cards_html += f'<div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">안전재고 {inventory_safety_rate:.0f}%</div>'
    cards_html += '</div>'
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)
    
    # 시작 필요 항목 체크 (경고 배너용)
    has_start_needed_struct = (assets.get('menu_count', 0) == 0 or 
                               assets.get('ing_count', 0) == 0 or 
                               recipe_rate == 0)
    
    # 경고 배너 표시 (시작 필요 항목이 있을 때)
    if has_start_needed_struct:
        start_needed_items = []
        if assets.get('menu_count', 0) == 0:
            start_needed_items.append("메뉴")
        if assets.get('ing_count', 0) == 0:
            start_needed_items.append("재료")
        if recipe_rate == 0:
            start_needed_items.append("레시피")
        
        items_text = ", ".join(start_needed_items)
        st.markdown(f"""
        <div style="padding: 0.8rem; background: rgba(245, 158, 11, 0.15); 
                    border-left: 4px solid #F59E0B; border-radius: 8px; 
                    margin-bottom: 1rem;">
            <div style="font-weight: 600; color: #F59E0B; margin-bottom: 0.3rem;">
                ⚠️ {items_text}이(가) 없어서 수익 분석을 사용할 수 없습니다
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8;">
                아래 버튼을 눌러 지금 시작하면 메뉴 수익 구조 분석이 활성화됩니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ACTION ZONE: 콘솔 영역 (항상 보완 기준으로 노출)
    st.markdown('<div class="ps-action-bar-wrapper"></div>', unsafe_allow_html=True)
    struct_btn_cols = st.columns(4)
    with struct_btn_cols[0]:
        # 메뉴 입력 버튼
        if assets.get('menu_count', 0) == 0:
            button_text = "🚀 메뉴 지금 시작"
            button_class = "ps-start-needed-button"
        else:
            button_text = "📘 메뉴 보완"
            button_class = ""
        if st.button(button_text, use_container_width=True, type="primary", key="btn_asset_menu"):
            st.session_state.current_page = "메뉴 입력"
            st.rerun()
    with struct_btn_cols[1]:
        # 재료 입력 버튼
        if assets.get('ing_count', 0) == 0:
            button_text = "🚀 재료 지금 시작"
            button_class = "ps-start-needed-button"
        else:
            button_text = "🧺 재료 보완"
            button_class = ""
        if st.button(button_text, use_container_width=True, type="primary", key="btn_asset_ing"):
            st.session_state.current_page = "재료 입력"
            st.rerun()
    with struct_btn_cols[2]:
        # 레시피 입력 버튼
        if recipe_rate == 0:
            button_text = "🚀 레시피 지금 시작"
            button_class = "ps-start-needed-button"
        else:
            button_text = "🍳 레시피 보완"
            button_class = ""
        if st.button(button_text, use_container_width=True, type="primary", key="btn_asset_recipe"):
            st.session_state.current_page = "레시피 등록"
            st.rerun()
    with struct_btn_cols[3]:
        # 재고 입력 버튼 (선택)
        if st.button("📦 재고 보완", use_container_width=True, type="primary", key="btn_asset_inv"):
            st.session_state.current_page = "재고 입력"
            st.rerun()
    
    st.markdown('<div class="ps-layer-section"></div>', unsafe_allow_html=True)
    
    # ────────────────────────────────────────────────────────────
    # B. 📒 운영 기록 자산 패널
    # ────────────────────────────────────────────────────────────
    # 매장의 일상 기록 데이터 자산입니다.
    st.markdown("""
    <h3 class="ps-layer-title">
        📒 운영 기록 자산
        <span style="
            font-size: 0.7rem;
            font-weight: 400;
            color: #64748B;
            margin-left: 0.5rem;
        ">(일일 마감·QSC·정산)</span>
    </h3>
    """, unsafe_allow_html=True)
    
    # 운영 기록 자산 중심 문구
    if has_daily_close:
        op_main_msg = "어제까지 기록 유지 중"
        op_main_color = "#10B981"
        op_sub_msg = f"최근 기록: {last_close_date}" if last_close_date != "기록 없음" else "오늘 기록 완료"
    else:
        op_main_msg = "오늘 매장 기록이 없습니다"
        op_main_color = "#F59E0B"
        op_sub_msg = last_close_date if last_close_date != "기록 없음" else "기록 없음"
    
    # 운영 기록 자산 진행률 계산
    op_score = 0
    if has_daily_close: op_score += 40
    if r4["status"] == "completed": op_score += 30
    if r5["status"] == "completed": op_score += 30
    
    # 게이지 0%일 때 특별 처리
    if op_score == 0:
        op_gauge_text = "시작 필요"
        op_gauge_color = "#F59E0B"
    else:
        op_gauge_text = f"{op_score}%"
        op_gauge_color = op_main_color
    
    # 운영 기록 자산 진행률 상세 정보 계산
    op_completed = sum([has_daily_close, r4["status"] == "completed", r5["status"] == "completed"])
    op_total = 3
    op_remaining = op_total - op_completed
    if op_remaining > 0:
        op_progress_html = f'<div style="font-size: 0.8rem; color: #F59E0B; margin-top: 0.5rem;">⚠️ {op_remaining}개 항목 남음</div>'
    else:
        op_progress_html = '<div style="font-size: 0.8rem; color: #10B981; margin-top: 0.5rem;">✅ 모든 항목 완료!</div>'
    
    # 운영 기록 자산 게이지 HTML을 문자열 연결로 구성
    op_gauge_html = f'<div style="padding: 1rem 1.2rem; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border-left: 3px solid {op_main_color}; margin-bottom: 1rem;">'
    op_gauge_html += f'<div style="font-size: 1rem; color: {op_main_color}; font-weight: 700; margin-bottom: 0.5rem;">{op_main_msg}</div>'
    op_gauge_html += f'<div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.8rem;">{op_sub_msg}</div>'
    op_gauge_html += '<div style="display: flex; align-items: center; gap: 0.8rem;">'
    op_gauge_html += '<div style="font-size: 0.75rem; color: #94A3B8;">운영 기록</div>'
    op_gauge_html += '<div style="flex: 1; background: rgba(255,255,255,0.05); border-radius: 4px; height: 6px; overflow: hidden;">'
    op_gauge_html += f'<div style="background: linear-gradient(90deg, {op_gauge_color} 0%, {op_gauge_color} 100%); width: {max(op_score, 5)}%; height: 100%;"></div>'
    op_gauge_html += '</div>'
    op_gauge_html += f'<div style="font-size: 0.75rem; color: {op_gauge_color}; font-weight: 600;">{op_gauge_text}</div>'
    op_gauge_html += '</div>'
    op_gauge_html += op_progress_html
    op_gauge_html += '</div>'
    st.markdown(op_gauge_html, unsafe_allow_html=True)
    
    # 하위 항목 상태 스트립 (3개) - 운영 체감 언어 + 색상
    if has_daily_close:
        daily_status_text = "정상 운영"
        daily_status_color = "#10B981"
        daily_card_class = ""
    else:
        daily_status_text = "🚨 지금 시작하세요"
        daily_status_color = "#F59E0B"
        daily_card_class = "ps-start-needed-card"
    
    if r4["status"] == "completed":
        qsc_status_text = "정상 운영"
        qsc_status_color = "#10B981"
        qsc_card_class = ""
    else:
        qsc_status_text = "보완 필요"
        qsc_status_color = "#F59E0B"
        qsc_card_class = ""
    
    if r5["status"] == "completed":
        settle_status_text = "정상 운영"
        settle_status_color = "#10B981"
        settle_card_class = ""
    else:
        settle_status_text = "보완 필요"
        settle_status_color = "#F59E0B"
        settle_card_class = ""
    
    # 시작 필요 카드는 기본 스타일은 유지하되 애니메이션을 위해 data 속성 추가
    if daily_card_class:
        # 시작 필요일 때는 기본 스타일 + data 속성 (Streamlit이 클래스를 제거할 수 있으므로)
        daily_card_style = "padding: 0.6rem; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border: 2px solid rgba(245, 158, 11, 0.6);"
        daily_card_data = 'data-ps-start-needed="true"'
        daily_step_badge = '<div style="display: inline-block; background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); color: white; font-size: 0.65rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 10px; margin-bottom: 0.3rem; box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);">STEP 5</div>'
    else:
        daily_card_style = f"padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);"
        daily_card_data = ''
        daily_step_badge = ""
    
    # 운영 기록 카드 HTML을 문자열 연결로 구성
    op_cards_html = f'<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.6rem; margin-bottom: 1rem;">'
    op_cards_html += f'<div class="{daily_card_class}" {daily_card_data} style="{daily_card_style}">'
    op_cards_html += daily_step_badge
    op_cards_html += f'<div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">📝 일일 마감</div>'
    op_cards_html += f'<div style="font-size: 0.85rem; font-weight: 600; color: {daily_status_color};">{daily_status_text}</div>'
    op_cards_html += f'<div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{last_close_date if last_close_date != "기록 없음" else "—"}</div>'
    op_cards_html += '</div>'
    qsc_border = 'rgba(245, 158, 11, 0.6)' if qsc_card_class else 'rgba(148, 163, 184, 0.15)'
    op_cards_html += f'<div class="{qsc_card_class}" style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid {qsc_border};">'
    op_cards_html += f'<div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">🩺 QSC</div>'
    op_cards_html += f'<div style="font-size: 0.85rem; font-weight: 600; color: {qsc_status_color};">{qsc_status_text}</div>'
    op_cards_html += f'<div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{r4["summary"]}</div>'
    op_cards_html += '</div>'
    settle_border = 'rgba(245, 158, 11, 0.6)' if settle_card_class else 'rgba(148, 163, 184, 0.15)'
    op_cards_html += f'<div class="{settle_card_class}" style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid {settle_border};">'
    op_cards_html += f'<div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">📅 월간 정산</div>'
    op_cards_html += f'<div style="font-size: 0.85rem; font-weight: 600; color: {settle_status_color};">{settle_status_text}</div>'
    op_cards_html += f'<div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{r5["summary"]}</div>'
    op_cards_html += '</div>'
    op_cards_html += '</div>'
    st.markdown(op_cards_html, unsafe_allow_html=True)
    
    # 시작 필요 항목 체크 (경고 배너용)
    if not has_daily_close:
        st.markdown("""
        <div style="padding: 0.8rem; background: rgba(245, 158, 11, 0.15); 
                    border-left: 4px solid #F59E0B; border-radius: 8px; 
                    margin-bottom: 1rem;">
            <div style="font-weight: 600; color: #F59E0B; margin-bottom: 0.3rem;">
                ⚠️ 일일 마감이 없어서 매출 흐름을 파악할 수 없습니다
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8;">
                오늘 매장 기록을 시작하면 매출 추이 분석이 가능합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ACTION ZONE: 콘솔 영역 (항상 보완 기준으로 노출)
    st.markdown('<div class="ps-action-bar-wrapper"></div>', unsafe_allow_html=True)
    op_btn_cols = st.columns(3)
    with op_btn_cols[0]:
        # 일일 마감 버튼
        if not has_daily_close:
            button_text = "🚀 오늘 기록 지금 시작"
            button_class = "ps-start-needed-button"
        else:
            button_text = "📝 오늘 매장 기록"
            button_class = ""
        if st.button(button_text, use_container_width=True, type="primary", key="btn_asset_daily"):
            st.session_state.current_page = "일일 입력(통합)"
            st.rerun()
    with op_btn_cols[1]:
        if st.button("🩺 운영 점검 보완", use_container_width=True, type="primary", key="btn_asset_qsc"):
            st.session_state.current_page = "건강검진 실시"
            st.rerun()
    with op_btn_cols[2]:
        if st.button("📅 월간 정산 보완", use_container_width=True, type="primary", key="btn_asset_settle"):
            st.session_state.current_page = "실제정산"
            st.rerun()
    
    st.markdown('<div class="ps-layer-section"></div>', unsafe_allow_html=True)
    
    # ────────────────────────────────────────────────────────────
    # C. 🎯 판단 기준 자산 패널
    # ────────────────────────────────────────────────────────────
    # 분석과 AI의 기준선 데이터 자산입니다.
    st.markdown("""
    <h3 class="ps-layer-title">
        🎯 판단 기준 자산
        <span style="
            font-size: 0.7rem;
            font-weight: 400;
            color: #64748B;
            margin-left: 0.5rem;
        ">(매출 목표·비용 목표)</span>
    </h3>
    """, unsafe_allow_html=True)
    
    # 판단 기준 자산 중심 문구 (운영 체감 언어)
    if assets.get('has_target'):
        target_main_msg = "이번 달 목표 설정 완료"
        target_main_color = "#10B981"
        target_sub_msg = f"{current_month_kst()}월 기준 정상 운영 중"
    else:
        target_main_msg = "이번 달 목표가 없습니다"
        target_main_color = "#F59E0B"
        target_sub_msg = "목표를 설정하면 전략 수립이 가능합니다"
    
    # 판단 기준 자산 진행률 계산 (운영 가능 기준)
    # 매출 목표와 비용 목표 모두 반영
    target_score = 0
    if assets.get('has_target'): target_score += 50
    if assets.get('has_cost_target'): target_score += 50
    
    # 게이지 0%일 때 특별 처리
    if target_score == 0:
        target_gauge_text = "시작 필요"
        target_gauge_color = "#F59E0B"
    else:
        target_gauge_text = f"{target_score}%"
        target_gauge_color = target_main_color
    
    # 판단 기준 자산 진행률 상세 정보 계산
    target_completed = sum([assets.get('has_target', False), assets.get('has_cost_target', False)])
    target_total = 2
    target_remaining = target_total - target_completed
    if target_remaining > 0:
        target_progress_html = f'<div style="font-size: 0.8rem; color: #F59E0B; margin-top: 0.5rem;">⚠️ {target_remaining}개 항목 남음</div>'
    else:
        target_progress_html = '<div style="font-size: 0.8rem; color: #10B981; margin-top: 0.5rem;">✅ 모든 항목 완료!</div>'
    
    # 판단 기준 자산 게이지 HTML을 문자열 연결로 구성
    target_gauge_html = f'<div style="padding: 1rem 1.2rem; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border-left: 3px solid {target_main_color}; margin-bottom: 1rem;">'
    target_gauge_html += f'<div style="font-size: 1rem; color: {target_main_color}; font-weight: 700; margin-bottom: 0.5rem;">{target_main_msg}</div>'
    target_gauge_html += f'<div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.8rem;">{target_sub_msg}</div>'
    target_gauge_html += '<div style="display: flex; align-items: center; gap: 0.8rem;">'
    target_gauge_html += '<div style="font-size: 0.75rem; color: #94A3B8;">판단 기준</div>'
    target_gauge_html += '<div style="flex: 1; background: rgba(255,255,255,0.05); border-radius: 4px; height: 6px; overflow: hidden;">'
    target_gauge_html += f'<div style="background: linear-gradient(90deg, {target_gauge_color} 0%, {target_gauge_color} 100%); width: {max(target_score, 5)}%; height: 100%;"></div>'
    target_gauge_html += '</div>'
    target_gauge_html += f'<div style="font-size: 0.75rem; color: {target_gauge_color}; font-weight: 600;">{target_gauge_text}</div>'
    target_gauge_html += '</div>'
    target_gauge_html += target_progress_html
    target_gauge_html += '</div>'
    st.markdown(target_gauge_html, unsafe_allow_html=True)
    
    # 하위 항목 상태 스트립 (2개) - 운영 체감 언어 + 색상
    if assets.get('has_target'):
        target_status_text = "정상 운영"
        target_status_color = "#10B981"
        target_card_class = ""
    else:
        target_status_text = "🚨 지금 시작하세요"
        target_status_color = "#F59E0B"
        target_card_class = "ps-start-needed-card"
    
    if assets.get('has_cost_target'):
        cost_target_status_text = "정상 운영"
        cost_target_color = "#10B981"
        cost_target_card_class = ""
    else:
        cost_target_status_text = "🚨 지금 시작하세요"
        cost_target_color = "#F59E0B"
        cost_target_card_class = "ps-start-needed-card"
    
    # 시작 필요 카드는 기본 스타일은 유지하되 애니메이션을 위해 data 속성 추가 (Streamlit이 클래스를 제거할 수 있으므로)
    target_card_style = "padding: 0.6rem; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border: 2px solid rgba(245, 158, 11, 0.6);" if target_card_class else f"padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);"
    cost_target_card_style = "padding: 0.6rem; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border: 2px solid rgba(245, 158, 11, 0.6);" if cost_target_card_class else f"padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);"
    
    # data 속성 추가
    target_card_data = 'data-ps-start-needed="true"' if target_card_class else ''
    cost_target_card_data = 'data-ps-start-needed="true"' if cost_target_card_class else ''
    
    # STEP 배지 추가 (시작 필요 항목에만)
    target_step_badge = '<div style="display: inline-block; background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); color: white; font-size: 0.65rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 10px; margin-bottom: 0.3rem; box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);">STEP 6</div>' if target_card_class else ""
    cost_target_step_badge = '<div style="display: inline-block; background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); color: white; font-size: 0.65rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 10px; margin-bottom: 0.3rem; box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);">STEP 6</div>' if cost_target_card_class else ""
    
    # 목표 카드 HTML을 문자열 연결로 구성
    target_cards_html = f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; margin-bottom: 1rem;">'
    target_cards_html += f'<div class="{target_card_class}" {target_card_data} style="{target_card_style}">'
    target_cards_html += target_step_badge
    target_cards_html += f'<div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">🎯 매출 목표</div>'
    target_cards_html += f'<div style="font-size: 0.85rem; font-weight: 600; color: {target_status_color};">{target_status_text}</div>'
    target_cards_html += f'<div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{current_month_kst()}월</div>'
    target_cards_html += '</div>'
    target_cards_html += f'<div class="{cost_target_card_class}" {cost_target_card_data} style="{cost_target_card_style}">'
    target_cards_html += cost_target_step_badge
    target_cards_html += f'<div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">🧾 비용 목표</div>'
    target_cards_html += f'<div style="font-size: 0.85rem; font-weight: 600; color: {cost_target_color};">{cost_target_status_text}</div>'
    target_cards_html += f'<div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{current_month_kst()}월</div>'
    target_cards_html += '</div>'
    target_cards_html += '</div>'
    st.markdown(target_cards_html, unsafe_allow_html=True)
    
    # 시작 필요 항목 체크 (경고 배너용)
    if not assets.get('has_target') or not assets.get('has_cost_target'):
        missing_targets = []
        if not assets.get('has_target'):
            missing_targets.append("매출 목표")
        if not assets.get('has_cost_target'):
            missing_targets.append("비용 목표")
        targets_text = ", ".join(missing_targets)
        st.markdown(f"""
        <div style="padding: 0.8rem; background: rgba(245, 158, 11, 0.15); 
                    border-left: 4px solid #F59E0B; border-radius: 8px; 
                    margin-bottom: 1rem;">
            <div style="font-weight: 600; color: #F59E0B; margin-bottom: 0.3rem;">
                ⚠️ {targets_text}이(가) 없어서 전략 수립을 사용할 수 없습니다
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8;">
                목표를 설정하면 목표 대비 성과 분석과 전략 보드가 활성화됩니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ACTION ZONE: 콘솔 영역 (항상 보완 기준으로 노출)
    st.markdown('<div class="ps-action-bar-wrapper"></div>', unsafe_allow_html=True)
    target_btn_cols = st.columns(2)
    with target_btn_cols[0]:
        # 매출 목표 버튼
        if not assets.get('has_target'):
            button_text = "🚀 목표 지금 시작"
            button_class = "ps-start-needed-button"
        else:
            button_text = "🎯 이번 달 목표 보완"
            button_class = ""
        if st.button(button_text, use_container_width=True, type="primary", key="btn_asset_target"):
            st.session_state.current_page = "목표 매출구조"
            st.rerun()
    with target_btn_cols[1]:
        # 비용 목표 버튼
        if not assets.get('has_cost_target'):
            button_text = "🚀 비용 기준 지금 시작"
            button_class = "ps-start-needed-button"
        else:
            button_text = "🧾 비용 기준 보완"
            button_class = ""
        if st.button(button_text, use_container_width=True, type="primary", key="btn_asset_cost"):
            st.session_state.current_page = "목표 비용구조"
            st.rerun()
    
    st.markdown('<div class="ps-layer-section"></div>', unsafe_allow_html=True)
    
    # ============================================================
    # ZONE 3: 매장 데이터 지도 (System Map)
    # ============================================================
    # 현재 매장이 어떤 데이터 자산을 가지고 있고,
    # 어디가 비어 있는지 한눈에 보여주는 지도입니다.
    st.markdown('<div class="ps-system-panels"></div>', unsafe_allow_html=True)
    st.markdown("### 🗺️ 매장 데이터 지도")
    st.caption("현재 매장이 어떤 데이터 자산을 가지고 있고, 어디가 비어 있는지 한눈에 보여주는 지도입니다.")
    
    # 데이터 지도 카드 (4개) - 축소형
    data_map_cols = st.columns(4)
    
    with data_map_cols[0]:
        close_map_status = "정상 운영" if has_daily_close else "시작 필요"
        close_map_color = "#10B981" if has_daily_close else "#64748B"
        st.markdown(f"""
        <div style="padding: 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid {close_map_color}40; min-height: 90px;">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.4rem;">일별 운영</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: {close_map_color}; margin-bottom: 0.3rem;">{close_map_status}</div>
            <div style="font-size: 0.7rem; color: #64748B;">{last_close_date if last_close_date != "기록 없음" else "—"}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with data_map_cols[1]:
        if r4["status"] == "completed":
            qsc_map_status = "정상 운영"
            qsc_map_color = "#10B981"
        else:
            qsc_map_status = "보완 필요"
            qsc_map_color = "#F59E0B"
        st.markdown(f"""
        <div style="padding: 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid {qsc_map_color}40; min-height: 90px;">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.4rem;">운영 점검</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: {qsc_map_color}; margin-bottom: 0.3rem;">{qsc_map_status}</div>
            <div style="font-size: 0.7rem; color: #64748B;">{r4["summary"][:15]}...</div>
        </div>
        """, unsafe_allow_html=True)
    
    with data_map_cols[2]:
        # 운영 가능 기준: 메뉴와 재료가 모두 있고 가격/단가가 모두 있으면 정상 운영
        structure_operable = (assets.get('menu_count', 0) > 0 and assets.get('missing_price', 0) == 0 and 
                             assets.get('ing_count', 0) > 0 and assets.get('missing_cost', 0) == 0)
        if structure_operable:
            structure_map_status = "정상 운영"
            structure_map_color = "#10B981"
        else:
            structure_map_status = "보완 필요"
            structure_map_color = "#F59E0B"
        st.markdown(f"""
        <div style="padding: 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid {structure_map_color}40; min-height: 90px;">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.4rem;">구조 데이터</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: {structure_map_color}; margin-bottom: 0.3rem;">{structure_map_status}</div>
            <div style="font-size: 0.7rem; color: #64748B;">메뉴 {assets.get('menu_count', 0)} / 재료 {assets.get('ing_count', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with data_map_cols[3]:
        target_map_status = "정상 운영" if assets.get('has_target') else "시작 필요"
        target_map_color = "#10B981" if assets.get('has_target') else "#64748B"
        st.markdown(f"""
        <div style="padding: 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid {target_map_color}40; min-height: 90px;">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.4rem;">기준 데이터</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: {target_map_color}; margin-bottom: 0.3rem;">{target_map_status}</div>
            <div style="font-size: 0.7rem; color: #64748B;">{current_month_kst()}월</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 과거 데이터 구축 (축소형) - 보완 기준
    st.markdown("### 🧮 과거 데이터 보완")
    past_cols = st.columns(2)
    with past_cols[0]:
        if st.button("🧮 매출/방문자 보완", use_container_width=True, type="primary", key="btn_panel_bulk_sales"):
            st.session_state.current_page = "매출 등록"
            st.rerun()
    with past_cols[1]:
        if st.button("📦 판매량 보완", use_container_width=True, type="primary", key="btn_panel_bulk_qty"):
            st.session_state.current_page = "판매량 등록"
            st.rerun()
    
    # 컨텐츠 wrapper 종료
    st.markdown('</div></div>', unsafe_allow_html=True)
