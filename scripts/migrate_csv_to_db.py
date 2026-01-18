"""
CSV 데이터를 Supabase DB로 마이그레이션하는 스크립트

사용법:
    python scripts/migrate_csv_to_db.py

주의: 이 스크립트는 service_role_key를 사용하여 RLS를 우회합니다.
"""
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import json

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase-py is not installed. Please install it with: pip install supabase")
    sys.exit(1)


def get_supabase_client(use_service_role: bool = False) -> Client:
    """Supabase 클라이언트 생성"""
    import streamlit as st
    
    try:
        # Streamlit secrets에서 읽기
        supabase_config = st.secrets.get("supabase", {})
        url = supabase_config.get("url", "")
        
        if use_service_role:
            key = supabase_config.get("service_role_key", "")
        else:
            key = supabase_config.get("anon_key", "")
        
        if not url or not key:
            print("Error: Supabase URL or Key not found in secrets")
            print("Please create .streamlit/secrets.toml file")
            sys.exit(1)
        
        return create_client(url, key)
    except Exception as e:
        print(f"Error creating Supabase client: {e}")
        sys.exit(1)


def load_csv_file(filename: str, data_dir: Path) -> pd.DataFrame:
    """CSV 파일 로드"""
    filepath = data_dir / filename
    if not filepath.exists():
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(filepath)
        if '날짜' in df.columns:
            df['날짜'] = pd.to_datetime(df['날짜'])
        return df
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return pd.DataFrame()


def migrate_store(supabase: Client, store_name: str = "Plate&Share") -> str:
    """매장 생성 (없으면 생성, 있으면 ID 반환)"""
    # 기존 매장 확인
    result = supabase.table("stores").select("id").eq("name", store_name).execute()
    
    if result.data:
        store_id = result.data[0]['id']
        print(f"✓ 매장 '{store_name}' 존재 (ID: {store_id})")
    else:
        # 매장 생성
        result = supabase.table("stores").insert({"name": store_name}).execute()
        store_id = result.data[0]['id']
        print(f"✓ 매장 '{store_name}' 생성됨 (ID: {store_id})")
    
    return store_id


def migrate_sales(supabase: Client, df: pd.DataFrame, store_id: str):
    """매출 데이터 마이그레이션"""
    if df.empty:
        print("  - 매출 데이터 없음")
        return
    
    records = []
    for _, row in df.iterrows():
        date = pd.to_datetime(row['날짜']).strftime('%Y-%m-%d')
        records.append({
            "store_id": store_id,
            "date": date,
            "card_sales": float(row.get('카드매출', 0)),
            "cash_sales": float(row.get('현금매출', 0)),
            "total_sales": float(row.get('총매출', 0))
        })
    
    if records:
        supabase.table("sales").upsert(records, on_conflict="store_id,date").execute()
        print(f"  ✓ 매출 {len(records)}건 마이그레이션 완료")


def migrate_visitors(supabase: Client, df: pd.DataFrame, store_id: str):
    """방문자 데이터 마이그레이션"""
    if df.empty:
        print("  - 방문자 데이터 없음")
        return
    
    records = []
    for _, row in df.iterrows():
        date = pd.to_datetime(row['날짜']).strftime('%Y-%m-%d')
        records.append({
            "store_id": store_id,
            "date": date,
            "visitors": int(row['방문자수'])
        })
    
    if records:
        supabase.table("naver_visitors").upsert(records, on_conflict="store_id,date").execute()
        print(f"  ✓ 방문자 {len(records)}건 마이그레이션 완료")


def migrate_menus(supabase: Client, df: pd.DataFrame, store_id: str) -> dict:
    """메뉴 데이터 마이그레이션 (메뉴명 -> ID 매핑 반환)"""
    if df.empty:
        print("  - 메뉴 데이터 없음")
        return {}
    
    menu_map = {}
    records = []
    for _, row in df.iterrows():
        menu_name = row['메뉴명']
        records.append({
            "store_id": store_id,
            "name": menu_name,
            "price": float(row['판매가']),
            "is_core": False
        })
    
    if records:
        result = supabase.table("menu_master").upsert(records, on_conflict="store_id,name").execute()
        # 메뉴명 -> ID 매핑 생성
        for menu in result.data:
            menu_map[menu['name']] = menu['id']
        print(f"  ✓ 메뉴 {len(records)}건 마이그레이션 완료")
    
    return menu_map


