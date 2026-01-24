"""
입력 허브 페이지
입력 관련 모든 페이지로의 네비게이션 허브 (4단계 고도화 버전 - 통합 가이드 및 워크플로우)
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

    st.markdown(f"""
    <div class="animate-in {delay_class}" style="padding: 1.5rem; background: {bg}; border-radius: 16px; border: 1px solid {border}; {glow} backdrop-filter: blur(10px); min-height: 150px; transition: all 0.3s ease; position: relative; overflow: hidden;">
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
    """입력 허브 페이지 렌더링 (Stage 6: 동적 경험 고도화 버전)"""
    render_page_header("✍ 입력 허브", "✍")
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다."); return

    # 데이터 로드
    recs = _get_today_recommendations(store_id)
    assets = _get_asset_readiness(store_id)

    # 디지털 성숙도 점수 계산
    score = 0
    if assets.get('menu_count', 0) > 0 and assets.get('missing_price', 0) == 0: score += 25
    if assets.get('ing_count', 0) > 0 and assets.get('missing_cost', 0) == 0: score += 25
    if assets.get('recipe_rate', 0) >= 80: score += 25
    if assets.get('has_target'): score += 25

    # [1] 통합 가이드 카드 (동적 애니메이션 적용)
    st.markdown(f"""
    <div class="animate-in" style="padding: 1.8rem; background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.2); margin-bottom: 2.5rem; box-shadow: 0 10px 25px rgba(0,0,0,0.4); position: relative; overflow: hidden;">
        <!-- 배경 일렁임 효과 -->
        <div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(59, 130, 246, 0.05) 0%, transparent 70%); animation: shimmer 10s infinite linear;"></div>
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; position: relative;">
            <div>
                <h4 style="margin: 0 0 0.6rem 0; color: #F8FAFC; font-size: 1.2rem; font-weight: 700;">💡 데이터 자산 가이드</h4>
                <p style="margin: 0; color: #94A3B8; font-size: 0.95rem; line-height: 1.6;">
                    정교한 분석의 시작은 정확한 데이터 입력입니다.<br>
                    <span style="color: #3B82F6; font-weight: 600;">데이터 성숙도</span>를 높여 매장 운영의 통찰력을 확보하세요.
                </p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.3rem; font-weight: 600;">MATURITY LEVEL</div>
                <div id="maturity-score" style="color: #3B82F6; font-weight: 800; font-size: 2rem; line-height: 1;">0<span style="font-size: 1rem; margin-left: 2px;">%</span></div>
            </div>
        </div>
        
        <script>
        var scoreElement = document.getElementById('maturity-score');
        var targetScore = {score};
        var currentScore = 0;
        var interval = setInterval(function() {{
            if (currentScore >= targetScore) {{
                clearInterval(interval);
            }} else {{
                currentScore++;
                scoreElement.innerHTML = currentScore + '<span style="font-size: 1rem; margin-left: 2px;">%</span>';
            }}
        }}, 20);
        </script>
        
        <!-- 물결 애니메이션이 포함된 프로그레스 바 -->
        <div style="background-color: rgba(255,255,255,0.05); border-radius: 20px; height: 12px; margin-bottom: 1.2rem; overflow: hidden; border: 1px solid rgba(255,255,255,0.05); position: relative;">
            <div style="background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%); width: {score}%; height: 100%; border-radius: 20px; box-shadow: 0 0 10px rgba(59, 130, 246, 0.4); position: relative; overflow: hidden;">
                <!-- 리퀴드 웨이브 효과 -->
                <div style="position: absolute; top: 0; left: 0; width: 200%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); animation: wave 2s infinite linear;"></div>
            </div>
        </div>
        
        <div style="display: flex; align-items: center; gap: 0.5rem; position: relative;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: { '#10B981' if score == 100 else '#3B82F6' }; animation: pulse 2s infinite;"></div>
            <p style="margin: 0; color: { '#10B981' if score == 100 else '#3B82F6' }; font-size: 0.85rem; font-weight: 600; letter-spacing: 0.02em;">
                {f"PREMIUM: 모든 지능형 분석 엔진이 활성화되었습니다!" if score == 100 else "🚩 미완료 데이터를 보완하여 정밀 분석 기능을 잠금 해제하세요."}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # [2] 관제 보드 (시퀀셜 등장 적용)
    st.markdown("### 📊 실시간 입력 현황")
    c1, c2, c3 = st.columns(3)
    r1 = next((r for r in recs if r["priority"] == 1), {"status": "pending", "summary": "확인 불가"})
    r4 = next((r for r in recs if r["priority"] == 4), {"status": "pending", "summary": "확인 불가"})
    r5 = next((r for r in recs if r["priority"] == 5), {"status": "pending", "summary": "확인 불가"})
    
    with c1: _hub_status_card("오늘의 마감", "✅ 완료" if r1["status"]=="completed" else "⚠️ 미완료", r1["summary"], "completed" if r1["status"]=="completed" else "warning", "delay-1")
    with c2: _hub_status_card("정기 QSC 점검", "✅ 완료" if r4["status"]=="completed" else "⏳ 권장", r4["summary"], "completed" if r4["status"]=="completed" else "pending", "delay-2")
    with c3: _hub_status_card("이번 달 정산", "✅ 완료" if r5["status"]=="completed" else "⏸️ 대기", r5["summary"], "completed" if r5["status"]=="completed" else "pending", "delay-3")

    st.markdown("<br>", unsafe_allow_html=True)

    # [3] 자산 구축 현황 (시퀀셜 등장 적용)
    st.markdown("### 🏗️ 가게 데이터 기초 체력")
    st.caption("매장의 '디지털 자산'입니다. 누락된 항목을 채워 분석 정밀도를 높이세요.")
    a1, a2, a3, a4 = st.columns(4)
    with a1: 
        _hub_asset_card("등록 메뉴", f"{assets.get('menu_count', 0)}개", "📘", "delay-1")
        if assets.get('missing_price', 0) > 0: st.markdown(f"<p class='animate-in delay-2' style='color: #F59E0B; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem; font-weight: 600;'>⚠️ {assets.get('missing_price')}개 가격 누락</p>", unsafe_allow_html=True)
        else: st.markdown("<p class='animate-in delay-2' style='color: #10B981; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem;'>✅ 등록 완료</p>", unsafe_allow_html=True)
    with a2: 
        _hub_asset_card("등록 재료", f"{assets.get('ing_count', 0)}개", "🧺", "delay-2")
        if assets.get('missing_cost', 0) > 0: st.markdown(f"<p class='animate-in delay-3' style='color: #F59E0B; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem; font-weight: 600;'>⚠️ {assets.get('missing_cost')}개 단가 누락</p>", unsafe_allow_html=True)
        else: st.markdown("<p class='animate-in delay-3' style='color: #10B981; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem;'>✅ 등록 완료</p>", unsafe_allow_html=True)
    with a3: 
        _hub_asset_card("레시피 완성도", f"{assets.get('recipe_rate', 0):.0f}%", "🍳", "delay-3")
        if assets.get('recipe_rate', 0) < 80: st.markdown("<p class='animate-in delay-4' style='color: #94A3B8; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem;'>⏳ 80% 달성 권장</p>", unsafe_allow_html=True)
        else: st.markdown("<p class='animate-in delay-4' style='color: #10B981; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem;'>✅ 정밀 분석 가능</p>", unsafe_allow_html=True)
    with a4: 
        goal_status = "✅ 설정 완료" if assets.get('has_target') else "❌ 미설정"
        _hub_asset_card("이번 달 목표", goal_status, "🎯", "delay-4")
        if not assets.get('has_target'): st.markdown("<p class='animate-in delay-4' style='color: #F59E0B; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem; font-weight: 600;'>⚠️ 목표 설정 필요</p>", unsafe_allow_html=True)
        else: st.markdown("<p class='animate-in delay-4' style='color: #10B981; font-size: 0.8rem; margin: 0.5rem 0 0 0.5rem;'>✅ 분석 중</p>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # [4] 사용 주기별 워크플로우
    st.markdown("#### ⚡ 매일 · 매주 · 매월 루틴")
    st.caption("정기적으로 기록해야 하는 핵심 데이터입니다.")
    col1, col2, col3 = st.columns(3)
    with col1:
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
    st.markdown("#### 🎯 목표 및 분석 기준")
    st.caption("비교 기준을 설정합니다. 누락 시 파란색으로 강조됩니다.")
    s1, s2 = st.columns(2)
    with s1:
        btn_type = "primary" if not assets.get('has_target') else "secondary"
        label = "🎯 매출 목표 설정" + (" (필수)" if not assets.get('has_target') else "")
        if st.button(label, use_container_width=True, type=btn_type, key="btn_target_sales"):
            st.session_state.current_page = "목표 매출구조"; st.rerun()
    with s2:
        if st.button("🧾 비용 목표 구조 설정", use_container_width=True, key="btn_target_cost"):
            st.session_state.current_page = "목표 비용구조"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🛠️ 가게 정의 (기초 뼈대)")
    st.caption("메뉴나 재료 변경 시 수정합니다. 누락 발견 시 파란색으로 강조됩니다.")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        btn_type = "primary" if assets.get('missing_price', 0) > 0 else "secondary"
        label = "📘 메뉴 관리" + (f" ({assets.get('missing_price')}건)" if assets.get('missing_price', 0) > 0 else "")
        if st.button(label, use_container_width=True, type=btn_type, key="btn_menu"):
            st.session_state.current_page = "메뉴 입력"; st.rerun()
    with b2:
        btn_type = "primary" if assets.get('missing_cost', 0) > 0 else "secondary"
        label = "🧺 재료 관리" + (f" ({assets.get('missing_cost')}건)" if assets.get('missing_cost', 0) > 0 else "")
        if st.button(label, use_container_width=True, type=btn_type, key="btn_ing"):
            st.session_state.current_page = "재료 입력"; st.rerun()
    with b3:
        btn_type = "primary" if assets.get('recipe_rate', 0) < 80 else "secondary"
        if st.button("🍳 레시피 관리", use_container_width=True, type=btn_type, key="btn_recipe"):
            st.session_state.current_page = "레시피 등록"; st.rerun()
    with b4:
        if st.button("📦 재고 관리", use_container_width=True, key="btn_inv"):
            st.session_state.current_page = "재고 입력"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚙️ 데이터 보정 도구 (과거 일괄 수정)"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧮 매출/방문자 일괄 등록", use_container_width=True, key="btn_bulk_sales"):
                st.session_state.current_page = "매출 등록"; st.rerun()
        with c2:
            if st.button("📦 판매량 일괄 등록", use_container_width=True, key="btn_bulk_qty"):
                st.session_state.current_page = "판매량 등록"; st.rerun()

    st.markdown("---")
    st.info("💡 **Tip**: 파란색 글로우(Glow)가 적용된 버튼은 현재 데이터 보완이 가장 필요한 항목입니다.")
