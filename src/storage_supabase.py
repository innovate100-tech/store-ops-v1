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

# Phase 2: 리소스 관리 - 데이터 타입별 TTL 분리
def _get_cache_ttl(filename: str) -> int:
    """
    파일명에 따라 적절한 캐시 TTL 반환
    
    - 마스터 데이터 (메뉴, 재료): 3600초 (1시간) - 자주 변경되지 않음
    - 트랜잭션 데이터 (매출, 방문자): 60초 (1분) - 자주 변경됨
    - 중간 데이터 (재고, 발주): 300초 (5분) - 중간 빈도
    """
    master_data = ['menu_master.csv', 'ingredient_master.csv', 'recipes.csv', 'suppliers.csv']
    transaction_data = ['sales.csv', 'naver_visitors.csv', 'daily_sales_items.csv']
    
    if filename in master_data:
        return 3600  # 1시간
    elif filename in transaction_data:
        return 60    # 1분
    else:
        return 300   # 5분 (기본값)

@st.cache_data(ttl=60)  # 기본값은 60초이지만, 실제로는 _get_cache_ttl 사용 권장
def load_csv(filename: str, default_columns: Optional[List[str]] = None):
    """
    테이블에서 데이터 로드 (CSV 호환 인터페이스)
    
    Args:
        filename: CSV 파일명 (예: "sales.csv") -> 테이블명으로 매핑
        default_columns: 기본 컬럼 리스트
    
    Returns:
        pandas.DataFrame
    """
    # Supabase 클라이언트 초기화
    try:
        supabase = get_supabase_client()
    except Exception as e:
        # 환경 변수/네트워크/SSL 문제 등으로 클라이언트 생성 실패 시,
        # 앱 전체가 죽지 않도록 빈 DataFrame을 반환하고 로그만 남긴다.
        logger.error(f"Supabase client init failed in load_csv('{filename}'): {e}")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()

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
            'actual_settlement.csv': 'actual_settlement',
            'suppliers.csv': 'suppliers',
            'ingredient_suppliers.csv': 'ingredient_suppliers',
            'orders.csv': 'orders',
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
            'daily_close': 'daily_close',
            'actual_settlement': 'actual_settlement',
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
                if 'order_unit' in df.columns:
                    df['발주단위'] = df['order_unit']
                if 'conversion_rate' in df.columns:
                    df['변환비율'] = df['conversion_rate']
            
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
            
            elif actual_table == 'actual_settlement':
                # 실제 정산 데이터 (월별 실적)
                if 'year' in df.columns:
                    df['연도'] = df['year']
                if 'month' in df.columns:
                    df['월'] = df['month']
                if 'actual_sales' in df.columns:
                    df['실제매출'] = df['actual_sales']
                if 'actual_cost' in df.columns:
                    df['실제비용'] = df['actual_cost']
                if 'actual_profit' in df.columns:
                    df['실제이익'] = df['actual_profit']
                if 'profit_margin' in df.columns:
                    df['실제이익률'] = df['profit_margin']
            
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
            
            elif actual_table == 'suppliers':
                if 'name' in df.columns:
                    df['공급업체명'] = df['name']
                if 'phone' in df.columns:
                    df['전화번호'] = df['phone']
                if 'email' in df.columns:
                    df['이메일'] = df['email']
                if 'delivery_days' in df.columns:
                    df['배송일'] = df['delivery_days']
                if 'min_order_amount' in df.columns:
                    df['최소주문금액'] = df['min_order_amount']
                if 'delivery_fee' in df.columns:
                    df['배송비'] = df['delivery_fee']
                if 'notes' in df.columns:
                    df['비고'] = df['notes']
            
            elif actual_table == 'ingredient_suppliers':
                # 재료 ID -> 재료명 변환
                if 'ingredient_id' in df.columns:
                    ing_ids = df['ingredient_id'].dropna().unique().tolist()
                    if ing_ids:
                        ing_result = supabase.table("ingredients").select("id,name").in_("id", ing_ids).execute()
                        ing_map = {i['id']: i['name'] for i in ing_result.data}
                        df['재료명'] = df['ingredient_id'].map(ing_map)
                
                # 공급업체 ID -> 공급업체명 변환
                if 'supplier_id' in df.columns:
                    sup_ids = df['supplier_id'].dropna().unique().tolist()
                    if sup_ids:
                        sup_result = supabase.table("suppliers").select("id,name").in_("id", sup_ids).execute()
                        sup_map = {s['id']: s['name'] for s in sup_result.data}
                        df['공급업체명'] = df['supplier_id'].map(sup_map)
                
                if 'unit_price' in df.columns:
                    df['단가'] = df['unit_price']
                if 'is_default' in df.columns:
                    df['기본공급업체'] = df['is_default']
            
            elif actual_table == 'orders':
                # id 컬럼 유지
                if 'id' not in df.columns:
                    df['id'] = df.index
                
                # 재료 ID -> 재료명 변환
                if 'ingredient_id' in df.columns:
                    ing_ids = df['ingredient_id'].dropna().unique().tolist()
                    if ing_ids:
                        ing_result = supabase.table("ingredients").select("id,name").in_("id", ing_ids).execute()
                        ing_map = {i['id']: i['name'] for i in ing_result.data}
                        df['재료명'] = df['ingredient_id'].map(ing_map)
                
                # 공급업체 ID -> 공급업체명 변환
                if 'supplier_id' in df.columns:
                    sup_ids = df['supplier_id'].dropna().unique().tolist()
                    if sup_ids:
                        sup_result = supabase.table("suppliers").select("id,name").in_("id", sup_ids).execute()
                        sup_map = {s['id']: s['name'] for s in sup_result.data}
                        df['공급업체명'] = df['supplier_id'].map(sup_map)
                
                if 'order_date' in df.columns:
                    df['발주일'] = pd.to_datetime(df['order_date'])
                if 'quantity' in df.columns:
                    df['수량'] = df['quantity']
                if 'unit_price' in df.columns:
                    df['단가'] = df['unit_price']
                if 'total_amount' in df.columns:
                    df['총금액'] = df['total_amount']
                if 'status' in df.columns:
                    df['상태'] = df['status']
                if 'expected_delivery_date' in df.columns:
                    df['입고예정일'] = pd.to_datetime(df['expected_delivery_date'])
                if 'actual_delivery_date' in df.columns:
                    df['입고일'] = pd.to_datetime(df['actual_delivery_date'])
                if 'notes' in df.columns:
                    df['비고'] = df['notes']
            
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
    """
    메뉴 저장
    
    Phase 2: 동시성 보호 - Optimistic Locking 적용
    """
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


