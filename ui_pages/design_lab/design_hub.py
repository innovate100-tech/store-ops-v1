"""
설계 허브 페이지
설계 상태 요약(9개 영역 완성도) + 우선순위 액션 + 세부설계 진입점
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from src.ui_helpers import render_page_header
from src.utils.time_utils import current_year_kst, current_month_kst
from src.storage_supabase import (
    load_csv,
    load_expense_structure,
    get_fixed_costs,
    get_variable_cost_ratio,
)
from src.analytics import calculate_menu_cost
from src.auth import get_current_store_id

bootstrap(page_title="설계 허브")


def _check_menu_completion(store_id: str) -> dict:
    """메뉴 포트폴리오 설계 완성도"""
    menu_df = load_csv("menu_master.csv", default_columns=["메뉴명", "판매가"], store_id=store_id)
    count = len(menu_df) if not menu_df.empty else 0
    completion = 100.0 if count > 0 else 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": f"메뉴 {count}개 등록",
        "page_key": "메뉴 등록",
    }


def _check_ingredient_completion(store_id: str) -> dict:
    """재료 구조 설계 완성도"""
    ing_df = load_csv("ingredient_master.csv", default_columns=["재료명", "단위", "단가"], store_id=store_id)
    count = len(ing_df) if not ing_df.empty else 0
    completion = 100.0 if count > 0 else 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": f"재료 {count}개 등록",
        "page_key": "재료 등록",
    }


def _check_recipe_completion(store_id: str) -> dict:
    """레시피 설계 완성도"""
    recipe_df = load_csv("recipes.csv", default_columns=["메뉴명", "재료명", "사용량"], store_id=store_id)
    count = len(recipe_df) if not recipe_df.empty else 0
    completion = 100.0 if count > 0 else 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": f"레시피 {count}개 등록",
        "page_key": "레시피 등록",
    }


def _check_menu_profit_completion(store_id: str) -> dict:
    """메뉴 수익 설계 완성도"""
    menu_df = load_csv("menu_master.csv", default_columns=["메뉴명", "판매가"], store_id=store_id)
    recipe_df = load_csv("recipes.csv", default_columns=["메뉴명", "재료명", "사용량"], store_id=store_id)
    ing_df = load_csv("ingredient_master.csv", default_columns=["재료명", "단위", "단가"], store_id=store_id)
    
    can_calculate = False
    if not menu_df.empty and not recipe_df.empty and not ing_df.empty:
        try:
            cost_df = calculate_menu_cost(menu_df, recipe_df, ing_df)
            can_calculate = not cost_df.empty
        except Exception:
            pass
    
    completion = 100.0 if can_calculate else 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": "원가율 계산 가능" if can_calculate else "원가율 계산 불가",
        "page_key": "메뉴 수익 구조 설계실",
    }


def _check_profit_structure_completion(store_id: str, year: int, month: int) -> dict:
    """수익 구조 설계 완성도"""
    fixed = get_fixed_costs(store_id, year, month) or 0.0
    var_ratio = get_variable_cost_ratio(store_id, year, month) or 0.0
    has_structure = (fixed is not None and fixed > 0) or (var_ratio is not None and var_ratio > 0)
    completion = 100.0 if has_structure else 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": f"고정비 {int(fixed):,}원, 변동비율 {var_ratio*100:.1f}%" if has_structure else "수익 구조 미설정",
        "page_key": "수익 구조 설계실",
    }


def _check_target_cost_completion(store_id: str, year: int, month: int) -> dict:
    """목표 비용 구조 입력 완성도"""
    try:
        exp_df = load_expense_structure(year, month, store_id=store_id)
        has_data = isinstance(exp_df, pd.DataFrame) and not exp_df.empty
    except Exception:
        has_data = False
    completion = 100.0 if has_data else 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": "목표 비용 구조 입력됨" if has_data else "목표 비용 구조 미입력",
        "page_key": "목표 비용구조",
    }


def _check_target_sales_completion(store_id: str, year: int, month: int) -> dict:
    """목표 매출 구조 입력 완성도"""
    try:
        targets_df = load_csv("targets.csv", default_columns=["연도", "월", "목표매출"], store_id=store_id)
        if targets_df.empty:
            has_data = False
        else:
            r = targets_df[(targets_df["연도"] == year) & (targets_df["월"] == month)]
            has_data = not r.empty and float(r.iloc[0].get("목표매출", 0) or 0) > 0
    except Exception:
        has_data = False
    completion = 100.0 if has_data else 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": f"{year}년 {month}월 목표 매출 입력됨" if has_data else "목표 매출 미입력",
        "page_key": "목표 매출구조",
    }


def _check_design_center_completion(store_id: str) -> dict:
    """가게 설계 센터 진단 완성도 (간단 체크)"""
    try:
        from ui_pages.design_lab.design_state_loader import get_design_state
        state = get_design_state(store_id)
        # 4개 설계실 진단 완료 여부 (간단 체크)
        has_state = state is not None and isinstance(state, dict)
        completion = 100.0 if has_state else 0.0
    except Exception:
        completion = 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": "통합 진단 완료" if completion == 100 else "통합 진단 미완료",
        "page_key": "가게 설계 센터",
    }


def _check_strategy_board_completion(store_id: str, year: int, month: int) -> dict:
    """전략 보드 완성도 (간단 체크)"""
    # 전략 보드 데이터 확인 (간단 체크)
    # 실제로는 전략 카드 생성 여부를 확인해야 함
    completion = 0.0  # 기본값: 미완료로 처리
    return {
        "completion": completion,
        "status": "진행중",
        "indicator": "전략 보드 확인 필요",
        "page_key": "전략 보드",
    }


def _calculate_overall_completion(completions: list) -> float:
    """전체 완성도 계산"""
    if not completions:
        return 0.0
    total = sum(c.get("completion", 0.0) for c in completions)
    return total / len(completions)


def _get_priority_actions(completions: list) -> list:
    """우선순위 액션 생성"""
    actions = []
    # 완성도가 0%인 핵심 영역 우선
    core_areas = [
        ("메뉴 포트폴리오 설계", "메뉴 등록"),
        ("재료 구조 설계", "재료 등록"),
        ("레시피 설계", "레시피 등록"),
        ("목표 매출 구조 입력", "목표 매출구조"),
    ]
    
    for area_name, page_key in core_areas:
        for comp in completions:
            if comp.get("page_key") == page_key and comp.get("completion", 0) == 0.0:
                actions.append({
                    "description": f"{area_name}가 없습니다. {area_name}부터 시작하세요.",
                    "page_key": page_key,
                })
                break
    
    # 완성도가 낮은 영역 추가
    for comp in completions:
        if comp.get("completion", 0) < 100 and comp.get("page_key") not in [a["page_key"] for a in actions]:
            area_name_map = {
                "메뉴 수익 구조 설계실": "메뉴 수익 설계",
                "수익 구조 설계실": "수익 구조 설계",
                "목표 비용구조": "목표 비용 구조 입력",
            }
            area_name = area_name_map.get(comp.get("page_key"), comp.get("page_key"))
            actions.append({
                "description": f"{area_name}를 완성하세요.",
                "page_key": comp.get("page_key"),
            })
    
    return actions[:5]


def _hub_card(title: str, completion: float, status: str, indicator: str, page_key: str, icon: str = "📊"):
    """설계 허브 카드 렌더링"""
    if completion == 100:
        border_color = "#10b981"  # 녹색
        status_emoji = "🟢"
    elif completion > 0:
        border_color = "#f59e0b"  # 노란색
        status_emoji = "🟡"
    else:
        border_color = "#ef4444"  # 빨간색
        status_emoji = "🔴"
    
    st.markdown(f"""
    <div style="padding: 1.2rem; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                border-radius: 12px; border-left: 4px solid {border_color}; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
            <span style="font-size: 1.5rem;">{icon}</span>
            <h3 style="margin: 0; font-size: 1rem; font-weight: 600; color: #e5e7eb;">{title}</h3>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #ffffff;">
                {status_emoji} {completion:.0f}%
            </div>
            <div style="font-size: 0.85rem; color: #94a3b8;">
                {status}
            </div>
        </div>
        <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.8rem;">
            {indicator}
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("자세히 보기", key=f"design_hub_go_{page_key}", use_container_width=True, type="primary"):
        st.session_state["current_page"] = page_key
        st.rerun()


