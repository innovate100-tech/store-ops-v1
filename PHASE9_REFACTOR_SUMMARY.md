# Phase 9 리팩토링 완료 보고서

## 📋 변경 파일 목록

### 주요 변경 파일
- `ui_pages/home.py` - 홈 구조 완전 통합

### 제거된 함수
- `render_day0_home()` - 제거됨 (사용되지 않음)
- `render_coach_home()` - 제거됨 (`_render_home_body`로 통합)
- `render_fast_home()` - 제거됨 (`_render_home_body`로 통합)

### 새로 추가된 함수
- `_render_home_body(store_id: str, coaching_enabled: bool)` - 통합 홈 렌더링 함수

### 수정된 함수
- `render_home()` - `_render_home_body` 호출로 단순화

---

## 🏠 홈 구조 변경 요약

### Before (Phase 8)
```
render_home()
  ├─ render_coach_home()  (별도 함수, 완전 분리)
  └─ render_fast_home()  (별도 함수, 완전 분리)
```

### After (Phase 9)
```
render_home()
  └─ _render_home_body(store_id, coaching_enabled)
      ├─ 공통 섹션 (항상 표시)
      └─ coach_only 섹션 (coaching_enabled=True일 때만)
```

### 핵심 변경사항
1. **단일 구조 통합**: `coach_home`과 `fast_home` 완전 분리 제거
2. **조건부 렌더링**: `if coaching_enabled:` 블록으로 coach_only 영역 분리
3. **정보 섹션 동일**: fast/coach 모드 모두 동일한 정보 섹션 표시
4. **LEVEL UI 제거**: "LEVEL 0/1/2/3" 직접 노출 금지, "열리는 조건 안내"로 대체

---

## 📝 coach_only 영역 목록

다음 섹션들은 `coaching_enabled=True`일 때만 표시됩니다:

### 1. 성장 단계 메시지 (DAY 연출)
- DAY1: "지금은 '기록 습관'을 만드는 단계입니다..."
- DAY3: "이제 가게가 숫자로 보이기 시작했습니다..."
- DAY7: "이제 이 앱은 사장님의 '매장 코치' 모드입니다..."
- **주의**: DAY 레이블("DAY1/DAY3/DAY7")은 UI에 노출하지 않음

### 2. 코치 모드 환영 메시지
- 최초 1회만 표시: "🎉 코치 모드가 활성화되었습니다..."

### 3. 시작 미션 3개
- 미션 1: 메뉴 3개 등록
- 미션 2: 점장마감 3회
- 미션 3: 이번 달 성적표 1회
- 진행률 바 및 완료 보상 문장 포함

### 4. 오늘 하나만 추천
- 제목: "🎯 오늘 코치의 한 가지 제안"
- 추천 액션 카드 + 버튼
- DAY 단계별 톤 튜닝 적용

### 5. 문제/이상징후 guide_text
- 문제 TOP3에 대한 행동 연결 문장
- 이상 징후에 대한 행동 연결 문장
- 예: "이 문제는 보통 요일/메뉴/객단가 흐름에서 원인이 보입니다."

### 6. 이번 달 가게 상태 한 줄 요약
- `get_month_status_summary()` 결과 표시
- DAY 단계별 prefix 변경 적용

---

## 🔢 LEVEL 재정의 문서

### LEVEL 개념
- **UI 노출 금지**: 사용자 화면에 "LEVEL 0/1/2/3" 직접 표시하지 않음
- **내부 전용**: 기능 활성 조건(gating)으로만 사용
- **데이터 부족 시**: 섹션을 숨기지 말고 "열리는 조건 안내 + 바로가기 버튼" 표시

### LEVEL 판별 기준 (`detect_data_level()`)

#### Level 0: 데이터 거의 없음
- **조건**: `sales` 테이블에 데이터 0건
- **특징**: 
  - daily_close 거의 없음
  - KPI 계산 불가
- **UI 처리**: 
  - 섹션 숨김 금지
  - "마감 입력 필요" 안내 + [점장 마감] 버튼 표시

#### Level 1: 매출만 있음
- **조건**: 
  - `sales` 존재
  - `daily_close` 3건 이하
- **특징**:
  - 매출/방문자/트렌드/예측 가능
  - daily_close 충분하지 않음
- **활성 기능**:
  - 월매출 표시
  - 기본 매출 분석

