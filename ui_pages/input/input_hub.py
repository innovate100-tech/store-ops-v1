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
    <style>
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
    
    /* prefers-reduced-motion 지원 */
    @media (prefers-reduced-motion: reduce) {
        [data-ps-scope="input_hub"] *,
        .guide-card-animated,
        .animate-in,
        .shimmer-overlay {
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
                
        return {
            "menu_count": menu_count, "missing_price": int(missing_price),
            "ing_count": ing_count, "missing_cost": int(missing_cost),
            "recipe_rate": recipe_rate, "has_target": has_target
        }
    except Exception: return {"menu_count": 0, "missing_price": 0, "ing_count": 0, "missing_cost": 0, "recipe_rate": 0, "has_target": False}

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
    render_page_header("✍ 데이터 입력 센터", "✍")
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다."); return

    # Ultra Premium CSS 주입 (1회만)
    inject_input_hub_ultra_premium_css()
    
    # 애니메이션 CSS 주입 (1회만)
    inject_input_hub_animations_css()
    
    # Control Board 컴팩트 레이아웃 CSS 주입 (1회만)
    inject_input_hub_controlboard_compact_css()
    
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
    # ZONE 1: System Snapshot (초압축 시스템 진단)
    # ============================================================
    # 할 일 목록이 아니라 시스템 상태판입니다.
    # 현재 단계, 병목, 못하는 것, PRIMARY ACTION만 표시합니다.
    st.markdown("### 🧠 시스템 진단 요약")
    st.markdown("<div style='margin-bottom: 0.3rem;'></div>", unsafe_allow_html=True)
    
    # 시스템이 못하는 것 계산
    system_blocked = []
    if not has_daily_close:
        system_blocked.append("매출 추이 분석")
    if assets.get('recipe_rate', 0) < 80:
        system_blocked.append("메뉴 수익성 분석")
        system_blocked.append("전략 보드")
    elif not assets.get('has_target'):
        system_blocked.append("전략 보드")
    
    stage_level = system_stage.get("level", 1)
    stage_name = system_stage.get("name", "기록 단계")
    bn_msg = bottleneck.get("message", "병목 없음") if bottleneck.get("bottleneck") else "병목 없음"
    blocked_text_full = ", ".join(system_blocked) if system_blocked else "없음 (모든 기능 활성화)"
    primary = recommendation.get("primary")
    
    # 잠김 기능 요약 (최대 3개만 노출, 나머지는 "+N")
    blocked_display = []
    if system_blocked:
        blocked_display = system_blocked[:3]
        if len(system_blocked) > 3:
            blocked_display.append(f"+{len(system_blocked) - 3}")
        blocked_summary = " · ".join(blocked_display)
    else:
        blocked_summary = "없음"
    
    # 1줄 요약 생성
    summary_line = f"LEVEL {stage_level} · {bn_msg} → {blocked_summary}"
    
    # 기본 카드 (압축형 - 35~45% 높이 감소)
    snapshot_html = f"""
    <div class="animate-in delay-1" style="padding: 0.8rem 1rem; background: rgba(30, 41, 59, 0.6); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.3); margin-bottom: 0.8rem;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-bottom: 0.6rem;">
            <div>
                <div style="font-size: 0.7rem; color: #94A3B8; margin-bottom: 0.2rem; font-weight: 600; letter-spacing: 0.05em;">현재 단계</div>
                <div style="font-size: 0.85rem; font-weight: 700; color: #3B82F6;">LEVEL {stage_level} · {stage_name}</div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #94A3B8; margin-bottom: 0.2rem; font-weight: 600; letter-spacing: 0.05em;">병목</div>
                <div style="font-size: 0.85rem; font-weight: 700; color: #F59E0B;">{bn_msg}</div>
            </div>
        </div>
        <div style="font-size: 0.75rem; color: #94A3B8; line-height: 1.3;">
            잠김: {blocked_summary}
        </div>
    </div>
    """
    st.markdown(snapshot_html, unsafe_allow_html=True)
    
    # 상세 정보 expander
    with st.expander("자세히 보기", expanded=False):
        st.markdown("**현재 시스템 단계**")
        st.markdown(f"LEVEL {stage_level} — {stage_name}")
        st.markdown("---")
        
        st.markdown("**시스템 병목**")
        st.markdown(f"{bn_msg}")
        st.markdown("---")
        
        st.markdown("**지금 시스템이 못하는 것**")
        st.markdown(f"{blocked_text_full}")
        
        if primary:
            next_step_text = primary.get('description', '')
            if next_step_text:
                st.markdown("---")
                st.markdown("**다음 단계**")
                st.markdown(next_step_text)
    
    # PRIMARY ACTION 버튼
    if primary:
        if st.button(primary.get('button_text', '이동'), use_container_width=True, type="primary", key="btn_primary_action"):
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
    st.markdown('<h3 class="ps-layer-title">🧱 매장 구조 자산</h3>', unsafe_allow_html=True)
    
    # 구조 자산 전체 요약 상태 계산
    menu_ready = assets.get('menu_count', 0) > 0 and assets.get('missing_price', 0) == 0
    ing_ready = assets.get('ing_count', 0) > 0 and assets.get('missing_cost', 0) == 0
    recipe_ready = assets.get('recipe_rate', 0) >= 80
    
    if menu_ready and ing_ready and recipe_ready:
        struct_summary = "구조 자산: 기본 틀은 구축됨"
        struct_summary_color = "#10B981"
    elif (assets.get('menu_count', 0) > 0 or assets.get('ing_count', 0) > 0) and assets.get('recipe_rate', 0) > 0:
        struct_summary = "구조 자산: 기본 틀은 있음 / 레시피 정리가 부족합니다"
        struct_summary_color = "#F59E0B"
    elif assets.get('menu_count', 0) > 0 or assets.get('ing_count', 0) > 0:
        struct_summary = "구조 자산: 일부 있음 / 메뉴와 재료 보완이 필요합니다"
        struct_summary_color = "#F59E0B"
    else:
        struct_summary = "구조 자산: 거의 없음 / 메뉴와 재료부터 구축해야 합니다"
        struct_summary_color = "#64748B"
    
    # 구조 자산 진행률 계산 (MATURITY LEVEL 연결)
    struct_score = 0
    if menu_ready: struct_score += 33
    if ing_ready: struct_score += 33
    if recipe_ready: struct_score += 34
    
    st.markdown(f"""
    <div style="padding: 0.8rem 1rem; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border-left: 3px solid {struct_summary_color}; margin-bottom: 1rem;">
        <div style="font-size: 0.9rem; color: {struct_summary_color}; font-weight: 600; margin-bottom: 0.5rem;">{struct_summary}</div>
        <div style="display: flex; align-items: center; gap: 0.8rem;">
            <div style="font-size: 0.75rem; color: #94A3B8;">구조 자산</div>
            <div style="flex: 1; background: rgba(255,255,255,0.05); border-radius: 4px; height: 6px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, {struct_summary_color} 0%, {struct_summary_color} 100%); width: {struct_score}%; height: 100%;"></div>
            </div>
            <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 600;">{struct_score}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 하위 항목 상태 스트립 (4개) - 의미 번역 포함
    menu_status_text = "구축됨" if menu_ready else ("일부 있음" if assets.get('menu_count', 0) > 0 else "거의 없음")
    ing_status_text = "구축됨" if ing_ready else ("일부 있음" if assets.get('ing_count', 0) > 0 else "거의 없음")
    
    # 레시피 의미 번역
    recipe_rate = assets.get('recipe_rate', 0)
    if recipe_rate >= 80:
        recipe_status_text = "구축됨"
    elif recipe_rate > 0:
        recipe_status_text = f"거의 없음 ({recipe_rate:.0f}%)"
    else:
        recipe_status_text = "비어 있음"
    
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 0.6rem; margin-bottom: 1rem;">
        <div style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">📘 메뉴</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #E2E8F0;">{menu_status_text}</div>
            <div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{assets.get('menu_count', 0)}개</div>
        </div>
        <div style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">🧺 재료</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #E2E8F0;">{ing_status_text}</div>
            <div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{assets.get('ing_count', 0)}개</div>
        </div>
        <div style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">🍳 레시피</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #E2E8F0;">{recipe_status_text}</div>
            <div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">완성도 {recipe_rate:.0f}%</div>
        </div>
        <div style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">📦 재고</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #94A3B8;">관리 중단</div>
            <div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">선택</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ACTION ZONE: 콘솔 영역
    st.markdown('<div class="ps-action-bar-wrapper"></div>', unsafe_allow_html=True)
    struct_btn_cols = st.columns(2)
    with struct_btn_cols[0]:
        btn_type = "primary" if not (menu_ready and ing_ready and recipe_ready) else "secondary"
        if st.button("🧱 구조 자산 보완하기", use_container_width=True, type=btn_type, key="btn_asset_struct"):
            # 가장 우선순위가 높은 항목으로 이동
            if assets.get('missing_price', 0) > 0 or assets.get('menu_count', 0) == 0:
                st.session_state.current_page = "메뉴 입력"
            elif assets.get('missing_cost', 0) > 0 or assets.get('ing_count', 0) == 0:
                st.session_state.current_page = "재료 입력"
            elif assets.get('recipe_rate', 0) < 80:
                st.session_state.current_page = "레시피 등록"
            else:
                st.session_state.current_page = "메뉴 입력"
            st.rerun()
    with struct_btn_cols[1]:
        if assets.get('recipe_rate', 0) < 80:
            if st.button("🍳 레시피 정리 시작", use_container_width=True, type="primary", key="btn_asset_recipe"):
                st.session_state.current_page = "레시피 등록"
                st.rerun()
        else:
            if st.button("📦 재고 관리 시작", use_container_width=True, type="secondary", key="btn_asset_inv"):
                st.session_state.current_page = "재고 입력"
                st.rerun()
    
    st.markdown('<div class="ps-layer-section"></div>', unsafe_allow_html=True)
    
    # ────────────────────────────────────────────────────────────
    # B. 📒 운영 기록 자산 패널
    # ────────────────────────────────────────────────────────────
    # 매장의 일상 기록 데이터 자산입니다.
    st.markdown('<h3 class="ps-layer-title">📒 운영 기록 자산</h3>', unsafe_allow_html=True)
    
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
    
    st.markdown(f"""
    <div style="padding: 1rem 1.2rem; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border-left: 3px solid {op_main_color}; margin-bottom: 1rem;">
        <div style="font-size: 1rem; color: {op_main_color}; font-weight: 700; margin-bottom: 0.5rem;">{op_main_msg}</div>
        <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.8rem;">{op_sub_msg}</div>
        <div style="display: flex; align-items: center; gap: 0.8rem;">
            <div style="font-size: 0.75rem; color: #94A3B8;">운영 기록</div>
            <div style="flex: 1; background: rgba(255,255,255,0.05); border-radius: 4px; height: 6px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, {op_main_color} 0%, {op_main_color} 100%); width: {op_score}%; height: 100%;"></div>
            </div>
            <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 600;">{op_score}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 하위 항목 상태 스트립 (3개)
    daily_status_text = "기록 중" if has_daily_close else "기록 없음"
    qsc_status_text = "기록 중" if r4["status"] == "completed" else "기록 없음"
    settle_status_text = "기록 중" if r5["status"] == "completed" else "기록 없음"
    
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.6rem; margin-bottom: 1rem;">
        <div style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">📝 일일 마감</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #E2E8F0;">{daily_status_text}</div>
            <div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{last_close_date if last_close_date != "기록 없음" else "—"}</div>
        </div>
        <div style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">🩺 QSC</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #E2E8F0;">{qsc_status_text}</div>
            <div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{r4["summary"]}</div>
        </div>
        <div style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">📅 월간 정산</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #E2E8F0;">{settle_status_text}</div>
            <div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{r5["summary"]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 지금 기록이 없으면 무엇이 불가능한지
    if not has_daily_close:
        st.markdown("""
        <div style="padding: 0.6rem; background: rgba(245, 158, 11, 0.1); border-radius: 8px; border-left: 3px solid rgba(245, 158, 11, 0.4); margin-bottom: 1rem;">
            <div style="font-size: 0.75rem; color: #F59E0B; font-weight: 600;">지금 기록이 없으면 매출 추이 분석이 불가능합니다</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ACTION ZONE: 콘솔 영역
    st.markdown('<div class="ps-action-bar-wrapper"></div>', unsafe_allow_html=True)
    op_btn_cols = st.columns(3)
    with op_btn_cols[0]:
        btn_type = "primary" if not has_daily_close else "secondary"
        if st.button("📝 오늘 매장 기록", use_container_width=True, type=btn_type, key="btn_asset_daily"):
            st.session_state.current_page = "일일 입력(통합)"
            st.rerun()
    with op_btn_cols[1]:
        if st.button("🩺 운영 점검 기록", use_container_width=True, type="secondary", key="btn_asset_qsc"):
            st.session_state.current_page = "건강검진 실시"
            st.rerun()
    with op_btn_cols[2]:
        if st.button("📅 월간 정산 기록", use_container_width=True, type="secondary", key="btn_asset_settle"):
            st.session_state.current_page = "실제정산"
            st.rerun()
    
    st.markdown('<div class="ps-layer-section"></div>', unsafe_allow_html=True)
    
    # ────────────────────────────────────────────────────────────
    # C. 🎯 판단 기준 자산 패널
    # ────────────────────────────────────────────────────────────
    # 분석과 AI의 기준선 데이터 자산입니다.
    st.markdown('<h3 class="ps-layer-title">🎯 판단 기준 자산</h3>', unsafe_allow_html=True)
    
    # 판단 기준 자산 중심 문구
    if assets.get('has_target'):
        target_main_msg = "이번 달 판단 기준 있음"
        target_main_color = "#10B981"
        target_sub_msg = f"{current_month_kst()}월 기준 설정됨"
    else:
        target_main_msg = "현재 매장은 '평가 기준' 없이 운영 중입니다"
        target_main_color = "#F59E0B"
        target_sub_msg = "목표를 설정하면 전략 보드가 활성화됩니다"
    
    # 판단 기준 자산 진행률 계산
    target_score = 50 if assets.get('has_target') else 0
    
    st.markdown(f"""
    <div style="padding: 1rem 1.2rem; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border-left: 3px solid {target_main_color}; margin-bottom: 1rem;">
        <div style="font-size: 1rem; color: {target_main_color}; font-weight: 700; margin-bottom: 0.5rem;">{target_main_msg}</div>
        <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.8rem;">{target_sub_msg}</div>
        <div style="display: flex; align-items: center; gap: 0.8rem;">
            <div style="font-size: 0.75rem; color: #94A3B8;">판단 기준</div>
            <div style="flex: 1; background: rgba(255,255,255,0.05); border-radius: 4px; height: 6px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, {target_main_color} 0%, {target_main_color} 100%); width: {target_score}%; height: 100%;"></div>
            </div>
            <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 600;">{target_score}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 하위 항목 상태 스트립 (2개)
    target_status_text = "설정됨" if assets.get('has_target') else "미설정"
    
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; margin-bottom: 1rem;">
        <div style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">🎯 매출 목표</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #E2E8F0;">{target_status_text}</div>
            <div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">{current_month_kst()}월</div>
        </div>
        <div style="padding: 0.6rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.15);">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem;">🧾 비용 목표</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #94A3B8;">관리 중단</div>
            <div style="font-size: 0.7rem; color: #64748B; margin-top: 0.2rem;">선택</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ACTION ZONE: 콘솔 영역
    st.markdown('<div class="ps-action-bar-wrapper"></div>', unsafe_allow_html=True)
    target_btn_cols = st.columns(2)
    with target_btn_cols[0]:
        btn_type = "primary" if not assets.get('has_target') else "secondary"
        if st.button("🎯 이번 달 목표 설정", use_container_width=True, type=btn_type, key="btn_asset_target"):
            st.session_state.current_page = "목표 매출구조"
            st.rerun()
    with target_btn_cols[1]:
        if st.button("🧾 비용 기준 점검", use_container_width=True, type="secondary", key="btn_asset_cost"):
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
        close_map_status = "구축됨" if has_daily_close else "비어 있음"
        close_map_color = "#10B981" if has_daily_close else "#64748B"
        st.markdown(f"""
        <div style="padding: 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid {close_map_color}40; min-height: 90px;">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.4rem;">일별 운영</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: {close_map_color}; margin-bottom: 0.3rem;">{close_map_status}</div>
            <div style="font-size: 0.7rem; color: #64748B;">{last_close_date if last_close_date != "기록 없음" else "—"}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with data_map_cols[1]:
        qsc_map_status = "구축됨" if r4["status"] == "completed" else "비어 있음"
        qsc_map_color = "#10B981" if r4["status"] == "completed" else "#64748B"
        st.markdown(f"""
        <div style="padding: 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid {qsc_map_color}40; min-height: 90px;">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.4rem;">운영 점검</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: {qsc_map_color}; margin-bottom: 0.3rem;">{qsc_map_status}</div>
            <div style="font-size: 0.7rem; color: #64748B;">{r4["summary"][:15]}...</div>
        </div>
        """, unsafe_allow_html=True)
    
    with data_map_cols[2]:
        structure_map_status = "구축됨" if (assets.get('menu_count', 0) > 0 and assets.get('ing_count', 0) > 0) else "비어 있음"
        structure_map_color = "#10B981" if (assets.get('menu_count', 0) > 0 and assets.get('ing_count', 0) > 0) else "#64748B"
        st.markdown(f"""
        <div style="padding: 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid {structure_map_color}40; min-height: 90px;">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.4rem;">구조 데이터</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: {structure_map_color}; margin-bottom: 0.3rem;">{structure_map_status}</div>
            <div style="font-size: 0.7rem; color: #64748B;">메뉴 {assets.get('menu_count', 0)} / 재료 {assets.get('ing_count', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with data_map_cols[3]:
        target_map_status = "구축됨" if assets.get('has_target') else "비어 있음"
        target_map_color = "#10B981" if assets.get('has_target') else "#64748B"
        st.markdown(f"""
        <div style="padding: 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: 8px; border: 1px solid {target_map_color}40; min-height: 90px;">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.4rem;">기준 데이터</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: {target_map_color}; margin-bottom: 0.3rem;">{target_map_status}</div>
            <div style="font-size: 0.7rem; color: #64748B;">{current_month_kst()}월</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 과거 데이터 구축 (축소형)
    st.markdown("### 🧮 과거 데이터 구축")
    past_cols = st.columns(2)
    with past_cols[0]:
        if st.button("🧮 매출/방문자 구축", use_container_width=True, key="btn_panel_bulk_sales"):
            st.session_state.current_page = "매출 등록"
            st.rerun()
    with past_cols[1]:
        if st.button("📦 판매량 구축", use_container_width=True, key="btn_panel_bulk_qty"):
            st.session_state.current_page = "판매량 등록"
            st.rerun()
    
    # 컨텐츠 wrapper 종료
    st.markdown('</div></div>', unsafe_allow_html=True)
