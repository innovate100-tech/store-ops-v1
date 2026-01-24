"""
입력 허브 페이지
입력 관련 모든 페이지로의 네비게이션 허브 (3단계 고도화 버전 - UI/UX 보정안)
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header
from src.auth import get_current_store_id, get_supabase_client, get_read_client
from src.storage_supabase import get_day_record_status, load_actual_settlement_items, load_csv
from src.utils.time_utils import today_kst, current_year_kst, current_month_kst
from datetime import timedelta
import pandas as pd

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

def _hub_status_card(title: str, value: str, sub: str, status: str = "pending"):
    bg = "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"
    border = "rgba(148,163,184,0.3)"
    if status == "completed": border = "rgba(74, 222, 128, 0.5)"
    elif status == "warning": border = "rgba(251, 191, 36, 0.5)"
    st.markdown(f'<div style="padding: 1.2rem; background: {bg}; border-radius: 12px; border: 1px solid {border}; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 1rem; min-height: 140px;"><div style="font-size: 0.85rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.8rem;">{title}</div><div style="font-size: 1.3rem; font-weight: 700; color: #ffffff; margin-bottom: 0.5rem;">{value}</div><div style="font-size: 0.8rem; color: #64748b;">{sub}</div></div>', unsafe_allow_html=True)

def _hub_asset_card(title: str, value: str, icon: str):
    # 경고 문구를 제거하고 디자인을 간결하게 통일 (높이 고정)
    card_style = "padding: 1rem; background-color: #111827; border-radius: 10px; border: 1px solid #374151; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.8rem; min-height: 90px;"
    title_style = "font-size: 0.75rem; color: #9ca3af; font-weight: 500; margin-bottom: 0.2rem;"
    value_style = "font-size: 1.1rem; font-weight: 700; color: #ffffff; line-height: 1;"
    html_content = f'<div style="{card_style}"><div style="font-size: 1.8rem; flex-shrink: 0;">{icon}</div><div style="display: flex; flex-direction: column; justify-content: center; flex-grow: 1;"><div style="{title_style}">{title}</div><div style="{value_style}">{value}</div></div></div>'
    st.markdown(html_content, unsafe_allow_html=True)

def render_input_hub_v2():
    """입력 허브 페이지 렌더링"""
    render_page_header("✍ 입력 허브", "✍")
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다."); return

    # [1] 철학적 가이드 - 입력의 가치 전달
    st.markdown(f'<div style="padding: 1.5rem; background-color: #f1f5f9; border-radius: 12px; border-left: 5px solid #64748b; margin-bottom: 2rem;"><h4 style="margin-top: 0; color: #1e293b; font-size: 1.1rem;">💡 왜 입력이 중요한가요?</h4><p style="margin-bottom: 0; color: #475569; font-size: 0.95rem; line-height: 1.6;">입력은 단순한 기록이 아니라, 사장님의 매장을 숫자로 바꾸는 <b>\'설계도\'</b>를 그리는 과정입니다.<br>정밀하게 입력된 기초 데이터는 <b>수익 분석, 원가 진단, 오늘의 전략</b>을 만드는 유일한 기반이 됩니다.</p></div>', unsafe_allow_html=True)

    recs = _get_today_recommendations(store_id)
    assets = _get_asset_readiness(store_id)
    
    # [2] 관제 보드
    st.markdown("### 📊 입력 관제 보드")
    st.caption("매장의 핵심 운영 데이터 입력 상태를 실시간으로 확인합니다.")
    c1, c2, c3 = st.columns(3)
    r1 = next((r for r in recs if r["priority"] == 1), {"status": "pending", "summary": "확인 불가"})
    r4 = next((r for r in recs if r["priority"] == 4), {"status": "pending", "summary": "확인 불가"})
    r5 = next((r for r in recs if r["priority"] == 5), {"status": "pending", "summary": "확인 불가"})
    
    with c1: _hub_status_card("오늘의 마감", "✅ 완료" if r1["status"]=="completed" else "⚠️ 미완료", r1["summary"], "completed" if r1["status"]=="completed" else "warning")
    with c2: _hub_status_card("정기 QSC 점검", "✅ 완료" if r4["status"]=="completed" else "⏳ 권장", r4["summary"], "completed" if r4["status"]=="completed" else "pending")
    with c3: _hub_status_card("이번 달 정산", "✅ 완료" if r5["status"]=="completed" else "⏸️ 대기", r5["summary"], "completed" if r5["status"]=="completed" else "pending")

    st.markdown("---")

    # [3] 자산 구축 현황 (개선: 타일 하단 문구 배치)
    st.markdown("### 🏗️ 가게 자산 구축 현황")
    st.caption("가게 분석을 위한 '데이터 뼈대'의 완성도입니다. 품질 가이드에 따라 데이터를 관리해 주세요.")
    a1, a2, a3, a4 = st.columns(4)
    
    with a1: 
        _hub_asset_card("등록 메뉴", f"{assets.get('menu_count', 0)}개", "📘")
        if assets.get('missing_price', 0) > 0: st.caption(f"⚠️ 가격 미입력 {assets.get('missing_price')}개")
        else: st.caption("✅ 모든 가격 등록 완료")
        
    with a2: 
        _hub_asset_card("등록 재료", f"{assets.get('ing_count', 0)}개", "🧺")
        if assets.get('missing_cost', 0) > 0: st.caption(f"⚠️ 단가 미입력 {assets.get('missing_cost', 0)}개")
        else: st.caption("✅ 모든 단가 등록 완료")
        
    with a3: 
        _hub_asset_card("레시피 완성도", f"{assets.get('recipe_rate', 0):.0f}%", "🍳")
        if assets.get('recipe_rate', 0) < 50: st.caption("⚠️ 수익 분석 위해 보완 필요")
        else: st.caption("✅ 정밀 분석 가능 상태")
        
    with a4: 
        _hub_asset_card("이번 달 목표", "✅ 설정" if assets.get('has_target') else "⚠️ 미설정", "🎯")
        if not assets.get('has_target'): st.caption("⚠️ 분석 기준이 없습니다")
        else: st.caption("✅ 목표 대비 실적 분석 중")

    st.markdown("---")

    # [4] 워크플로우별 버튼 배치
    st.markdown("#### ⚡ STEP 1. 매일 운영 기록 (루틴)")
    st.caption("매일 발생하는 영업 실적을 기록하여 흐름을 파악합니다.")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 일일 마감 입력", use_container_width=True, type="primary", key="btn_daily"):
            st.session_state.current_page = "일일 입력(통합)"; st.rerun()
    with col2:
        if st.button("🩺 QSC 점검", use_container_width=True, key="btn_qsc"):
            st.session_state.current_page = "건강검진 실시"; st.rerun()
    with col3:
        if st.button("📅 월간 실제 정산", use_container_width=True, key="btn_settle"):
            st.session_state.current_page = "실제정산"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🎯 STEP 2. 목표 및 기준 설정 (Standards)")
    st.caption("운영 결과와 비교할 기준점(목표)을 설정합니다. (매월 1회 권장)")
    s1, s2 = st.columns(2)
    with s1:
        btn_type = "primary" if not assets.get('has_target') else "secondary"
        if st.button("🎯 이번 달 매출 목표 구조 설정", use_container_width=True, type=btn_type, key="btn_target_sales"):
            st.session_state.current_page = "목표 매출구조"; st.rerun()
    with s2:
        if st.button("🧾 이번 달 비용 목표 구조 설정", use_container_width=True, key="btn_target_cost"):
            st.session_state.current_page = "목표 비용구조"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🛠️ STEP 3. 가게 기초 정의 (뼈대 만들기)")
    st.caption("메뉴, 재료, 레시피 등 가게의 변하지 않는 기초 정보를 관리합니다.")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("📘 메뉴 관리", use_container_width=True, key="btn_menu"):
            st.session_state.current_page = "메뉴 입력"; st.rerun()
    with b2:
        if st.button("🧺 재료 관리", use_container_width=True, key="btn_ing"):
            st.session_state.current_page = "재료 입력"; st.rerun()
    with b3:
        if st.button("🧑‍🍳 레시피 관리", use_container_width=True, key="btn_recipe"):
            st.session_state.current_page = "레시피 입력"; st.rerun()
    with b4:
        if st.button("📦 재고 관리", use_container_width=True, key="btn_inv"):
            st.session_state.current_page = "재고 입력"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚙️ STEP 4. 데이터 보정 및 도구")
    with st.expander("과거 데이터 수정이나 일괄 보정 도구 열기"):
        st.caption("누락된 과거 데이터를 한꺼번에 채우거나 잘못된 정보를 수정할 때 사용합니다.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧮 매출/방문자 일괄 등록", use_container_width=True, key="btn_bulk_sales"):
                st.session_state.current_page = "매출 등록"; st.rerun()
        with c2:
            if st.button("📦 판매량 일괄 등록", use_container_width=True, key="btn_bulk_qty"):
                st.session_state.current_page = "판매량 등록"; st.rerun()

    st.markdown("---")
    st.info("💡 **Tip**: 정확한 분석은 정확한 입력에서 시작됩니다. 품질 가이드에 따라 데이터를 보완해 보세요.")
