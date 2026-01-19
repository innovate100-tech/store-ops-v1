"""
Supabase 기반 저장소 모듈 (기존 storage.py의 DB 버전)
auth.uid() 기반 RLS로 보안 적용
"""
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, List, Tuple
import json

# auth.py에서 함수 import
from src.auth import get_supabase_client, get_current_store_id
import streamlit as st

logger = logging.getLogger(__name__)


def setup_logger():
    """로깅 시스템 설정"""
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger


setup_logger()


# ============================================
# Helper Functions
# ============================================

def _check_supabase_for_dev_mode():
    """
    Supabase 클라이언트 반환 (에러 처리)
    
    DEV MODE(st.session_state['dev_mode'] == True)에서는
    Supabase를 사용하지 않으므로 None을 반환하고,
    호출하는 쪽에서 이를 감지해 로컬/빈 데이터로 처리하게 한다.
    """
    # DEV MODE에서는 Supabase를 사용하지 않음
    if st.session_state.get("dev_mode", False):
        logger.info("DEV MODE: Supabase client is disabled (returning None).")
        return None
    
    supabase = get_supabase_client()
    if not supabase:
        raise Exception("Supabase not available")
    return supabase


# ============================================
# Load Functions (CSV 호환 인터페이스 유지)
# ============================================

