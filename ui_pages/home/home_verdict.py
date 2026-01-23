"""
홈 코치 판결 로직 (HOME v2)
- get_coach_verdict: 이번 달 가장 중요한 문제 1개 판결
- 3개 분류: 수익 구조 위험, 메뉴 수익 구조 위험, 재료 구조 위험
- 설계 DB 데이터를 우선 근거로 사용
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.storage_supabase import (
    load_best_available_daily_sales,
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
    load_csv,
)
from src.auth import get_supabase_client
from ui_pages.design_lab.design_insights import get_design_insights
from ui_pages.design_lab.design_state_loader import get_design_state, get_primary_risk_area


def get_coach_verdict(store_id: str, year: int, month: int, monthly_sales: int) -> dict:
    """
    이번 달 코치 판결 (가장 중요한 문제 1개)
    설계 DB 데이터를 우선 근거로 사용
    
    Returns:
        {
            "verdict_type": "revenue_structure" | "menu_profit" | "ingredient_structure" | None,
            "verdict_text": str,
            "reasons": [{"title": str, "value": str}],
            "target_page": str,
            "button_label": str
        }
    """
    if not store_id:
        return {
            "verdict_type": None,
            "verdict_text": "데이터가 부족하여 판결할 수 없습니다.",
            "reasons": [],
            "target_page": "점장 마감",
            "button_label": "📋 점장 마감 하러가기"
        }
    
    try:
        # 설계 상태 로드 (점수화 + 상태 판정)
        design_state = get_design_state(store_id, year, month)
        
        # 설계 인사이트 로드 (상세 데이터)
        insights = get_design_insights(store_id, year, month)
        
        # 1순위: 설계 상태 기반 판단 (우선순위 높음)
        design_verdict = _check_design_state_risks(design_state, insights)
        if design_verdict:
            return design_verdict
        
        # 2순위: 운영 데이터 기반 판단 (fallback)
        # 수익 구조 위험 판단
        revenue_risk = _check_revenue_structure_risk(store_id, year, month, monthly_sales)
        if revenue_risk:
            return revenue_risk
        
        # 메뉴 수익 구조 위험 판단
        menu_risk = _check_menu_profit_risk(store_id, year, month, monthly_sales)
        if menu_risk:
            return menu_risk
        
        # 재료 구조 위험 판단
        ingredient_risk = _check_ingredient_structure_risk(store_id, year, month)
        if ingredient_risk:
            return ingredient_risk
        
        # 위험 없음
        return {
            "verdict_type": None,
            "verdict_text": "이번 달은 구조적으로 안정적인 상태입니다.",
            "reasons": [
                {"title": "수익 구조", "value": "정상 범위"},
                {"title": "메뉴 수익", "value": "정상 범위"},
            ],
            "target_page": "매출 관리",
            "button_label": "📊 매출 관리 보러가기"
        }
    except Exception as e:
        return {
            "verdict_type": None,
            "verdict_text": "판결 분석 중 오류가 발생했습니다.",
            "reasons": [],
            "target_page": "점장 마감",
            "button_label": "📋 점장 마감 하러가기"
        }


def _check_design_based_risks(insights: dict, store_id: str, year: int, month: int, monthly_sales: int) -> dict | None:
    """설계 DB 기반 위험 판단 (우선순위 높음)"""
    try:
        # 1순위: 메뉴 수익 구조 위험 (마진 메뉴 0개)
        menu_profit = insights.get("menu_profit", {})
        menu_portfolio = insights.get("menu_portfolio", {})
        
        if menu_portfolio.get("has_data") and menu_portfolio.get("margin_menu_count", 0) == 0:
            menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
            if not menu_df.empty and len(menu_df) >= 3:
                return {
                    "verdict_type": "menu_profit",
                    "verdict_text": "메뉴 수익 구조가 위험합니다. 마진 메뉴가 없어 수익 기여도가 낮습니다.",
                    "reasons": [
                        {"title": "마진 메뉴", "value": "0개 (필요: 최소 1개)"},
                        {"title": "총 메뉴 수", "value": f"{len(menu_df)}개"},
                    ],
                    "target_page": "메뉴 수익 구조 설계실",
                    "button_label": "💰 메뉴 수익 구조 설계실"
                }
        
        # 2순위: 재료 구조 위험 (TOP3 집중 >= 70% AND 대체재 미설정)
        ingredient = insights.get("ingredient_structure", {})
        if ingredient.get("has_data"):
            top3_concentration = ingredient.get("top3_concentration", 0.0)
            missing_substitute = ingredient.get("missing_substitute_count", 0)
            
            if top3_concentration >= 0.70 and missing_substitute > 0:
                return {
                    "verdict_type": "ingredient_structure",
                    "verdict_text": "재료 구조가 위험합니다. 상위 3개 재료에 과도하게 집중되어 있고 대체재가 설정되지 않았습니다.",
                    "reasons": [
                        {"title": "TOP3 집중도", "value": f"{top3_concentration * 100:.1f}%"},
                        {"title": "대체재 미설정", "value": f"{missing_substitute}개"},
                    ],
                    "target_page": "재료 등록",
                    "button_label": "🔧 재료 구조 설계실"
                }
        
        # 3순위: 수익 구조 위험 (손익분기점 미달)
        revenue = insights.get("revenue_structure", {})
        if revenue.get("has_data"):
            break_even_gap_ratio = revenue.get("break_even_gap_ratio", 1.0)
            
            if break_even_gap_ratio < 1.0:
                break_even = revenue.get("break_even_sales", 0)
                expected = revenue.get("expected_month_sales", 0)
                gap = break_even - expected
                gap_pct = ((gap / break_even) * 100) if break_even > 0 else 0
                
                return {
                    "verdict_type": "revenue_structure",
                    "verdict_text": "수익 구조가 위험합니다. 예상 매출이 손익분기점보다 낮습니다.",
                    "reasons": [
                        {"title": "손익분기점", "value": f"{break_even:,.0f}원"},
                        {"title": "예상 매출", "value": f"{expected:,.0f}원 (부족: {gap_pct:.1f}%)"},
                    ],
                    "target_page": "수익 구조 설계실",
                    "button_label": "💰 수익 구조 설계실"
                }
        
        return None
    except Exception:
        return None


def _check_revenue_structure_risk(store_id: str, year: int, month: int, monthly_sales: int) -> dict | None:
    """수익 구조 위험 판단 (손익분기점, 고정비, 변동비율)"""
    try:
        break_even = calculate_break_even_sales(store_id, year, month)
        fixed_costs = get_fixed_costs(store_id, year, month)
        variable_ratio = get_variable_cost_ratio(store_id, year, month)
        
        if break_even <= 0 or fixed_costs <= 0:
            return None
        
        reasons = []
        risk_score = 0
        
        # 손익분기점 위험
        if monthly_sales < break_even:
            gap = break_even - monthly_sales
            gap_pct = (gap / break_even * 100) if break_even > 0 else 0
            reasons.append({
                "title": "손익분기점 미달",
                "value": f"{gap:,.0f}원 ({gap_pct:.1f}%)"
            })
            risk_score += 3
        
        # 고정비 위험 (월매출 대비 30% 이상)
        fixed_ratio = (fixed_costs / monthly_sales * 100) if monthly_sales > 0 else 0
        if fixed_ratio >= 30:
            reasons.append({
                "title": "고정비 비율",
                "value": f"{fixed_ratio:.1f}% (위험: 30% 이상)"
            })
            risk_score += 2
        elif fixed_ratio >= 20:
            reasons.append({
                "title": "고정비 비율",
                "value": f"{fixed_ratio:.1f}% (주의: 20% 이상)"
            })
            risk_score += 1
        
        # 변동비율 위험 (50% 이상)
        variable_pct = variable_ratio * 100
        if variable_pct >= 50:
            reasons.append({
                "title": "변동비율",
                "value": f"{variable_pct:.1f}% (위험: 50% 이상)"
            })
            risk_score += 2
        elif variable_pct >= 40:
            reasons.append({
                "title": "변동비율",
                "value": f"{variable_pct:.1f}% (주의: 40% 이상)"
            })
            risk_score += 1
        
        if risk_score >= 3 and reasons:
            verdict_text = "수익 구조가 위험한 상태입니다. 손익분기점 미달 또는 비용 구조 불안정이 확인되었습니다."
            return {
                "verdict_type": "revenue_structure",
                "verdict_text": verdict_text,
                "reasons": reasons[:3],  # 최대 3개
                "target_page": "목표 비용구조",
                "button_label": "💰 수익 구조 설계실"
            }
        
        return None
    except Exception:
        return None


def _check_menu_profit_risk(store_id: str, year: int, month: int, monthly_sales: int) -> dict | None:
    """메뉴 수익 구조 위험 판단 (원가율, 공헌이익, 저마진 매출 집중)"""
    try:
        # 메뉴별 원가 데이터 로드
        menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
        if menu_df.empty:
            return None
        
        # 레시피 데이터로 원가 계산 (간단 버전)
        recipes_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
        ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단가'])
        
        if recipes_df.empty or ingredient_df.empty:
            return None
        
        # 메뉴별 원가 계산
        menu_costs = {}
        for _, menu_row in menu_df.iterrows():
            menu_name = menu_row.get('메뉴명', '')
            menu_recipes = recipes_df[recipes_df['메뉴명'] == menu_name]
            total_cost = 0.0
            for _, recipe_row in menu_recipes.iterrows():
                ing_name = recipe_row.get('재료명', '')
                usage = float(recipe_row.get('사용량', 0) or 0)
                ing_info = ingredient_df[ingredient_df['재료명'] == ing_name]
                if not ing_info.empty:
                    unit_price = float(ing_info.iloc[0].get('단가', 0) or 0)
                    total_cost += usage * unit_price
            menu_costs[menu_name] = total_cost
        
        # 원가율 및 공헌이익 계산
        high_cost_rate_menus = []
        low_margin_menus = []
        
        for menu_name, cost in menu_costs.items():
            menu_info = menu_df[menu_df['메뉴명'] == menu_name]
            if not menu_info.empty:
                price = float(menu_info.iloc[0].get('판매가', 0) or 0)
                if price > 0:
                    cost_rate = (cost / price * 100)
                    contribution = price - cost
                    margin_rate = (contribution / price * 100) if price > 0 else 0
                    
                    # 원가율 50% 이상
                    if cost_rate >= 50:
                        high_cost_rate_menus.append({
                            "name": menu_name,
                            "cost_rate": cost_rate,
                            "margin_rate": margin_rate
                        })
                    
                    # 마진율 20% 미만
                    if margin_rate < 20:
                        low_margin_menus.append({
                            "name": menu_name,
                            "cost_rate": cost_rate,
                            "margin_rate": margin_rate
                        })
        
        reasons = []
        risk_score = 0
        
        # 고원가율 메뉴 위험
        if len(high_cost_rate_menus) >= 3:
            top_menu = high_cost_rate_menus[0]
            reasons.append({
                "title": "고원가율 메뉴",
                "value": f"{len(high_cost_rate_menus)}개 (예: {top_menu['name']} {top_menu['cost_rate']:.1f}%)"
            })
            risk_score += 2
        
        # 저마진 메뉴 위험
        if len(low_margin_menus) >= 3:
            top_menu = low_margin_menus[0]
            reasons.append({
                "title": "저마진 메뉴",
                "value": f"{len(low_margin_menus)}개 (예: {top_menu['name']} 마진 {top_menu['margin_rate']:.1f}%)"
            })
            risk_score += 2
        
        if risk_score >= 2 and reasons:
            verdict_text = "메뉴 수익 구조가 위험한 상태입니다. 고원가율 또는 저마진 메뉴가 다수 확인되었습니다."
            return {
                "verdict_type": "menu_profit",
                "verdict_text": verdict_text,
                "reasons": reasons[:3],
                "target_page": "원가 파악",
                "button_label": "💰 메뉴 수익 구조 설계실"
            }
        
        return None
    except Exception:
        return None


def _check_ingredient_structure_risk(store_id: str, year: int, month: int) -> dict | None:
    """재료 구조 위험 판단 (원가 TOP 재료 집중/의존)"""
    try:
        # 재료별 사용량 집계 (최근 30일)
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        start_date = (today - __import__('datetime').timedelta(days=30)).isoformat()
        end_date = today.isoformat()
        
        # daily_sales_items에서 재료별 사용량 집계
        supabase = get_supabase_client()
        if not supabase:
            return None
        
        # 메뉴별 판매량 조회 (메뉴명으로 조회)
        # daily_sales_items는 menu_id를 사용하므로, menu_master와 조인 필요
        # 간단 버전: 메뉴명으로 직접 조회 (v_daily_sales_items_effective 사용)
        try:
            sales_items_result = supabase.table("v_daily_sales_items_effective")\
                .select("menu_name, qty, date")\
                .eq("store_id", store_id)\
                .gte("date", start_date)\
                .lt("date", end_date)\
                .execute()
        except Exception:
            # view가 없으면 daily_sales_items 직접 조회
            sales_items_result = supabase.table("daily_sales_items")\
                .select("menu_id, qty, date")\
                .eq("store_id", store_id)\
                .gte("date", start_date)\
                .lt("date", end_date)\
                .execute()
        
        if not sales_items_result.data:
            return None
        
        # 레시피 데이터로 재료별 사용량 계산
        recipes_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
        if recipes_df.empty:
            return None
        
        # 재료별 총 사용량 집계
        ingredient_usage = {}
        for item in sales_items_result.data:
            # view 사용 시 menu_name, 직접 조회 시 menu_id
            menu_name = item.get('menu_name')
            if not menu_name:
                # menu_id인 경우 메뉴명 조회
                menu_id = item.get('menu_id')
                if menu_id:
                    menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['id', '메뉴명'])
                    menu_info = menu_df[menu_df['id'] == str(menu_id)]
                    if not menu_info.empty:
                        menu_name = menu_info.iloc[0].get('메뉴명', '')
            
            if menu_name:
                qty = float(item.get('qty', 0) or 0)
                menu_recipes = recipes_df[recipes_df['메뉴명'] == menu_name]
                for _, recipe_row in menu_recipes.iterrows():
                    ing_name = recipe_row.get('재료명', '')
                    usage = float(recipe_row.get('사용량', 0) or 0)
                    if ing_name not in ingredient_usage:
                        ingredient_usage[ing_name] = 0.0
                    ingredient_usage[ing_name] += usage * qty
        
        if not ingredient_usage:
            return None
        
        # 재료별 사용량 정렬
        sorted_ingredients = sorted(ingredient_usage.items(), key=lambda x: x[1], reverse=True)
        total_usage = sum(ingredient_usage.values())
        
        if total_usage <= 0:
            return None
        
        # TOP 3 재료 집중도 계산
        top3_usage = sum([v for _, v in sorted_ingredients[:3]])
        top3_ratio = (top3_usage / total_usage * 100) if total_usage > 0 else 0
        
        reasons = []
        risk_score = 0
        
        # 재료 집중도 위험 (TOP 3가 70% 이상)
        if top3_ratio >= 70:
            top_names = [name for name, _ in sorted_ingredients[:3]]
            reasons.append({
                "title": "재료 집중도",
                "value": f"TOP 3 재료가 {top3_ratio:.1f}% 차지"
            })
            reasons.append({
                "title": "주요 재료",
                "value": ", ".join(top_names[:3])
            })
            risk_score += 2
        
        if risk_score >= 2 and reasons:
            verdict_text = "재료 구조가 위험한 상태입니다. 특정 재료에 과도하게 의존하고 있습니다."
            return {
                "verdict_type": "ingredient_structure",
                "verdict_text": verdict_text,
                "reasons": reasons[:3],
                "target_page": "재료 등록",
                "button_label": "🔧 재료 구조 설계실"
            }
        
        return None
    except Exception:
        return None
