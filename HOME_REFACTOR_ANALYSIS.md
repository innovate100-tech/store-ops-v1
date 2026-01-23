# 홈 화면 리팩토링 분석 및 설계 문서

## Step 1. 현재 home 코드 구조 분석 요약

### 파일 구조
- **파일**: `ui_pages/home.py` (약 2,127 라인)
- **함수 수**: 18개 함수 정의
- **주요 진입점**: `render_home()` → `_render_home_body(store_id, coaching_enabled)`

### 함수 분류

#### 데이터 로더 함수 (9개)
1. `get_monthly_close_stats()` - 마감률/스트릭 계산
2. `get_problems_top3()` - 문제 TOP3 추출
3. `get_good_points_top3()` - 잘한 점 TOP3 추출
4. `get_anomaly_signals()` - 이상 징후 감지
5. `get_store_financial_structure()` - 숫자 구조 조회
6. `check_actual_settlement_exists()` - 정산 존재 여부
7. `get_menu_count()` - 메뉴 개수
8. `get_close_count()` - 마감 개수
9. `get_monthly_memos()` - 운영 메모 조회

#### 판별/분석 함수 (5개)
1. `detect_data_level()` - 데이터 성숙도 판별 (LEVEL 0-3)
2. `detect_owner_day_level()` - DAY 단계 판별 (DAY1/DAY3/DAY7)
3. `is_auto_coach_mode()` - 자동 코치 모드 활성화 여부
4. `get_coach_summary()` - 코치 요약 문장 생성
5. `get_month_status_summary()` - 이번 달 상태 요약

#### 추천/액션 함수 (2개)
1. `get_today_one_action_with_day_context()` - 오늘 하나만 추천 (DAY 컨텍스트)
2. `get_today_one_action()` - 오늘 하나만 추천 (기본)

#### 렌더링 함수 (2개)
1. `_render_home_body()` - 통합 홈 렌더링 (약 800 라인)
2. `render_home()` - 홈 진입점

---

## Step 2. 홈 최초 진입 시 실행되는 함수 목록화

### 즉시 실행 (홈 진입 시 필수)

#### 데이터 로딩
1. `detect_data_level(store_id)` - LEVEL 판별 (sales, daily_close, expense_structure 조회)
2. `detect_owner_day_level(store_id)` - DAY 판별 (daily_close_count, actual_settlement 조회)
3. `load_monthly_sales_total(store_id, year, month)` - 이번 달 매출 (외부 함수)
4. `get_monthly_close_stats(store_id, year, month)` - 마감률/스트릭 (daily_close 전체 조회)
5. `get_supabase_client().table("daily_close").select("total_sales")` - 오늘 매출 조회
6. `get_supabase_client().table("daily_close").select("visitors")` - 이번 달 방문자 조회 (객단가 계산용)
7. `load_monthly_settlement_snapshot(store_id, year, month)` - 이번 달 이익 (외부 함수)

#### 분석 함수 (무거운 작업)
8. `get_problems_top3(store_id)` - 문제 분석 (내부에서 여러 DB 쿼리 실행)
9. `get_good_points_top3(store_id)` - 잘한 점 분석 (내부에서 여러 DB 쿼리 실행)
10. `get_anomaly_signals(store_id)` - 이상 징후 감지 (내부에서 여러 DB 쿼리 실행)

#### coach_only (coaching_enabled=True일 때만)
11. `get_menu_count(store_id)` - 메뉴 개수
12. `get_close_count(store_id)` - 마감 개수
13. `check_actual_settlement_exists(store_id, year, month)` - 정산 존재 여부
14. `get_today_one_action_with_day_context(store_id, data_level, True, day_level)` - 오늘 추천
15. `get_month_status_summary(store_id, year, month, day_level)` - 상태 요약

#### Lazy 영역 (항상 실행되지만 사용자에게 보이지 않을 수 있음)
16. `get_store_financial_structure(store_id, year, month)` - 숫자 구조 (고정비/변동비/손익분기점 계산)
17. `get_monthly_memos(store_id, year, month, limit=5)` - 운영 메모

### 문제점
- **무거운 분석 함수들이 즉시 실행**: `get_problems_top3`, `get_good_points_top3`, `get_anomaly_signals`는 내부에서 복잡한 쿼리 실행
- **숫자 구조 계산이 즉시 실행**: `get_store_financial_structure`는 고정비/변동비/손익분기점 계산 포함
- **운영 메모가 즉시 로드**: 사용자가 스크롤하지 않아도 로드됨
- **중복 데이터 로딩**: `load_monthly_sales_total`이 상태판과 핵심 숫자 카드에서 각각 호출됨

---

## Step 3. 홈 전용 경량 데이터 함수 설계

### 신규 함수: `home_data.py`