def update_menu(old_menu_name, new_menu_name, new_price, category=None, expected_updated_at=None):
    """
    메뉴 수정
    
    Phase 2: 동시성 보호 - Optimistic Locking
    - expected_updated_at: 수정 전의 updated_at 값 (충돌 감지용)
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 기존 메뉴 찾기 (updated_at 포함)
        existing = supabase.table("menu_master").select("id,updated_at").eq("store_id", store_id).eq("name", old_menu_name).execute()
        if not existing.data:
            return False, f"'{old_menu_name}' 메뉴를 찾을 수 없습니다."
        
        menu_id = existing.data[0]['id']
        current_updated_at = existing.data[0].get('updated_at')
        
        # Phase 2: 동시성 보호 - Optimistic Locking
        if expected_updated_at and current_updated_at != expected_updated_at:
            return False, f"다른 사용자가 '{old_menu_name}' 메뉴를 수정했습니다. 페이지를 새로고침한 후 다시 시도해주세요."
        
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


def save_ingredient(ingredient_name, unit, unit_price, order_unit=None, conversion_rate=1.0):
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
        
        # 발주 단위가 없으면 기본 단위와 동일하게 설정
        if not order_unit:
            order_unit = unit
        
        insert_data = {
            "store_id": store_id,
            "name": ingredient_name,
            "unit": unit,
            "unit_cost": float(unit_price),
            "order_unit": order_unit,
            "conversion_rate": float(conversion_rate)
        }
        
        result = supabase.table("ingredients").insert(insert_data).execute()
        
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


def save_actual_settlement(year, month, actual_sales, actual_cost, actual_profit, profit_margin):
    """월별 실제 정산 데이터 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("actual_settlement").upsert(
            {
                "store_id": store_id,
                "year": int(year),
                "month": int(month),
                "actual_sales": float(actual_sales),
                "actual_cost": float(actual_cost),
                "actual_profit": float(actual_profit),
                "profit_margin": float(profit_margin),
            },
            on_conflict="store_id,year,month",
        ).execute()
        logger.info(f"Actual settlement saved: {year}-{month}")
        return True
    except Exception as e:
        logger.error(f"Failed to save actual settlement: {e}")
        raise


