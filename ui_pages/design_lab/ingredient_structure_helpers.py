"""
재료 구조 설계실 헬퍼 함수
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple, Optional
from src.storage_supabase import load_csv, get_read_client, get_current_store_id
from src.auth import get_current_store_id


def calculate_ingredient_usage_cost(store_id: str) -> pd.DataFrame:
    """
    재료별 사용금액 계산
    
    계산식: daily_sales_items × recipes × ingredients.unit_cost
    
    Returns:
        DataFrame with columns: ['재료명', '총_사용금액', '원가_비중_%', '연결_메뉴_수', '연결_메뉴_목록']
    """
    try:
        # 1. 재료 마스터 로드
        ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
        if ingredient_df.empty:
            return pd.DataFrame(columns=['재료명', '총_사용금액', '원가_비중_%', '연결_메뉴_수', '연결_메뉴_목록'])
        
        # 2. 레시피 로드
        recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
        if recipe_df.empty:
            return pd.DataFrame(columns=['재료명', '총_사용금액', '원가_비중_%', '연결_메뉴_수', '연결_메뉴_목록'])
        
        # 3. 판매량 데이터 로드 (최근 30일 또는 이번 달)
        sales_items_df = load_csv('daily_sales_items_effective.csv', store_id=store_id, default_columns=['날짜', '메뉴명', '판매수량'])
        if sales_items_df.empty:
            # 판매량 데이터가 없으면 레시피 기반으로만 계산 (사용량만)
            sales_items_df = pd.DataFrame(columns=['날짜', '메뉴명', '판매수량'])
        
        # 4. 재료별 사용금액 계산
        ingredient_usage = {}
        
        for _, ingredient_row in ingredient_df.iterrows():
            ingredient_name = ingredient_row['재료명']
            unit_cost = float(ingredient_row.get('단가', 0))
            
            if unit_cost <= 0:
                continue
            
            # 이 재료를 사용하는 메뉴 찾기
            recipes_using = recipe_df[recipe_df['재료명'] == ingredient_name]
            if recipes_using.empty:
                continue
            
            total_cost = 0.0
            menu_list = set()
            
            for _, recipe_row in recipes_using.iterrows():
                menu_name = recipe_row['메뉴명']
                usage_qty = float(recipe_row.get('사용량', 0))
                
                menu_list.add(menu_name)
                
                # 이 메뉴의 판매량 합계
                if not sales_items_df.empty and '메뉴명' in sales_items_df.columns:
                    menu_sales = sales_items_df[sales_items_df['메뉴명'] == menu_name]
                    if not menu_sales.empty and '판매수량' in menu_sales.columns:
                        total_qty = menu_sales['판매수량'].sum()
                    else:
                        # 판매량 데이터가 없으면 기본값 1 (레시피만 고려)
                        total_qty = 1
                else:
                    total_qty = 1
                
                # 사용금액 = 판매수량 × 사용량 × 단가
                cost = total_qty * usage_qty * unit_cost
                total_cost += cost
            
            if total_cost > 0:
                ingredient_usage[ingredient_name] = {
                    '총_사용금액': total_cost,
                    '연결_메뉴_수': len(menu_list),
                    '연결_메뉴_목록': list(menu_list)
                }
        
        if not ingredient_usage:
            return pd.DataFrame(columns=['재료명', '총_사용금액', '원가_비중_%', '연결_메뉴_수', '연결_메뉴_목록'])
        
        # DataFrame 생성
        result_df = pd.DataFrame([
            {
                '재료명': name,
                '총_사용금액': data['총_사용금액'],
                '연결_메뉴_수': data['연결_메뉴_수'],
                '연결_메뉴_목록': ', '.join(data['연결_메뉴_목록'])
            }
            for name, data in ingredient_usage.items()
        ])
        
        # 원가 비중 계산
        total_cost = result_df['총_사용금액'].sum()
        if total_cost > 0:
            result_df['원가_비중_%'] = (result_df['총_사용금액'] / total_cost * 100).round(2)
        else:
            result_df['원가_비중_%'] = 0.0
        
        # 총 사용금액 내림차순 정렬
        result_df = result_df.sort_values('총_사용금액', ascending=False).reset_index(drop=True)
        
        return result_df
        
    except Exception as e:
        st.error(f"재료 사용금액 계산 중 오류: {e}")
        return pd.DataFrame(columns=['재료명', '총_사용금액', '원가_비중_%', '연결_메뉴_수', '연결_메뉴_목록'])


def calculate_cost_concentration(ingredient_usage_df: pd.DataFrame) -> Tuple[float, float]:
    """
    원가 집중도 계산 (TOP3, TOP5)
    
    Returns:
        (top3_concentration: float, top5_concentration: float) - 비율 (%)
    """
    if ingredient_usage_df.empty:
        return 0.0, 0.0
    
    total_cost = ingredient_usage_df['총_사용금액'].sum()
    if total_cost == 0:
        return 0.0, 0.0
    
    top3_cost = ingredient_usage_df.head(3)['총_사용금액'].sum()
    top5_cost = ingredient_usage_df.head(5)['총_사용금액'].sum()
    
    top3_pct = (top3_cost / total_cost * 100) if total_cost > 0 else 0.0
    top5_pct = (top5_cost / total_cost * 100) if total_cost > 0 else 0.0
    
    return top3_pct, top5_pct


def identify_high_risk_ingredients(ingredient_usage_df: pd.DataFrame, cost_threshold: float = 20.0, menu_threshold: int = 3) -> pd.DataFrame:
    """
    고위험 재료 판별
    
    기준:
    - 원가 비중 상위 threshold% AND 연결 메뉴 수 >= menu_threshold
    
    Args:
        ingredient_usage_df: calculate_ingredient_usage_cost 결과
        cost_threshold: 원가 비중 임계값 (%)
        menu_threshold: 연결 메뉴 수 임계값
    
    Returns:
        고위험 재료 DataFrame
    """
    if ingredient_usage_df.empty:
        return pd.DataFrame(columns=['재료명', '총_사용금액', '원가_비중_%', '연결_메뉴_수', '연결_메뉴_목록', '위험_사유'])
    
    # 원가 비중 상위 threshold% 계산
    total_cost = ingredient_usage_df['총_사용금액'].sum()
    threshold_cost = total_cost * (cost_threshold / 100.0)
    
    cumulative_cost = 0.0
    top_ingredients = []
    
    for _, row in ingredient_usage_df.iterrows():
        cumulative_cost += row['총_사용금액']
        if cumulative_cost <= threshold_cost:
            top_ingredients.append(row['재료명'])
        else:
            break
    
    # 고위험 재료 필터링
    high_risk = ingredient_usage_df[
        (ingredient_usage_df['재료명'].isin(top_ingredients)) &
        (ingredient_usage_df['연결_메뉴_수'] >= menu_threshold)
    ].copy()
    
    # 위험 사유 추가
    def get_risk_reason(row):
        reasons = []
        if row['원가_비중_%'] >= cost_threshold:
            reasons.append(f"원가 비중 {row['원가_비중_%']:.1f}%")
        if row['연결_메뉴_수'] >= menu_threshold:
            reasons.append(f"연결 메뉴 {row['연결_메뉴_수']}개")
        return " / ".join(reasons) if reasons else "기타"
    
    high_risk['위험_사유'] = high_risk.apply(get_risk_reason, axis=1)
    
    return high_risk


def check_order_structure_status(store_id: str) -> Tuple[str, str]:
    """
    발주 구조 상태 판정
    
    Returns:
        (status: str, reason: str)
        status: "안전" | "주의" | "위험"
    """
    try:
        # 재료 마스터 로드
        ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
        if ingredient_df.empty:
            return "위험", "재료가 등록되지 않았습니다"
        
        # 공급업체 정보 확인 (suppliers 테이블 또는 ingredient에 supplier_id 컬럼)
        # 일단 간단하게: 발주단위가 설정되어 있는지 확인
        has_order_unit = '발주단위' in ingredient_df.columns
        if has_order_unit:
            order_unit_set = ingredient_df['발주단위'].notna().sum()
            total_ingredients = len(ingredient_df)
            
            if order_unit_set == 0:
                return "위험", "발주 단위가 설정되지 않은 재료가 있습니다"
            elif order_unit_set < total_ingredients * 0.8:
                return "주의", f"발주 단위 미설정 재료 {total_ingredients - order_unit_set}개"
            else:
                return "안전", "발주 구조가 안정적입니다"
        else:
            return "주의", "발주 단위 정보가 없습니다"
            
    except Exception as e:
        return "위험", f"발주 구조 확인 중 오류: {e}"


def get_ingredient_structure_verdict(store_id: str, ingredient_usage_df: pd.DataFrame, high_risk_df: pd.DataFrame, top3_concentration: float) -> Tuple[str, str, str]:
    """
    재료 구조 판결문 생성
    
    Returns:
        (verdict_text: str, action_title: str, action_target_page: str)
    """
    if ingredient_usage_df.empty:
        return "재료가 등록되지 않았습니다. 재료를 등록하면 구조 분석이 시작됩니다.", "재료 등록 시작하기", "재료 등록"
    
    # 판결 우선순위
    if top3_concentration >= 70:
        return f"현재 원가의 {top3_concentration:.1f}%가 상위 3개 재료에 집중되어 있습니다. 가격 변동에 매우 취약합니다.", "고위험 재료 보기", "재료 구조 설계실"
    
    if not high_risk_df.empty:
        high_risk_count = len(high_risk_df)
        return f"고위험 재료가 {high_risk_count}개 발견되었습니다. 이 중 일부는 여러 메뉴에 동시에 사용되어 구조 리스크가 큽니다.", "고위험 재료 보기", "재료 구조 설계실"
    
    if top3_concentration >= 50:
        return f"원가의 {top3_concentration:.1f}%가 상위 3개 재료에 집중되어 있습니다. 대체 구조를 검토하세요.", "대체 구조 설계", "재료 구조 설계실"
    
    return "재료 구조가 비교적 안정적입니다. 주기적으로 집중도를 확인하세요.", None, None
