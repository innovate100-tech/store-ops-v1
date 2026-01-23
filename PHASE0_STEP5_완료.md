# Phase 0 STEP 5 완료 보고서
## "마지막 rerun 정리 + 저장/메시지/캐시 무효화 패턴 표준화"

**작업 일자**: 2026-01-24  
**목표**: 남아있는 불필요 rerun을 마지막으로 정리하고, 저장/메시지/캐시 무효화 패턴을 표준화

---

## 1️⃣ Expander lazy loading rerun 제거 결과

### settlement_actual.py

| 라인 | 이전 패턴 | 변경 후 | 근거 |
|------|----------|---------|------|
| 1587-1589 | 버튼 클릭 → `session_state` True → `st.rerun()` | 버튼 클릭 → 즉시 렌더 → `session_state` True | rerun 없이 그 자리에서 즉시 로드 |
| 1601-1603 | 버튼 클릭 → `session_state` True → `st.rerun()` | 버튼 클릭 → 즉시 렌더 → `session_state` True | rerun 없이 그 자리에서 즉시 로드 |

**변경 전**:
```python
if st.button("📊 성적표 보기", key="settlement_expand_analysis", use_container_width=True):
    st.session_state['settlement_analysis_expanded'] = True
    st.rerun()  # ← rerun 발생
```

**변경 후**:
```python
if st.button("📊 성적표 보기", key="settlement_expand_analysis", use_container_width=True):
    # Phase 0 STEP 5: rerun 없이 즉시 로드 (버튼 클릭 시 그 자리에서 렌더)
    _render_analysis_section(store_id, year, month, expense_items, totals, total_sales)
    st.session_state['settlement_analysis_expanded'] = True
```

**효과**: expander 열기 시 전체 페이지 rerun 없이 해당 섹션만 즉시 로드

### home_page.py

| 라인 | 이전 패턴 | 변경 후 | 근거 |
|------|----------|---------|------|
| 272-274 | 버튼 클릭 → `session_state` True → `st.rerun()` | 버튼 클릭 → 즉시 렌더 → `session_state` True | rerun 없이 그 자리에서 즉시 로드 |
| 286-288 | 버튼 클릭 → `session_state` True → `st.rerun()` | 버튼 클릭 → 즉시 렌더 → `session_state` True | rerun 없이 그 자리에서 즉시 로드 |

**변경 전**:
```python
if st.button("📋 우선순위 보기", key="home_expand_zone4", use_container_width=True):
    st.session_state['home_zone4_expanded'] = True
    st.rerun()  # ← rerun 발생
```

**변경 후**:
```python
if st.button("📋 우선순위 보기", key="home_expand_zone4", use_container_width=True):
    # Phase 0 STEP 5: rerun 없이 즉시 로드 (버튼 클릭 시 그 자리에서 렌더)
    _render_zone4_weekly_priorities(store_id, year, month)
    st.session_state['home_zone4_expanded'] = True
```

**효과**: expander 열기 시 전체 페이지 rerun 없이 해당 섹션만 즉시 로드

**총 제거**: 4개 `st.rerun()` 호출 (expander lazy loading)

---

## 2️⃣ 저장 패턴 표준화 적용 지점

### 공용 헬퍼 함수 추가 (src/ui_helpers.py)

다음 함수들을 추가하여 저장/메시지/상태 갱신 패턴을 표준화:

1. **`ui_flash_success(msg: str, show_toast: bool = True)`**
   - 성공 메시지 표시 (st.success + st.toast)
   - 표준화된 성공 피드백

2. **`ui_flash_error(msg: str, show_toast: bool = True)`**
   - 에러 메시지 표시 (st.error + st.toast)
   - 표준화된 에러 피드백

3. **`ui_flash_warning(msg: str, show_toast: bool = True)`**
   - 경고 메시지 표시 (st.warning + st.toast)
   - 표준화된 경고 피드백

4. **`apply_state_patch(patches: Dict[str, Any])`**
   - session_state에 여러 값을 한 번에 업데이트
   - 상태 갱신 표준화

5. **`invalidate_keys(targets: list, reason: str = "user_action")`**
   - 캐시 무효화 (soft_invalidate 래핑)
   - key 기반 캐시 무효화 표준화

### settlement_actual.py 적용 지점

| 라인 | 이전 패턴 | 변경 후 |
|------|----------|---------|
| 271 | `st.success("✅ 템플릿을 다시 불러왔습니다...")` | `ui_flash_success("템플릿을 다시 불러왔습니다...")` |
| 340 | `st.success(f"✅ sales 월합계로...")` | `ui_flash_success(f"sales 월합계로...")` |
| 344 | `st.error(f"❌ 매출 불러오기 실패...")` | `ui_flash_error(f"매출 불러오기 실패...")` |
| 352 | `st.success(f"✅ 자동값으로 되돌렸습니다...")` | `ui_flash_success(f"자동값으로 되돌렸습니다...")` |
| 355 | `st.warning("자동값이 없습니다...")` | `ui_flash_warning("자동값이 없습니다...")` |
| 549-553 | `st.success(...)` + `try: st.toast(...)` | `ui_flash_success(...)` |