@st.cache_data(ttl=120)  # 2분 캐시 (동적 데이터와 마스터 데이터 모두 고려)
def load_csv(filename: str, default_columns: Optional[List[str]] = None):
    """
    테이블에서 데이터 로드 (CSV 호환 인터페이스)
    
    Args:
        filename: CSV 파일명 (예: "sales.csv") -> 테이블명으로 매핑
        default_columns: 기본 컬럼 리스트
    
    Returns:
        pandas.DataFrame
    """
    supabase = get_supabase_client()
    if not supabase:
        logger.warning(f"Supabase not available, returning empty DataFrame for {filename}")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    store_id = get_current_store_id()
    if not store_id:
        logger.warning(f"No store_id found, returning empty DataFrame for {filename}")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    try:
        # CSV 파일명 -> DB 테이블명 매핑
        table_mapping = {
            'sales.csv': 'sales',
            'naver_visitors.csv': 'naver_visitors',
            'menu_master.csv': 'menu_master',
            'ingredient_master.csv': 'ingredients',
            'recipes.csv': 'recipes',
            'daily_sales_items.csv': 'daily_sales_items',
            'inventory.csv': 'inventory',
            'targets.csv': 'targets',
            'abc_history.csv': 'abc_history',
            'daily_close.csv': 'daily_close',
            # 파일명 없이 테이블명으로 직접 호출 가능
            'sales': 'sales',
            'naver_visitors': 'naver_visitors',
            'menu_master': 'menu_master',
            'ingredient_master': 'ingredients',
            'recipes': 'recipes',
            'daily_sales_items': 'daily_sales_items',
            'inventory': 'inventory',
            'targets': 'targets',
            'abc_history': 'abc_history',
            'daily_close': 'daily_close'
        }
        
        actual_table = table_mapping.get(filename, filename.replace('.csv', ''))
        
        # store_id로 필터링하여 조회 (RLS가 자동으로 적용됨)
        result = supabase.table(actual_table).select("*").eq("store_id", store_id).execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            
            # 컬럼명 변환 (DB -> CSV 호환)
            if actual_table == 'sales':
                if 'date' in df.columns:
                    df['날짜'] = pd.to_datetime(df['date'])
                if 'card_sales' in df.columns:
                    df['카드매출'] = df['card_sales']
                if 'cash_sales' in df.columns:
                    df['현금매출'] = df['cash_sales']
                if 'total_sales' in df.columns:
                    df['총매출'] = df['total_sales']
                # store_id로 매장명 조회
                store_result = supabase.table("stores").select("name").eq("id", store_id).execute()
                if store_result.data:
                    df['매장'] = store_result.data[0]['name']
            
            elif actual_table == 'naver_visitors':
                if 'date' in df.columns:
                    df['날짜'] = pd.to_datetime(df['date'])
                if 'visitors' in df.columns:
                    df['방문자수'] = df['visitors']
            
            elif actual_table == 'menu_master':
                if 'name' in df.columns:
                    df['메뉴명'] = df['name']
                if 'price' in df.columns:
                    df['판매가'] = df['price']
            
            elif actual_table == 'ingredients':
                if 'name' in df.columns:
                    df['재료명'] = df['name']
                if 'unit' in df.columns:
                    df['단위'] = df['unit']
                if 'unit_cost' in df.columns:
                    df['단가'] = df['unit_cost']
            
            elif actual_table == 'recipes':
                # menu_id와 ingredient_id를 이름으로 변환
                if 'menu_id' in df.columns:
                    menu_ids = df['menu_id'].dropna().unique().tolist()
                    if menu_ids:
                        menu_result = supabase.table("menu_master").select("id,name").in_("id", menu_ids).execute()
                        menu_map = {m['id']: m['name'] for m in menu_result.data}
                        df['메뉴명'] = df['menu_id'].map(menu_map)
                
                if 'ingredient_id' in df.columns:
                    ing_ids = df['ingredient_id'].dropna().unique().tolist()
                    if ing_ids:
                        ing_result = supabase.table("ingredients").select("id,name").in_("id", ing_ids).execute()
                        ing_map = {i['id']: i['name'] for i in ing_result.data}
                        df['재료명'] = df['ingredient_id'].map(ing_map)
                
                if 'qty' in df.columns:
                    df['사용량'] = df['qty']
            
            elif actual_table == 'daily_sales_items':
                if 'date' in df.columns:
                    df['날짜'] = pd.to_datetime(df['date'])
                
                if 'menu_id' in df.columns:
                    menu_ids = df['menu_id'].dropna().unique().tolist()
                    if menu_ids:
                        menu_result = supabase.table("menu_master").select("id,name").in_("id", menu_ids).execute()
                        menu_map = {m['id']: m['name'] for m in menu_result.data}
                        df['메뉴명'] = df['menu_id'].map(menu_map)
                
                if 'qty' in df.columns:
                    df['판매수량'] = df['qty']
            
            elif actual_table == 'inventory':
                if 'ingredient_id' in df.columns:
                    ing_ids = df['ingredient_id'].dropna().unique().tolist()
                    if ing_ids:
                        ing_result = supabase.table("ingredients").select("id,name").in_("id", ing_ids).execute()
                        ing_map = {i['id']: i['name'] for i in ing_result.data}
                        df['재료명'] = df['ingredient_id'].map(ing_map)
                
                if 'on_hand' in df.columns:
                    df['현재고'] = df['on_hand']
                if 'safety_stock' in df.columns:
                    df['안전재고'] = df['safety_stock']
            
            elif actual_table == 'targets':
                if 'year' in df.columns:
                    df['연도'] = df['year']
                if 'month' in df.columns:
                    df['월'] = df['month']
                if 'target_sales' in df.columns:
                    df['목표매출'] = df['target_sales']
                if 'target_cost_rate' in df.columns:
                    df['목표원가율'] = df['target_cost_rate']
                if 'target_labor_rate' in df.columns:
                    df['목표인건비율'] = df['target_labor_rate']
                if 'target_rent_rate' in df.columns:
                    df['목표임대료율'] = df['target_rent_rate']
                if 'target_other_rate' in df.columns:
                    df['목표기타비용율'] = df['target_other_rate']
                if 'target_profit_rate' in df.columns:
                    df['목표순이익률'] = df['target_profit_rate']
            
            elif actual_table == 'abc_history':
                # 컬럼명이 이미 일치하는 경우도 있음
                if 'menu_name' in df.columns:
                    df['메뉴명'] = df['menu_name']
                if 'sales_qty' in df.columns:
                    df['판매량'] = df['sales_qty']
                if 'sales_amount' in df.columns:
                    df['매출'] = df['sales_amount']
                if 'contribution_margin' in df.columns:
                    df['공헌이익'] = df['contribution_margin']
                if 'qty_ratio' in df.columns:
                    df['판매량비중'] = df['qty_ratio']
                if 'sales_ratio' in df.columns:
                    df['매출비중'] = df['sales_ratio']
                if 'margin_ratio' in df.columns:
                    df['공헌이익비중'] = df['margin_ratio']
                if 'abc_grade' in df.columns:
                    df['ABC등급'] = df['abc_grade']
                if 'year' in df.columns:
                    df['연도'] = df['year']
                if 'month' in df.columns:
                    df['월'] = df['month']
            
            return df
        else:
            return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()


