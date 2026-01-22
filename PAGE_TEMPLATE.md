# 새 페이지 만들 때 표준 템플릿

## 기본 구조

```python
"""
페이지 설명
"""
import streamlit as st
from src.bootstrap import bootstrap
from src.auth import get_current_store_id, ensure_store_context, get_supabase_client

# 1. Bootstrap 호출 (항상 최상단)
bootstrap(page_title="페이지 제목")

# 2. Store 컨텍스트 확보 (필수)
store_id = ensure_store_context()
if not store_id:
    # ensure_store_context()가 이미 에러/경고를 표시하고 st.stop()을 호출했으므로
    # 여기 도달하지 않지만, 타입 체크를 위해 명시적으로 체크
    return

# 3. Supabase 클라이언트 생성 (필요한 경우)
# 디버그/테스트가 아닌 경우 기본값 사용
supabase = get_supabase_client()  # reset_session_on_fail=True (기본값)

# 또는 디버그/테스트 시 세션 보존이 필요한 경우:
# supabase = get_supabase_client(reset_session_on_fail=False)

# 4. 데이터 로드 (store_id 사용)
# stores 테이블 필터는 반드시 id 컬럼만 사용
# ❌ 잘못된 예: .eq("store_id", store_id)
# ✅ 올바른 예: .eq("id", store_id)
result = supabase.table("stores").select("name").eq("id", store_id).execute()

# 5. 페이지 렌더링
st.title("페이지 제목")
# ... 나머지 UI 코드
```

## 주요 규칙

### 1. Bootstrap 호출
- 항상 페이지 최상단에서 호출
- `bootstrap()` 내부에서 `st.stop()` 호출 금지 (에러만 표시)

### 2. Store 컨텍스트
- `ensure_store_context()` 사용 권장
- `get_current_store_id()`만 사용하는 경우 None 체크 필수

### 3. Supabase 클라이언트
- `get_supabase_client()` 단일 함수로 통일
- 디버그/테스트: `reset_session_on_fail=False`
- 일반 사용: 기본값 (`reset_session_on_fail=True`)

### 4. Stores 테이블 필터
- **반드시 `id` 컬럼만 사용**
- ❌ `.eq("store_id", store_id)` 금지
- ✅ `.eq("id", store_id)` 사용

### 5. DEV MODE
- `secrets.toml`에 `auto_login_dev=true/false` 옵션으로 자동 로그인 토글 가능
- 기본값: `true` (새로고침 시 자동 로그인)

## 예시: 완전한 페이지 템플릿

```python
"""
예시 페이지
"""
import streamlit as st
from src.bootstrap import bootstrap
from src.auth import ensure_store_context, get_supabase_client
from src.storage_supabase import load_csv

# Bootstrap
bootstrap(page_title="예시 페이지")

# Store 컨텍스트 확보
store_id = ensure_store_context()
if not store_id:
    return  # ensure_store_context()가 이미 처리함

# Supabase 클라이언트
supabase = get_supabase_client()

# 데이터 로드
try:
    # stores 테이블은 id 컬럼으로 필터링
    store_info = supabase.table("stores").select("name").eq("id", store_id).execute()
    store_name = store_info.data[0]['name'] if store_info.data else "알 수 없음"
    
    # 다른 테이블은 store_id 컬럼으로 필터링 (stores 테이블이 아닌 경우)
    sales_df = load_csv("sales.csv")
    
except Exception as e:
    st.error(f"데이터 로드 실패: {e}")
    st.stop()

# 페이지 렌더링
st.title(f"예시 페이지 - {store_name}")
st.write(f"Store ID: {store_id}")

# ... 나머지 UI 코드
```
