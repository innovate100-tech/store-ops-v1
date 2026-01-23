# PHASE 10 (STEP 10-1 + 10-2 + 10-3) — "사장 의존성 엔진" 통합 구현 완료

## 📋 작업 목표

HOME v2 + 가게 설계 센터 + 4개 설계실(브리핑/실행) 위에
"코치 판결 시스템(헌법)" + "월간 구조 리포트" + "사장 루틴 UX 배지/미완료 상태"를 통합 구현했습니다.

---

## ✅ 완료된 작업

### STEP 10-1: 코치 엔진 "헌법" 만들기

#### A. 신규 공통 모듈 생성
1. **`ui_pages/coach/coach_contract.py`** (신규 생성)
   - `CoachVerdict` dataclass: 표준 판결 스키마
   - `Evidence` dataclass: 근거 항목
   - `Action` dataclass: 액션 항목
   - `LEVEL_CONFIG`: Level별 아이콘/색상 매핑

2. **`ui_pages/coach/coach_renderer.py`** (신규 생성)
   - `render_verdict_card()`: 판결 카드 렌더링 (compact 옵션)
   - `render_verdict_strip()`: 홈/상단 스트립용 한줄 렌더링
   - `render_evidence_grid()`: 근거 그리드 렌더링
   - `render_actions()`: 액션 버튼 렌더링

3. **`ui_pages/coach/coach_adapters.py`** (신규 생성)
   - `get_home_coach_verdict()`: HOME v2 판결을 CoachVerdict로 변환
   - `get_design_center_verdict()`: Design Center 판결을 CoachVerdict로 변환

#### B. 기존 판결 로직 연결
- `ui_pages/home/home_verdict.py`: 기존 로직 유지, 어댑터로 변환
- `ui_pages/design_lab/design_center_data.py`: 기존 로직 유지, 어댑터로 변환

#### C. UI 적용
- **HOME v2**: ZONE 2 "이번 달 코치 판결"을 `coach_renderer` 기반으로 표시
- **Design Center**: ZONE C "코치 1차 판결"을 `coach_renderer` 기반으로 표시

### STEP 10-2: 월간 "구조 리포트"

#### A. 신규 파일 생성
- **`ui_pages/reports/monthly_structure_report.py`** (신규 생성)
  - `build_monthly_structure_report()`: 월간 구조 리포트 생성
  - 포함 내용:
    1. `verdicts`: 4개 구조(메뉴 포트폴리오, 메뉴 수익, 재료, 수익) CoachVerdict 요약
    2. `primary_concern`: 이번 달 최우선 구조 1개(Design Center 기준)
    3. `delta_vs_prev_month`: 지난달 대비 핵심지표 변화(가능한 범위만)
    4. `next_month_actions`: 다음달 추천 과제 3개(CTA 포함)

#### B. "월간 성적표" 페이지에 삽입
- **파일**: `ui_pages/settlement_actual.py` (수정)
- **추가 섹션**: "📌 이번 달 구조 판결"
  - 4개 구조 요약 표(점수/상태/한줄요약)
  - "이번 달 최우선 과제" 카드 1개(코치 렌더러)
  - "지난달 대비 변화" (가능한 지표만, 없으면 안내)
  - "다음달 추천 과제" 버튼 3개
  - "이번 달 판결 확인 완료 처리" 버튼

### STEP 10-3: 사장 루틴 UX 고정

#### A. 루틴 상태 정의
- "오늘 입력" 상태: 오늘 날짜 기준 daily_close 존재 여부
- "이번 주 구조 점검" 상태: session_state 기반 (임시)
- "이번 달 구조 판결" 상태: session_state 기반 (임시)

#### B. 신규 파일 생성
- **`ui_pages/routines/routine_state.py`** (신규 생성)
  - `get_routine_status()`: 루틴 상태 조회
  - `mark_weekly_check_done()`: 이번 주 구조 점검 완료 처리
  - `mark_monthly_review_done()`: 이번 달 구조 판결 확인 완료 처리

#### C. HOME v2에 루틴 배지 추가
- **파일**: `ui_pages/home/home_page.py` (수정)
- **위치**: ZONE 1 아래 "오늘 입력 바로가기" 버튼 아래
- **배지 3개**:
  1. 오늘 마감 ✅/미완료 ⚠️ (CTA: 점장 마감)
  2. 이번 주 구조 점검 ✅/미완료 ⚠️ (CTA: 가게 설계 센터)
  3. 이번 달 구조 판결 ✅/미완료 ⚠️ (CTA: 실제정산)

