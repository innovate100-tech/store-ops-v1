# Supabase 업그레이드 변경 사항 요약

## 📁 새로 생성된 파일

### 1. `sql/schema.sql`
- Supabase Postgres 데이터베이스 스키마
- 모든 테이블 정의 및 RLS(Row Level Security) 정책 포함
- 필수: Supabase SQL Editor에서 실행 필요

### 2. `src/storage_db.py` (새로 생성)
- Supabase 기반 저장소 모듈 (작업 중)
- 현재 구현된 함수:
  - `get_supabase_client()`: Supabase 클라이언트 생성
  - `get_current_user_store_id()`: 현재 사용자의 store_id 조회
  - `load_csv()`: 테이블 데이터 로드 (CSV 호환 인터페이스)
  - `load_key_menus()`: 핵심 메뉴 목록 로드
  - `save_sales()`, `save_visitor()`, `save_menu()`, `save_key_menus()`: 기본 저장 함수

**⚠️ 아직 구현 필요한 함수들:**
- `update_menu()`, `delete_menu()`
- `save_ingredient()`, `update_ingredient()`, `delete_ingredient()`
- `save_recipe()`, `delete_recipe()`
- `save_daily_sales_item()`, `save_inventory()`
- `save_targets()`, `save_abc_history()`, `save_daily_close()`
- `delete_sales()`, `delete_visitor()`
- `create_backup()` (DB 백업용)

### 3. `.streamlit/secrets.toml.example`
- Streamlit Secrets 설정 예시 파일
- 실제 사용 시 `.streamlit/secrets.toml`로 복사하여 사용

### 4. `scripts/migrate_csv_to_db.py`
- CSV 데이터를 Supabase로 마이그레이션하는 스크립트
- `service_role_key` 사용 (RLS 우회)

### 5. `README_SUPABASE_SETUP.md`
- Supabase 설정 완전 초보자용 가이드
- 단계별 상세 설명 포함

---

## 🔄 수정된 파일

### 1. `requirements.txt`
**추가된 패키지:**
```
supabase>=2.0.0
python-dotenv>=1.0.0
```

### 2. `src/storage.py` (대대적 수정 필요)
**변경 방향:**
- DB 모드를 감지하여 `storage_db` 모듈 사용
- 또는 전체 함수를 DB 버전으로 교체

**권장 방법:**
```python
# storage.py 상단에 추가
try:
    import streamlit as st
    USE_DB = bool(st.secrets.get("supabase", {}).get("url"))
except:
    USE_DB = False

if USE_DB:
    # storage_db 모듈에서 함수 import
    from src.storage_db import *
else:
    # 기존 CSV 로직 유지
    ...
```

**⚠️ 현재 상태:** 아직 수정 안 됨 (DB 버전으로 교체 필요)

### 3. `app.py` (로그인 화면 추가 필요)
**추가 필요:**
- 로그인 체크 로직
- Supabase Auth 로그인 화면
- 로그인 후 현재 매장명 표시

**예시 구조:**
```python
# app.py 상단에 추가
import streamlit as st
from src.auth import check_login, show_login_page, get_current_store_name

# 로그인 체크
if not check_login():
    show_login_page()
    st.stop()

# 로그인 성공 시 매장명 표시
store_name = get_current_store_name()
st.sidebar.markdown(f"**🏪 현재 매장: {store_name}**")
```

**⚠️ 현재 상태:** 아직 수정 안 됨

---

## 📝 구현 필요 사항

### 1. `src/auth.py` (새로 생성 필요)
로그인 관련 함수들을 담는 모듈:
- `check_login()`: 로그인 상태 확인
- `show_login_page()`: 로그인 UI 표시
- `login(email, password)`: 로그인 실행
- `logout()`: 로그아웃
- `get_current_store_name()`: 현재 매장명 조회

### 2. `src/storage_db.py` 확장
나머지 저장/수정/삭제 함수들 구현

### 3. `src/storage.py` DB 통합
storage_db 모듈을 사용하도록 수정

### 4. `app.py` 로그인 통합
로그인 화면 및 체크 로직 추가

---

## 🚀 다음 단계

1. **Supabase 설정 완료** (README_SUPABASE_SETUP.md 참고)
2. **storage_db.py 완성**: 나머지 함수들 구현
3. **auth.py 생성**: 로그인 관련 함수 구현
4. **storage.py 수정**: DB 모드 지원 추가
5. **app.py 수정**: 로그인 통합

---

## 💡 빠른 시작 가이드

1. `sql/schema.sql`을 Supabase SQL Editor에서 실행
2. `.streamlit/secrets.toml` 생성 (예시 파일 참고)
3. `python scripts/migrate_csv_to_db.py` 실행
4. Supabase Auth에서 사용자 생성 후 `users` 테이블에 등록
5. `streamlit run app.py` 실행하여 테스트

---

## ⚠️ 주의사항

- `storage_db.py`와 `storage.py`의 인터페이스는 동일하게 유지해야 `app.py` 수정이 최소화됩니다
- RLS 정책이 제대로 작동하는지 확인하세요
- `service_role_key`는 절대 공개하지 마세요