#### Level 2: 운영 데이터 있음
- **조건**:
  - `daily_close` 4건 이상 또는
  - `daily_sales_items` 존재
- **특징**:
  - 메뉴 성과/원가/이익/재료 분석 가능
  - 판매 데이터 기반 분석 가능
- **활성 기능**:
  - 객단가 계산
  - 판매 관리 기능
  - 메뉴별 분석

#### Level 3: 재무 구조 있음
- **조건**:
  - `expense_structure` 또는 `actual_settlement` 존재
- **특징**:
  - 손익분기점 계산 가능
  - 이익 구조 분석 가능
- **활성 기능**:
  - 이번 달 이익 표시
  - 숫자 구조 섹션 완전 활성화
  - 비용 구조 분석

### LEVEL 사용 규칙
1. **UI 분기 금지**: `if data_level == 0:` 같은 조건으로 섹션 숨기기 금지
2. **데이터 기반 표시**: 실제 데이터 존재 여부로 표시/숨김 결정
3. **안내 문구 사용**: "열리는 조건 안내 + 바로가기 버튼" 패턴 사용
4. **숫자 로딩 차단 금지**: LEVEL로 인해 숫자 표시를 막지 않음

---

## 📅 DAY 개념 정리

### DAY 사용 규칙
- **코치모드에서만 사용**: fast 모드에서는 DAY 개념 사용 안 함
- **기능 개방 기준으로 사용 금지**: DAY로 기능을 제한하지 않음
- **오직 다음 용도만 허용**:
  1. 성장 문구 (DAY1/DAY3/DAY7 메시지)
  2. 관계 연출 (사용자와의 관계 톤)
  3. 루틴/스트릭 강조 (마감 습관 강조)

### DAY 판별 기준 (`detect_owner_day_level()`)
- **DAY1**: daily_close 존재 AND daily_close_count < 3
- **DAY3**: daily_close_count >= 3 AND 이번 달 actual_settlement 없음
- **DAY7**: daily_close_count >= 3 AND 이번 달 actual_settlement 존재
- **None**: 데이터 거의 없음

### DAY UI 노출 금지
- ❌ "DAY1", "DAY3", "DAY7" 레이블 직접 표시 금지
- ✅ 성장 메시지만 표시 (레이블 없이)
- ✅ "오늘 하나만" 추천 문구 톤만 조정

---

## ✅ 테스트 체크리스트

### 기본 기능 테스트
- [ ] coach 모드 홈 정상 표시
- [ ] fast 모드 홈 정상 표시
- [ ] 모드 전환 시 홈 구조 변경 없음 (숫자/정보 섹션 동일)
- [ ] coach 모드에서 coach_only 섹션 표시
- [ ] fast 모드에서 coach_only 섹션 숨김

### LEVEL 관련 테스트
- [ ] LEVEL 0/1/2/3 레이블이 UI에 표시되지 않음
- [ ] 데이터 없을 때 "열리는 조건 안내 + 바로가기" 표시
- [ ] 섹션이 LEVEL로 인해 숨겨지지 않음
- [ ] 숫자 로딩이 LEVEL로 차단되지 않음

### DAY 관련 테스트
- [ ] DAY1/DAY3/DAY7 레이블이 UI에 표시되지 않음
- [ ] coach 모드에서만 성장 메시지 표시
- [ ] fast 모드에서 성장 메시지 숨김
- [ ] DAY가 기능 개방 기준으로 사용되지 않음

### 섹션별 테스트
- [ ] 상태판: 이번 달 매출, 마감률/스트릭 정상 표시
- [ ] 핵심 숫자 카드: 오늘 매출, 이번 달 매출, 객단가, 이번 달 이익
- [ ] 문제 TOP3 / 잘한 점 TOP3 정상 표시
- [ ] 이상 징후 정상 표시
- [ ] 숫자 구조 섹션 정상 표시
- [ ] 운영 메모 정상 표시
- [ ] 미니 차트: "열리는 조건 안내" 표시

### coach_only 섹션 테스트
- [ ] 성장 단계 메시지 (coach 모드만)
- [ ] 코치 모드 환영 (최초 1회만)
- [ ] 시작 미션 3개 (coach 모드만)
- [ ] 오늘 하나만 추천 (coach 모드만)
- [ ] 문제/이상징후 guide_text (coach 모드만)
- [ ] 이번 달 가게 상태 한 줄 (coach 모드만)