**효과**: 
- 메시지 표시 패턴 통일
- toast 메시지 자동 처리
- 코드 중복 제거

### sales_entry.py 적용 계획

현재 `sales_entry.py`는 이미 `session_state` 기반 메시지 표시 패턴을 사용하고 있어, 추가 표준화는 선택사항입니다. 향후 필요 시 `ui_flash_*` 함수로 마이그레이션 가능합니다.

---

## 3️⃣ 캐시 무효화 개선 지점

### app.py - 레시피 저장/수정/삭제

| 라인 | 이전 패턴 | 변경 후 | 근거 |
|------|----------|---------|------|
| 2102 | `st.cache_data.clear()` (전체 clear) | `invalidate_keys(targets=["recipes"])` | key 기반 무효화로 변경 |
| 2318 | `st.cache_data.clear()` (전체 clear) | `invalidate_keys(targets=["recipes"])` | key 기반 무효화로 변경 |
| 2334 | `st.cache_data.clear()` (전체 clear) | `invalidate_keys(targets=["recipes"])` | key 기반 무효화로 변경 |

**변경 전**:
```python
try:
    st.cache_data.clear()  # ← 전체 캐시 클리어
except Exception as e:
    logging.getLogger(__name__).warning(f"캐시 클리어 실패 (레시피 저장): {e}")
```

**변경 후**:
```python
try:
    from src.ui_helpers import invalidate_keys
    invalidate_keys(targets=["recipes"], reason="레시피 저장")  # ← key 기반 무효화
except Exception as e:
    logging.getLogger(__name__).warning(f"캐시 무효화 실패 (레시피 저장): {e}")
```

**효과**: 
- 전체 캐시 클리어 대신 필요한 캐시만 무효화
- 다른 캐시는 유지하여 성능 향상
- 무효화 이유(reason) 기록으로 디버깅 용이

### 유지한 전체 캐시 clear

다음 위치는 전체 캐시 clear가 의도된 동작이므로 유지:

1. **home_page.py (라인 204-205)**: 새로고침 버튼
   - 사용자가 명시적으로 전체 새로고침을 요청하는 경우
   - 전체 캐시 clear가 적절함

2. **src/ui_helpers.py (라인 235)**: safe_clear_cache 함수
   - 최후의 수단으로 전체 clear 사용
   - 주석으로 key 기반 무효화 사용 권장 명시

---

## 4️⃣ 신규계정/기존계정 테스트 체크리스트

### Expander lazy loading rerun 제거 테스트

- [ ] **settlement_actual.py - 성적표 섹션**
  - 실제정산 페이지 진입
  - ✅ 성적표 섹션이 접혀있는지 확인
  - ✅ "성적표 보기" 버튼 클릭
  - ✅ 성적표가 즉시 로드되는지 확인 (rerun 없이)
  - ✅ 성적표 데이터가 올바르게 표시되는지 확인
  - ✅ 페이지 전체가 다시 로드되지 않는지 확인

- [ ] **settlement_actual.py - 히스토리 섹션**
  - 실제정산 페이지 진입
  - ✅ 히스토리 섹션이 접혀있는지 확인
  - ✅ "히스토리 보기" 버튼 클릭
  - ✅ 히스토리가 즉시 로드되는지 확인 (rerun 없이)
  - ✅ 히스토리 데이터가 올바르게 표시되는지 확인
  - ✅ 페이지 전체가 다시 로드되지 않는지 확인

- [ ] **home_page.py - ZONE 4 (우선순위 TOP3)**
  - 홈 페이지 진입
  - ✅ ZONE 4가 접혀있는지 확인
  - ✅ "우선순위 보기" 버튼 클릭
  - ✅ 우선순위가 즉시 로드되는지 확인 (rerun 없이)
  - ✅ 우선순위 데이터가 올바르게 표시되는지 확인
  - ✅ 페이지 전체가 다시 로드되지 않는지 확인

- [ ] **home_page.py - ZONE 5 (구조 스냅샷)**
  - 홈 페이지 진입
  - ✅ ZONE 5가 접혀있는지 확인
  - ✅ "구조 스냅샷 보기" 버튼 클릭
  - ✅ 구조 스냅샷이 즉시 로드되는지 확인 (rerun 없이)
  - ✅ 구조 스냅샷 데이터가 올바르게 표시되는지 확인
  - ✅ 페이지 전체가 다시 로드되지 않는지 확인

### 저장 패턴 표준화 테스트

- [ ] **settlement_actual.py - 템플릿 다시 불러오기**
  - 템플릿 다시 불러오기 버튼 클릭
  - ✅ 성공 메시지가 표시되는지 확인
  - ✅ toast 메시지가 표시되는지 확인

- [ ] **settlement_actual.py - 매출 불러오기**
  - 매출 불러오기 버튼 클릭
  - ✅ 성공 메시지가 표시되는지 확인
  - ✅ toast 메시지가 표시되는지 확인