@st.cache_data(ttl=300)  # 5분 캐시 (마스터 데이터)
def load_key_menus() -> List[str]:
    """핵심 메뉴 목록 로드 (is_core=True인 메뉴들)"""
    supabase = get_supabase_client()
    if not supabase:
        return []
    
    store_id = get_current_store_id()
    if not store_id:
        return []
    
    try:
        result = supabase.table("menu_master").select("name").eq("store_id", store_id).eq("is_core", True).execute()
        if result.data:
            return [m['name'] for m in result.data]
        return []
    except Exception as e:
        logger.error(f"Failed to load key menus: {e}")
        return []


# ============================================
# Save Functions
# ============================================

def save_sales(date, store_name, card_sales, cash_sales, total_sales=None):
    """매출 데이터 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    if total_sales is None:
        total_sales = card_sales + cash_sales
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        
        result = supabase.table("sales").upsert({
            "store_id": store_id,
            "date": date_str,
            "card_sales": float(card_sales),
            "cash_sales": float(cash_sales),
            "total_sales": float(total_sales)
        }, on_conflict="store_id,date").execute()
        
        logger.info(f"Sales saved: {date_str}, {total_sales}")
        return True
    except Exception as e:
        logger.error(f"Failed to save sales: {e}")
        raise


def save_visitor(date, visitors):
    """방문자 데이터 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        
        result = supabase.table("naver_visitors").upsert({
            "store_id": store_id,
            "date": date_str,
            "visitors": int(visitors)
        }, on_conflict="store_id,date").execute()
        
        logger.info(f"Visitor saved: {date_str}, {visitors}")
        return True
    except Exception as e:
        logger.error(f"Failed to save visitor: {e}")
        raise


def save_menu(menu_name, price):
    """메뉴 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 저장할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 중복 체크
        existing = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if existing.data:
            return False, f"'{menu_name}' 메뉴는 이미 등록되어 있습니다."
        
        result = supabase.table("menu_master").insert({
            "store_id": store_id,
            "name": menu_name,
            "price": float(price),
            "is_core": False
        }).execute()
        
        logger.info(f"Menu saved: {menu_name}, {price}")
        return True, "저장 성공"
    except Exception as e:
        logger.error(f"Failed to save menu: {e}")
        raise


def update_menu(old_menu_name, new_menu_name, new_price, category=None):
    """메뉴 수정"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 기존 메뉴 찾기
        existing = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", old_menu_name).execute()
        if not existing.data:
            return False, f"'{old_menu_name}' 메뉴를 찾을 수 없습니다."
        
        menu_id = existing.data[0]['id']
        
        # 새 메뉴명이 다른 경우 중복 체크
        if new_menu_name != old_menu_name:
            dup_check = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", new_menu_name).execute()
            if dup_check.data:
                return False, f"'{new_menu_name}' 메뉴명은 이미 사용 중입니다."
        
        # 업데이트 데이터 준비
        update_data = {
            "name": new_menu_name,
            "price": float(new_price)
        }
        if category is not None:
            update_data["category"] = category
        
        # 업데이트
        supabase.table("menu_master").update(update_data).eq("id", menu_id).execute()
        
        logger.info(f"Menu updated: {old_menu_name} -> {new_menu_name}")
        return True, "수정 성공"
    except Exception as e:
        logger.error(f"Failed to update menu: {e}")
        raise


def update_menu_category(menu_name, category):
    """메뉴 카테고리 업데이트"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 기존 메뉴 찾기
        existing = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not existing.data:
            return False, f"'{menu_name}' 메뉴를 찾을 수 없습니다."
        
        menu_id = existing.data[0]['id']
        
        # 카테고리 업데이트
        supabase.table("menu_master").update({
            "category": category
        }).eq("id", menu_id).execute()
        
        logger.info(f"Menu category updated: {menu_name} -> {category}")
        return True, "카테고리 수정 성공"
    except Exception as e:
        logger.error(f"Failed to update menu category: {e}")
        raise


def update_menu_cooking_method(menu_name, cooking_method):
    """메뉴 조리방법 업데이트"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 기존 메뉴 찾기
        existing = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not existing.data:
            return False, f"'{menu_name}' 메뉴를 찾을 수 없습니다."
        
        menu_id = existing.data[0]['id']
        
        # 조리방법 업데이트 (cooking_method 컬럼이 있다면)
        try:
            supabase.table("menu_master").update({
                "cooking_method": cooking_method.strip()
            }).eq("id", menu_id).execute()
            logger.info(f"Menu cooking method updated: {menu_name}")
            return True, "조리방법 저장 성공"
        except Exception as e:
            # 컬럼이 없으면 경고만 하고 성공으로 처리 (나중에 스키마 업데이트 필요)
            logger.warning(f"Cooking method column may not exist: {e}")
            return True, "조리방법 저장 성공 (스키마 업데이트 필요할 수 있음)"
    except Exception as e:
        logger.error(f"Failed to update menu cooking method: {e}")
        raise


