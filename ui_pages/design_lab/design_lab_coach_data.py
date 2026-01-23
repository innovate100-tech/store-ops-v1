"""
설계실별 Coach Board 데이터 생성
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.storage_supabase import (
    load_csv,
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
    load_monthly_sales_total,
)
from src.analytics import calculate_menu_cost
from src.auth import get_current_store_id, get_supabase_client


def get_menu_design_coach_data(store_id: str) -> dict:
    """메뉴 설계실 Coach Board 데이터"""
    try:
        menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
        
        cards = []
        menu_count = len(menu_df) if not menu_df.empty else 0
        cards.append({
            "title": "메뉴 개수",
            "value": f"{menu_count}개",
            "subtitle": None
        })
        
        if not menu_df.empty and '판매가' in menu_df.columns:
            avg_price = menu_df['판매가'].mean()
            cards.append({
                "title": "평균 가격",
                "value": f"{int(avg_price):,}원",
                "subtitle": None
            })
            
            # 평균 원가율 계산 (가능하면)
            try:
                recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
                ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단가'])
                
                if not recipe_df.empty and not ingredient_df.empty:
                    cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
                    if not cost_df.empty and '원가율' in cost_df.columns:
                        avg_cost_rate = cost_df['원가율'].mean()
                        cards.append({
                            "title": "평균 원가율",
                            "value": f"{avg_cost_rate:.1f}%",
                            "subtitle": None
                        })
            except Exception:
                pass
        
        # 판결문
        if menu_count == 0:
            verdict_text = "메뉴가 등록되지 않았습니다. 메뉴를 등록하면 판매/원가 분석이 시작됩니다."
            action_title = "메뉴 등록 시작하기"
            action_reason = "메뉴가 있어야 판매/원가/분석이 의미가 생깁니다."
            action_target_page = "메뉴 등록"
        elif menu_count < 3:
            verdict_text = f"현재 {menu_count}개 메뉴만 등록되어 있습니다. 최소 3개 이상 등록하면 메뉴별 분석이 가능합니다."
            action_title = "메뉴 추가하기"
            action_reason = "메뉴가 3개 이상이면 판매 패턴 분석이 시작됩니다."
            action_target_page = "메뉴 등록"
        else:
            verdict_text = f"현재 {menu_count}개 메뉴가 등록되어 있습니다. 메뉴별 판매 흐름과 원가 분석이 가능합니다."
            action_title = None
            action_reason = None
            action_target_page = None
        
        return {
            "cards": cards,
            "verdict_text": verdict_text,
            "action_title": action_title,
            "action_reason": action_reason,
            "action_target_page": action_target_page,
            "action_button_label": "메뉴 등록 하러가기" if action_target_page else None
        }
    except Exception:
        return {
            "cards": [{"title": "메뉴 개수", "value": "-", "subtitle": None}],
            "verdict_text": "데이터를 불러올 수 없습니다.",
            "action_title": None,
            "action_reason": None,
            "action_target_page": None,
            "action_button_label": None
        }


def get_ingredient_design_coach_data(store_id: str) -> dict:
    """재료 구조 설계실 Coach Board 데이터"""
    try:
        ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
        
        cards = []
        ingredient_count = len(ingredient_df) if not ingredient_df.empty else 0
        cards.append({
            "title": "재료 개수",
            "value": f"{ingredient_count}개",
            "subtitle": None
        })
        
        # 안전재고 설정 개수
        try:
            inventory_df = load_csv('inventory.csv', store_id=store_id, default_columns=['재료명', '안전재고'])
            safety_stock_count = len(inventory_df[inventory_df['안전재고'] > 0]) if not inventory_df.empty else 0
            cards.append({
                "title": "안전재고 설정",
                "value": f"{safety_stock_count}개",
                "subtitle": None
            })
        except Exception:
            pass
        
        # 원가 TOP 재료 (가능하면)
        try:
            if not ingredient_df.empty and '단가' in ingredient_df.columns:
                top_ingredient = ingredient_df.nlargest(1, '단가')
                if not top_ingredient.empty:
                    top_name = top_ingredient.iloc[0].get('재료명', '')
                    top_price = top_ingredient.iloc[0].get('단가', 0)
                    cards.append({
                        "title": "최고 단가 재료",
                        "value": top_name[:10] if len(top_name) > 10 else top_name,
                        "subtitle": f"{float(top_price):,.0f}원/단위"
                    })
        except Exception:
            pass
        
        # 판결문
        if ingredient_count == 0:
            verdict_text = "재료가 등록되지 않았습니다. 재료를 등록하면 레시피와 원가 계산이 가능합니다."
            action_title = "재료 등록 시작하기"
            action_reason = "재료가 있어야 레시피와 원가 계산이 시작됩니다."
            action_target_page = "재료 등록"
        elif ingredient_count < 5:
            verdict_text = f"현재 {ingredient_count}개 재료만 등록되어 있습니다. 더 많은 재료를 등록하면 정확한 원가 계산이 가능합니다."
            action_title = "재료 추가하기"
            action_reason = "재료가 5개 이상이면 원가 계산 정확도가 향상됩니다."
            action_target_page = "재료 등록"
        else:
            verdict_text = f"현재 {ingredient_count}개 재료가 등록되어 있습니다. 재료 구조가 안정적으로 관리되고 있습니다."
            action_title = None
            action_reason = None
            action_target_page = None
        
        return {
            "cards": cards,
            "verdict_text": verdict_text,
            "action_title": action_title,
            "action_reason": action_reason,
            "action_target_page": action_target_page,
            "action_button_label": "재료 등록 하러가기" if action_target_page else None
        }
    except Exception:
        return {
            "cards": [{"title": "재료 개수", "value": "-", "subtitle": None}],
            "verdict_text": "데이터를 불러올 수 없습니다.",
            "action_title": None,
            "action_reason": None,
            "action_target_page": None,
            "action_button_label": None
        }


def get_menu_profit_design_coach_data(store_id: str) -> dict:
    """메뉴 수익 구조 설계실 Coach Board 데이터"""
    try:
        menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
        recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
        ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단가'])
        
        cards = []
        
        if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
            cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
            
            if not cost_df.empty and '원가율' in cost_df.columns:
                # 원가율 35% 초과 메뉴 수
                high_cost_menus = cost_df[cost_df['원가율'] > 35]
                high_cost_count = len(high_cost_menus)
                cards.append({
                    "title": "고원가율 메뉴",
                    "value": f"{high_cost_count}개",
                    "subtitle": "원가율 35% 초과"
                })
                
                # 최고/최저 원가율 메뉴
                if not cost_df.empty:
                    max_cost_rate = cost_df['원가율'].max()
                    min_cost_rate = cost_df['원가율'].min()
                    max_menu = cost_df[cost_df['원가율'] == max_cost_rate].iloc[0]
                    min_menu = cost_df[cost_df['원가율'] == min_cost_rate].iloc[0]
                    
                    cards.append({
                        "title": "최고 원가율",
                        "value": f"{max_cost_rate:.1f}%",
                        "subtitle": max_menu.get('메뉴명', '')[:15]
                    })
                    
                    cards.append({
                        "title": "최저 원가율",
                        "value": f"{min_cost_rate:.1f}%",
                        "subtitle": min_menu.get('메뉴명', '')[:15]
                    })
        
        # 판결문
        high_cost_count = 0
        if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
            if not cost_df.empty and '원가율' in cost_df.columns:
                high_cost_menus = cost_df[cost_df['원가율'] > 35]
                high_cost_count = len(high_cost_menus)
        
        if menu_df.empty or recipe_df.empty or ingredient_df.empty:
            verdict_text = "메뉴, 레시피, 재료 데이터가 모두 필요합니다. 데이터를 채우면 메뉴별 원가 분석이 가능합니다."
            action_title = "데이터 입력하기"
            action_reason = "메뉴/레시피/재료가 모두 있어야 원가 분석이 시작됩니다."
            action_target_page = "메뉴 등록"
        elif high_cost_count > 0:
            verdict_text = f"원가율 35%를 초과하는 메뉴가 {high_cost_count}개 있습니다. 가격 조정 또는 메뉴 교체를 고려하세요."
            action_title = "가격 조정 후보 TOP3 확인"
            action_reason = "고원가율 메뉴는 수익 기여도가 낮을 수 있습니다."
            action_target_page = "메뉴 수익 구조 설계실"
        else:
            verdict_text = "메뉴별 원가 구조가 안정적인 범위에 있습니다."
            action_title = None
            action_reason = None
            action_target_page = None
        
        return {
            "cards": cards if cards else [{"title": "원가율 분석", "value": "-", "subtitle": "데이터 필요"}],
            "verdict_text": verdict_text,
            "action_title": action_title,
            "action_reason": action_reason,
            "action_target_page": action_target_page,
            "action_button_label": "메뉴 수익 구조 설계실 보러가기" if action_target_page else None
        }
    except Exception:
        return {
            "cards": [{"title": "원가율 분석", "value": "-", "subtitle": None}],
            "verdict_text": "데이터를 불러올 수 없습니다.",
            "action_title": None,
            "action_reason": None,
            "action_target_page": None,
            "action_button_label": None
        }


def get_revenue_structure_design_coach_data(store_id: str, year: int, month: int) -> dict:
    """수익 구조 설계실 Coach Board 데이터"""
    try:
        fixed_costs = get_fixed_costs(store_id, year, month)
        variable_ratio = get_variable_cost_ratio(store_id, year, month)
        break_even = calculate_break_even_sales(store_id, year, month)
        monthly_sales = load_monthly_sales_total(store_id, year, month) or 0
        
        cards = []
        
        # 고정비 합계
        cards.append({
            "title": "고정비 합계",
            "value": f"{int(fixed_costs):,}원",
            "subtitle": None
        })
        
        # 변동비율
        variable_pct = variable_ratio * 100
        cards.append({
            "title": "변동비율",
            "value": f"{variable_pct:.1f}%",
            "subtitle": None
        })
        
        # 손익분기점
        if break_even > 0:
            cards.append({
                "title": "손익분기점",
                "value": f"{int(break_even):,}원",
                "subtitle": None
            })
            
            # 손익분기점 대비 매출
            if monthly_sales > 0:
                be_ratio = (monthly_sales / break_even * 100) if break_even > 0 else 0
                cards.append({
                    "title": "손익분기점 대비",
                    "value": f"{be_ratio:.1f}%",
                    "subtitle": None
                })
        
        # 판결문
        if fixed_costs <= 0:
            verdict_text = "고정비가 설정되지 않았습니다. 고정비를 입력하면 손익분기점 계산이 가능합니다."
            action_title = "고정비 입력하기"
            action_reason = "고정비가 있어야 손익분기점과 수익 구조 분석이 시작됩니다."
            action_target_page = "목표 비용구조"
        elif break_even > 0 and monthly_sales < break_even:
            gap = break_even - monthly_sales
            verdict_text = f"현재 매출이 손익분기점보다 약 {gap:,.0f}원 부족합니다. 매출 증대 또는 비용 절감이 필요합니다."
            action_title = "수익 구조 분석하기"
            action_reason = "손익분기점 미달 시 구조 조정이 필요합니다."
            action_target_page = "수익 구조 설계실"
        elif variable_pct >= 50:
            verdict_text = f"변동비율이 {variable_pct:.1f}%로 높습니다. 원가 관리가 시급합니다."
            action_title = "원가 관리하기"
            action_reason = "변동비율이 50% 이상이면 수익성이 낮을 수 있습니다."
            action_target_page = "메뉴 수익 구조 설계실"
        else:
            verdict_text = "수익 구조가 안정적인 범위에 있습니다."
            action_title = None
            action_reason = None
            action_target_page = None
        
        return {
            "cards": cards,
            "verdict_text": verdict_text,
            "action_title": action_title,
            "action_reason": action_reason,
            "action_target_page": action_target_page,
            "action_button_label": "수익 구조 설계실 보러가기" if action_target_page else None
        }
    except Exception:
        return {
            "cards": [{"title": "고정비 합계", "value": "-", "subtitle": None}],
            "verdict_text": "데이터를 불러올 수 없습니다.",
            "action_title": None,
            "action_reason": None,
            "action_target_page": None,
            "action_button_label": None
        }
