# Supabase 업그레이드 구현 상태

## ✅ 완료된 파일

1. **`sql/schema.sql`** - 완전 구현
   - `user_profiles` 테이블 사용 (users 아님)
   - 모든 테이블 + RLS 정책 완성
   - `auth.uid()` 기반 보안 정책

2. **`src/auth.py`** - 완전 구현
   - `check_login()`, `login()`, `logout()` 함수
   - `get_current_store_id()`, `get_current_store_name()` 함수
   - `show_login_page()` UI

3. **`scripts/bootstrap_store_and_manager.py`** - 완전 구현
   - 매장 및 사용자 프로필 생성 가이드 SQL 생성

4. **`.streamlit/secrets.toml.example`** - 완전 구현

## ⚠️ 부분 구현 / 완성 필요

### `src/storage_supabase.py` (작업 중)

**현재 상태:**
- `storage_db.py`에 기본 구조는 있으나, `auth.py`와 통합 필요
- `user_profiles` 테이블 사용으로 변경 필요
- `get_current_store_id()`를 `auth.py`에서 import 필요

**구현 필요 함수들:**
기존 `storage.py`와 동일한 인터페이스로 다음 함수들을 구현해야 함:

```python
# Load 함수들
- load_csv(filename, default_columns)  # 부분 구현됨
- load_key_menus()  # 부분 구현됨

# Save 함수들  
- save_sales(date, store_name, card_sales, cash_sales, total_sales)  # 부분 구현됨
- save_visitor(date, visitors)  # 부분 구현됨
- save_menu(menu_name, price)  # 부분 구현됨
- update_menu(old_menu_name, new_menu_name, new_price)  # 필요
- delete_menu(menu_name, check_references=True)  # 필요
- save_ingredient(ingredient_name, unit, unit_price)  # 필요
- update_ingredient(...)  # 필요
- delete_ingredient(...)  # 필요
- save_recipe(menu_name, ingredient_name, quantity)  # 필요
- delete_recipe(...)  # 필요
- save_daily_sales_item(date, menu_name, quantity)  # 필요
- save_inventory(ingredient_name, current_stock, safety_stock)  # 필요
- save_targets(...)  # 필요
- save_abc_history(...)  # 필요
- save_key_menus(menu_list)  # 부분 구현됨
- save_daily_close(...)  # 필요
- delete_sales(date, store=None)  # 필요
- delete_visitor(date)  # 필요
- create_backup()  # DB 백업용, 필요
```

### `app.py` (수정 필요)

**필요한 변경:**
1. 상단에 로그인 체크 추가:
```python
from src.auth import check_login, show_login_page, get_current_store_name, logout

if not check_login():
    show_login_page()
    st.stop()

# 로그인 성공 시
store_name = get_current_store_name()
st.sidebar.markdown(f"**🏪 현재 매장: {store_name}**")
st.sidebar.button("로그아웃", on_click=logout)
```

2. `storage` import를 `storage_supabase`로 변경:
```python
# 기존: from src.storage import *
# 변경: from src.storage_supabase import *
```

### `scripts/migrate_csv_to_db.py` (수정 필요)

**필요한 변경:**
- `service_role_key` 사용 부분 제거 (사용자 요구사항에 따라)
- 또는 마이그레이션은 수동 SQL로 안내

## 📝 다음 단계

1. **`src/storage_supabase.py` 완성**
   - `storage_db.py`를 `storage_supabase.py`로 복사
   - `auth.py`의 함수들 사용하도록 수정
   - 나머지 함수들 구현

2. **`app.py` 로그인 통합**
   - 로그인 체크 추가
   - storage import 변경

3. **README 업데이트**
   - `README_SUPABASE_SETUP.md`에 `user_profiles` 관련 내용 추가
   - 초보자용 가이드 업데이트

## 🔒 보안 확인 사항

- ✅ `service_role_key`는 Streamlit 앱에 포함 안 됨
- ✅ RLS 정책은 `auth.uid()` 기반으로 설정됨
- ✅ 모든 테이블에 RLS ON
- ✅ `user_profiles` 테이블 사용 (auth.users와 충돌 없음)