def delete_menu(menu_name, check_references=True):
    """메뉴 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다.", None
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 메뉴 찾기
        menu_result = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not menu_result.data:
            return False, f"'{menu_name}' 메뉴를 찾을 수 없습니다.", None
        
        menu_id = menu_result.data[0]['id']
        
        references = {}
        if check_references:
            # 레시피 참조 확인
            recipe_check = supabase.table("recipes").select("id").eq("menu_id", menu_id).execute()
            if recipe_check.data:
                references['레시피'] = len(recipe_check.data)
            
            # 판매 내역 참조 확인
            sales_check = supabase.table("daily_sales_items").select("id").eq("menu_id", menu_id).execute()
            if sales_check.data:
                references['판매내역'] = len(sales_check.data)
        
        if references:
            ref_info = ", ".join([f"{k}: {v}개" for k, v in references.items()])
            return False, f"'{menu_name}' 메뉴는 다음 데이터에서 사용 중입니다: {ref_info}", references
        
        # 삭제
        supabase.table("menu_master").delete().eq("id", menu_id).execute()
        logger.info(f"Menu deleted: {menu_name}")
        return True, "삭제 성공", None
    except Exception as e:
        logger.error(f"Failed to delete menu: {e}")
        raise


def save_ingredient(ingredient_name, unit, unit_price):
    """재료 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 저장할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 중복 체크
        existing = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if existing.data:
            return False, f"'{ingredient_name}' 재료는 이미 등록되어 있습니다."
        
        result = supabase.table("ingredients").insert({
            "store_id": store_id,
            "name": ingredient_name,
            "unit": unit,
            "unit_cost": float(unit_price)
        }).execute()
        
        logger.info(f"Ingredient saved: {ingredient_name}")
        return True, "저장 성공"
    except Exception as e:
        logger.error(f"Failed to save ingredient: {e}")
        raise


def update_ingredient(old_ingredient_name, new_ingredient_name, new_unit, new_unit_price):
    """재료 수정"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 기존 재료 찾기
        existing = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", old_ingredient_name).execute()
        if not existing.data:
            return False, f"'{old_ingredient_name}' 재료를 찾을 수 없습니다."
        
        ing_id = existing.data[0]['id']
        
        # 새 재료명이 다른 경우 중복 체크
        if new_ingredient_name != old_ingredient_name:
            dup_check = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", new_ingredient_name).execute()
            if dup_check.data:
                return False, f"'{new_ingredient_name}' 재료명은 이미 사용 중입니다."
        
        # 업데이트
        supabase.table("ingredients").update({
            "name": new_ingredient_name,
            "unit": new_unit,
            "unit_cost": float(new_unit_price)
        }).eq("id", ing_id).execute()
        
        logger.info(f"Ingredient updated: {old_ingredient_name} -> {new_ingredient_name}")
        return True, "수정 성공"
    except Exception as e:
        logger.error(f"Failed to update ingredient: {e}")
        raise


def delete_ingredient(ingredient_name, check_references=True):
    """재료 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다.", None
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 재료 찾기
        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            return False, f"'{ingredient_name}' 재료를 찾을 수 없습니다.", None
        
        ing_id = ing_result.data[0]['id']
        
        references = {}
        if check_references:
            # 레시피 참조 확인
            recipe_check = supabase.table("recipes").select("id").eq("ingredient_id", ing_id).execute()
            if recipe_check.data:
                references['레시피'] = len(recipe_check.data)
            
            # 재고 정보 참조 확인
            inv_check = supabase.table("inventory").select("id").eq("ingredient_id", ing_id).execute()
            if inv_check.data:
                references['재고정보'] = 1
        
        if references:
            ref_info = ", ".join([f"{k}: {v}개" for k, v in references.items()])
            return False, f"'{ingredient_name}' 재료는 다음 데이터에서 사용 중입니다: {ref_info}", references
        
        # 삭제
        supabase.table("ingredients").delete().eq("id", ing_id).execute()
        logger.info(f"Ingredient deleted: {ingredient_name}")
        return True, "삭제 성공", None
    except Exception as e:
        logger.error(f"Failed to delete ingredient: {e}")
        raise