def render_design_hub():
    """설계 허브 페이지 렌더링"""
    render_page_header("설계 허브", "🏗️")

    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return

    st.markdown("""
    <div style="padding: 1rem; background: #f0f9ff; border-left: 4px solid #3b82f6; border-radius: 8px; margin-bottom: 1.5rem;">
        <p style="margin: 0; font-size: 1rem; line-height: 1.6;">
            <strong>설계는 가게의 구조를 만드는 일입니다.</strong><br>
            핵심만 먼저 보세요. 세부는 아래 '세부설계선택'에서 골라 들어가면 됩니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    year = current_year_kst()
    month = current_month_kst()

    # 각 영역 완성도 계산
    completions = [
        {"name": "가게 설계 센터", "icon": "🏗️", **(_check_design_center_completion(store_id)))},
        {"name": "전략 보드", "icon": "📋", **(_check_strategy_board_completion(store_id, year, month))},
        {"name": "메뉴 포트폴리오 설계", "icon": "🍽️", **(_check_menu_completion(store_id))},
        {"name": "메뉴 수익 설계", "icon": "💰", **(_check_menu_profit_completion(store_id))},
        {"name": "재료 구조 설계", "icon": "🧺", **(_check_ingredient_completion(store_id))},
        {"name": "수익 구조 설계", "icon": "📊", **(_check_profit_structure_completion(store_id, year, month))},
        {"name": "레시피 설계", "icon": "📝", **(_check_recipe_completion(store_id))},
        {"name": "목표 비용 구조 입력", "icon": "💳", **(_check_target_cost_completion(store_id, year, month))},
        {"name": "목표 매출 구조 입력", "icon": "🎯", **(_check_target_sales_completion(store_id, year, month))},
    ]

    # 전체 완성도 계산
    overall_completion = _calculate_overall_completion(completions)

    # ZONE A: 설계 상태 요약 헤더
    st.markdown("### 설계 완성도")
    st.caption("9개 설계 영역의 완성도를 확인하세요.")

    # 완성도 바
    st.progress(overall_completion / 100.0)
    st.markdown(f"**전체 완성도: {overall_completion:.0f}%**")

    # 핵심 메시지
    if overall_completion == 100:
        st.success("✅ 설계가 완료되었습니다. 분석·운영으로 넘어가세요.")
    elif overall_completion >= 50:
        st.info("⚠️ 설계가 진행 중입니다. 누락된 영역을 채워주세요.")
    else:
        st.warning("🔴 설계가 부족합니다. 핵심 설계부터 시작하세요.")

    st.markdown("---")

    # ZONE B: 설계 영역별 완성도 카드 (9개)
    st.markdown("### 설계 영역별 완성도")

    # 3열 그리드로 표시
    cols = st.columns(3)
    for idx, comp in enumerate(completions):
        col = cols[idx % 3]
        with col:
            _hub_card(
                comp["name"],
                comp["completion"],
                comp["status"],
                comp["indicator"],
                comp["page_key"],
                comp["icon"],
            )

    st.markdown("---")

    # ZONE C: 우선순위 액션
    st.markdown("### 우선순위 액션")

    priority_actions = _get_priority_actions(completions)
    if priority_actions:
        for i, action in enumerate(priority_actions):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(action["description"])
            with col2:
                if st.button("이동", key=f"design_hub_action_{i}_{action['page_key']}", use_container_width=True):
                    st.session_state["current_page"] = action["page_key"]
                    st.rerun()
    else:
        st.info("모든 설계 영역이 완료되었습니다. 🎉")

    st.markdown("---")

    # ZONE D: 세부설계선택 (expander)
    sub_items = [
        ("가게 설계 센터", "가게 설계 센터"),
        ("전략 보드", "전략 보드"),
        ("메뉴 포트폴리오 설계", "메뉴 등록"),
        ("메뉴 수익 설계", "메뉴 수익 구조 설계실"),
        ("재료 구조 설계", "재료 등록"),
        ("수익 구조 설계", "수익 구조 설계실"),
        ("레시피 설계", "레시피 등록"),
        ("목표 비용 구조 입력", "목표 비용구조"),
        ("목표 매출 구조 입력", "목표 매출구조"),
    ]
    with st.expander("세부설계선택", expanded=False):
        st.caption("상세 설계가 필요할 때 페이지를 골라 들어가세요.")
        for label, key in sub_items:
            if st.button(label, key=f"design_hub_sub_{key}", use_container_width=True, type="secondary"):
                st.session_state["current_page"] = key
                st.rerun()
