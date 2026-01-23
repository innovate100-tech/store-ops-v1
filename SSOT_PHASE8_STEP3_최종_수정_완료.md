# SSOT PHASE 8 - STEP 3 최종 수정 완료

## 📋 작업 목표

매출보정(sales_entry)과 점장마감(manager_close)을 하나의 운영 흐름으로 통합.

**핵심 원칙**:
- 매출보정은 "빠른 숫자 수정 화면" (매출 + 네이버 방문자)
- 마감 여부와 관계없이 매출보정에서 수정 가능
- 마감된 날짜(has_close=true)의 매출/네이버 방문자 수정 시 daily_close와 자동 동기화
- 점장마감은 "공식 확정 + 운영 기록(판매량/메모)" 중심 화면

**용어 정책**: UI 전반의 "방문자" → "네이버 방문자"로 명칭 통일

---

## ✅ 수정 완료 항목

### 1. `get_day_record_status()` 헬퍼 함수
- **위치**: `src/storage_supabase.py` 라인 3439-3520
- **기능**: 특정 날짜의 기록 상태 조회 (최소 쿼리)
- **반환값**: `has_close`, `has_sales`, `has_visitors`, `best_total_sales`, `official_total_sales`, `visitors_best`, `visitors_official`

### 2. `save_sales_entry()` 통합 저장 함수
- **위치**: `src/storage_supabase.py` 라인 1280-1370
- **기능**:
  - 항상 `sales` / `naver_visitors` upsert
  - `has_close=true`인 경우 `daily_close`도 동기화 (매출 + 네이버 방문자)
  - `memo` / `sales_items`는 절대 수정하지 않음
- **반환값**: `{success, synced_to_close, has_close, message}`

### 3. `sales_entry.py` UX 재설계
- **위치**: `ui_pages/sales_entry.py`
- **변경 내용**:
  - 날짜 선택 시 상태바 표시 (마감 완료 / 임시 기록 / 아직 기록 없음)
  - 네이버 방문자 입력 추가 (매출과 함께 저장)
  - 저장 버튼 텍스트 분기 (공식 반영 / 임시 저장)
  - "지금 마감으로 승격하기" CTA 버튼 추가
  - `save_sales_entry()` 사용으로 통합 저장

### 4. `manager_close.py` 프리필/승격 강화
- **위치**: `ui_pages/manager_close.py`, `src/ui.py`
- **변경 내용**:
  - query params 또는 session_state에서 날짜 자동 선택
  - `daily_close` 없고 `sales`/`naver_visitors` 있으면 프리필 + 승격 안내
  - `daily_close` 있으면 기존 수정모드 유지
  - 저장 성공 후 "마감 완료 ✅" 요약 카드 + "매출보정으로 돌아가기" 버튼

### 5. UI 용어 전면 교체
- **변경**: "방문자" → "네이버 방문자"
- **대상 파일**:
  - `src/ui.py`: `render_visitor_batch_input()`, `render_daily_closing_input()`
  - `ui_pages/manager_close.py`: 요약 카드
  - 기타 UI 텍스트

---

## 📝 수정 파일 목록

### 1. `src/storage_supabase.py`
**변경 내용**:
- 라인 3439-3520: `get_day_record_status()` 함수 추가
- 라인 1280-1370: `save_sales_entry()` 함수 추가

### 2. `ui_pages/sales_entry.py`
**변경 내용**:
- import 추가: `save_sales_entry`, `get_day_record_status`
- 날짜 선택 시 상태바 표시 (3가지 상태)
- 네이버 방문자 입력 추가
- 저장 로직을 `save_sales_entry()`로 변경
- "지금 마감으로 승격하기" 버튼 추가

### 3. `ui_pages/manager_close.py`
**변경 내용**:
- import 추가: `get_day_record_status`
- query params / session_state에서 날짜 자동 선택
- 승격 안내 표시 (임시 기록 → 공식 마감)
- 저장 성공 후 요약 카드 + "매출보정으로 돌아가기" 버튼

### 4. `src/ui.py`
**변경 내용**:
- `render_manager_closing_input()`: `initial_date` 파라미터 추가
- 날짜 선택 시 기존 데이터 프리필 로직 추가
- 프리필 값 사용 후 session_state에서 삭제
- 용어 변경: "방문자" → "네이버 방문자"

---

## 🧪 테스트 시나리오 10개

### 시나리오 1: 마감된 날짜 → 매출보정에서 매출/네이버 방문자 수정 → daily_close와 통계 동시에 변경
**전제 조건**: 2026-01-20에 `daily_close` 존재  
**예상 결과**:
- ✅ 상태바: "✅ 마감 완료(공식)" 표시
- ✅ 저장 버튼: "💾 매출·네이버 방문자 수정(공식 반영)"
- ✅ 저장 후: "공식 마감 매출이 함께 수정되었습니다." 메시지
- ✅ `daily_close`와 `sales` 모두 업데이트됨
- ✅ 통계에 즉시 반영

### 시나리오 2: 미마감 날짜 → 매출보정 저장 → 통계 반영 + 미마감 표시
**전제 조건**: 2026-01-20에 `daily_close` 없음  
**예상 결과**:
- ✅ 상태바: "⚠️ 임시 기록(미마감)" 표시
- ✅ 저장 버튼: "💾 임시 저장"
- ✅ 저장 후: "임시 매출/네이버 방문자가 저장되었습니다." 메시지
- ✅ 통계에 반영 (best_available)
- ✅ 미마감 배지 표시