def migrate_ingredients(supabase: Client, df: pd.DataFrame, store_id: str) -> dict:
    """재료 데이터 마이그레이션 (재료명 -> ID 매핑 반환)"""
    if df.empty:
        print("  - 재료 데이터 없음")
        return {}
    
    ingredient_map = {}
    records = []
    for _, row in df.iterrows():
        ing_name = row['재료명']
        records.append({
            "store_id": store_id,
            "name": ing_name,
            "unit": row['단위'],
            "unit_cost": float(row['단가'])
        })
    
    if records:
        result = supabase.table("ingredients").upsert(records, on_conflict="store_id,name").execute()
        # 재료명 -> ID 매핑 생성
        for ing in result.data:
            ingredient_map[ing['name']] = ing['id']
        print(f"  ✓ 재료 {len(records)}건 마이그레이션 완료")
    
    return ingredient_map


def migrate_recipes(supabase: Client, df: pd.DataFrame, store_id: str, menu_map: dict, ingredient_map: dict):
    """레시피 데이터 마이그레이션"""
    if df.empty:
        print("  - 레시피 데이터 없음")
        return
    
    records = []
    for _, row in df.iterrows():
        menu_name = row['메뉴명']
        ing_name = row['재료명']
        
        menu_id = menu_map.get(menu_name)
        ing_id = ingredient_map.get(ing_name)
        
        if menu_id and ing_id:
            records.append({
                "store_id": store_id,
                "menu_id": menu_id,
                "ingredient_id": ing_id,
                "qty": float(row['사용량'])
            })
    
    if records:
        supabase.table("recipes").upsert(records, on_conflict="store_id,menu_id,ingredient_id").execute()
        print(f"  ✓ 레시피 {len(records)}건 마이그레이션 완료")


def migrate_daily_sales(supabase: Client, df: pd.DataFrame, store_id: str, menu_map: dict):
    """일일 판매 데이터 마이그레이션"""
    if df.empty:
        print("  - 일일 판매 데이터 없음")
        return
    
    records = []
    for _, row in df.iterrows():
        date = pd.to_datetime(row['날짜']).strftime('%Y-%m-%d')
        menu_name = row['메뉴명']
        menu_id = menu_map.get(menu_name)
        
        if menu_id:
            records.append({
                "store_id": store_id,
                "date": date,
                "menu_id": menu_id,
                "qty": int(row['판매수량'])
            })
    
    if records:
        supabase.table("daily_sales_items").upsert(records, on_conflict="store_id,date,menu_id").execute()
        print(f"  ✓ 일일 판매 {len(records)}건 마이그레이션 완료")


def migrate_inventory(supabase: Client, df: pd.DataFrame, store_id: str, ingredient_map: dict):
    """재고 데이터 마이그레이션"""
    if df.empty:
        print("  - 재고 데이터 없음")
        return
    
    records = []
    for _, row in df.iterrows():
        ing_name = row['재료명']
        ing_id = ingredient_map.get(ing_name)
        
        if ing_id:
            records.append({
                "store_id": store_id,
                "ingredient_id": ing_id,
                "on_hand": float(row['현재고']),
                "safety_stock": float(row['안전재고'])
            })
    
    if records:
        supabase.table("inventory").upsert(records, on_conflict="store_id,ingredient_id").execute()
        print(f"  ✓ 재고 {len(records)}건 마이그레이션 완료")