```python
# home_data.py

@st.cache_data(ttl=300)  # 5분 캐시
def load_home_kpis(store_id: str, year: int, month: int) -> dict:
    """
    홈 최초 진입 시 필요한 핵심 KPI만 로드
    
    Returns:
        {
            "monthly_sales": int,
            "today_sales": int,
            "close_stats": (closed_days, total_days, close_rate, streak_days),
            "avg_customer_spend": int | None,
            "monthly_profit": int | None
        }
    """
    # 단일 쿼리로 최적화 가능한 데이터만
    pass

@st.cache_data(ttl=300)
def load_home_alerts(store_id: str) -> dict:
    """
    이상 징후만 경량으로 로드 (매출 급락, 마감 누락 등)
    
    Returns:
        {
            "anomaly_signals": list,  # 최대 3개
            "critical_count": int
        }
    """
    # 최소한의 쿼리만 실행
    pass

@st.cache_data(ttl=300)
def load_home_status(store_id: str, year: int, month: int) -> dict:
    """
    홈 상태판용 데이터
    
    Returns:
        {
            "monthly_sales": int,
            "close_stats": tuple,
            "data_level": int,
            "day_level": str | None
        }
    """
    pass
```

### 제거/이동 대상 함수
- `get_problems_top3()` → `home_rules.py`로 이동, lazy load
- `get_good_points_top3()` → `home_rules.py`로 이동, lazy load
- `get_anomaly_signals()` → `home_alerts.py`로 이동, 경량 버전과 전체 버전 분리
- `get_store_financial_structure()` → `home_lazy.py`로 이동
- `get_monthly_memos()` → `home_lazy.py`로 이동

---

## Step 4. 홈 UI 구조 재배치 (섹션 분리)

### 현재 섹션 순서
1. 헤더
2. coach_only: 성장 단계 메시지
3. coach_only: 코치 모드 환영
4. 공통: 빠른 이동 (3개 버튼)
5. 공통: 상태판 (이번 달 매출, 마감률)
6. coach_only: 시작 미션 3개
7. 공통: 핵심 숫자 카드 (오늘 매출, 이번 달 매출, 객단가, 이번 달 이익)
8. coach_only: 오늘 하나만 추천
9. 공통: 문제 TOP3 / 잘한 점 TOP3
10. 공통: 이상 징후
11. 공통: 미니 차트 (현재는 placeholder)
12. coach_only: 이번 달 가게 상태 한 줄 요약
13. 공통: 우리 가게 숫자 구조
14. 공통: 이번 달 운영 메모

### 리디자인 후 섹션 순서

#### 즉시 표시 영역 (First View)
1. 헤더
2. 공통: 빠른 이동 (3개 버튼)
3. 공통: 오늘 상태 요약 (5개 카드)
   - 이번 달 매출
   - 마감률
   - 오늘 매출
   - 객단가
   - 이번 달 이익
4. 공통: 이상 징후 (홈 핵심, 최대 3개)
5. 공통: 문제 TOP1 / 잘한 점 TOP1 (기본 1개만, "자세히 보기" 버튼)

#### coach_only 영역 (First View)
6. coach_only: 성장 단계 메시지
7. coach_only: 코치 모드 환영
8. coach_only: 시작 미션 3개 (간소화)
9. coach_only: 오늘 하나만 추천

#### Lazy 영역 (expander/버튼 클릭 시)
10. 공통: 인사이트 더보기 (expander)
    - 우리 가게 숫자 구조
    - 매출 구간별 예상 이익
    - 미니 차트
    - 운영 메모
11. coach_only: 이번 달 가게 상태 한 줄 요약 (expander)

---

## Step 5. Lazy 영역 분리

### `home_lazy.py` 설계

```python
# home_lazy.py

def render_lazy_insights(store_id: str, year: int, month: int):
    """
    인사이트 더보기 expander 내부 렌더링
    - 우리 가게 숫자 구조
    - 매출 구간별 예상 이익
    - 미니 차트
    - 운영 메모
    """
    with st.expander("📊 인사이트 더보기", expanded=False):
        # 숫자 구조
        # 차트
        # 운영 메모
        pass

def render_lazy_financial_structure(store_id: str, year: int, month: int):
    """숫자 구조만 lazy load"""
    pass

def render_lazy_charts(store_id: str, year: int, month: int):
    """차트만 lazy load"""
    pass

def render_lazy_memos(store_id: str, year: int, month: int):
    """운영 메모만 lazy load"""
    pass
```

### 문제/잘한 점 전체 보기
- 기본: TOP1만 표시
- "자세히 보기" 버튼 클릭 시: `get_problems_top3()`, `get_good_points_top3()` 전체 로드

---

## Step 6. Coach / Fast 모드 UI 분기 정리

### coach_only 영역 (coaching_enabled=True일 때만)
1. 성장 단계 메시지 (DAY 연출)
2. 코치 모드 환영 (최초 1회)
3. 시작 미션 3개
4. 오늘 하나만 추천
5. 문제/이상징후 guide_text (행동 연결 문장)
6. 이번 달 가게 상태 한 줄 요약

