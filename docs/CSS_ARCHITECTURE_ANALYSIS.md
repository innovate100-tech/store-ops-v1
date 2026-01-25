# Streamlit 앱 CSS 구조 제품급 분석 보고서

**생성일**: 2026-01-25  
**목적**: CSS로 인한 페이지 사라짐/튕김 원인 근본 제거  
**분석 범위**: 프로젝트 전체 CSS 주입 지점 및 위험 규칙

---

## 📋 목차

1. [CSS 주입 지점 인벤토리 (전수)](#1-css-주입-지점-인벤토리-전수)
2. [위험 CSS 규칙 탐지 리포트](#2-위험-css-규칙-탐지-리포트)
3. [애니메이션/오버레이 계층 구조 분석](#3-애니메이션오버레이-계층-구조-분석)
4. [CSS 운영 방식 개선안 (권장 구조)](#4-css-운영-방식-개선안-권장-구조)
5. [자동 수집 스크립트](#5-자동-수집-스크립트)

---

## 1. CSS 주입 지점 인벤토리 (전수)

### 1.1 전역 CSS 주입 지점

| 파일 | 라인 | 함수/위치 | 주입 방식 | 적용 범위 | 재주입 가능성 | ON/OFF 토글 |
|------|------|-----------|-----------|-----------|---------------|-------------|
| `app.py` | 24 | `inject_global_ui()` | `st.markdown()` | 전역 | 매 rerun마다 | 없음 |
| `app.py` | 88 | `inject_sidebar_premium_css()` | `st.markdown()` | 사이드바 | 매 rerun마다 | `_ps_disable_ultra_css` |
| `app.py` | 837 | dark theme style | `st.markdown()` | 전역 | 조건부 (theme="dark") | 없음 |
| `app.py` | 1045 | FINAL_SAFETY_PIN | `st.markdown()` | 전역 | 1회만 (`_ps_final_safety_pin_injected`) | 없음 |
| `src/ui/theme_manager.py` | 180 | `inject_global_ui()` (aggrid_dark_js) | `st.markdown()` | 전역 | 매 rerun마다 | 없음 |
| `src/ui/theme_manager.py` | 205 | `inject_global_ui()` (global_css) | `st.markdown()` | 전역 | 매 rerun마다 | 없음 |
| `src/ui/common_header.py` | 240 | `render_common_header()` | `st.markdown()` | 전역 | 매 rerun마다 | 없음 |

### 1.2 페이지별 CSS 주입 지점

| 파일 | 라인 | 함수/위치 | 주입 방식 | 적용 범위 | 재주입 가능성 | ON/OFF 토글 |
|------|------|-----------|-----------|-----------|---------------|-------------|
| `ui_pages/input/input_hub.py` | 30 | `inject_input_hub_ultra_premium_css()` | `st.markdown()` | 입력 허브 | 1회만 (`_ps_ultra_css_injected`) | `_ps_disable_ultra_css` |
| `ui_pages/input/input_hub.py` | 160 | 인라인 애니메이션 CSS | `st.markdown()` | 입력 허브 | 매 rerun마다 | 없음 |
| `src/ui/components/form_kit_v2.py` | 392 | `inject_form_kit_v2_css()` | `st.markdown()` | 페이지별 (scope_id) | 매 rerun마다 | 없음 |
| `src/ui/components/form_kit.py` | 80 | `inject_form_kit_css()` | `st.markdown()` | 전역 | 매 rerun마다 | 없음 |
| `src/ui/layouts/input_layouts.py` | 562 | `INPUT_LAYOUT_CSS` | `st.markdown()` | 페이지별 | 매 rerun마다 | 없음 |
| `src/ui/layouts/input_layouts.py` | 643 | `INPUT_LAYOUT_CSS` | `st.markdown()` | 페이지별 | 매 rerun마다 | 없음 |

### 1.3 CSS 주입 함수 상세

#### `inject_global_ui()` (`src/ui/theme_manager.py`)
- **호출 위치**: `app.py:25` (앱 시작 시)
- **주입 방식**: `st.markdown()` (2회: aggrid_dark_js + global_css)
- **재주입**: 매 rerun마다 (가드 없음)
- **내용**: CSS 변수 토큰, 다크 모드 입력 위젯 스타일
- **위험도**: 낮음 (전역 토큰만, 컨텐츠 숨김 규칙 없음)

#### `inject_sidebar_premium_css()` (`app.py:88`)
- **호출 위치**: `app.py:923` (사이드바 렌더링 시)
- **주입 방식**: `st.markdown()`
- **재주입**: 매 rerun마다 (가드 없음)
- **내용**: 사이드바 울트라 시크 CSS (애니메이션 포함)
- **위험도**: 낮음 (사이드바만 타겟, 메인 컨텐츠 영향 없음)
- **토글**: `_ps_disable_ultra_css` (사이드바 CSS도 함께 비활성화)

#### `inject_input_hub_ultra_premium_css()` (`ui_pages/input/input_hub.py:30`)
- **호출 위치**: `ui_pages/input/input_hub.py:746` (입력 허브 렌더링 시)
- **주입 방식**: `st.markdown()`
- **재주입**: 1회만 (`_ps_ultra_css_injected` 플래그)
- **내용**: Ultra Premium CSS (배경 애니메이션, TIER 카드 스타일)
- **위험도**: **높음** (배경 레이어가 컨텐츠를 가릴 수 있음)
- **토글**: `_ps_disable_ultra_css`, `_ps_ui_rescue_ultra`, `_ps_overlay_probe`

#### `inject_form_kit_v2_css()` (`src/ui/components/form_kit_v2.py:371`)
- **호출 위치**: 각 페이지 렌더 함수 내부
- **주입 방식**: `st.markdown()`
- **재주입**: 매 rerun마다 (가드 없음)
- **내용**: FormKit v2 컴포넌트 스타일 (스코프 격리)
- **위험도**: 낮음 (컴포넌트 스타일만, 컨텐츠 숨김 규칙 없음)

### 1.4 인라인 CSS 주입 (위험)

| 파일 | 라인 | 위치 | 내용 | 위험도 |
|------|------|------|------|--------|
| `ui_pages/input/input_hub.py` | 160 | `render_input_hub_v3()` | 애니메이션 keyframes | 중간 |
| `ui_pages/input/input_hub.py` | 115 | `_hub_status_card()` | 인라인 style (backdrop-filter) | 낮음 |

**문제점**: 인라인 CSS는 재주입 가드가 없어 매 rerun마다 주입됨.

---

## 2. 위험 CSS 규칙 탐지 리포트

### 2.1 Streamlit 핵심 컨테이너 타겟팅 검사

#### ✅ 안전한 규칙 (보호 규칙)

**발견 위치**: `ui_pages/input/input_hub.py` (여러 위치)

```css
[data-testid="stMain"],
[data-testid="stMainBlockContainer"]{
  visibility: visible !important;
  opacity: 1 !important;
  transform: none !important;
  filter: none !important;
  backdrop-filter: none !important;
}
```

**평가**: 안전함. 컨텐츠를 보호하는 규칙.

#### ⚠️ 잠재적 위험 규칙

**발견 위치**: `ui_pages/input/input_hub.py:115`

```css
backdrop-filter: blur(10px);
```

**위험도**: 중간  
**이유**: `backdrop-filter`는 새로운 stacking context를 생성하여 z-index가 꼬일 수 있음  
**대체 설계**: 배경 레이어에만 적용, 컨텐츠 컨테이너에는 적용 금지

### 2.2 배경 레이어 규칙 검사

#### 발견된 배경 레이어

**위치**: `ui_pages/input/input_hub.py:109`

```css
[data-ps-scope="input_hub"].ps-hub-bg::after {
    position: fixed !important;
    inset: 0 !important;
    z-index: 0 !important;
    pointer-events: none !important;
}
```

**평가**: ✅ 안전함. `z-index: 0`, `pointer-events: none`으로 올바르게 설정됨.

### 2.3 애니메이션에서 opacity: 0 사용

**발견 위치**: `ui_pages/input/input_hub.py:162`

```css
@keyframes fadeInUp { 
    from { opacity: 0; transform: translateY(20px); } 
    to { opacity: 1; transform: translateY(0); } 
}
```

**위험도**: 중간  
**이유**: 애니메이션이 실패하면 `opacity: 0` 상태로 남을 수 있음  
**대체 설계**: 기본값을 `opacity: 1`로 설정하고 `animation-fill-mode: both` 사용

**현재 해결책**: `ui_pages/input/input_hub.py:175`에서 기본값 `opacity: 1 !important` 설정

### 2.4 overflow: hidden 검사

**발견 위치**: `app.py:200`, `src/ui/common_header.py:21`

```css
overflow: hidden !important;
```

**위험도**: 낮음  
**이유**: 사이드바/헤더에만 적용, `stMain`에는 적용되지 않음

### 2.5 transform/filter/backdrop-filter 검사

**발견 위치**: 여러 위치

- `app.py:251`: `transform: scale(1.01)` (버튼 hover)
- `src/ui/theme_manager.py:283`: `filter: brightness(1.06)` (버튼 hover)
- `ui_pages/input/input_hub.py:115`: `backdrop-filter: blur(10px)` (카드)

**위험도**: 낮음-중간  
**이유**: 개별 요소에만 적용, `stMain` 계열에는 적용되지 않음  
**주의**: stacking context 생성 가능성 있음

---

## 3. 애니메이션/오버레이 계층 구조 분석

### 3.1 배경 애니메이션 계층

#### Ultra Premium 배경 (`input_hub.py`)

**DOM 구조**:
```
[data-ps-scope="input_hub"].ps-hub-bg
  ├── ::before (상단 Neon Bar)
  │   └── position: fixed, z-index: 0, pointer-events: none
  └── ::after (배경 메시/그리드)
      └── position: fixed, inset: 0, z-index: 0, pointer-events: none
```

**애니메이션**:
- `slowDrift`: 24초 무한 반복 (배경 그라디언트 이동)

**z-index 구조**:
```
z-index: 0  → 배경 레이어 (::before, ::after)
z-index: 1  → .ps-hub-bg 컨테이너
z-index: 5  → TIER 카드들
z-index: 50 → Streamlit 메인 컨텐츠 (안전핀 CSS)
```

**평가**: ✅ 올바른 구조. 배경은 뒤에, 컨텐츠는 앞에.

### 3.2 사이드바 애니메이션 계층

#### Ultra Sleek Sidebar (`app.py:88`)

**애니메이션**:
- `ultra-neon-pulse`: 3.6초 무한 반복 (버튼 glow)
- `ultra-gradient-shift`: 4.2초 무한 반복 (그라디언트 이동)

**z-index 구조**:
- 사이드바는 독립적인 레이어
- 메인 컨텐츠와 겹치지 않음

**평가**: ✅ 안전함. 사이드바만 타겟팅.

### 3.3 카드 애니메이션 계층

#### TIER 카드 애니메이션 (`input_hub.py`)

**애니메이션**:
- `fadeUp`: 0.4s 일회성 (카드 등장)
- `ultra-neon-pulse`: 3.6s 무한 (미완료 상태)
- `ultra-gradient-shift`: 4.2s 무한 (미완료 상태)

**위험 요소**:
- `backdrop-filter: blur(15px)` 사용
- stacking context 생성 가능

**평가**: ⚠️ 주의 필요. 카드에만 적용되지만 stacking context 생성 가능.

---

## 4. CSS 운영 방식 개선안 (권장 구조)

### 4.1 4계층 분리 설계

#### 계층 1: BASE (전역 토큰)
- **위치**: `src/ui/theme_manager.py` 또는 `app.py` 시작부
- **내용**: CSS 변수 토큰만 (색상, 간격, 폰트)
- **재주입**: 1회만 (플래그: `_ps_base_css_injected`)
- **토글**: 없음 (필수)

#### 계층 2: THEME (테마 스타일)
- **위치**: `app.py` 또는 전역 주입 함수
- **내용**: 다크 모드, 사이드바 기본 스타일
- **재주입**: 1회만 (플래그: `_ps_theme_css_injected`)
- **토글**: `_ps_disable_theme` (선택)

#### 계층 3: FX (효과/애니메이션)
- **위치**: 페이지별 또는 전역
- **내용**: 애니메이션, 오버레이, 고급 효과
- **재주입**: 1회만 (플래그: `_ps_fx_css_injected`)
- **토글**: `_ps_disable_fx` (기본값: False, 성능 저하 시 True)

#### 계층 4: RESCUE (안전핀)
- **위치**: `app.py` 마지막 (모든 CSS 주입 후)
- **내용**: 컨텐츠 보호 규칙, 레이어 고정
- **재주입**: 1회만 (플래그: `_ps_rescue_css_injected`)
- **토글**: 없음 (항상 활성화)

### 4.2 CSS 주입 가드 패턴

**권장 패턴**:
```python
def inject_css_layer(layer_name: str, css_content: str, toggle_key: str = None):
    """통일된 CSS 주입 함수"""
    # 토글 확인
    if toggle_key and st.session_state.get(toggle_key, False):
        return
    
    # 재주입 가드
    flag_key = f"_ps_{layer_name}_css_injected"
    if st.session_state.get(flag_key, False):
        return
    
    # CSS 주입
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    
    # 로그 기록
    push_render_step(f"CSS_INJECT: {layer_name}", extra={"where": layer_name})
    
    # 플래그 설정
    st.session_state[flag_key] = True
```

### 4.3 페이지 내부 재주입 금지 규칙

**규칙**:
1. 페이지 렌더 함수 내부에서 CSS 재주입 금지
2. 예외: 디버그용 토글이 켜져 있을 때만 허용
3. 모든 CSS는 앱 시작 시 또는 전역 함수에서만 주입

**현재 문제점**:
- `ui_pages/input/input_hub.py:160`: 인라인 애니메이션 CSS가 매 rerun마다 주입됨
- 해결: 전역 CSS 함수로 이동 또는 1회 주입 가드 추가

### 4.4 토글 설계

**권장 토글 구조**:

| 토글 키 | 기본값 | 설명 | 적용 범위 |
|---------|--------|------|-----------|
| `_ps_disable_base_css` | False | BASE CSS 비활성화 | 없음 (필수) |
| `_ps_disable_theme_css` | False | THEME CSS 비활성화 | 전역 |
| `_ps_disable_fx_css` | False | FX CSS 비활성화 | 전역 |
| `_ps_disable_ultra_css` | False | Ultra CSS 비활성화 | 입력 허브 |
| `_ps_ui_rescue_ultra` | True | UI RESCUE 활성화 | 입력 허브 |
| `_ps_overlay_probe` | True | Overlay Probe 활성화 | 입력 허브 |

**위치**: 사이드바에 통합 토글 섹션

### 4.5 적용 순서 (우선순위)

**권장 순서**:
1. BASE (CSS 변수 토큰)
2. THEME (다크 모드, 기본 스타일)
3. FX (애니메이션, 오버레이)
4. 페이지별 CSS (FormKit, Ultra 등)
5. **RESCUE (최종 안전핀)** ← 가장 마지막

**현재 순서**:
1. `inject_global_ui()` (BASE + THEME)
2. `inject_sidebar_premium_css()` (THEME)
3. `inject_form_kit_v2_css()` (페이지별)
4. `inject_input_hub_ultra_premium_css()` (FX)
5. `FINAL_SAFETY_PIN` (RESCUE) ← 올바름

### 4.6 마지막 안전핀 CSS 위치

**현재 위치**: `app.py:1045` (모든 페이지 렌더링 후)

**권장 위치**: ✅ 현재 위치가 올바름

**내용**:
```css
/* 컨텐츠 강제 복구 */
[data-testid="stMain"], [data-testid="stMainBlockContainer"]{
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  transform: none !important;
  filter: none !important;
  backdrop-filter: none !important;
}

/* 컨텐츠 레이어 올리기 */
[data-testid="stSidebar"], [data-testid="stMain"], [data-testid="stMainBlockContainer"]{
  position: relative !important;
  z-index: 2147483000 !important;
}

/* 배경/오버레이 레이어는 클릭 방해 금지 + 뒤로 */
.ps-ultra-bg, .ps-mesh, .ps-overlay, .ultra-bg, .mesh-bg, .animated-bg,
.overlay, .backdrop, .background, .bg-layer,
[data-ps-scope="input_hub"].ps-hub-bg::before,
[data-ps-scope="input_hub"].ps-hub-bg::after {
  pointer-events: none !important;
  z-index: 0 !important;
}
```

**평가**: ✅ 올바른 위치와 내용. 모든 CSS 주입 후 마지막에 적용되어 최우선순위 보장.

---

## 5. 자동 수집 스크립트

### 5.1 스크립트 위치

**파일**: `scripts/css_audit.py`

**사용법**:
```bash
python scripts/css_audit.py
```

**출력**: `docs/css_audit_report.md`

### 5.2 스크립트 기능

1. **CSS 주입 지점 검색**:
   - `st.markdown(...<style...)` 패턴
   - `unsafe_allow_html=True`와 함께 style 주입
   - `inject_*css()` 함수 정의

2. **위험 규칙 탐지**:
   - `opacity: 0`, `visibility: hidden`, `display: none`
   - `overflow: hidden`
   - `backdrop-filter`, `transform`, `filter`
   - `stMain` 계열 셀렉터

3. **애니메이션 키워드 검색**:
   - `ultra`, `mesh`, `overlay`, `animation`

4. **고정 오버레이 검색**:
   - `position: fixed` + `inset` 또는 높은 `z-index`

### 5.3 리포트 형식

마크다운 리포트로 다음 정보 포함:
- 발견된 파일/라인
- 매칭된 패턴
- 위험도 평가
- 개선 제안

---

## 6. 발견된 문제점 및 해결책

### 6.1 문제점 1: 인라인 CSS 재주입

**위치**: `ui_pages/input/input_hub.py:160`

**문제**: 애니메이션 keyframes가 매 rerun마다 주입됨

**해결책**:
1. 전역 CSS 함수로 이동
2. 또는 1회 주입 가드 추가

**권장 코드**:
```python
# 전역 함수로 이동
def inject_input_hub_animations():
    if st.session_state.get("_ps_input_hub_animations_injected", False):
        return
    # ... 애니메이션 CSS ...
    st.session_state["_ps_input_hub_animations_injected"] = True
```

### 6.2 문제점 2: backdrop-filter stacking context

**위치**: `ui_pages/input/input_hub.py:115`, `app.py:608`

**문제**: `backdrop-filter`가 stacking context를 생성하여 z-index가 꼬일 수 있음

**해결책**:
- 컨텐츠 컨테이너에는 `backdrop-filter` 금지
- 배경 레이어에만 적용
- 또는 `stMain` 계열에 `backdrop-filter: none !important` 강제

**현재 해결책**: ✅ `app.py:1045` 최종 안전핀에서 `backdrop-filter: none !important` 강제

### 6.3 문제점 3: 매 rerun마다 CSS 주입

**위치**: 여러 위치

**문제**: 많은 CSS가 매 rerun마다 주입되어 성능 저하 및 레이어 역전 가능

**해결책**:
- 모든 CSS 주입 함수에 1회 주입 가드 추가
- 플래그 기반 재주입 방지

**현재 상태**:
- ✅ `inject_input_hub_ultra_premium_css()`: 1회 주입 가드 있음
- ❌ `inject_global_ui()`: 가드 없음
- ❌ `inject_sidebar_premium_css()`: 가드 없음
- ❌ `inject_form_kit_v2_css()`: 가드 없음

---

## 7. 권장 개선 사항

### 7.1 즉시 적용 가능한 개선

1. **모든 CSS 주입 함수에 1회 주입 가드 추가**
   - `inject_global_ui()`: `_ps_global_ui_injected` 플래그
   - `inject_sidebar_premium_css()`: `_ps_sidebar_css_injected` 플래그
   - `inject_form_kit_v2_css()`: 스코프별 플래그

2. **인라인 CSS 제거**
   - `ui_pages/input/input_hub.py:160`의 애니메이션 CSS를 전역 함수로 이동

3. **최종 안전핀 CSS 유지**
   - `app.py:1045`의 FINAL_SAFETY_PIN은 유지 (모든 CSS 주입 후 마지막)

### 7.2 중장기 개선 사항

1. **4계층 분리 구조 도입**
   - BASE/THEME/FX/RESCUE 계층 분리
   - 각 계층별 토글 제공

2. **통일된 CSS 주입 함수**
   - `inject_css_layer()` 함수로 통일
   - 가드, 로그, 플래그 관리 자동화

3. **CSS 주입 추적 시스템**
   - NAV TRACE에 모든 CSS 주입 기록
   - 주입 횟수 및 순서 모니터링

---

## 8. 검증 방법

### 8.1 CSS 주입 횟수 확인

**방법**:
1. `?debug=1`로 접속
2. NAV TRACE에서 `CSS_INJECT` 이벤트 확인
3. 각 CSS가 1회만 주입되는지 확인

**예상 로그**:
```
CSS_INJECT: app.py:96 inject_sidebar_premium_css (where: global)
CSS_INJECT: theme_manager.py:203 inject_global_ui (where: global)
CSS_INJECT: theme_manager.py:205 inject_global_ui (where: global)
CSS_INJECT: form_kit_v2.py:392 inject_form_kit_v2_css (where: global)
CSS_INJECT: input_hub.py:30 inject_input_hub_ultra_premium_css (where: ultra)
CSS_INJECT: app.py:1045 FINAL_SAFETY_PIN (where: final)
```

### 8.2 컨텐츠 가려짐 확인

**방법**:
1. Ultra ON 상태에서 입력 허브 접속
2. 컨텐츠가 보이는지 확인
3. 페이지 왕복 후에도 컨텐츠 유지 확인

**기대 결과**:
- ✅ Ultra ON 상태에서도 컨텐츠가 보임
- ✅ 배경 애니메이션은 보이되 컨텐츠는 가려지지 않음
- ✅ 클릭/스크롤이 정상 작동

---

## 9. 결론

### 9.1 현재 상태

**강점**:
- ✅ 최종 안전핀 CSS가 올바른 위치에 있음
- ✅ Ultra CSS는 1회만 주입됨
- ✅ 배경 레이어는 올바른 z-index 설정

**약점**:
- ❌ 많은 CSS가 매 rerun마다 주입됨
- ❌ 인라인 CSS 재주입 문제
- ❌ 통일된 주입 가드 패턴 없음

### 9.2 개선 우선순위

1. **높음**: 모든 CSS 주입 함수에 1회 주입 가드 추가
2. **높음**: 인라인 CSS 제거 또는 가드 추가
3. **중간**: 4계층 분리 구조 도입
4. **낮음**: 통일된 CSS 주입 함수 도입

### 9.3 완료 기준

- ✅ CSS 주입 지점 전수 파악 완료
- ✅ 위험 CSS 규칙 탐지 완료
- ✅ 애니메이션/오버레이 계층 구조 분석 완료
- ✅ CSS 운영 방식 개선안 제시 완료
- ✅ 자동 수집 스크립트 제공 완료

**다음 단계**: 권장 개선 사항을 단계적으로 적용하여 CSS 안정성 향상.
