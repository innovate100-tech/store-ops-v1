"""
Supabase/Postgres 기반 저장소 모듈
"""
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
import json

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: supabase-py not installed. Please install it with: pip install supabase")


def setup_logger():
    """로깅 시스템 설정"""
    logger = logging.getLogger('store_ops_db')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()


def get_supabase_client() -> Optional[Client]:
    """
    Supabase 클라이언트 생성
    
    Returns:
        Supabase Client or None
    """
    if not SUPABASE_AVAILABLE:
        logger.error("supabase-py is not installed")
        return None
    
    import streamlit as st
    
    try:
        url = st.secrets.get("supabase", {}).get("url", "")
        key = st.secrets.get("supabase", {}).get("anon_key", "")
        
        if not url or not key:
            logger.error("Supabase URL or Anon Key not found in secrets")
            return None
        
        return create_client(url, key)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None


def get_current_user_store_id() -> Optional[str]:
    """
    현재 로그인한 사용자의 store_id 조회
    
    Returns:
        store_id (UUID string) or None
    """
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        user = supabase.auth.get_user()
        if not user or not user.user:
            return None
        
        user_id = user.user.id
        
        # users 테이블에서 store_id 조회
        result = supabase.table("users").select("store_id").eq("id", user_id).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0].get("store_id")
        
        return None
    except Exception as e:
        logger.error(f"Failed to get user store_id: {e}")
        return None


# ============================================
# Load Functions (CSV 호환 인터페이스 유지)
# ============================================

def load_csv(table_name: str, default_columns: Optional[List[str]] = None):
    """
    테이블에서 데이터 로드 (CSV 호환 인터페이스)
    
    Args:
        table_name: 테이블명 (예: "sales")
        default_columns: 기본 컬럼 리스트
    
    Returns:
        pandas.DataFrame
    """
    supabase = get_supabase_client()
    if not supabase:
        logger.warning(f"Supabase not available, returning empty DataFrame for {table_name}")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    store_id = get_current_user_store_id()
    if not store_id:
        logger.warning(f"No store_id found, returning empty DataFrame for {table_name}")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    try:
        # 테이블명 매핑
        table_mapping = {
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
        
        actual_table = table_mapping.get(table_name, table_name)
        
        # store_id로 필터링하여 조회
        result = supabase.table(actual_table).select("*").eq("store_id", store_id).execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            
            # 컬럼명 변환 (DB -> CSV 호환)
            if table_name == 'sales':
                if 'date' in df.columns:
                    df['날짜'] = pd.to_datetime(df['date'])
                if 'card_sales' in df.columns:
                    df['카드매출'] = df['card_sales']
                if 'cash_sales' in df.columns:
                    df['현금매출'] = df['cash_sales']
                if 'total_sales' in df.columns:
                    df['총매출'] = df['total_sales']
                if 'store_id' in df.columns:
                    # store_id로 매장명 조회
                    store_result = supabase.table("stores").select("name").eq("id", store_id).execute()
                    if store_result.data:
                        df['매장'] = store_result.data[0]['name']
            
            elif table_name == 'naver_visitors':
                if 'date' in df.columns:
                    df['날짜'] = pd.to_datetime(df['date'])
                if 'visitors' in df.columns:
                    df['방문자수'] = df['visitors']
            
            elif table_name == 'menu_master':
                if 'name' in df.columns:
                    df['메뉴명'] = df['name']
                if 'price' in df.columns:
                    df['판매가'] = df['price']
            
            elif table_name == 'ingredient_master':
                if 'name' in df.columns:
                    df['재료명'] = df['name']
                if 'unit' in df.columns:
                    df['단위'] = df['unit']
                if 'unit_cost' in df.columns:
                    df['단가'] = df['unit_cost']
            
            elif table_name == 'recipes':
                # menu_id와 ingredient_id를 이름으로 변환
                if 'menu_id' in df.columns:
                    menu_ids = df['menu_id'].unique().tolist()
                    if menu_ids:
                        menu_result = supabase.table("menu_master").select("id,name").in_("id", menu_ids).execute()
                        menu_map = {m['id']: m['name'] for m in menu_result.data}
                        df['메뉴명'] = df['menu_id'].map(menu_map)
                
                if 'ingredient_id' in df.columns:
                    ing_ids = df['ingredient_id'].unique().tolist()
                    if ing_ids:
                        ing_result = supabase.table("ingredients").select("id,name").in_("id", ing_ids).execute()
                        ing_map = {i['id']: i['name'] for i in ing_result.data}
                        df['재료명'] = df['ingredient_id'].map(ing_map)
                
                if 'qty' in df.columns:
                    df['사용량'] = df['qty']
            
            elif table_name == 'daily_sales_items':
                if 'date' in df.columns:
                    df['날짜'] = pd.to_datetime(df['date'])
                
                if 'menu_id' in df.columns:
                    menu_ids = df['menu_id'].unique().tolist()
                    if menu_ids:
                        menu_result = supabase.table("menu_master").select("id,name").in_("id", menu_ids).execute()
                        menu_map = {m['id']: m['name'] for m in menu_result.data}
                        df['메뉴명'] = df['menu_id'].map(menu_map)
                
                if 'qty' in df.columns:
                    df['판매수량'] = df['qty']
            
            elif table_name == 'inventory':
                if 'ingredient_id' in df.columns:
                    ing_ids = df['ingredient_id'].unique().tolist()
                    if ing_ids:
                        ing_result = supabase.table("ingredients").select("id,name").in_("id", ing_ids).execute()
                        ing_map = {i['id']: i['name'] for i in ing_result.data}
                        df['재료명'] = df['ingredient_id'].map(ing_map)
                
                if 'on_hand' in df.columns:
                    df['현재고'] = df['on_hand']
                if 'safety_stock' in df.columns:
                    df['안전재고'] = df['safety_stock']
            
            elif table_name == 'targets':
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
            
            return df
        else:
            return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Failed to load {table_name}: {e}")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()


def load_key_menus() -> List[str]:
    """
    핵심 메뉴 목록 로드 (is_core=True인 메뉴들)
    
    Returns:
        메뉴명 리스트
    """
    supabase = get_supabase_client()
    if not supabase:
        return []
    
    store_id = get_current_user_store_id()
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
    """
    매출 데이터 저장
    
    Args:
        date: 날짜
        store_name: 매장명 (사용 안 함, 현재 사용자의 store_id 사용)
        card_sales: 카드매출
        cash_sales: 현금매출
        total_sales: 총매출
    """
    supabase = get_supabase_client()
    if not supabase:
        raise Exception("Supabase not available")
    
    store_id = get_current_user_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    if total_sales is None:
        total_sales = card_sales + cash_sales
    
    try:
        # 날짜 문자열로 변환
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        
        # UPSERT (날짜가 같으면 업데이트)
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
    supabase = get_supabase_client()
    if not supabase:
        raise Exception("Supabase not available")
    
    store_id = get_current_user_store_id()
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
    supabase = get_supabase_client()
    if not supabase:
        raise Exception("Supabase not available")
    
    store_id = get_current_user_store_id()
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


def save_key_menus(menu_list: List[str]):
    """핵심 메뉴 저장"""
    supabase = get_supabase_client()
    if not supabase:
        raise Exception("Supabase not available")
    
    store_id = get_current_user_store_id()
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