### 공통 영역 (모든 모드)
- 빠른 이동 버튼
- 오늘 상태 요약
- 이상 징후
- 문제 TOP1 / 잘한 점 TOP1
- 인사이트 더보기 (lazy)

### 분기 로직 정리
```python
# home_page.py
def _render_home_body(store_id: str, coaching_enabled: bool):
    # 공통: 빠른 이동
    _render_quick_actions()
    
    # 공통: 오늘 상태 요약 (경량 데이터)
    kpis = load_home_kpis(store_id, year, month)
    _render_status_summary(kpis)
    
    # 공통: 이상 징후 (경량)
    alerts = load_home_alerts(store_id)
    _render_alerts(alerts, coaching_enabled)
    
    # 공통: 문제/잘한 점 TOP1
    _render_problems_good_points_summary(store_id, coaching_enabled)
    
    # coach_only: 성장 메시지, 미션, 추천
    if coaching_enabled:
        _render_coach_sections(store_id, day_level)
    
    # 공통: Lazy 영역
    _render_lazy_insights(store_id, year, month)
```

---

## Step 7. 성능 영향 요약

### 현재 (Before)
- 홈 진입 시 실행 함수: **17개**
- 무거운 분석 함수: **3개** (problems, good_points, anomaly_signals)
- 숫자 구조 계산: **즉시 실행**
- 운영 메모: **즉시 로드**
- 예상 로딩 시간: **2-5초** (데이터 양에 따라)

### 리팩토링 후 (After)
- 홈 진입 시 실행 함수: **7개** (약 60% 감소)
  - `load_home_kpis()` - 통합 KPI 로더
  - `load_home_alerts()` - 경량 이상 징후
  - `detect_data_level()` - LEVEL 판별
  - `detect_owner_day_level()` - DAY 판별 (coach_only)
  - `get_menu_count()` - 미션용 (coach_only)
  - `get_close_count()` - 미션용 (coach_only)
  - `check_actual_settlement_exists()` - 미션용 (coach_only)
- 무거운 분석 함수: **0개** (lazy load로 이동)
- 숫자 구조 계산: **lazy load**
- 운영 메모: **lazy load**
- 예상 로딩 시간: **0.5-1.5초** (약 70% 개선)

### 스크롤 길이 감소
- 현재: 약 8-10개 섹션 (스크롤 필요)
- 리팩토링 후: 약 5-6개 섹션 (First View 완성)
- 예상 감소율: **40-50%**

---

## 변경 파일 목록

### 신규 파일
1. `ui_pages/home/home_page.py` - 메인 렌더링 로직
2. `ui_pages/home/home_data.py` - 경량 데이터 로더
3. `ui_pages/home/home_alerts.py` - 이상 징후 로직
4. `ui_pages/home/home_rules.py` - 문제/잘한 점 룰
5. `ui_pages/home/home_components.py` - 카드/UI 컴포넌트
6. `ui_pages/home/home_lazy.py` - Lazy 영역 렌더링
7. `ui_pages/home/__init__.py` - 모듈 초기화

### 수정 파일
1. `ui_pages/home.py` - 기존 파일은 `home_page.py`로 이동 후 삭제 또는 레거시 호환용으로 유지

### 제거/이동 로직
- `get_problems_top3()` → `home_rules.py`
- `get_good_points_top3()` → `home_rules.py`
- `get_anomaly_signals()` → `home_alerts.py` (경량 버전 추가)
- `get_store_financial_structure()` → `home_lazy.py`
- `get_monthly_memos()` → `home_lazy.py`
- `get_monthly_close_stats()` → `home_data.py` (통합)
- 중복 데이터 로딩 제거 (monthly_sales 등)

---

## 다음 단계

1. ✅ Step 1-7 분석 완료
2. ✅ `home/` 패키지 생성 및 모듈 분리
3. ✅ 경량 데이터 로더 (`home_data.load_home_kpis`) 구현
4. ✅ UI 구조 재배치 (`home_page._render_home_body`)
5. ✅ Lazy 영역 (`home_lazy.render_lazy_insights`) 구현
6. ⏳ 테스트 및 검증

### 구현 완료 (2025-01)

- `ui_pages/home/` 패키지 구성: `home_page`, `home_data`, `home_alerts`, `home_rules`, `home_components`, `home_lazy`
- `from ui_pages.home import render_home` → 패키지 로드 (기존 `home.py`와 공존 시 패키지 우선)
- `load_home_kpis`로 상태판·핵심 숫자 카드 일괄 로드, `@st.cache_data(ttl=300)` 적용
- 숫자 구조·운영 메모 → `인사이트 더보기` expander 내 lazy 로드
- `pdf_scorecard_mvp` 호환: `get_problems_top3`, `get_good_points_top3`, `get_anomaly_signals`, `get_coach_summary`, `get_month_status_summary`, `get_monthly_close_stats`, `detect_owner_day_level`, `get_store_financial_structure` re-export