---

## 🎯 성공 기준 확인

### ✅ 완료된 항목
1. ✅ fast/coach 전환해도 숫자/정보 구조가 바뀌지 않음
2. ✅ fast 모드는 "말 없는 홈", coach 모드는 "말하는 홈"
3. ✅ LEVEL/DAY 개념이 사용자 화면에 직접 노출되지 않음
4. ✅ 사용자가 이해해야 할 개념이 "모드" 하나로 축소됨

### 📊 구조 비교

#### Before (Phase 8)
- coach_home: 별도 함수, 완전 분리
- fast_home: 별도 함수, 완전 분리
- LEVEL UI 노출: "📊 현재 데이터 단계: **LEVEL 1: 매출만 있음**"
- DAY UI 노출: 없음 (내부 전용)

#### After (Phase 9)
- `_render_home_body`: 단일 통합 함수
- 공통 섹션: 두 모드 모두 동일
- coach_only: 조건부 표시
- LEVEL UI 노출: ❌ 제거됨
- DAY UI 노출: ❌ 제거됨 (메시지만 표시, 레이블 없음)

---

## 📌 핵심 페이지 점검 결과 (Phase 9 후속)

### 점장마감 (`manager_close.py`)
- **LEVEL/DAY UI**: ❌ 없음 (제거 작업 불필요)
- **구조**: 헤더 → 안내 박스 → 마감 입력 폼 → 마감 완료/수정 버튼
- **빈 상태**: 메뉴 없을 때 `menu_list` 비어 있어도 입력 폼 동작
- **다음 액션**: "✅ 마감 완료" / "✅ 마감 수정 저장" 명확

### 매출관리 (`sales_management.py`)
- **LEVEL/DAY UI**: ❌ 없음 (제거 작업 불필요)
- **구조**: 헤더 → store_id 체크 → 매출 새로고침 → 데이터 로드 → 분석 섹션
- **빈 상태**: `store_id` 없으면 "매장 정보를 찾을 수 없습니다" + [매장 선택으로 이동] 버튼
- **다음 액션**: 새로고침 버튼, 매장 선택 버튼 존재

### 대시보드
- **구현 위치**: "통합 대시보드" 페이지는 **app.py 인라인** 구현 (즉, `dashboard.py` 미사용).
- **LEVEL/DAY UI**: ❌ 없음 (제거 작업 불필요)
- **참고**: `dashboard.py` + `dashboard/` 모듈은 별도 구성이며, 앱 라우팅에서는 사용하지 않음. 해당 모듈 내 `diagnostics` 등에도 LEVEL/DAY 미사용.

### 결론
- 점장마감, 매출관리, 대시보드 **모두 LEVEL/DAY UI 미사용** → 별도 제거 작업 없음.
- Phase 9 홈 리팩토링 대상 외 페이지는 현재 규격 준수 상태로 유지.

---

## 📌 다음 단계

### 우선순위
1. ✅ 홈 구조 리팩토링 - **완료**
2. ✅ 핵심 페이지 점검 (점장마감, 매출관리, 대시보드) - **완료**
3. ✅ LEVEL 재정의 문서화 - **완료**
4. ✅ DAY 개념 정리 - **완료**

### 완료된 작업
- [x] 점장마감 페이지: LEVEL/DAY UI 없음 확인
- [x] 매출관리 페이지: LEVEL/DAY UI 없음 확인
- [x] 대시보드 페이지: LEVEL/DAY UI 없음 확인

### 선택적 후속 (추가 UX 개선)
- [ ] 전체 페이지 "사용자 역할 / 단일 핵심 질문 / 빈 상태 / 다음 액션" UX 점검
- [ ] 데이터 부족 시 "열리는 조건 안내 + 바로가기" 패턴 확대 적용 검토

---

## 📝 참고사항

### 변경된 함수 시그니처
```python
# Before
def render_coach_home():
def render_fast_home():

# After
def _render_home_body(store_id: str, coaching_enabled: bool):
def render_home():  # 내부에서 _render_home_body 호출
```

### coach_only 조건
```python
if coaching_enabled:
    # coach_only 섹션 렌더링
```

### 공통 섹션
- 빠른 이동 버튼
- 상태판
- 핵심 숫자 카드
- 문제 TOP3 / 잘한 점 TOP3
- 이상 징후
- 미니 차트
- 숫자 구조
- 운영 메모