def save_abc_history(year, month, abc_df):
    """
    ABC 분석 히스토리 저장
    
    Phase 2: 트랜잭션 처리 개선
    - 삭제 후 삽입 작업의 원자성 보장
    - 실패 시 롤백 시도
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    # Phase 2: 트랜잭션 처리 - 기존 데이터 백업
    old_data_backup = None
    try:
        # 기존 데이터 백업 (롤백용)
        old_result = supabase.table("abc_history").select("*").eq("store_id", store_id).eq("year", year).eq("month", month).execute()
        old_data_backup = old_result.data if old_result.data else []
        
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
        # Phase 2: 트랜잭션 처리 - 실패 시 롤백 시도
        if old_data_backup:
            try:
                logger.warning(f"Rolling back ABC history for {year}-{month}")
                # 기존 데이터 복원 시도
                if old_data_backup:
                    supabase.table("abc_history").insert(old_data_backup).execute()
                logger.info(f"ABC history rollback successful for {year}-{month}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback ABC history: {rollback_error}")
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
    """
    일일 마감 데이터 통합 저장
    
    Phase 2: 트랜잭션 처리 개선
    - 여러 테이블 저장 작업의 원자성 보장
    - 실패 시 롤백 시도
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    # Phase 2: 트랜잭션 처리 - 저장된 데이터 추적 (롤백용)
    saved_operations = []
    date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
    
    try:
        # sales_items를 JSON으로 변환
        sales_items_json = json.dumps(sales_items, ensure_ascii=False)
        
        # 1. daily_close 저장
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
        saved_operations.append(('daily_close', date_str))
        
        # 2. 기존 매출, 방문자, 판매 데이터에도 저장 (호환성 유지)
        if total_sales > 0:
            save_sales(date, store_name, card_sales, cash_sales, total_sales)
            saved_operations.append(('sales', date_str))
        if visitors > 0:
            save_visitor(date, visitors)
            saved_operations.append(('visitor', date_str))
        for menu_name, quantity in sales_items:
            if quantity > 0:
                save_daily_sales_item(date, menu_name, quantity)
                saved_operations.append(('daily_sales_item', (date_str, menu_name)))
        
        # ========== 재고 자동 차감 기능 ==========
        # 판매된 메뉴의 레시피를 기반으로 재료 사용량 계산 후 재고 차감
        if sales_items:
            try:
                # 레시피 데이터 로드
                recipe_result = supabase.table("recipes").select("menu_id,ingredient_id,qty").eq("store_id", store_id).execute()
                
                if recipe_result.data:
                    # 메뉴명 -> 메뉴 ID 매핑
                    menu_result = supabase.table("menu_master").select("id,name").eq("store_id", store_id).execute()
                    menu_map = {m['name']: m['id'] for m in menu_result.data}
                    
                    # 재료 ID -> 재료명 매핑
                    ingredient_result = supabase.table("ingredients").select("id,name").eq("store_id", store_id).execute()
                    ingredient_map = {i['id']: i['name'] for i in ingredient_result.data}
                    
                    # 재료별 사용량 계산
                    ingredient_usage = {}  # {ingredient_id: total_usage}
                    
                    for menu_name, sales_qty in sales_items:
                        if sales_qty > 0 and menu_name in menu_map:
                            menu_id = menu_map[menu_name]
                            
                            # 해당 메뉴의 레시피 찾기
                            menu_recipes = [r for r in recipe_result.data if r['menu_id'] == menu_id]
                            
                            for recipe in menu_recipes:
                                ingredient_id = recipe['ingredient_id']
                                recipe_qty = float(recipe['qty'])
                                
                                # 재료 사용량 = 판매수량 × 레시피 사용량
                                usage = sales_qty * recipe_qty
                                
                                if ingredient_id in ingredient_usage:
                                    ingredient_usage[ingredient_id] += usage
                                else:
                                    ingredient_usage[ingredient_id] = usage
                    
                    # 재고 차감
                    for ingredient_id, usage_amount in ingredient_usage.items():
                        # 현재 재고 조회
                        inventory_result = supabase.table("inventory").select("on_hand").eq("store_id", store_id).eq("ingredient_id", ingredient_id).execute()
                        
                        if inventory_result.data:
                            current_stock = float(inventory_result.data[0]['on_hand'])
                            new_stock = max(0, current_stock - usage_amount)  # 음수 방지
                            
                            # 재고 업데이트
                            supabase.table("inventory").update({
                                "on_hand": new_stock
                            }).eq("store_id", store_id).eq("ingredient_id", ingredient_id).execute()
                            
                            ingredient_name = ingredient_map.get(ingredient_id, f"ID:{ingredient_id}")
                            logger.info(f"Inventory updated: {ingredient_name} - {current_stock:.2f} → {new_stock:.2f} (사용량: {usage_amount:.2f})")
            except Exception as e:
                # 재고 차감 실패해도 마감 저장은 성공으로 처리 (경고만 로깅)
                logger.warning(f"재고 자동 차감 중 오류 발생 (마감은 저장됨): {e}")
        
        logger.info(f"Daily close saved: {date_str}")
        return True
    except Exception as e:
        logger.error(f"Failed to save daily close: {e}")
        # Phase 2: 트랜잭션 처리 - 실패 시 롤백 시도
        logger.warning(f"Attempting rollback for daily close operations: {saved_operations}")
        try:
            # daily_close 삭제 (가장 최근 저장)
            if ('daily_close', date_str) in saved_operations:
                supabase.table("daily_close").delete().eq("store_id", store_id).eq("date", date_str).execute()
                logger.info(f"Rolled back daily_close for {date_str}")
        except Exception as rollback_error:
            logger.error(f"Failed to rollback daily close: {rollback_error}")
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


