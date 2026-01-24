"""
입력 허브 페이지
입력 관련 모든 페이지로의 네비게이션 허브 (4단계 고도화 버전 - 지능형 워크플로우)
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
    card_style = "padding: 1rem; background-color: #111827; border-radius: 10px; border: 1px solid #374151; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.8rem; min-height: 90px;"
    title_style = "font-size: 0.75rem; color: #9ca3af; font-weight: 500; margin-bottom: 0.2rem;"
    value_style = "font-size: 1.1rem; font-weight: 700; color: #ffffff; line-height: 1;"
    html_content = (
        f'<div style="{card_style}">'
        f'<div style="font-size: 1.8rem; flex-shrink: 0;">{icon}</div>'
        f'<div style="display: flex; flex-direction: column; justify-content: center; flex-grow: 1;">'
        f'<div style="{title_style}">{title}</div>'
        f'<div style="{value_style}">{value}</div>'
        f'</div></div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)

def render_input_hub_v2():
    """입력 허브 페이지 렌더링"""
    render_page_header("✍ 입력 허브", "✍")
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다."); return

    # 데이터 로드
    recs = _get_today_recommendations(store_id)
    assets = _get_asset_readiness(store_id)

    # [1] 디지털 성숙도 게이지 (Maturity Score)
    # 계산: 메뉴가격(25) + 재료단가(25) + 레시피80%(25) + 목표설정(25)
    score = 0
    if assets.get('menu_count', 0) > 0 and assets.get('missing_price', 0) == 0: score += 25
    if assets.get('ing_count', 0) > 0 and assets.get('missing_cost', 0) == 0: score += 25
    if assets.get('recipe_rate', 0) >= 80: score += 25
    if assets.get('has_target'): score += 25

    # 최상단 가이드 및 성숙도 바
    st.markdown(f"""
    <div style="padding: 1.5rem; background-color: #111827; border-radius: 12px; border-left: 5px solid #3b82f6; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h4 style="margin: 0; color: #ffffff; font-size: 1.1rem;">📊 매장 데이터 관리 상태</h4>
            <span style="color: #3b82f6; font-weight: 700; font-size: 1.2rem;">{score}%</span>
        </div>
        <div style="background-color: #374151; border-radius: 10px; height: 10px; margin-bottom: 1.5rem; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%); width: {score}%; height: 100%; transition: width 0.5s ease-in-out;"></div>
        </div>
        <p style="margin-bottom: 0; color: #9ca3af; font-size: 0.9rem; line-height: 1.6;">
            {f"축하합니다! 이제 <b>정밀 분석 엔진</b>이 작동할 준비가 되었습니다." if score == 100 else "누락된 기초 데이터를 보완하면 <b>수익 분석 및 전략 리포트</b> 기능이 활성화됩니다."}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # [2] 관제 보드
    st.markdown("### 📊 실시간 입력 현황")
    c1, c2, c3 = st.columns(3)
    r1 = next((r for r in recs if r["priority"] == 1), {"status": "pending", "summary": "확인 불가"})
    r4 = next((r for r in recs if r["priority"] == 4), {"status": "pending", "summary": "확인 불가"})
    r5 = next((r for r in recs if r["priority"] == 5), {"status": "pending", "summary": "확인 불가"})
    
    with c1: _hub_status_card("오늘의 마감", "✅ 완료" if r1["status"]=="completed" else "⚠️ 미완료", r1["summary"], "completed" if r1["status"]=="completed" else "warning")
    with c2: _hub_status_card("정기 QSC 점검", "✅ 완료" if r4["status"]=="completed" else "⏳ 권장", r4["summary"], "completed" if r4["status"]=="completed" else "pending")
    with c3: _hub_status_card("이번 달 정산", "✅ 완료" if r5["status"]=="completed" else "⏸️ 대기", r5["summary"], "completed" if r5["status"]=="completed" else "pending")

    st.markdown("---")

    # [3] 자산 구축 현황
    st.markdown("### 🏗️ 가게 데이터 기초 체력")
    a1, a2, a3, a4 = st.columns(4)
    
    with a1: 
        _hub_asset_card("등록 메뉴", f"{assets.get('menu_count', 0)}개", "📘")
        if assets.get('missing_price', 0) > 0: st.caption(f"⚠️ {assets.get('missing_price')}개 가격 누락")
        else: st.caption("✅ 판매가 등록 완료")
        
    with a2: 
        _hub_asset_card("등록 재료", f"{assets.get('ing_count', 0)}개", "🧺")
        if assets.get('missing_cost', 0) > 0: st.caption(f"⚠️ {assets.get('missing_cost')}개 단가 누락")
        else: st.caption("✅ 구매 단가 등록 완료")
        
    with a3: 
        _hub_asset_card("레시피 완성도", f"{assets.get('recipe_rate', 0):.0f}%", "🍳")
        if assets.get('recipe_rate', 0) < 80: st.caption("⚠️ 원가 분석 정밀도 낮음")
        else: st.caption("✅ 정밀 분석 가능")
        
    with a4: 
        goal_status = "✅ 설정 완료" if assets.get('has_target') else "❌ 설정 미완료"
        _hub_asset_card("이번 달 목표 설정", goal_status, "🎯")
        if not assets.get('has_target'): st.caption("⚠️ 분석 기준이 없습니다")
        else: st.caption("✅ 목표 대비 실적 분석 중")

    st.markdown("---")

    # [4] 사용 주기별 워크플로우
    
    # 1. 매일/매주/매월 (운영)
    st.markdown("#### ⚡ 매일 · 매주 · 매월 루틴")
    st.caption("정기적으로 기록해야 하는 핵심 영업 데이터입니다.")
    col1, col2, col3 = st.columns(3)
    with col1:
        # 오늘 마감 안 했으면 강조
        btn_type = "primary" if r1["status"] != "completed" else "secondary"
        if st.button("📝 오늘 마감 입력", use_container_width=True, type=btn_type, key="btn_daily"):
            st.session_state.current_page = "일일 입력(통합)"; st.rerun()
    with col2:
        if st.button("🩺 QSC 점검 (격주)", use_container_width=True, key="btn_qsc"):
            st.session_state.current_page = "건강검진 실시"; st.rerun()
    with col3:
        if st.button("📅 월간 실제 정산", use_container_width=True, key="btn_settle"):
            st.session_state.current_page = "실제정산"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. 목표 및 기준 (매월 초)
    st.markdown("#### 🎯 목표 및 분석 기준")
    st.caption("비교 기준을 설정합니다. 데이터 누락 시 해당 버튼이 강조됩니다.")
    s1, s2 = st.columns(2)
    with s1:
        # 목표 미설정 시 강조
        btn_type = "primary" if not assets.get('has_target') else "secondary"
        label = "🎯 매출 목표 설정" + (" (필수)" if not assets.get('has_target') else "")
        if st.button(label, use_container_width=True, type=btn_type, key="btn_target_sales"):
            st.session_state.current_page = "목표 매출구조"; st.rerun()
    with s2:
        if st.button("🧾 비용 목표 구조 설정", use_container_width=True, key="btn_target_cost"):
            st.session_state.current_page = "목표 비용구조"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. 가게 정의 (필요시)
    st.markdown("#### 🛠️ 가게 정의 (기초 뼈대)")
    st.caption("메뉴나 재료가 변경될 때 수정합니다. 누락 데이터 발견 시 버튼이 강조됩니다.")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        # 가격 누락 시 강조
        btn_type = "primary" if assets.get('missing_price', 0) > 0 else "secondary"
        label = "📘 메뉴 관리" + (f" ({assets.get('missing_price')}개 보완)" if assets.get('missing_price', 0) > 0 else "")
        if st.button(label, use_container_width=True, type=btn_type, key="btn_menu"):
            st.session_state.current_page = "메뉴 입력"; st.rerun()
    with b2:
        # 단가 누락 시 강조
        btn_type = "primary" if assets.get('missing_cost', 0) > 0 else "secondary"
        label = "🧺 재료 관리" + (f" ({assets.get('missing_cost')}개 보완)" if assets.get('missing_cost', 0) > 0 else "")
        if st.button(label, use_container_width=True, type=btn_type, key="btn_ing"):
            st.session_state.current_page = "재료 입력"; st.rerun()
    with b3:
        # 레시피 완성도 낮으면 강조
        btn_type = "primary" if assets.get('recipe_rate', 0) < 80 else "secondary"
        if st.button("🍳 레시피 관리", use_container_width=True, type=btn_type, key="btn_recipe"):
            st.session_state.current_page = "레시피 입력"; st.rerun()
    with b4:
        if st.button("📦 재고 관리", use_container_width=True, key="btn_inv"):
            st.session_state.current_page = "재고 입력"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. 데이터 보정
    st.markdown("#### ⚙️ 데이터 보정 도구")
    with st.expander("과거 데이터 일괄 수정"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧮 매출/방문자 일괄 등록", use_container_width=True, key="btn_bulk_sales"):
                st.session_state.current_page = "매출 등록"; st.rerun()
        with c2:
            if st.button("📦 판매량 일괄 등록", use_container_width=True, key="btn_bulk_qty"):
                st.session_state.current_page = "판매량 등록"; st.rerun()

    st.markdown("---")
    st.info("💡 **Tip**: 파란색으로 강조된 버튼은 현재 데이터 보완이 시급한 항목입니다.")
