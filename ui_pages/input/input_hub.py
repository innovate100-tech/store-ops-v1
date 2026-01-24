"""
입력 허브 페이지
입력 관련 모든 페이지로의 네비게이션 허브 (고도화 버전)
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header
from src.auth import get_current_store_id, get_supabase_client
from src.storage_supabase import get_day_record_status, load_actual_settlement_items, load_csv
from src.utils.time_utils import today_kst, current_year_kst, current_month_kst
from datetime import timedelta
import pandas as pd

# 공통 설정 적용
bootstrap(page_title="Input Hub")


def _count_completed_checklists_last_7_days(store_id: str) -> int:
    if not store_id: return 0
    try:
        supabase = get_supabase_client()
        if not supabase: return 0
        today = today_kst()
        cutoff_date = (today - timedelta(days=6)).isoformat()
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
        has_sales = status.get("has_sales", False)
        has_any = has_sales or status.get("has_visitors", False) or has_close
        
        # 상세 데이터 가져오기 (요약용)
        sales_val = 0
        visitors_val = 0
        if has_any:
            try:
                # 일일 매출/방문자 데이터 조회
                df = load_csv("daily_close", store_id=store_id)
                if not df.empty:
                    today_str = today.isoformat()
                    row = df[df["date"] == today_str]
                    if not row.empty:
                        sales_val = row.iloc[0].get("total_sales", 0)
                        visitors_val = row.iloc[0].get("visitors", 0)
            except Exception: pass

        # P1: 일일 마감
        if not has_close:
            msg = "📝 오늘 입력을 시작하세요" if not has_any else "📝 오늘 마감을 완료하세요"
            recommendations.append({
                "status": "pending", 
                "message": msg, 
                "button_label": "📝 일일 마감 입력", 
                "page_key": "일일 입력(통합)", 
                "priority": 1,
                "summary": f"매출: {int(sales_val):,}원 / 방문: {int(visitors_val)}명" if has_any else "입력 대기 중"
            })
        else:
            recommendations.append({
                "status": "completed", 
                "message": "✅ 오늘 마감 완료", 
                "button_label": "📝 일일 마감 입력", 
                "page_key": "일일 입력(통합)", 
                "priority": 1,
                "summary": f"매출: {int(sales_val):,}원 / 방문: {int(visitors_val)}명"
            })
        
        # P4: QSC
        checklist_count = _count_completed_checklists_last_7_days(store_id)
        last_date_str = "기록 없음"
        try:
            supabase = get_supabase_client()
            res = supabase.table("health_check_sessions").select("completed_at").eq("store_id", store_id).not_.is_("completed_at", "null").order("completed_at", desc=True).limit(1).execute()
            if res.data:
                last_date_str = res.data[0]["completed_at"][:10]
        except Exception: pass

        if checklist_count == 0:
            recommendations.append({
                "status": "pending", 
                "message": "📋 이번 주 점검을 해보세요", 
                "button_label": "🩺 QSC 입력", 
                "page_key": "건강검진 실시", 
                "priority": 4,
                "summary": f"최근 실시: {last_date_str}"
            })
        else:
            recommendations.append({
                "status": "completed", 
                "message": f"✅ 체크리스트 완료 ({checklist_count}회)", 
                "button_label": "🩺 QSC 입력", 
                "page_key": "건강검진 실시", 
                "priority": 4,
                "summary": f"최근 실시: {last_date_str}"
            })
            
        # P5: 정산
        today_day = today.day
        if today_day <= 7 or today_day >= 25:
            is_done = _is_current_month_settlement_done(store_id)
            profit_val = 0
            if is_done:
                try:
                    items = load_actual_settlement_items(store_id, today.year, today.month)
                    profit_val = sum(float(it.get("amount", 0)) for it in items if it.get("category") == "이익") # 카테고리명은 실제 데이터에 따라 다를 수 있음
                except Exception: pass

            if not is_done:
                recommendations.append({
                    "status": "pending", 
                    "message": "📅 월간 정산을 진행하세요", 
                    "button_label": "📅 월간 정산 입력", 
                    "page_key": "실제정산", 
                    "priority": 5,
                    "summary": "이번 달 정산 전"
                })
            else:
                recommendations.append({
                    "status": "completed", 
                    "message": "✅ 이번달 정산 완료", 
                    "button_label": "📅 월간 정산 입력", 
                    "page_key": "실제정산", 
                    "priority": 5,
                    "summary": "정산 완료"
                })
        
        return recommendations
    except Exception: return []


def _get_asset_readiness(store_id: str) -> dict:
    if not store_id: return {}
    try:
        # 1. 메뉴 마스터 및 품질 체크
        menu_df = load_csv("menu_master.csv", store_id=store_id)
        menu_count = len(menu_df) if not menu_df.empty else 0
        missing_price_count = 0
        if not menu_df.empty and "판매가" in menu_df.columns:
            missing_price_count = menu_df["판매가"].isna().sum() + (menu_df["판매가"] == 0).sum()
        
        # 2. 재료 마스터 및 품질 체크
        ing_df = load_csv("ingredient_master.csv", store_id=store_id)
        ing_count = len(ing_df) if not ing_df.empty else 0
        missing_cost_count = 0
        if not ing_df.empty and "단가" in ing_df.columns:
            missing_cost_count = ing_df["단가"].isna().sum() + (ing_df["단가"] == 0).sum()
        
        # 3. 레시피 완성도
        recipe_df = load_csv("recipes.csv", store_id=store_id)
        recipe_ready_count = 0
        if not menu_df.empty and not recipe_df.empty:
            menus_with_recipes = recipe_df["메뉴명"].unique()
            recipe_ready_count = len([m for m in menu_df["메뉴명"] if m in menus_with_recipes])
        recipe_rate = (recipe_ready_count / menu_count * 100) if menu_count > 0 else 0
        
        # 4. 목표 설정 여부
        targets_df = load_csv("targets.csv", store_id=store_id)
        has_target = False
        if not targets_df.empty:
            target_row = targets_df[(targets_df["연도"] == current_year_kst()) & (targets_df["월"] == current_month_kst())]
            if not target_row.empty and target_row.iloc[0].get("목표매출", 0) > 0:
                has_target = True
                
        return {
            "menu_count": menu_count, 
            "missing_price_count": int(missing_price_count),
            "ing_count": ing_count, 
            "missing_cost_count": int(missing_cost_count),
            "recipe_rate": recipe_rate, 
            "has_target": has_target
        }
    except Exception: return {"menu_count": 0, "ing_count": 0, "recipe_rate": 0, "has_target": False}


def _hub_status_card(title: str, value: str, sub: str, status: str = "pending"):
    bg = "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"
    border = "rgba(148,163,184,0.3)"
    if status == "completed": border = "rgba(74, 222, 128, 0.5)"
    elif status == "warning": border = "rgba(251, 191, 36, 0.5)"
    st.markdown(f"""
    <div style="padding: 1.2rem; background: {bg}; border-radius: 12px; border: 1px solid {border}; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 1rem; min-height: 140px;">
        <div style="font-size: 0.85rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.8rem;">{title}</div>
        <div style="font-size: 1.3rem; font-weight: 700; color: #ffffff; margin-bottom: 0.5rem;">{value}</div>
        <div style="font-size: 0.8rem; color: #64748b;">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def _hub_asset_card(title: str, value: str, icon: str, warning_text: str = ""):
    warning_html = f'<div style="font-size: 0.75rem; color: #ef4444; font-weight: 600; margin-top: 0.2rem;">⚠️ {warning_text}</div>' if warning_text else ''
    st.markdown(f"""
    <div style="padding: 1rem; background: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 0.8rem; display: flex; align-items: center; gap: 1rem;">
        <div style="font-size: 1.8rem;">{icon}</div>
        <div style="flex-grow: 1;">
            <div style="font-size: 0.75rem; color: #64748b;">{title}</div>
            <div style="font-size: 1rem; font-weight: 700; color: #1e293b;">{value}</div>
            {warning_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_input_hub():
    """입력 허브 페이지 렌더링"""
    render_page_header("✍ 입력 허브", "✍")
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return

    recs = _get_today_recommendations(store_id)
    assets = _get_asset_readiness(store_id)
    
    st.markdown("### 📊 입력 관제 보드")
    c1, c2, c3 = st.columns(3)
    today_rec = next((r for r in recs if r["priority"] == 1), None)
    with c1:
        if today_rec and today_rec["status"] == "completed": _hub_status_card("오늘의 마감", "✅ 완료", "정상적으로 마감되었습니다", "completed")
        else: _hub_status_card("오늘의 마감", "⚠️ 미완료", "오늘 영업 데이터를 입력하세요", "warning")
    qsc_rec = next((r for r in recs if r["priority"] == 4), None)
    with c2:
        if qsc_rec and qsc_rec["status"] == "completed": _hub_status_card("이번 주 QSC", "✅ 완료", "주간 점검을 마쳤습니다", "completed")
        else: _hub_status_card("이번 주 QSC", "⏳ 미실시", "가게 건강 상태를 체크하세요", "pending")
    settle_rec = next((r for r in recs if r["priority"] == 5), None)
    with c3:
        if settle_rec and settle_rec["status"] == "completed": _hub_status_card("이번 달 정산", "✅ 완료", "월간 성적이 확정되었습니다", "completed")
        else: _hub_status_card("이번 달 정산", "⏸️ 대기", "정산 주기에 진행하세요", "pending")

    st.markdown("---")
    
    # 2. 자산 구축 현황 (품질 체크 반영)
    st.markdown("### 🏗️ 가게 자산 구축 현황")
    st.caption("시스템 운영을 위한 기초 데이터 완성도입니다.")
    a1, a2, a3, a4 = st.columns(4)
    with a1: 
        m_warn = f"가격 미입력 {assets['missing_price_count']}개" if assets.get('missing_price_count', 0) > 0 else ""
        _hub_asset_card("등록 메뉴", f"{assets.get('menu_count', 0)}개", "📘", m_warn)
    with a2: 
        i_warn = f"단가 미입력 {assets['missing_cost_count']}개" if assets.get('missing_cost_count', 0) > 0 else ""
        _hub_asset_card("등록 재료", f"{assets.get('ing_count', 0)}개", "🧺", i_warn)
    with a3: 
        r_warn = "레시피가 부족합니다" if assets.get('recipe_rate', 0) < 50 else ""
        _hub_asset_card("레시피 완성도", f"{assets.get('recipe_rate', 0):.0f}%", "🧑‍🍳", r_warn)
    with a4: 
        t_warn = "이번 달 목표를 설정하세요" if not assets.get('has_target') else ""
        _hub_asset_card("이번 달 목표", "✅ 설정" if assets.get('has_target') else "⚠️ 미설정", "🎯", t_warn)

    st.markdown("---")
    
    # 3-1. 루틴 & 정기 작업
    st.markdown("### ⚡ 루틴 & 정기 작업")
    st.caption("매일 또는 정기적으로 수행하는 핵심 작업")
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

    # 3-2. 목표 및 기준 설정 (표준화 - 전진 배치)
    st.markdown("### 🎯 목표 및 기준 설정 (Standards)")
    st.caption("가게 운영의 나침반이 되는 기준을 설정합니다.")
    s1, s2 = st.columns(2)
    with s1:
        # 목표 미설정 시 버튼 강조
        btn_type = "primary" if not assets.get('has_target') else "secondary"
        if st.button("🎯 이번 달 매출 목표 구조 설정", use_container_width=True, type=btn_type, key="btn_target_sales"):
            st.session_state.current_page = "목표 매출구조"; st.rerun()
    with s2:
        if st.button("🧾 이번 달 비용 목표 구조 설정", use_container_width=True, key="btn_target_cost"):
            st.session_state.current_page = "목표 비용구조"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 3-3. 가게 기초 정의
    st.markdown("### 🛠️ 가게 기초 정의 (뼈대 만들기)")
    st.caption("가게가 무엇으로 이루어져 있는지 정의하는 곳입니다.")
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

    # 3-4. 데이터 보정
    st.markdown("### ⚙️ 데이터 보정 및 도구")
    with st.expander("과거 데이터 수정이나 일괄 보정 도구 열기"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧮 매출/방문자 일괄 등록", use_container_width=True, key="btn_bulk_sales"):
                st.session_state.current_page = "매출 등록"; st.rerun()
        with c2:
            if st.button("📦 판매량 일괄 등록", use_container_width=True, key="btn_bulk_qty"):
                st.session_state.current_page = "판매량 등록"; st.rerun()

    st.markdown("---")
    st.info("💡 **Tip**: 정확한 분석은 정확한 입력에서 시작됩니다. 품질 경고(⚠️)가 있는 데이터를 먼저 보완해 보세요.")

    st.markdown("---")
    st.info("💡 **Tip**: 입력은 가게의 현실을 만드는 일입니다. 분석은 해석, 설계는 실험입니다.")