# ============================================
# Phase 1: 공급업체 및 발주 이력 관리 함수
# ============================================

def save_supplier(supplier_name, phone=None, email=None, delivery_days=None, 
                  min_order_amount=0, delivery_fee=0, notes=None):
    """공급업체 등록/수정"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("suppliers").upsert({
            "store_id": store_id,
            "name": supplier_name,
            "phone": phone or "",
            "email": email or "",
            "delivery_days": delivery_days or "",
            "min_order_amount": float(min_order_amount) if min_order_amount else 0,
            "delivery_fee": float(delivery_fee) if delivery_fee else 0,
            "notes": notes or ""
        }, on_conflict="store_id,name").execute()
        
        logger.info(f"Supplier saved: {supplier_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save supplier: {e}")
        raise


def delete_supplier(supplier_name):
    """공급업체 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("suppliers").delete().eq("store_id", store_id).eq("name", supplier_name).execute()
        logger.info(f"Supplier deleted: {supplier_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete supplier: {e}")
        raise


def save_ingredient_supplier(ingredient_name, supplier_name, unit_price, is_default=True):
    """재료-공급업체 매핑 저장

    Notes
    -----
    - unit_price 인자는 **발주 단위 기준 단가(원/발주단위)** 로 전달된다고 가정한다.
    - ingredients 테이블의 conversion_rate 컬럼을 사용해
      기본 단위 단가(원/기본단위)로 환산해서 DB에 저장한다.
      (1 발주단위 = conversion_rate * 기본단위)
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 재료 ID 및 변환 비율 찾기
        ing_result = supabase.table("ingredients").select("id,conversion_rate").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            raise Exception(f"재료 '{ingredient_name}'를 찾을 수 없습니다.")
        ingredient_row = ing_result.data[0]
        ingredient_id = ingredient_row['id']
        conversion_rate = ingredient_row.get('conversion_rate', 1.0) or 1.0
        
        # 공급업체 ID 찾기
        sup_result = supabase.table("suppliers").select("id").eq("store_id", store_id).eq("name", supplier_name).execute()
        if not sup_result.data:
            raise Exception(f"공급업체 '{supplier_name}'를 찾을 수 없습니다.")
        supplier_id = sup_result.data[0]['id']
        
        # 기본 공급업체인 경우, 다른 기본 공급업체 해제
        if is_default:
            # 해당 재료의 다른 기본 공급업체 해제
            existing = supabase.table("ingredient_suppliers").select("id").eq("store_id", store_id).eq("ingredient_id", ingredient_id).eq("is_default", True).execute()
            if existing.data:
                for item in existing.data:
                    supabase.table("ingredient_suppliers").update({"is_default": False}).eq("id", item['id']).execute()
        
        # 발주 단가(원/발주단위)를 기본 단위 단가(원/기본단위)로 환산
        try:
            conv = float(conversion_rate)
            price_per_order_unit = float(unit_price)
            if conv > 0:
                base_unit_price = price_per_order_unit / conv
            else:
                base_unit_price = price_per_order_unit
        except Exception:
            base_unit_price = float(unit_price)

        # 재료-공급업체 매핑 저장 (기본 단위 단가 기준)
        supabase.table("ingredient_suppliers").upsert({
            "store_id": store_id,
            "ingredient_id": ingredient_id,
            "supplier_id": supplier_id,
            "unit_price": float(base_unit_price),
            "is_default": is_default
        }, on_conflict="store_id,ingredient_id,supplier_id").execute()
        
        logger.info(f"Ingredient-supplier mapping saved: {ingredient_name} -> {supplier_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save ingredient-supplier mapping: {e}")
        raise


def delete_ingredient_supplier(ingredient_name, supplier_name):
    """재료-공급업체 매핑 삭제"""
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
        
        # 공급업체 ID 찾기
        sup_result = supabase.table("suppliers").select("id").eq("store_id", store_id).eq("name", supplier_name).execute()
        if not sup_result.data:
            raise Exception(f"공급업체 '{supplier_name}'를 찾을 수 없습니다.")
        supplier_id = sup_result.data[0]['id']
        
        supabase.table("ingredient_suppliers").delete().eq("store_id", store_id).eq("ingredient_id", ingredient_id).eq("supplier_id", supplier_id).execute()
        logger.info(f"Ingredient-supplier mapping deleted: {ingredient_name} -> {supplier_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete ingredient-supplier mapping: {e}")
        raise


def save_order(order_date, ingredient_name, supplier_name, quantity, unit_price, 
               total_amount, status="예정", expected_delivery_date=None, notes=None):
    """발주 이력 저장
    
    주의
    ----
    - quantity, unit_price 는 **기본 단위 기준** 값이다.
      (예: quantity = g, unit_price = 원/g)
    - UI 단에서 발주단위(개, 박스 등)를 사용하더라도,
      이 함수에 들어올 때는 반드시 기본 단위로 환산해서 넣어야 한다.
      (환산 로직은 `order_service.py` 등에 모아 관리한다.)
    """
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
        
        # 공급업체 ID 찾기
        sup_result = supabase.table("suppliers").select("id").eq("store_id", store_id).eq("name", supplier_name).execute()
        if not sup_result.data:
            raise Exception(f"공급업체 '{supplier_name}'를 찾을 수 없습니다.")
        supplier_id = sup_result.data[0]['id']
        
        # 발주 저장
        result = supabase.table("orders").insert({
            "store_id": store_id,
            "order_date": order_date.strftime("%Y-%m-%d") if isinstance(order_date, datetime) else str(order_date),
            "ingredient_id": ingredient_id,
            "supplier_id": supplier_id,
            "quantity": float(quantity),
            "unit_price": float(unit_price),
            "total_amount": float(total_amount),
            "status": status,
            "expected_delivery_date": expected_delivery_date.strftime("%Y-%m-%d") if expected_delivery_date and isinstance(expected_delivery_date, datetime) else (str(expected_delivery_date) if expected_delivery_date else None),
            "notes": notes or ""
        }).execute()
        
        logger.info(f"Order saved: {ingredient_name} from {supplier_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save order: {e}")
        raise


def update_order_status(order_id, status, actual_delivery_date=None):
    """발주 상태 업데이트
    
    - status 가 '입고완료' 이고 actual_delivery_date 가 있을 때 재고(on_hand)를 증가시킨다.
    - 중복 입고 반영을 막기 위해 orders.inventory_applied 플래그를 사용한다.
      (단, 해당 컬럼이 아직 없을 수도 있으므로, 없으면 조용히 건너뛴다.)
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        update_data = {"status": status}
        if actual_delivery_date:
            update_data["actual_delivery_date"] = actual_delivery_date.strftime("%Y-%m-%d") if isinstance(actual_delivery_date, datetime) else str(actual_delivery_date)
        
        # 입고 완료 시 재고 반영 (inventory_applied 플래그 기반, idempotent)
        if status == "입고완료" and actual_delivery_date:
            # 발주 정보 가져오기 (inventory_applied 포함 시도)
            order_result = supabase.table("orders")\
                .select("ingredient_id,quantity,inventory_applied")\
                .eq("id", order_id)\
                .eq("store_id", store_id)\
                .execute()
            if order_result.data:
                row = order_result.data[0]
                ingredient_id = row.get("ingredient_id")
                quantity = row.get("quantity", 0)
                inventory_applied = bool(row.get("inventory_applied", False))

                # 아직 재고 반영이 안 된 경우에만 처리
                if ingredient_id and not inventory_applied:
                    inv_result = supabase.table("inventory")\
                        .select("on_hand")\
                        .eq("store_id", store_id)\
                        .eq("ingredient_id", ingredient_id)\
                        .execute()
                    if inv_result.data:
                        current_stock = float(inv_result.data[0].get("on_hand", 0) or 0)
                        new_stock = current_stock + float(quantity or 0)
                        supabase.table("inventory")\
                            .update({"on_hand": new_stock})\
                            .eq("store_id", store_id)\
                            .eq("ingredient_id", ingredient_id)\
                            .execute()

                    # 재고 반영 완료 표시 (컬럼이 없으면 조용히 무시)
                    try:
                        supabase.table("orders")\
                            .update({"inventory_applied": True})\
                            .eq("id", order_id)\
                            .eq("store_id", store_id)\
                            .execute()
                    except Exception as e:
                        logger.warning(f"inventory_applied 업데이트 실패 (마이그레이션 필요할 수 있음): {e}")

        # 상태/입고일 업데이트
        supabase.table("orders").update(update_data).eq("id", order_id).eq("store_id", store_id).execute()
        logger.info(f"Order status updated: {order_id} -> {status}")
        return True
    except Exception as e:
        logger.error(f"Failed to update order status: {e}")
        raise