def save_recipe(menu_name, ingredient_name, quantity):
    """레시피 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 메뉴 ID 찾기
        menu_result = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not menu_result.data:
            raise Exception(f"메뉴 '{menu_name}'를 찾을 수 없습니다.")
        menu_id = menu_result.data[0]['id']
        
        # 재료 ID 찾기
        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            raise Exception(f"재료 '{ingredient_name}'를 찾을 수 없습니다.")
        ingredient_id = ing_result.data[0]['id']
        
        # 레시피 저장
        result = supabase.table("recipes").upsert({
            "store_id": store_id,
            "menu_id": menu_id,
            "ingredient_id": ingredient_id,
            "qty": float(quantity)
        }, on_conflict="store_id,menu_id,ingredient_id").execute()
        
        logger.info(f"Recipe saved: {menu_name} - {ingredient_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save recipe: {e}")
        raise


def delete_recipe(menu_name, ingredient_name):
    """레시피 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 메뉴 ID 찾기
        menu_result = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not menu_result.data:
            return False, f"'{menu_name}' 메뉴를 찾을 수 없습니다."
        menu_id = menu_result.data[0]['id']
        
        # 재료 ID 찾기
        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            return False, f"'{ingredient_name}' 재료를 찾을 수 없습니다."
        ingredient_id = ing_result.data[0]['id']
        
        # 레시피 삭제
        supabase.table("recipes").delete().eq("store_id", store_id).eq("menu_id", menu_id).eq("ingredient_id", ingredient_id).execute()
        
        logger.info(f"Recipe deleted: {menu_name} - {ingredient_name}")
        return True, "삭제 성공"
    except Exception as e:
        logger.error(f"Failed to delete recipe: {e}")
        raise


def save_daily_sales_item(date, menu_name, quantity):
    """일일 판매 아이템 저장 (같은 날짜/메뉴가 있으면 수량 합산)"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        
        # 메뉴 ID 찾기
        menu_result = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not menu_result.data:
            raise Exception(f"메뉴 '{menu_name}'를 찾을 수 없습니다.")
        menu_id = menu_result.data[0]['id']
        
        # 기존 데이터 확인
        existing = supabase.table("daily_sales_items").select("qty").eq("store_id", store_id).eq("date", date_str).eq("menu_id", menu_id).execute()
        
        if existing.data:
            # 기존 수량에 추가
            new_qty = existing.data[0]['qty'] + quantity
            supabase.table("daily_sales_items").update({"qty": new_qty}).eq("store_id", store_id).eq("date", date_str).eq("menu_id", menu_id).execute()
        else:
            # 새로 추가
            supabase.table("daily_sales_items").insert({
                "store_id": store_id,
                "date": date_str,
                "menu_id": menu_id,
                "qty": int(quantity)
            }).execute()
        
        logger.info(f"Daily sales item saved: {date_str}, {menu_name}, {quantity}")
        return True
    except Exception as e:
        logger.error(f"Failed to save daily sales item: {e}")
        raise


def save_inventory(ingredient_name, current_stock, safety_stock):
    """재고 정보 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 재료 ID 찾기
        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            raise Exception(f"재료 '{ingredient_name}'를 찾을 수 없습니다.")
        ingredient_id = ing_result.data[0]['id']
        
        # 재고 정보 저장/업데이트
        supabase.table("inventory").upsert({
            "store_id": store_id,
            "ingredient_id": ingredient_id,
            "on_hand": float(current_stock),
            "safety_stock": float(safety_stock)
        }, on_conflict="store_id,ingredient_id").execute()
        
        logger.info(f"Inventory saved: {ingredient_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save inventory: {e}")
        raise


