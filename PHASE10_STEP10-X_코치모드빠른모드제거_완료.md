# PHASE 10 / STEP 10-X: 코치모드/빠른모드 제거 완료

## 작업 개요
앱 전역의 "코치모드 / 빠른모드" 개념을 제거하고, 단일 UX로 통일 완료.

---

## 변경된 파일 목록

### 1. `app.py`
- **모드 전환 UI 제거** (라인 1472-1513)
  - 사이드바의 모드 전환 버튼 및 UI 전체 제거
  - `get_onboarding_mode`, `set_onboarding_mode` import 제거
  - `_mode_changed` session_state 관련 코드 제거

### 2. `ui_pages/home/home_page.py`
- **함수 시그니처 수정**:
  - `get_today_one_action(store_id, level, is_coach_mode=False)` → `get_today_one_action(store_id, level)`
  - `get_today_one_action_with_day_context(store_id, level, is_coach_mode=False, day_level=None)` → `get_today_one_action_with_day_context(store_id, level, day_level=None)`
  - `_render_home_body(store_id, coaching_enabled)` → `_render_home_body(store_id)`
  - `_render_problems_good_points(store_id, coaching_enabled)` → `_render_problems_good_points(store_id)`
  - `_render_compressed_alerts(store_id, coaching_enabled)` → `_render_compressed_alerts(store_id)`
  - `_render_anomaly_signals(store_id, coaching_enabled)` → `_render_anomaly_signals(store_id)`

- **분기 로직 제거**:
  - 모든 `if coaching_enabled:` 분기 제거 (항상 실행)
  - `if is_coach_mode:` 분기 제거
  - `coach_mode_welcomed` session_state 관련 코드 제거

- **import 제거**:
  - `get_onboarding_mode` import 제거

- **렌더링 로직 통일**:
  - "코치 모드 전용" 섹션을 일반 섹션으로 변경
  - 모든 사용자에게 동일한 UX 제공

---

## 제거된 session_state 키

1. `coach_mode_welcomed` - 코치 모드 환영 메시지 표시 여부
2. `_mode_changed` - 모드 변경 플래그

**참고**: 기존에 이 키들이 남아 있어도 무시되도록 안전하게 처리됨 (하위호환)

---

## 제거된 UI 위치

### 사이드바 (`app.py`)
- 모드 표시 라벨 ("🎓 현재 모드: 코치 모드" / "⚡ 현재 모드: 빠른 모드")
- 모드 변경 버튼 ("🔄 ⚡ 빠른 모드로 변경" / "🔄 🎓 코치 모드로 변경")
- 모드 디버깅 expander (개발 모드 전용)

### 홈 페이지 (`ui_pages/home/home_page.py`)
- "🎉 코치 모드가 활성화되었습니다" 환영 메시지
- DAY 레벨별 안내 메시지 (DAY1, DAY3, DAY7)
- 코치 모드 전용 섹션 분기

---

## 변경된 UX 흐름

### 이전 (모드 분기)
- 코치 모드: 판결 + 근거 + CTA + 추가 설명
- 빠른 모드: 간소화된 정보만

### 현재 (단일 UX)
- 모든 사용자: 판결 + 근거 + CTA (기본 노출)
- 추가 설명: expander("자세히") 안으로 이동

---

## 회귀 테스트 체크리스트

### ✅ 기본 기능
- [x] 홈 진입 OK
- [x] 설계센터 진입 OK
- [x] 4개 설계실 진입 OK
  - [x] 메뉴 포트폴리오 설계실
  - [x] 메뉴 수익 구조 설계실
  - [x] 재료 구조 설계실
  - [x] 수익 구조 설계실
- [x] 브리핑/실행 탭 정상 작동

### ✅ UI 확인
- [x] 사이드바에 모드 관련 UI 없음
- [x] 홈에 모드 관련 문구 없음
- [x] 모든 페이지에서 모드 관련 에러/경고 없음

### ✅ 기능 확인
- [x] 홈의 판결 카드 정상 표시
- [x] 홈의 근거 카드 정상 표시
- [x] 홈의 CTA 버튼 정상 작동
- [x] "오늘 코치의 한 가지 제안" 섹션 정상 표시
- [x] 문제/잘한 점 섹션 정상 표시

---

## 주의사항

1. **하위호환성**: 기존 `coach_mode_welcomed`, `_mode_changed` session_state 키가 남아 있어도 무시됨 (에러 없음)

2. **onboarding_mode 테이블**: `user_profiles.onboarding_mode` 컬럼은 여전히 DB에 존재하지만, 앱에서 사용하지 않음. 향후 정리 가능.

3. **레거시 파일**: `ui_pages/home.py`, `ui_pages/home_legacy.py`에 유사한 코드가 있을 수 있으나, 현재 사용되지 않는 파일로 보임.

---

## 완료일
2026-01-23
