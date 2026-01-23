# 순환 Import 문제 해결 완료 보고서

**작업 일자**: 2026-01-24  
**문제**: ImportError - 순환 import 발생

---

## 🔴 문제 상황

**에러 메시지**:
```
ImportError: This app has encountered an error...
File "/mount/src/store-ops-v1/ui_pages/coach/coach_adapters.py", line 7, in <module>
    from ui_pages.home.home_verdict import get_coach_verdict
File "/mount/src/store-ops-v1/ui_pages/home/__init__.py", line 5, in <module>
    from ui_pages.home.home_page import (
File "/mount/src/store-ops-v1/ui_pages/home/home_page.py", line 36, in <module>
    from ui_pages.coach.coach_adapters import get_home_coach_verdict
```

**순환 import 체인**:
1. `coach_adapters.py` → `home_verdict.py` (top-level import)
2. `home_verdict.py` → `home/__init__.py` (간접)
3. `home/__init__.py` → `home_page.py` (top-level import)
4. `home_page.py` → `coach_adapters.py` (top-level import) ← 순환!

---

## ✅ 해결 방법

### 1. `coach_adapters.py` 수정

**변경 전**:
```python
from ui_pages.home.home_verdict import get_coach_verdict

def get_home_coach_verdict(store_id: str, year: int, month: int) -> CoachVerdict:
    ...
    verdict_dict = get_coach_verdict(store_id, year, month, monthly_sales)
```

**변경 후**:
```python
# top-level import 제거

def get_home_coach_verdict(store_id: str, year: int, month: int) -> CoachVerdict:
    # 순환 import 방지를 위해 함수 내부에서 import
    from ui_pages.home.home_verdict import get_coach_verdict
    ...
    verdict_dict = get_coach_verdict(store_id, year, month, monthly_sales)
```

**파일**: `ui_pages/coach/coach_adapters.py`

---

### 2. `home_page.py` 수정

**변경 전**:
```python
from ui_pages.coach.coach_adapters import get_home_coach_verdict

def _render_zone2_coach_verdict(...):
    ...
    verdict = get_home_coach_verdict(store_id, year, month)
```

**변경 후**:
```python
# top-level import 제거
# get_home_coach_verdict는 순환 import 방지를 위해 함수 내부에서 import

def _render_zone2_coach_verdict(...):
    ...
    # 순환 import 방지를 위해 함수 내부에서 import
    from ui_pages.coach.coach_adapters import get_home_coach_verdict
    verdict = get_home_coach_verdict(store_id, year, month)
```

**파일**: `ui_pages/home/home_page.py`

---

## 📊 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `ui_pages/coach/coach_adapters.py` | `get_coach_verdict` import를 함수 내부로 이동 |
| `ui_pages/home/home_page.py` | `get_home_coach_verdict` import를 함수 내부로 이동 |

**총 수정 파일**: 2개

---

## 🎯 해결 원리

**순환 import 문제 해결 방법**:
1. **함수 내부 import**: 필요한 시점에만 import하여 순환 체인을 끊음
2. **Lazy loading**: 모듈 로드 시점이 아닌 함수 실행 시점에 import
3. **의존성 지연**: 실제 사용하는 시점까지 import를 지연

**장점**:
- ✅ 순환 import 문제 해결
- ✅ 모듈 로드 시간 단축 (불필요한 import 방지)
- ✅ 코드 구조 유지 (기능 변경 없음)

**단점**:
- ⚠️ 함수 실행 시점에 import 오류 발생 가능 (런타임 에러)
- ⚠️ 코드 가독성 약간 저하 (import 위치가 분산)

---

## 🔍 검증

**수정 후 import 체인**:
1. `app.py` → `settlement_actual.py`
2. `settlement_actual.py` → `monthly_structure_report.py`
3. `monthly_structure_report.py` → `coach_adapters.py` (top-level import)
4. `coach_adapters.py` → `home_verdict.py` (함수 내부 import) ✓
5. `home_verdict.py` → `home_page.py`를 import하지 않음 ✓
6. `home_page.py` → `coach_adapters.py` (함수 내부 import) ✓

**결과**: 순환 import 체인 해제 완료 ✅

---

## 📝 주의사항

1. **함수 내부 import 사용 시**:
   - 함수가 호출될 때만 import되므로, 함수 호출 전에 import 오류를 발견하기 어려울 수 있음
   - 테스트 시 함수 호출까지 해야 import 오류를 확인할 수 있음

2. **향후 개선**:
   - 의존성 구조를 재설계하여 순환 import가 발생하지 않도록 하는 것이 이상적
   - 공통 인터페이스나 추상화 계층을 도입하여 의존성을 분리

---

**작성일**: 2026-01-24  
**담당**: 순환 import 문제 해결
