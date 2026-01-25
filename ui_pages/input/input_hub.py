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
</div>"""
    st.markdown(guide_html, unsafe_allow_html=True)

    # ============================================================
    # ZONE 1: System Snapshot (초압축 시스템 진단)
    # ============================================================
    # 할 일 목록이 아니라 시스템 상태판입니다.
    # 현재 단계, 병목, 못하는 것, PRIMARY ACTION만 표시합니다.
    st.markdown("### 🧠 시스템 진단 요약")
    
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
    blocked_text = ", ".join(system_blocked) if system_blocked else "없음 (모든 기능 활성화)"
    primary = recommendation.get("primary")
    
    snapshot_html = f"""
    <div class="animate-in delay-1" style="padding: 1.5rem; background: rgba(30, 41, 59, 0.6); border-radius: 14px; border: 1px solid rgba(59, 130, 246, 0.3); margin-bottom: 2rem;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
            <div>
                <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem; font-weight: 600; letter-spacing: 0.05em;">현재 시스템 단계</div>
                <div style="font-size: 1rem; font-weight: 700; color: #3B82F6;">LEVEL {stage_level} — {stage_name}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem; font-weight: 600; letter-spacing: 0.05em;">시스템 병목</div>
                <div style="font-size: 1rem; font-weight: 700; color: #F59E0B;">{bn_msg}</div>
            </div>
        </div>
        <div style="margin-bottom: 1rem; padding-top: 1rem; border-top: 1px solid rgba(148, 163, 184, 0.1);">
            <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.3rem; font-weight: 600; letter-spacing: 0.05em;">지금 시스템이 못하는 것</div>
            <div style="font-size: 0.9rem; color: #E2E8F0;">{blocked_text}</div>
        </div>
    </div>
    """
    st.markdown(snapshot_html, unsafe_allow_html=True)
    
    # PRIMARY ACTION 버튼
    if primary:
        if st.button(primary.get('button_text', '이동'), use_container_width=True, type="primary", key="btn_primary_action"):
            st.session_state.current_page = primary.get('page_key', '홈')
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # ZONE 2: INPUT CONTROL BOARD (페이지 본체)
    # ============================================================
    # 입력센터의 핵심 영역입니다.
    # 모든 입력 네비게이션이 여기서 이루어집니다.
    # 3개 레이어로 구성: 구조 데이터 → 운영 데이터 → 기준 데이터
    st.markdown("## 🕹 INPUT CONTROL BOARD")
    st.markdown("**매장을 시스템으로 만드는 입력 모듈**")
    st.markdown("<br>", unsafe_allow_html=True)
    
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
    # 1️⃣ 구조 데이터 (설계 레이어)
    # ────────────────────────────────────────────────────────────
    # 매장의 구조를 정의하는 데이터입니다.
    # 환경설정 / 시스템 설계 톤으로 유지합니다.
    st.markdown("### 🏗 구조 데이터 (설계 레이어)")
    struct_cols = st.columns(4)
    
    with struct_cols[0]:
        menu_status = "✅ 있음" if assets.get('menu_count', 0) > 0 and assets.get('missing_price', 0) == 0 else ("⚠️ 미완성" if assets.get('menu_count', 0) > 0 else "❌ 없음")
        menu_value = f"{assets.get('menu_count', 0)}개" + (f" ({assets.get('missing_price')}개 가격 누락)" if assets.get('missing_price', 0) > 0 else "")
        st.markdown(f"""
        <div style="padding: 1.2rem; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">📘 메뉴 구조</div>
            <div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.3rem; font-weight: 600;">{menu_status}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.8rem;">{menu_value}</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 1rem; line-height: 1.4;">→ 없으면 메뉴 수익 구조 분석 불가</div>
        </div>
        """, unsafe_allow_html=True)
        btn_type = "primary" if assets.get('missing_price', 0) > 0 or assets.get('menu_count', 0) == 0 else "secondary"
        if st.button("📘 메뉴 입력", use_container_width=True, type=btn_type, key="btn_control_menu"):
            st.session_state.current_page = "메뉴 입력"
            st.rerun()
    
    with struct_cols[1]:
        ing_status = "✅ 있음" if assets.get('ing_count', 0) > 0 and assets.get('missing_cost', 0) == 0 else ("⚠️ 미완성" if assets.get('ing_count', 0) > 0 else "❌ 없음")
        ing_value = f"{assets.get('ing_count', 0)}개" + (f" ({assets.get('missing_cost')}개 단가 누락)" if assets.get('missing_cost', 0) > 0 else "")
        st.markdown(f"""
        <div style="padding: 1.2rem; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🧺 재료 구조</div>
            <div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.3rem; font-weight: 600;">{ing_status}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.8rem;">{ing_value}</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 1rem; line-height: 1.4;">→ 없으면 원가 계산 불가</div>
        </div>
        """, unsafe_allow_html=True)
        btn_type = "primary" if assets.get('missing_cost', 0) > 0 or assets.get('ing_count', 0) == 0 else "secondary"
        if st.button("🧺 재료 입력", use_container_width=True, type=btn_type, key="btn_control_ing"):
            st.session_state.current_page = "재료 입력"
            st.rerun()
    
    with struct_cols[2]:
        recipe_status = "✅ 완성" if assets.get('recipe_rate', 0) >= 80 else ("⚠️ 미완성" if assets.get('recipe_rate', 0) > 0 else "❌ 없음")
        recipe_value = f"{assets.get('recipe_rate', 0):.0f}%"
        st.markdown(f"""
        <div style="padding: 1.2rem; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🍳 레시피 구조</div>
            <div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.3rem; font-weight: 600;">{recipe_status}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.8rem;">완성도 {recipe_value}</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 1rem; line-height: 1.4;">→ 없으면 메뉴 수익성 분석 불가</div>
        </div>
        """, unsafe_allow_html=True)
        btn_type = "primary" if assets.get('recipe_rate', 0) < 80 else "secondary"
        if st.button("🍳 레시피 입력", use_container_width=True, type=btn_type, key="btn_control_recipe"):
            st.session_state.current_page = "레시피 등록"
            st.rerun()
    
    with struct_cols[3]:
        st.markdown(f"""
        <div style="padding: 1.2rem; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">📦 재고 구조</div>
            <div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.3rem; font-weight: 600;">⏳ 선택 입력</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.8rem;">재고 관리용</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 1rem; line-height: 1.4;">→ 없으면 발주 최적화 분석 불가</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📦 재고 입력", use_container_width=True, type="secondary", key="btn_control_inv"):
            st.session_state.current_page = "재고 입력"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ⚡ 운영 데이터 (기록 레이어)
    st.markdown("### ⚡ 운영 데이터 (기록 레이어)")
    op_cols = st.columns(3)
    
    with op_cols[0]:
        daily_status = "✅ 오늘 기록 있음" if has_daily_close else "❌ 오늘 기록 없음"
        daily_value = f"최근: {last_close_date}" if last_close_date != "기록 없음" else "기록 없음"
        st.markdown(f"""
        <div style="padding: 1.2rem; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">📝 일일 마감</div>
            <div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.3rem; font-weight: 600;">{daily_status}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.8rem;">{daily_value}</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 1rem; line-height: 1.4;">→ 없으면 매출 추이 분석 불가</div>
        </div>
        """, unsafe_allow_html=True)
        btn_type = "primary" if not has_daily_close else "secondary"
        if st.button("📝 오늘 마감 입력", use_container_width=True, type=btn_type, key="btn_control_daily"):
            st.session_state.current_page = "일일 입력(통합)"
            st.rerun()
    
    with op_cols[1]:
        qsc_status = "✅ 완료" if r4["status"] == "completed" else "⏳ 권장"
        qsc_value = r4["summary"]
        st.markdown(f"""
        <div style="padding: 1.2rem; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🩺 QSC</div>
            <div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.3rem; font-weight: 600;">{qsc_status}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.8rem;">{qsc_value}</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 1rem; line-height: 1.4;">→ 없으면 운영 품질 모니터링 불가</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🩺 QSC 입력", use_container_width=True, type="secondary", key="btn_control_qsc"):
            st.session_state.current_page = "건강검진 실시"
            st.rerun()
    
    with op_cols[2]:
        settle_status = "✅ 완료" if r5["status"] == "completed" else "⏸️ 대기"
        settle_value = r5["summary"]
        st.markdown(f"""
        <div style="padding: 1.2rem; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">📅 월간 정산</div>
            <div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.3rem; font-weight: 600;">{settle_status}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.8rem;">{settle_value}</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 1rem; line-height: 1.4;">→ 없으면 목표 대비 성과 분석 불가</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📅 월간 정산 입력", use_container_width=True, type="secondary", key="btn_control_settle"):
            st.session_state.current_page = "실제정산"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ────────────────────────────────────────────────────────────
    # 3️⃣ 기준 데이터 (판단 레이어)
    # ────────────────────────────────────────────────────────────
    # 분석과 AI의 기준선 데이터입니다.
    # AI 판단 기준 세팅 톤으로 유지합니다.
    st.markdown("### 🎯 기준 데이터 (판단 레이어)")
    target_cols = st.columns(2)
    
    with target_cols[0]:
        target_status = "✅ 설정됨" if assets.get('has_target') else "⚠️ 미설정"
        target_value = f"{current_month_kst()}월" if assets.get('has_target') else "미설정"
        st.markdown(f"""
        <div style="padding: 1.2rem; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🎯 매출 목표</div>
            <div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.3rem; font-weight: 600;">{target_status}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.8rem;">{target_value}</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 1rem; line-height: 1.4;">→ 없으면 전략 보드 비활성</div>
        </div>
        """, unsafe_allow_html=True)
        btn_type = "primary" if not assets.get('has_target') else "secondary"
        if st.button("🎯 목표 입력", use_container_width=True, type=btn_type, key="btn_control_target"):
            st.session_state.current_page = "목표 매출구조"
            st.rerun()
    
    with target_cols[1]:
        st.markdown(f"""
        <div style="padding: 1.2rem; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.2); margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🧾 비용 목표</div>
            <div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.3rem; font-weight: 600;">⏳ 선택 입력</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.8rem;">비용 최적화용</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 1rem; line-height: 1.4;">→ 없으면 비용 최적화 분석 불가</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🧾 비용 목표 입력", use_container_width=True, type="secondary", key="btn_control_cost"):
            st.session_state.current_page = "목표 비용구조"
            st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # ============================================================
    # ZONE 3: System Panels (접힘 영역)
    # ============================================================
    # 고급 사용자용 상세 현황입니다.
    # 기본은 접힘 상태로 유지합니다.
    with st.expander("⚫ System Panels (상세 현황)"):
        # 우리 매장 데이터 지도
        st.markdown("### 📊 우리 매장 데이터 지도")
        st.caption("데이터 종류별로 현재 보유 현황을 확인하세요.")
        
        data_map_cols = st.columns(4)
        with data_map_cols[0]:
            close_status = "✅ 보유" if has_daily_close else "❌ 없음"
            close_summary = f"최근: {last_close_date}" if last_close_date != "기록 없음" else "기록 없음"
            _hub_status_card("일별 운영 데이터", close_status, close_summary, "completed" if has_daily_close else "warning", "delay-1")
            if st.button("📝 일일 마감 입력", use_container_width=True, key="btn_panel_daily", type="primary" if not has_daily_close else "secondary"):
                st.session_state.current_page = "일일 입력(통합)"
                st.rerun()
        
        with data_map_cols[1]:
            qsc_status = "✅ 보유" if r4["status"] == "completed" else "⏳ 권장"
            _hub_status_card("운영 점검 데이터", qsc_status, r4["summary"], "completed" if r4["status"] == "completed" else "pending", "delay-2")
            if st.button("🩺 QSC 입력", use_container_width=True, key="btn_panel_qsc"):
                st.session_state.current_page = "건강검진 실시"
                st.rerun()
        
        with data_map_cols[2]:
            structure_status = "✅ 구축됨" if (assets.get('menu_count', 0) > 0 and assets.get('ing_count', 0) > 0) else "❌ 미구축"
            structure_summary = f"메뉴 {assets.get('menu_count', 0)}개 / 재료 {assets.get('ing_count', 0)}개"
            _hub_status_card("구조 데이터", structure_status, structure_summary, "completed" if structure_status == "✅ 구축됨" else "warning", "delay-3")
            if st.button("📘 메뉴/재료 입력", use_container_width=True, key="btn_panel_structure", type="primary" if structure_status != "✅ 구축됨" else "secondary"):
                st.session_state.current_page = "메뉴 입력"
                st.rerun()
        
        with data_map_cols[3]:
            target_status = "✅ 설정됨" if assets.get('has_target') else "❌ 미설정"
            target_summary = f"{current_month_kst()}월" if assets.get('has_target') else "미설정"
            _hub_status_card("기준 데이터", target_status, target_summary, "completed" if assets.get('has_target') else "pending", "delay-4")
            if st.button("🎯 목표 입력", use_container_width=True, key="btn_panel_target", type="primary" if not assets.get('has_target') else "secondary"):
                st.session_state.current_page = "목표 매출구조"
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 데이터 자산 완성도 상세
        st.markdown("### 🏗️ 데이터 자산 완성도 상세")
        st.caption("각 데이터 자산의 완성도와 목적을 확인하세요.")
        a1, a2, a3, a4 = st.columns(4)
        with a1: 
            _hub_asset_card("등록 메뉴", f"{assets.get('menu_count', 0)}개", "📘", "delay-1")
            if assets.get('missing_price', 0) > 0: 
                st.markdown(f"<p class='animate-in delay-2' style='color: #F59E0B; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem; font-weight: 600;'>⚠️ {assets.get('missing_price')}개 가격 누락</p>", unsafe_allow_html=True)
            else: 
                st.markdown("<p class='animate-in delay-2' style='color: #10B981; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem;'>✅ 등록 완료</p>", unsafe_allow_html=True)
        with a2: 
            _hub_asset_card("등록 재료", f"{assets.get('ing_count', 0)}개", "🧺", "delay-2")
            if assets.get('missing_cost', 0) > 0: 
                st.markdown(f"<p class='animate-in delay-3' style='color: #F59E0B; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem; font-weight: 600;'>⚠️ {assets.get('missing_cost')}개 단가 누락</p>", unsafe_allow_html=True)
            else: 
                st.markdown("<p class='animate-in delay-3' style='color: #10B981; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem;'>✅ 등록 완료</p>", unsafe_allow_html=True)
        with a3: 
            _hub_asset_card("레시피 완성도", f"{assets.get('recipe_rate', 0):.0f}%", "🍳", "delay-3")
            if assets.get('recipe_rate', 0) < 80: 
                st.markdown("<p class='animate-in delay-4' style='color: #94A3B8; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem;'>⏳ 80% 달성 권장</p>", unsafe_allow_html=True)
            else: 
                st.markdown("<p class='animate-in delay-4' style='color: #10B981; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem;'>✅ 정밀 분석 가능</p>", unsafe_allow_html=True)
        with a4: 
            goal_status = "✅ 설정 완료" if assets.get('has_target') else "❌ 미설정"
            _hub_asset_card("이번 달 목표", goal_status, "🎯", "delay-4")
            if not assets.get('has_target'): 
                st.markdown("<p class='animate-in delay-4' style='color: #F59E0B; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem; font-weight: 600;'>⚠️ 목표 설정 필요</p>", unsafe_allow_html=True)
            else: 
                st.markdown("<p class='animate-in delay-4' style='color: #10B981; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem;'>✅ 분석 중</p>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 과거 데이터 구축
        st.markdown("### 🧮 과거 데이터 구축")
        st.caption("과거 데이터를 일괄 입력할 때 사용합니다.")
        past_cols = st.columns(2)
        with past_cols[0]:
            if st.button("🧮 매출/방문자 입력", use_container_width=True, key="btn_panel_bulk_sales"):
                st.session_state.current_page = "매출 등록"
                st.rerun()
        with past_cols[1]:
            if st.button("📦 판매량 입력", use_container_width=True, key="btn_panel_bulk_qty"):
                st.session_state.current_page = "판매량 등록"
                st.rerun()
    
    # 컨텐츠 wrapper 종료
    st.markdown('</div></div>', unsafe_allow_html=True)