def migrate_targets(supabase: Client, df: pd.DataFrame, store_id: str):
    """목표 데이터 마이그레이션"""
    if df.empty:
        print("  - 목표 데이터 없음")
        return
    
    records = []
    for _, row in df.iterrows():
        records.append({
            "store_id": store_id,
            "year": int(row['연도']),
            "month": int(row['월']),
            "target_sales": float(row.get('목표매출', 0)),
            "target_cost_rate": float(row.get('목표원가율', 0)),
            "target_labor_rate": float(row.get('목표인건비율', 0)),
            "target_rent_rate": float(row.get('목표임대료율', 0)),
            "target_other_rate": float(row.get('목표기타비용율', 0)),
            "target_profit_rate": float(row.get('목표순이익률', 0))
        })
    
    if records:
        supabase.table("targets").upsert(records, on_conflict="store_id,year,month").execute()
        print(f"  ✓ 목표 {len(records)}건 마이그레이션 완료")


def main():
    """메인 마이그레이션 함수"""
    print("=" * 60)
    print("CSV to Supabase Migration Script")
    print("=" * 60)
    
    # Supabase 클라이언트 생성 (service_role_key 사용)
    print("\n[1] Supabase 연결 중...")
    supabase = get_supabase_client(use_service_role=True)
    print("✓ Supabase 연결 완료")
    
    # 데이터 디렉토리 확인
    data_dir = project_root / "data"
    if not data_dir.exists():
        print(f"\nError: data 디렉토리를 찾을 수 없습니다: {data_dir}")
        sys.exit(1)
    
    print(f"\n[2] CSV 파일 로드 중: {data_dir}")
    
    # 매장 생성/조회
    store_id = migrate_store(supabase, "Plate&Share")
    
    # CSV 파일 로드
    sales_df = load_csv_file("sales.csv", data_dir)
    visitors_df = load_csv_file("naver_visitors.csv", data_dir)
    menu_df = load_csv_file("menu_master.csv", data_dir)
    ingredient_df = load_csv_file("ingredient_master.csv", data_dir)
    recipe_df = load_csv_file("recipes.csv", data_dir)
    daily_sales_df = load_csv_file("daily_sales_items.csv", data_dir)
    inventory_df = load_csv_file("inventory.csv", data_dir)
    targets_df = load_csv_file("targets.csv", data_dir)
    
    print("\n[3] 데이터 마이그레이션 시작...")
    
    # 메뉴와 재료를 먼저 마이그레이션 (ID 매핑 필요)
    menu_map = migrate_menus(supabase, menu_df, store_id)
    ingredient_map = migrate_ingredients(supabase, ingredient_df, store_id)
    
    # 나머지 데이터 마이그레이션
    migrate_sales(supabase, sales_df, store_id)
    migrate_visitors(supabase, visitors_df, store_id)
    migrate_recipes(supabase, recipe_df, store_id, menu_map, ingredient_map)
    migrate_daily_sales(supabase, daily_sales_df, store_id, menu_map)
    migrate_inventory(supabase, inventory_df, store_id, ingredient_map)
    migrate_targets(supabase, targets_df, store_id)
    
    print("\n" + "=" * 60)
    print("✓ 마이그레이션 완료!")
    print("=" * 60)
    print(f"\n매장 ID: {store_id}")
    print("\n다음 단계:")
    print("1. Supabase에서 사용자 계정을 생성하세요")
    print("2. users 테이블에 사용자 정보를 등록하고 store_id를 연결하세요")
    print("3. Streamlit 앱에서 로그인하여 사용하세요")


if __name__ == "__main__":
    # Streamlit secrets를 로드하기 위한 임시 설정
    import streamlit as st
    
    # secrets.toml 파일이 없으면 직접 읽기 시도
    secrets_path = project_root / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print(f"Error: {secrets_path} 파일을 찾을 수 없습니다.")
        print("Please create .streamlit/secrets.toml file with Supabase credentials")
        sys.exit(1)
    
    # secrets.toml을 읽어서 환경 변수로 설정
    import tomllib
    with open(secrets_path, 'rb') as f:
        secrets = tomllib.load(f)
    
    # streamlit.secrets를 모킹
    class MockSecrets:
        def get(self, key, default=None):
            return secrets.get(key, default)
    
    st.secrets = MockSecrets()
    
    main()
