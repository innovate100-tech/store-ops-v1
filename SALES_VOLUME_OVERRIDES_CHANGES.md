# 판매량등록 → overrides UPSERT 변경 요약

## 수정한 파일 / 함수

| 파일 | 함수/위치 | 변경 내용 |
|------|-----------|-----------|
| `src/storage_supabase.py` | `save_daily_sales_item` | overrides 전용 UPSERT, `supabase` 없을 때 raise, `note` null, `updated_by` optional |
| `src/storage_supabase.py` | `verify_overrides_saved` (신규) | 저장 직후 overrides 조회로 건수 검증 (DEV용) |
| `ui_pages/sales_volume_entry.py` | 저장 블록 | 성공 문구 변경, DEV 시 `verify_overrides_saved` 호출 후 "override 저장 확인됨" 표시 |

---

## daily_sales_items 저장 → overrides UPSERT 변경

- **기존**: `save_daily_sales_item`이 이미 `daily_sales_items_overrides`에 upsert하고 있었으나,  
  - `_check_supabase_for_dev_mode()`가 `None`이면 `return False`만 하고 **예외를 던지지 않음** → UI에서 성공으로 처리되어 **조용히 실패**  
  - `note`에 고정 문구 저장, `updated_by` 미사용  
- **변경**:
  1. **Supabase 없음(DEV 등)**: `return False` 제거, **`raise Exception(...)`** 로 실패를 반드시 노출.
  2. **저장 대상**: 계속 **`daily_sales_items_overrides`** 만 사용. `daily_sales_items`에는 **쓰지 않음** (기존부터 overrides 전용).
  3. **UPSERT**:
     - 테이블: `daily_sales_items_overrides`
     - 키: `(store_id, sale_date, menu_id)`
     - 값: `store_id`, `sale_date`(날짜→`sale_date` 매핑), `menu_id`, `qty`(최종값), `updated_at`(DB default), `updated_by`(가능 시 `auth.get_session().user.id`, 아니면 null), `note`=null
  4. **성공 시**: `soft_invalidate(..., targets=["daily_sales_items"])` 유지.

---

## UI 변경 (sales_volume_entry)

- **성공 메시지**:  
  `"✅ 최종 판매량이 저장되었습니다(마감 입력보다 우선 적용)."`
- **실패**: 기존처럼 `st.error`로 예외 메시지 표시 (조용히 실패 없음).
- **DEV 모드**: 저장 성공 직후 `verify_overrides_saved(store_id, sales_date, success_count)` 호출 후,  
  확인되면 `st.info("🔧 override 저장 확인됨 (DEV)")` 출력.

---

## 테스트 시나리오 및 체크리스트

### 사전 조건

- [ ] `public.daily_sales_items_overrides` 테이블, `public.v_daily_sales_items_effective` 뷰 생성 완료
- [ ] DEV MODE가 아닌 상태에서 Supabase 연결 가능 (또는 DEV에서 저장 시 Supabase 사용 가능한 설정)
- [ ] 로그인 후 `store_id` 확보, 메뉴·마감 사용 가능

### STEP 5 시나리오

1. **날짜 D 선택 → 점장마감에서 메뉴A qty=10 저장**
   - [ ] 점장 마감 페이지에서 날짜 D, 메뉴A 수량 10 입력 후 마감 완료
   - [ ] `daily_sales_items`에 해당 (store_id, D, menu_a_id) 행 존재 확인

2. **판매량등록에서 메뉴A qty=3 저장**
   - [ ] 판매량 등록 페이지에서 날짜 D, 메뉴A 수량 3 입력 후 일괄 저장
   - [ ] 성공 시 `"최종 판매량이 저장되었습니다(마감 입력보다 우선 적용)."` 표시
   - [ ] 실패 시 `st.error`에 에러 메시지 표시 (조용히 실패 없음)

3. **Supabase SQL Editor로 확인**
   ```sql
   SELECT * FROM public.daily_sales_items_overrides
   WHERE store_id = '<해당 store_id>' AND sale_date = 'D';
   ```
   - [ ] 메뉴A에 해당하는 행 존재, `qty = 3`

   ```sql
   SELECT * FROM public.v_daily_sales_items_effective
   WHERE store_id = '<해당 store_id>' AND date = 'D';
   ```
   - [ ] 메뉴A의 `qty`가 **3**으로 보임 (override 적용)

4. **마감 재저장 후 effective 유지**
   - [ ] 점장 마감에서 같은 날짜 D로 메뉴A qty=8 등 **다시 마감 저장**
   - [ ] `v_daily_sales_items_effective`에서 메뉴A `qty`가 **여전히 3** (override 우선 유지)

### DEV 모드 시 (해당되는 경우)

- [ ] DEV 모드에서 저장 성공 시 `"🔧 override 저장 확인됨 (DEV)"` 표시되는지 확인  
  (이때는 Supabase 사용 가능해야 하며, `verify_overrides_saved`가 True를 반환하는 경우에만 표시)

---

## 요약

- **저장 경로**: 판매량등록 → `save_daily_sales_item` → **`daily_sales_items_overrides` UPSERT만** 사용. `daily_sales_items` 직접 저장/누적 없음.
- **실패 처리**: Supabase 없음(DEV 등) 포함, **예외 발생** → UI에서 `st.error`로 표시.
- **성공 문구**: `"최종 판매량이 저장되었습니다(마감 입력보다 우선 적용)."`
- **검증**: DEV 모드에서 저장 직후 `verify_overrides_saved`로 override 저장 여부 확인 후, 확인 시 `"override 저장 확인됨 (DEV)"` 출력.