#### D. Design Center에 "이번 주 점검 완료" 버튼
- **파일**: `ui_pages/design_lab/design_center.py` (수정)
- **위치**: 페이지 상단 (제목 아래)
- **버튼**: [✅ 이번 주 구조 점검 완료 처리]
- **표시**: 완료면 ✅ "이번 주 점검 완료" 배지 표시

#### E. 월간 성적표에 "이번 달 판결 확인 완료" 버튼
- **파일**: `ui_pages/settlement_actual.py` (수정)
- **위치**: 구조 리포트 섹션 하단
- **버튼**: [✅ 이번 달 구조 판결 확인 완료 처리]

---

## 📝 수정된 파일 목록

### 신규 생성 파일
1. **`ui_pages/coach/__init__.py`**
   - 코치 모듈 초기화

2. **`ui_pages/coach/coach_contract.py`**
   - CoachVerdict 표준 스키마 정의

3. **`ui_pages/coach/coach_renderer.py`**
   - 표준 렌더러 함수들

4. **`ui_pages/coach/coach_adapters.py`**
   - 기존 판결 로직을 CoachVerdict로 변환하는 어댑터

5. **`ui_pages/reports/__init__.py`**
   - 리포트 모듈 초기화

6. **`ui_pages/reports/monthly_structure_report.py`**
   - 월간 구조 리포트 생성 함수

7. **`ui_pages/routines/__init__.py`**
   - 루틴 모듈 초기화

8. **`ui_pages/routines/routine_state.py`**
   - 루틴 상태 관리 함수들

### 수정된 파일
1. **`ui_pages/home/home_page.py`**
   - ZONE 2: CoachVerdict 표준 렌더러 사용
   - ZONE 1 아래: 루틴 배지 3개 추가

2. **`ui_pages/design_lab/design_center.py`**
   - ZONE C: CoachVerdict 표준 렌더러 사용
   - 상단: "이번 주 점검 완료" 버튼 추가

3. **`ui_pages/settlement_actual.py`**
   - 구조 리포트 섹션 추가 (`_render_structure_report_section`)
   - "이번 달 판결 확인 완료" 버튼 추가

---

## ✅ 앱 실행 시 확인 체크리스트

### STEP 10-1: 코치 엔진 "헌법"
- [ ] HOME v2 ZONE 2에서 표준 판결 카드 정상 표시
  - [ ] 근거 그리드 정상 표시
  - [ ] 액션 버튼 정상 동작
- [ ] Design Center ZONE C에서 표준 판결 카드 정상 표시
  - [ ] 근거 그리드 정상 표시
  - [ ] 액션 버튼 정상 동작

### STEP 10-2: 월간 구조 리포트
- [ ] 월간 성적표 페이지에서 "📌 이번 달 구조 판결" 섹션 정상 표시
  - [ ] 4개 구조 요약 표 정상 표시
  - [ ] 이번 달 최우선 과제 카드 정상 표시
  - [ ] 지난달 대비 변화 정상 표시 (또는 "데이터 부족" 안내)
  - [ ] 다음달 추천 과제 버튼 3개 정상 동작
  - [ ] "이번 달 판결 확인 완료 처리" 버튼 정상 동작

### STEP 10-3: 사장 루틴 UX
- [ ] HOME v2에서 루틴 배지 3개 정상 표시
  - [ ] 오늘 마감 배지 정상 동작
  - [ ] 이번 주 구조 점검 배지 정상 동작
  - [ ] 이번 달 구조 판결 배지 정상 동작
- [ ] Design Center에서 "이번 주 점검 완료" 버튼 정상 동작
- [ ] 월간 성적표에서 "이번 달 판결 확인 완료" 버튼 정상 동작
- [ ] 루틴 완료 후 배지 상태 변경 확인

---

## 🎯 기대 동작

### 사용자 경험
1. **표준 판결**: 모든 판결이 동일한 형식으로 표시되어 일관성 확보
2. **월간 구조 리포트**: 성적표가 단순 숫자 모음이 아닌 경영 기록으로 기능
3. **루틴 습관**: 배지/경고로 앱 사용 습관 형성

### 코드 안정성
- 기존 판결 로직 유지 (어댑터 패턴으로 변환만)
- 기존 성적표 계산 로직 변경 없음 (추가 섹션만)
- session_state 기반 루틴 상태 관리 (DB 저장은 다음 단계)

---

## 📌 참고사항