def save_targets(year, month, target_sales, target_cost_rate, target_labor_rate, 
                 target_rent_rate, target_other_rate, target_profit_rate):
    """목표 매출/비용 구조 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("targets").upsert({
            "store_id": store_id,
            "year": int(year),
            "month": int(month),
            "target_sales": float(target_sales),
            "target_cost_rate": float(target_cost_rate),
            "target_labor_rate": float(target_labor_rate),
            "target_rent_rate": float(target_rent_rate),
            "target_other_rate": float(target_other_rate),
            "target_profit_rate": float(target_profit_rate)
        }, on_conflict="store_id,year,month").execute()
        
        logger.info(f"Targets saved: {year}-{month}")
        return True
    except Exception as e:
        logger.error(f"Failed to save targets: {e}")
        raise


def save_abc_history(year, month, abc_df):
    """ABC 분석 히스토리 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 기존 데이터 삭제 (해당 연도/월)
        supabase.table("abc_history").delete().eq("store_id", store_id).eq("year", year).eq("month", month).execute()
        
        # 새 데이터 추가
        records = []
        for _, row in abc_df.iterrows():
            records.append({
                "store_id": store_id,
                "year": int(year),
                "month": int(month),
                "menu_name": str(row.get('메뉴명', '')),
                "sales_qty": int(row.get('판매량', 0)),
                "sales_amount": float(row.get('매출', 0)),
                "contribution_margin": float(row.get('공헌이익', 0)),
                "qty_ratio": float(row.get('판매량비중', 0)),
                "sales_ratio": float(row.get('매출비중', 0)),
                "margin_ratio": float(row.get('공헌이익비중', 0)),
                "abc_grade": str(row.get('ABC등급', ''))
            })
        
        if records:
            supabase.table("abc_history").insert(records).execute()
        
        logger.info(f"ABC history saved: {year}-{month}")
        return True
    except Exception as e:
        logger.error(f"Failed to save abc history: {e}")
        raise


def save_key_menus(menu_list):
    """핵심 메뉴 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 먼저 모든 메뉴의 is_core를 False로
        supabase.table("menu_master").update({"is_core": False}).eq("store_id", store_id).execute()
        
        # 선택된 메뉴들의 is_core를 True로
        if menu_list:
            for menu_name in menu_list:
                supabase.table("menu_master").update({"is_core": True}).eq("store_id", store_id).eq("name", menu_name).execute()
        
        logger.info(f"Key menus saved: {len(menu_list)} menus")
        return True
    except Exception as e:
        logger.error(f"Failed to save key menus: {e}")
        raise


def save_daily_close(date, store_name, card_sales, cash_sales, total_sales, 
                     visitors, sales_items, issues, memo):
    """일일 마감 데이터 통합 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        
        # sales_items를 JSON으로 변환
        sales_items_json = json.dumps(sales_items, ensure_ascii=False)
        
        # daily_close 저장
        supabase.table("daily_close").upsert({
            "store_id": store_id,
            "date": date_str,
            "card_sales": float(card_sales),
            "cash_sales": float(cash_sales),
            "total_sales": float(total_sales),
            "visitors": int(visitors),
            "out_of_stock": bool(issues.get('품절', False)),
            "complaint": bool(issues.get('컴플레인', False)),
            "group_customer": bool(issues.get('단체손님', False)),
            "staff_issue": bool(issues.get('직원이슈', False)),
            "memo": str(memo) if memo else None,
            "sales_items": sales_items_json
        }, on_conflict="store_id,date").execute()
        
        # 기존 매출, 방문자, 판매 데이터에도 저장 (호환성 유지)
        if total_sales > 0:
            save_sales(date, store_name, card_sales, cash_sales, total_sales)
        if visitors > 0:
            save_visitor(date, visitors)
        for menu_name, quantity in sales_items:
            if quantity > 0:
                save_daily_sales_item(date, menu_name, quantity)
        
        logger.info(f"Daily close saved: {date_str}")
        return True
    except Exception as e:
        logger.error(f"Failed to save daily close: {e}")
        raise


def delete_sales(date, store=None):
    """매출 데이터 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        supabase.table("sales").delete().eq("store_id", store_id).eq("date", date_str).execute()
        logger.info(f"Sales deleted: {date_str}")
        return True, "삭제 성공"
    except Exception as e:
        logger.error(f"Failed to delete sales: {e}")
        raise


def delete_visitor(date):
    """방문자 데이터 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        supabase.table("naver_visitors").delete().eq("store_id", store_id).eq("date", date_str).execute()
        logger.info(f"Visitor deleted: {date_str}")
        return True, "삭제 성공"
    except Exception as e:
        logger.error(f"Failed to delete visitor: {e}")
        raise


