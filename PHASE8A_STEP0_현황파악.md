# Phase 8-A Step 0: 리포/코드 현황 파악 결과

## 1. 현재 인증 세션 키 이름

### 세션 상태 키:
- `st.session_state.user_id` - 로그인한 사용자의 UUID
- `st.session_state.access_token` - Supabase 인증 토큰
- `st.session_state.refresh_token` - 토큰 갱신용
- `st.session_state.store_id` - 레거시 호환용 store_id
- `st.session_state._active_store_id` - 단일 소스 오브 트루스 (SSOT)
- `st.session_state.user_role` - 사용자 역할 ('manager', 'admin')
- `st.session_state._cached_store_name` - 캐시된 매장명

### 인증 체크 함수:
- `check_login()` - `src/auth.py:421` - user_id와 access_token 존재 여부 확인
- `require_auth_and_store()` - `src/ui/guards.py:10` - 로그인 + store_id 확인

### 로그인 플로우:
1. `app.py:23` - `check_login()` 호출
2. 실패 시 `show_login_page()` 표시
3. 성공 시 `login()` 함수에서 `user_profiles` 조회하여 `store_id` 설정

---

## 2. 현재 데이터 로더 함수 목록 (SSOT)

### 핵심 데이터 로더 (src/storage_supabase.py):

#### 매출 관련:
- `load_monthly_sales_total(store_id, year, month)` - 월간 매출 합계
- `save_sales(date, store_name, ...)` - 매출 저장 (레거시: store_name 사용)

#### 마감 관련:
- `save_daily_close(date, store_name, ...)` - 일일 마감 저장 (레거시: store_name 사용)
- `load_daily_close()` - 일일 마감 조회 (확인 필요)

#### 판매량 관련:
- `save_daily_sales_item(date, menu_name, quantity)` - 일일 판매량 저장
- `load_daily_sales_items()` - 일일 판매량 조회 (확인 필요)

#### 메뉴/재료/레시피:
- `save_menu(menu_name, price)` - 메뉴 저장
- `save_ingredient(ingredient_name, unit, unit_price, ...)` - 재료 저장
- `save_recipe(menu_name, ingredient_name, quantity)` - 레시피 저장

#### 비용 구조:
- `load_expense_structure(year, month, store_id, ...)` - 비용 구조 조회
- `save_expense_item(year, month, category, item_name, amount, ...)` - 비용 항목 저장
- `get_fixed_costs(store_id, year, month)` - 고정비 계산
- `get_variable_cost_ratio(store_id, year, month)` - 변동비율 계산

#### 정산 관련:
- `load_actual_settlement_items(store_id, year, month)` - 실제 정산 항목 조회
- `get_month_settlement_status(store_id, year, month)` - 정산 상태 조회
- `load_available_settlement_months(store_id, limit)` - 정산 가능 월 목록

---

## 3. store_id 컬럼 현황

### ✅ store_id가 이미 있는 테이블 (schema.sql 기준):

| 테이블명 | store_id 컬럼 | NOT NULL | 참조 |
|---------|--------------|----------|------|
| `stores` | 없음 (PK가 id) | - | - |
| `user_profiles` | `store_id` | NULL 허용 | `stores(id)` |
| `sales` | `store_id` | NOT NULL | `stores(id)` |
| `naver_visitors` | `store_id` | NOT NULL | `stores(id)` |
| `menu_master` | `store_id` | NOT NULL | `stores(id)` |
| `ingredients` | `store_id` | NOT NULL | `stores(id)` |
| `recipes` | `store_id` | NOT NULL | `stores(id)` |
| `daily_sales_items` | `store_id` | NOT NULL | `stores(id)` |
| `inventory` | `store_id` | NOT NULL | `stores(id)` |
| `daily_close` | `store_id` | NOT NULL | `stores(id)` |
| `targets` | `store_id` | NOT NULL | `stores(id)` |
| `abc_history` | `store_id` | NOT NULL | `stores(id)` |
| `expense_structure` | `store_id` | NOT NULL | `stores(id)` |

### ⚠️ 확인 필요 (추가 테이블):
- `cost_item_templates` - 비용 항목 템플릿 (확인 필요)
- `suppliers` - 공급업체 (확인 필요)
- `ingredient_suppliers` - 재료-공급업체 매핑 (확인 필요)
- `orders` - 발주 (확인 필요)

### 📝 주의사항:
- 일부 함수는 아직 `store_name`을 사용하는 레거시 방식 (예: `save_sales`, `save_daily_close`)
- `user_profiles.store_id`는 NULL 허용 (단일 매장 연결 방식)
- 새로운 요구사항: `store_members` 테이블 필요 (다중 매장 지원)

---

## 4. Supabase 클라이언트 초기화

### 클라이언트 생성 함수 (src/auth.py):
- `get_supabase_client()` - 인증된 클라이언트 (RLS 적용)
- `get_auth_client()` - 인증 클라이언트 (별칭)
- `get_read_client()` - 읽기 전용 클라이언트
- `get_anon_client()` - 익명 클라이언트 (RLS 없음, 진단용)
- `get_service_client()` - Service Role 클라이언트 (DEV MODE 전용, RLS 우회)

### 사용 위치:
- `src/storage_supabase.py` - 모든 데이터 로더에서 사용
- `src/auth.py` - 인증 관련 작업

---

## 5. 현재 구조의 문제점

### 1. 단일 매장만 지원:
- `user_profiles.store_id`는 단일 값만 저장
- 다중 매장 소속 불가능

### 2. 레거시 함수:
- `save_sales()`, `save_daily_close()` 등이 `store_name` 사용
- `store_id`를 직접 받지 않고 내부에서 조회

### 3. 매장 선택 기능 없음:
- 로그인 시 자동으로 `user_profiles.store_id` 사용
- 매장 전환 기능 없음

### 4. 회원가입 기능 없음:
- 수동으로 Supabase Auth에서 사용자 생성 필요
- `user_profiles` 수동 등록 필요

---

## 다음 단계 (Step 1) 준비사항

1. ✅ 현재 구조 파악 완료
2. ⏭️ Step 1: 새로운 테이블 생성 (`stores`, `store_members`, `user_profiles` 업데이트)
3. ⏭️ Step 2: RLS 정책 완성
4. ⏭️ Step 3: 기존 테이블에 store_id 추가 (필요시)
5. ⏭️ Step 4: 회원가입 UI 추가
6. ⏭️ Step 5: 매장 생성 플로우
7. ⏭️ Step 6: 매장 선택 화면
8. ⏭️ Step 7: store_id 필터 강제
9. ⏭️ Step 8: 마이그레이션
10. ⏭️ Step 9: 검증