### CoachVerdict 표준 스키마
- **Level**: "OK" | "WARN" | "RISK"
- **Title**: 한줄 결론 제목
- **Summary**: 결론 문장 (숫자 포함)
- **Evidence**: 근거 2~4개 (label, value, note)
- **Actions**: CTA 1~3개 (label, page, intent)
- **Source**: 판결 출처 ("home" | "design_center" | "monthly_report")
- **As_of**: 표시용 날짜 ("YYYY-MM-DD")

### 월간 구조 리포트
- **데이터 소스**: Design Center 데이터 헬퍼 재사용
- **지난달 대비**: 현재는 같은 로직 사용 (실제로는 이전 달 데이터 필요)
- **다음달 과제**: 점수 70점 미만 구조에서 자동 추천 (최대 3개)

### 루틴 상태 관리
- **session_state 키 규칙**:
  - `routine_weekly_checked::{store_id}::{YYYY-WW}`
  - `routine_monthly_reviewed::{store_id}::{YYYY-MM}`
- **오늘 마감**: `load_official_daily_sales`로 확인
- **임시 저장**: DB 저장은 다음 단계로 미룸

---

## 🚀 배포 준비

모든 수정이 완료되었습니다. 다음 단계:
1. ✅ 앱 재시작
2. ✅ HOME v2에서 루틴 배지 3개 확인
3. ✅ HOME v2 ZONE 2에서 표준 판결 카드 확인
4. ✅ Design Center에서 "이번 주 점검 완료" 버튼 확인
5. ✅ 월간 성적표에서 구조 리포트 섹션 확인
6. ✅ 루틴 완료 처리 후 배지 상태 변경 확인

---

## 📊 작업 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| CoachVerdict 표준 스키마 생성 | ✅ 완료 | coach_contract.py |
| CoachVerdict 표준 렌더러 생성 | ✅ 완료 | coach_renderer.py |
| HOME v2 판결 어댑터 | ✅ 완료 | coach_adapters.py |
| Design Center 판결 어댑터 | ✅ 완료 | coach_adapters.py |
| HOME v2 표준 렌더러 적용 | ✅ 완료 | home_page.py |
| Design Center 표준 렌더러 적용 | ✅ 완료 | design_center.py |
| 월간 구조 리포트 생성 | ✅ 완료 | monthly_structure_report.py |
| 월간 성적표 구조 리포트 삽입 | ✅ 완료 | settlement_actual.py |
| 루틴 상태 관리 모듈 생성 | ✅ 완료 | routine_state.py |
| HOME v2 루틴 배지 추가 | ✅ 완료 | home_page.py |
| Design Center 점검 완료 버튼 | ✅ 완료 | design_center.py |
| 월간 성적표 확인 완료 버튼 | ✅ 완료 | settlement_actual.py |

---

## ✅ 최종 확인

- [x] CoachVerdict 표준 스키마 생성 완료
- [x] CoachVerdict 표준 렌더러 생성 완료
- [x] 기존 판결 로직 어댑터 연결 완료
- [x] HOME v2 / Design Center 표준 렌더러 적용 완료
- [x] 월간 구조 리포트 생성 완료
- [x] 월간 성적표 구조 리포트 삽입 완료
- [x] 루틴 상태 관리 모듈 생성 완료
- [x] HOME v2 루틴 배지 추가 완료
- [x] Design Center / 월간 성적표 완료 버튼 추가 완료
- [ ] 앱 실행 및 동작 확인 (사용자 확인 필요)

**참고**: 
- 모든 판결이 표준 형식(CoachVerdict)으로 통일되었습니다.
- 월간 성적표가 구조 판결을 포함한 경영 기록으로 기능합니다.
- 루틴 배지로 앱 사용 습관을 형성할 수 있습니다.

---

## 📋 CoachVerdict 표준 예시

```python
CoachVerdict(
    level="RISK",
    title="수익 구조가 위험한 상태입니다",
    summary="손익분기점 미달 또는 비용 구조 불안정이 확인되었습니다.",
    evidence=[
        Evidence(label="손익분기점 미달", value="500,000원 (20.0%)", note=None),
        Evidence(label="고정비 비율", value="25.5% (주의: 20% 이상)", note=None),
        Evidence(label="변동비율", value="45.2% (주의: 40% 이상)", note=None),
    ],
    actions=[
        Action(label="💰 수익 구조 설계실", page="수익 구조 설계실", intent="revenue_structure")
    ],
    source="home",
    as_of="2026-01-23"
)
```