def save_expense_item(year, month, category, item_name, amount, notes=None):
    """비용구조 항목 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("expense_structure").insert({
            "store_id": store_id,
            "year": int(year),
            "month": int(month),
            "category": category,
            "item_name": item_name,
            "amount": float(amount),
            "notes": notes if notes else None
        }).execute()
        
        logger.info(f"Expense item saved: {year}-{month}, {category}, {item_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save expense item: {e}")
        raise


def update_expense_item(expense_id, item_name, amount, notes=None):
    """비용구조 항목 수정"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        update_data = {
            "item_name": item_name,
            "amount": float(amount),
            "updated_at": datetime.now().isoformat()
        }
        if notes is not None:
            update_data["notes"] = notes
        
        supabase.table("expense_structure")\
            .update(update_data)\
            .eq("id", expense_id)\
            .eq("store_id", store_id)\
            .execute()
        
        logger.info(f"Expense item updated: {expense_id}")
        return True, "수정 성공"
    except Exception as e:
        logger.error(f"Failed to update expense item: {e}")
        raise


def delete_expense_item(expense_id):
    """비용구조 항목 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("expense_structure").delete().eq("id", expense_id).eq("store_id", store_id).execute()
        logger.info(f"Expense item deleted: {expense_id}")
        return True, "삭제 성공"
    except Exception as e:
        logger.error(f"Failed to delete expense item: {e}")
        raise


@st.cache_data(ttl=60)  # 1분 캐시 (비용구조는 자주 변경될 수 있으므로 짧게)
def load_expense_structure(year, month):
    """비용구조 데이터 로드 (특정 연도/월)"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return pd.DataFrame()
    
    store_id = get_current_store_id()
    if not store_id:
        return pd.DataFrame()
    
    try:
        result = supabase.table("expense_structure")\
            .select("*")\
            .eq("store_id", store_id)\
            .eq("year", int(year))\
            .eq("month", int(month))\
            .execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            return df
        else:
            return pd.DataFrame(columns=['id', 'category', 'item_name', 'amount', 'notes'])
    except Exception as e:
        logger.error(f"Failed to load expense structure: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)  # 1분 캐시
def load_expense_structure_range(year_start, month_start, year_end, month_end):
    """비용구조 데이터 로드 (기간 범위)"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return pd.DataFrame()
    
    store_id = get_current_store_id()
    if not store_id:
        return pd.DataFrame()
    
    try:
        # 모든 데이터를 가져온 후 필터링
        result = supabase.table("expense_structure")\
            .select("*")\
            .eq("store_id", store_id)\
            .execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            # 기간 필터링
            def in_range(row):
                y, m = row['year'], row['month']
                if y < year_start or y > year_end:
                    return False
                if y == year_start and m < month_start:
                    return False
                if y == year_end and m > month_end:
                    return False
                return True
            
            df = df[df.apply(in_range, axis=1)]
            return df
        else:
            return pd.DataFrame(columns=['id', 'category', 'item_name', 'amount', 'notes', 'year', 'month'])
    except Exception as e:
        logger.error(f"Failed to load expense structure range: {e}")
        return pd.DataFrame()


def copy_expense_structure_from_previous_month(year, month):
    """전월 비용구조 데이터를 현재 월로 복사"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 복사할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 전월 계산
        prev_month = month - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year = year - 1
        
        # 전월 데이터 로드
        prev_data = load_expense_structure(prev_year, prev_month)
        if prev_data.empty:
            return False, "복사할 전월 데이터가 없습니다."
        
        # 현재 월 데이터 확인
        current_data = load_expense_structure(year, month)
        if not current_data.empty:
            return False, "이미 현재 월에 데이터가 있습니다. 먼저 삭제해주세요."
        
        # 전월 데이터 복사
        records = []
        for _, row in prev_data.iterrows():
            records.append({
                "store_id": store_id,
                "year": int(year),
                "month": int(month),
                "category": row['category'],
                "item_name": row['item_name'],
                "amount": float(row['amount']),
                "notes": row.get('notes')
            })
        
        if records:
            supabase.table("expense_structure").insert(records).execute()
            logger.info(f"Expense structure copied from {prev_year}-{prev_month} to {year}-{month}")
            return True, f"전월({prev_year}년 {prev_month}월) 데이터가 복사되었습니다."
        else:
            return False, "복사할 데이터가 없습니다."
    except Exception as e:
        logger.error(f"Failed to copy expense structure: {e}")
        raise


def create_backup():
    """데이터 백업 (DB 기반에서는 단순 로그만)"""
    logger = logging.getLogger(__name__)
    logger.info("Backup requested (DB mode - data is already persisted in Supabase)")
    return True, "데이터는 Supabase에 자동으로 영구 저장됩니다."
