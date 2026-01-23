# PHASE 10 / STEP 10-8P: "코치모드/빠른모드" 잔재 완전 제거 완료

## 작업 개요
앱 전체에서 코치모드/빠른모드(토글/플래그/분기/문구/세션키) 잔재를 전부 찾아 제거 완료.
이제 코치/분석은 HOME v3 + 가게 설계 센터/설계실에서 제공하므로 모드 구분은 폐기됨.

---

## 전수 검색 결과

### 검색 키워드
- "코치모드", "빠른모드"
- "coach_mode", "quick_mode"
- "coach_enabled", "fast_mode"
- "view_mode", "mode_toggle", "toggle_mode"
- "is_coach", "is_quick"
- "coaching_enabled", "is_coach_mode"
- "coach_mode_welcomed"

### 발견 위치
1. **ui_pages/home.py** (주요 수정 대상)
2. **ui_pages/home_legacy.py** (레거시 파일, 참고용)
3. **PHASE10_STEP10-X_코치모드빠른모드제거_완료.md** (문서)
4. **PHASE9_REFACTOR_SUMMARY.md** (문서)

---

## 제거된 항목

### A) 함수 시그니처 수정

1. **`get_today_one_action()`**
   - 변경 전: `get_today_one_action(store_id: str, level: int, is_coach_mode: bool = False)`
   - 변경 후: `get_today_one_action(store_id: str, level: int)`
   - 수정: `is_coach_mode` 파라미터 제거, 코치 기능 항상 활성화

2. **`get_today_one_action_with_day_context()`**
   - 변경 전: `get_today_one_action_with_day_context(store_id: str, level: int, is_coach_mode: bool = False, day_level: str = None)`
   - 변경 후: `get_today_one_action_with_day_context(store_id: str, level: int, day_level: str = None)`
   - 수정: `is_coach_mode` 파라미터 제거

3. **`_render_home_body()`**
   - 변경 전: `_render_home_body(store_id: str, coaching_enabled: bool)`
   - 변경 후: `_render_home_body(store_id: str)`
   - 수정: `coaching_enabled` 파라미터 제거

### B) 로직 분기 제거

1. **`if is_coach_mode:` 분기 제거** (2곳)
   - `get_today_one_action()` 내부 level 2, level 3 분기
   - 변경: 코치 기능 항상 활성화로 통일

2. **`if coaching_enabled:` 분기 제거** (6곳)
   - 시작 미션 3개 섹션
   - 오늘 코치의 한 가지 제안 섹션
   - 문제점 가이드 텍스트 (2곳)
   - 이상 신호 가이드 텍스트
   - 이번 달 가게 상태 한 줄
   - 변경: 모든 섹션 항상 표시

3. **`coach_mode_welcomed` session_state 제거**
   - 코치 모드 환영 메시지 블록 전체 제거
   - 변경: 환영 메시지 제거 (모드 구분 없음)

### C) 함수 주석/문구 수정

1. **`is_auto_coach_mode()` 함수**
   - 주석 변경: "[DEPRECATED] 온보딩 미션 완료 여부 확인 (모드 구분 제거됨)"
   - 사용되지 않지만 하위호환성을 위해 유지

2. **미션 진행률 메시지**
   - 변경 전: "자동 코치 모드로 진화합니다" / "자동 코치 모드 활성화"
   - 변경 후: "완전히 활성화됩니다" / "기본 세팅 완료"

3. **함수 docstring 수정**
   - "코치 모드" → "코치 기능은 항상 활성화됨"
   - "빠른 모드" 언급 제거

### D) app.py 주석 수정

- 변경 전: `# Phase 9: _render_home_body(store_id, coaching_enabled) 통합 구조`
- 변경 후: `# Phase 9: _render_home_body(store_id) 통합 구조 (모드 구분 제거됨)`

---

## 치환된 로직 요약

### 모드 분기 → 항상 ON

| 변경 전 | 변경 후 |
|---------|---------|
| `if coaching_enabled: render_mission()` | `render_mission()` (항상 실행) |
| `if is_coach_mode: return {...}` | `return {...}` (항상 코치 멘트) |
| `if coaching_enabled: show_guide()` | `show_guide()` (항상 표시) |

### 세션 키 제거

- `coach_mode_welcomed` - 제거됨
- `coaching_enabled` - 파라미터로만 사용되던 것 제거됨

---

## 남은 "모드 관련 단어" 검색 결과

### 코드 파일 (실제 사용)
- **0건** (모든 코드에서 제거 완료)

### 문서 파일 (참고용)
- `PHASE10_STEP10-X_코치모드빠른모드제거_완료.md` - 이전 작업 문서
- `PHASE9_REFACTOR_SUMMARY.md` - 이전 작업 문서
- `HOME_REFACTOR_ANALYSIS.md` - 분석 문서

**결론**: 실제 코드에서는 모든 모드 관련 잔재가 제거되었습니다.

---

## 잠재 리스크 및 다음 조치

### 1. 하위호환성
- **리스크**: 기존 세션에 `coach_mode_welcomed` 키가 남아있을 수 있음
- **조치**: 무시됨 (더 이상 사용하지 않음)
- **상태**: ✅ 안전 (에러 없음)

### 2. 레거시 파일
- **리스크**: `ui_pages/home_legacy.py`에 잔재 존재
- **조치**: 레거시 파일이므로 현재 사용되지 않음
- **상태**: ✅ 안전 (import되지 않음)

### 3. `is_auto_coach_mode()` 함수
- **리스크**: 함수가 남아있지만 사용되지 않음
- **조치**: DEPRECATED 표시, 향후 제거 가능
- **상태**: ✅ 안전 (호출되지 않음)

---

## 회귀 테스트 체크리스트

- [x] HOME 진입 OK
- [x] 가게 설계 센터 진입 OK
- [x] 4개 설계실 진입 OK (전략 브리핑/실행 탭)
- [x] 매출 하락 원인 찾기 진입 버튼 OK
- [x] 마감 입력 / 매출·네이버방문자 보정 진입 OK
- [x] 앱 재실행 후(세션 초기화) 에러 없음
- [x] 린트 에러 없음

---

## 완료일
2026-01-24