- [ ] **settlement_actual.py - 이번달 저장(draft)**
  - 비용 항목 입력 후 저장 버튼 클릭
  - ✅ 성공 메시지가 표시되는지 확인
  - ✅ toast 메시지가 표시되는지 확인

### 캐시 무효화 개선 테스트

- [ ] **app.py - 레시피 저장**
  - 레시피 저장 후
  - ✅ 레시피 데이터가 즉시 반영되는지 확인
  - ✅ 다른 캐시(메뉴, 재료 등)는 유지되는지 확인

- [ ] **app.py - 레시피 수정**
  - 레시피 수정 후
  - ✅ 수정된 레시피 데이터가 즉시 반영되는지 확인
  - ✅ 다른 캐시는 유지되는지 확인

- [ ] **app.py - 레시피 삭제**
  - 레시피 삭제 후
  - ✅ 삭제된 레시피가 즉시 반영되는지 확인
  - ✅ 다른 캐시는 유지되는지 확인

### 신규 계정 테스트

- [ ] **신규 계정으로 로그인**
  - 신규 계정 생성 후 로그인
  - ✅ 모든 페이지가 에러 없이 로드되는지 확인
  - ✅ expander lazy loading이 정상 작동하는지 확인
  - ✅ 저장 기능이 정상 작동하는지 확인

### 기존 계정 테스트

- [ ] **기존 계정으로 로그인**
  - 기존 계정으로 로그인
  - ✅ 모든 페이지가 에러 없이 로드되는지 확인
  - ✅ expander lazy loading이 정상 작동하는지 확인
  - ✅ 저장 기능이 정상 작동하는지 확인
  - ✅ 캐시 무효화가 정상 작동하는지 확인

---

## 5️⃣ 수정된 파일 리스트

1. **ui_pages/settlement_actual.py**
   - Expander lazy loading rerun 제거: 2개
   - 저장 패턴 표준화: 5개 지점

2. **ui_pages/home/home_page.py**
   - Expander lazy loading rerun 제거: 2개

3. **src/ui_helpers.py**
   - 공용 헬퍼 함수 추가: 5개 함수
     - `ui_flash_success()`
     - `ui_flash_error()`
     - `ui_flash_warning()`
     - `apply_state_patch()`
     - `invalidate_keys()`

4. **app.py**
   - 전체 캐시 clear → key 기반 무효화: 3개 지점 (레시피 저장/수정/삭제)

---

## 6️⃣ 아직 남은 작업 (선택사항)

### 1. sales_entry.py 표준화

현재 `sales_entry.py`는 `session_state` 기반 메시지 표시를 사용하고 있어, 추가 표준화는 선택사항입니다. 향후 필요 시 `ui_flash_*` 함수로 마이그레이션 가능합니다.

### 2. 다른 페이지의 전체 캐시 clear

다음 파일들에도 전체 캐시 clear가 있지만, 각각의 컨텍스트를 확인하여 필요 시 개선 가능:
- `ui_pages/ingredient_management.py` (3개)
- `ui_pages/menu_management.py` (6개)
- `ui_pages/recipe_management.py` (3개)

이들은 각각의 저장 함수에서 이미 `soft_invalidate`를 사용하고 있을 가능성이 높으므로, 추가 확인 후 개선 가능합니다.

---

## 7️⃣ 결론

### 완료된 작업

1. ✅ **Expander lazy loading rerun 제거**: 4개 `st.rerun()` 호출 제거
2. ✅ **저장/메시지/상태 갱신 표준화**: 5개 공용 헬퍼 함수 추가 및 적용
3. ✅ **전체 캐시 clear 제거**: 3개 지점을 key 기반 무효화로 변경

### 예상 성능 개선

- **Expander 열기**: 전체 페이지 rerun 없이 해당 섹션만 즉시 로드
- **캐시 무효화**: 필요한 캐시만 무효화하여 다른 캐시 유지
- **메시지 표시**: 표준화된 패턴으로 일관된 UX

### 다음 단계 (Phase 0 완료)

Phase 0의 주요 안정화 작업이 완료되었습니다:
- ✅ STEP 1: 크래시 방지 (`.iloc[0]` 패턴 제거)
- ✅ STEP 2: Supabase 응답 처리 안전화 (`.data[0]` 패턴 제거)
- ✅ STEP 3: 불필요한 rerun 제거 (12개)
- ✅ STEP 4: rerun 구조 개선 + lazy loading (16개 rerun 제거, 4개 섹션 lazy loading)
- ✅ STEP 5: 마지막 rerun 정리 + 패턴 표준화 (4개 rerun 제거, 5개 헬퍼 함수 추가)

**총 제거된 rerun**: 32개 (STEP 3: 12개 + STEP 4: 16개 + STEP 5: 4개)

---

**작업 완료일**: 2026-01-24  
**담당**: Phase 0 STEP 5 안정화 엔지니어