### 시나리오 3: 미마감 → 승격 → 마감률/스트릭 증가
**전제 조건**: 2026-01-20에 `sales`만 있음 → "지금 마감으로 승격하기" 클릭  
**예상 결과**:
- ✅ 점장마감 페이지로 이동
- ✅ 날짜 자동 선택
- ✅ 매출/네이버 방문자 프리필
- ✅ 승격 안내 표시
- ✅ 마감 저장 후 마감률/스트릭 증가

### 시나리오 4: 매출보정/마감 어디서 저장해도 숫자 불일치 발생 안 함
**전제 조건**: 2026-01-20에 `daily_close` 존재  
**예상 결과**:
- ✅ 매출보정에서 수정 → `daily_close` 동기화
- ✅ 점장마감에서 수정 → `sales` 동기화 (기존 로직)
- ✅ 통계는 항상 일치

### 시나리오 5: UI 전반에 "네이버 방문자"로만 표시
**전제 조건**: 모든 페이지 확인  
**예상 결과**:
- ✅ 매출보정: "네이버 방문자" 표시
- ✅ 점장마감: "네이버 방문자" 표시
- ✅ 요약 카드: "네이버 방문자" 표시
- ✅ 일괄 입력: "네이버 방문자" 표시

### 시나리오 6: query params로 날짜 전달
**전제 조건**: `?date=2026-01-20` query params  
**예상 결과**:
- ✅ 점장마감 페이지에서 날짜 자동 선택
- ✅ 기존 데이터 프리필

### 시나리오 7: session_state로 날짜 전달 (승격 버튼)
**전제 조건**: 매출보정에서 "지금 마감으로 승격하기" 클릭  
**예상 결과**:
- ✅ `st.session_state["manager_close_date"]` 설정
- ✅ 점장마감 페이지에서 날짜 자동 선택
- ✅ session_state 사용 후 삭제

### 시나리오 8: daily_close 없고 sales만 있는 경우 프리필
**전제 조건**: 2026-01-20에 `sales`만 있음  
**예상 결과**:
- ✅ 점장마감에서 날짜 선택 시 매출 프리필
- ✅ 승격 안내 표시

### 시나리오 9: daily_close 없고 naver_visitors만 있는 경우 프리필
**전제 조건**: 2026-01-20에 `naver_visitors`만 있음  
**예상 결과**:
- ✅ 점장마감에서 날짜 선택 시 네이버 방문자 프리필
- ✅ 승격 안내 표시

### 시나리오 10: 저장 성공 후 요약 카드 및 돌아가기 버튼
**전제 조건**: 점장마감 저장 성공  
**예상 결과**:
- ✅ "✅ 마감 완료" 요약 카드 표시
- ✅ "🛠 매출보정으로 돌아가기" 버튼 표시
- ✅ 버튼 클릭 시 매출보정 페이지로 이동

---

## ✅ 검증 체크리스트

- [x] `get_day_record_status()` 함수 추가
- [x] `save_sales_entry()` 함수 추가 (동기화 로직 포함)
- [x] `sales_entry.py` 상태바 표시 (3가지 상태)
- [x] `sales_entry.py` 네이버 방문자 입력 추가
- [x] `sales_entry.py` 저장 로직 분기
- [x] `sales_entry.py` "지금 마감으로 승격하기" 버튼
- [x] `manager_close.py` query params 날짜 자동 선택
- [x] `manager_close.py` session_state 날짜 자동 선택
- [x] `manager_close.py` 프리필 로직
- [x] `manager_close.py` 승격 안내 표시
- [x] `manager_close.py` 저장 성공 후 요약 카드
- [x] `manager_close.py` "매출보정으로 돌아가기" 버튼
- [x] UI 용어 전면 교체 ("방문자" → "네이버 방문자")

---

## 🎯 기대 동작

### 매출보정 (sales_entry)
- ✅ 마감 여부와 관계없이 매출/네이버 방문자 수정 가능
- ✅ 마감된 날짜 수정 시 `daily_close` 자동 동기화
- ✅ 미마감 날짜는 임시 저장 + 승격 버튼 제공
- ✅ 상태바로 현재 상태 명확히 표시

### 점장마감 (manager_close)
- ✅ query params / session_state로 날짜 자동 선택
- ✅ 임시 기록 승격 시 프리필 + 안내
- ✅ 저장 성공 후 요약 카드 + 돌아가기 버튼
- ✅ 공식 확정 + 운영 기록 중심

### 용어 통일
- ✅ UI 전반에 "네이버 방문자"로 표시
- ✅ 일관된 사용자 경험

---

## 📌 추가 참고사항

### 저장 로직 분기
- `has_close=true`: `sales` + `naver_visitors` + `daily_close` 동기화
- `has_close=false`: `sales` + `naver_visitors`만 저장

### 프리필 로직
- `daily_close` 있으면 `daily_close`에서 프리필
- `daily_close` 없고 `sales`/`naver_visitors` 있으면 각각에서 프리필
- 프리필 값은 `session_state`에 저장 후 사용 후 삭제

### 승격 흐름
1. 매출보정에서 "지금 마감으로 승격하기" 클릭
2. `st.session_state["manager_close_date"]` 설정
3. 점장마감 페이지로 이동
4. 날짜 자동 선택 + 프리필 + 승격 안내
5. 마감 저장 후 마감률/스트릭 증가

---

## 🚀 배포 준비

모든 수정이 완료되었습니다. 다음 단계:
1. 앱 재시작
2. 테스트 시나리오 10개 실행
3. 매출보정/점장마감 통합 흐름 확인
4. 용어 통일 확인
