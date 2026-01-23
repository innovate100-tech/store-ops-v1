# storage_supabase.py 수정 요약

## 변경된 함수

### 1. `save_daily_close()` 수정

**변경사항:**
- `p_changed_by` 파라미터를 RPC 호출에 추가 (audit용 사용자 ID)
- 주석에 SSOT 정책 명시

**코드 위치:** `src/storage_supabase.py` ~1975 라인

**변경 내용:**
```python
# 변경 전
supabase.rpc('save_daily_close_transaction', {
    ...
    'p_sales_items': sales_items_payload,
}).execute()

# 변경 후
changed_by = None
try:
    session = supabase.auth.get_session()
    if session and getattr(session, "user", None):
        u = getattr(session.user, "id", None)
        if u:
            changed_by = str(u)
except Exception:
    pass

supabase.rpc('save_daily_close_transaction', {
    ...
    'p_sales_items': sales_items_payload,
    'p_changed_by': changed_by,  # audit용 사용자 ID
}).execute()
```

---

### 2. `save_daily_sales_item()` 대폭 수정

**변경사항:**
- ❌ `daily_sales_items_overrides` 테이블 사용 중단
- ✅ `daily_sales_items` 테이블에 직접 upsert
- ✅ Audit 로깅 추가 (`log_daily_sales_item_change` RPC 호출)
- ✅ DELETE 금지, UPSERT 구조로 변경
- ✅ `reason` 파라미터 추가 (선택사항)

**코드 위치:** `src/storage_supabase.py` ~1704 라인

**주요 변경:**
```python
# 변경 전: daily_sales_items_overrides에 저장
supabase.table("daily_sales_items_overrides").upsert(...)

# 변경 후: daily_sales_items에 직접 저장 + audit
# 1. 기존 qty 조회
old_qty = ... (기존 값 조회)

# 2. UPSERT
supabase.table("daily_sales_items").upsert({
    "store_id": store_id,
    "date": date_str,
    "menu_id": menu_id,
    "qty": new_qty
}, on_conflict="store_id,date,menu_id").execute()

# 3. Audit 로깅
supabase.rpc('log_daily_sales_item_change', {
    'p_store_id': str(store_id),
    'p_date': date_str,
    'p_menu_id': str(menu_id),
    'p_action': action,  # 'insert' or 'update' or 'soft_delete'
    'p_old_qty': old_qty,
    'p_new_qty': new_qty,
    'p_source': 'override',
    'p_reason': audit_reason,
    'p_changed_by': changed_by
}).execute()
```

---

### 3. 새 함수 추가

#### `load_official_daily_sales()`

**목적:** 공식 매출 SSOT 조회 (daily_close 기준)

**위치:** `src/storage_supabase.py` ~3430 라인 (추가)

**사용법:**
```python
df = load_official_daily_sales(
    store_id="...",  # 선택사항 (None이면 현재 매장)
    start_date="2024-01-01",  # 선택사항
    end_date="2024-01-31"  # 선택사항
)
```

**반환값:**
- `pd.DataFrame` with columns: store_id, date, total_sales, card_sales, cash_sales, visitors, memo, is_official, source
- `is_official` = True
- `source` = 'daily_close'

---

#### `load_best_available_daily_sales()`

**목적:** 최선의 매출 데이터 조회 (daily_close 우선, 없으면 sales 사용)

**위치:** `src/storage_supabase.py` ~3470 라인 (추가)

**사용법:**
```python
df = load_best_available_daily_sales(
    store_id="...",  # 선택사항 (None이면 현재 매장)
    start_date="2024-01-01",  # 선택사항
    end_date="2024-01-31"  # 선택사항
)
```

**반환값:**
- `pd.DataFrame` with columns: store_id, date, total_sales, card_sales, cash_sales, visitors, memo, is_official, source
- `is_official` = True (daily_close 있으면) or False (sales만 있으면)
- `source` = 'daily_close' or 'sales'

---

## 주의사항

### ⚠️ 중요

1. **`save_daily_sales_item()` 함수 시그니처 변경**
   - 기존: `save_daily_sales_item(date, menu_name, quantity)`
   - 변경: `save_daily_sales_item(date, menu_name, quantity, reason=None)`
   - `reason` 파라미터는 선택사항이므로 기존 호출 코드는 그대로 동작

2. **`daily_sales_items_overrides` 테이블 사용 중단**
   - 이제 `daily_sales_items` 테이블에 직접 저장
   - 기존 overrides 테이블은 사용하지 않음 (마이그레이션 필요 시 별도 작업)

3. **Audit 로깅 실패 시 경고만 출력**
   - Audit 로깅이 실패해도 저장은 계속 진행
   - 로그에 경고 메시지 출력

---

## 테스트 체크리스트

- [ ] `save_daily_close()` 실행 시 `p_changed_by` 전달 확인
- [ ] `save_daily_sales_item()` 실행 시 `daily_sales_items`에 저장 확인
- [ ] `save_daily_sales_item()` 실행 시 audit 기록 확인
- [ ] `load_official_daily_sales()` 조회 테스트
- [ ] `load_best_available_daily_sales()` 조회 테스트
- [ ] DELETE 사용하지 않는지 확인 (코드 검색)

---

## 마이그레이션 가이드

기존 코드는 대부분 그대로 동작하지만, 다음 사항을 확인하세요:

1. **`save_daily_sales_item()` 호출 코드**
   - 기존 호출은 그대로 동작 (reason은 선택사항)
   - 필요 시 reason 파라미터 추가 권장

2. **`daily_sales_items_overrides` 테이블 사용 코드**
   - 더 이상 사용하지 않으므로 제거 또는 마이그레이션 필요
   - 현재는 `daily_sales_items` 테이블만 사용

3. **VIEW 사용 권장**
   - 공식 매출 조회: `load_official_daily_sales()` 사용
   - 최선의 매출 조회: `load_best_available_daily_sales()` 사용
   - 기존 `load_csv('sales.csv')`는 여전히 동작하지만, VIEW 사용 권장
