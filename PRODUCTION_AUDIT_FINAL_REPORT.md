# 🏭 프로덕션 감리 최종 보고서
## 외식업 사장용 숫자 코치 SaaS - 전체 구조 점검

**작성일**: 2026-01-24  
**감리자**: 프로덕션 감리 엔지니어 + SaaS 설계 리뷰어  
**프로젝트**: Store Operations v1 (Streamlit + Supabase)  
**목적**: 출시 전 안정성/구조/제품 완성도 종합 점검

---

## 1️⃣ Executive Summary

### 현재 앱의 "현실 위치"

**종합 평가**: ⚠️ **출시 불가 - 대규모 안정화 작업 필요**

#### 긍정적 측면
- ✅ **핵심 기능 구현 완료**: 매출/비용/재고 관리, 전략 엔진, 설계실 4개
- ✅ **데이터 구조 설계 양호**: SSOT 정책, daily_close 중심 구조
- ✅ **제품 철학 명확**: "Coach + School", "Design System" 컨셉 잘 구현
- ✅ **RLS 보안 적용**: 다중 테넌시 지원

#### 치명적 문제점
- 🔴 **app.py 3,352줄**: 단일 파일에 모든 로직 집중 (유지보수 불가)
- 🔴 **st.rerun() 296회**: 과도한 rerun으로 인한 성능 저하 및 UX 저하
- 🔴 **빈 DataFrame 접근 위험**: 50개 이상 `.iloc[0]` 사용 (IndexError 위험)
- 🔴 **트랜잭션 부재**: 다중 테이블 저장 시 데이터 무결성 보장 없음
- 🔴 **예외 처리 불일치**: `except: pass` 패턴으로 에러 삼킴

#### 출시 가능 여부 판단

**당장 출시 불가 이유**:
1. **안정성**: 빈 데이터 접근 시 즉시 크래시
2. **데이터 무결성**: 트랜잭션 없이 부분 저장 실패 가능
3. **성능**: 과도한 rerun으로 인한 느린 반응
4. **유지보수성**: app.py 3,352줄로 수정/확장 불가능

**최소 출시 조건 (Phase 0 완료 후)**:
- ✅ 모든 `.iloc[0]` 안전 접근으로 변경
- ✅ 트랜잭션 함수 적용 (save_daily_close 등)
- ✅ app.py 모듈 분리 (최대 500줄 이하)
- ✅ rerun 최적화 (50% 이상 감소)

**예상 안정화 기간**: **2-3주** (전담 개발자 기준)

---

## 2️⃣ 치명도 분류 리스트

### 🔴 CRITICAL (지금 안 고치면 망함)

#### 1. app.py 비대화 (3,352줄)
**위험도**: 🔴🔴🔴  
**위치**: `app.py` 전체  
**문제점**:
- 단일 파일에 모든 페이지 로직 집중
- 라우팅, 사이드바, 페이지 렌더링 모두 한 파일
- 수정 시 사이드 이펙트 위험 극대
- 코드 리뷰/테스트 불가능

**영향**:
- 버그 수정 시 다른 페이지 영향
- 신규 기능 추가 시 충돌
- 팀 협업 불가능
- 유지보수 비용 폭증

**즉시 수정 필요**:
```python
# 현재 구조 (위험)
app.py (3,352줄)
  ├── 라우팅 로직
  ├── 사이드바 구성
  ├── 30개 이상 페이지 렌더링
  └── 공통 로직

# 목표 구조 (안전)
app.py (200줄 이하)
  ├── 라우팅만
  └── 페이지 모듈 import

ui_pages/
  ├── home/
  ├── design_lab/
  ├── strategy/
  └── ...
```

#### 2. 빈 DataFrame 접근 위험 (50개 이상)
**위험도**: 🔴🔴🔴  
**위치**: 전역 (50개 `.iloc[0]` 사용)  
**문제점**:
- `df.iloc[0]` 호출 전 빈 DataFrame 체크 누락
- 신규 사용자 데이터 입력 전 페이지 접근 시 즉시 크래시
- 필터링 결과 없을 때 IndexError

**즉시 수정 필요 위치**:
- `ui_pages/home/home_data.py`: 2개
- `ui_pages/strategy/strategy_cards.py`: 1개
- `ui_pages/ingredient_management.py`: 2개
- `ui_pages/menu_profit_design_lab.py`: 1개
- `ui_pages/settlement_actual.py`: 1개
- `src/analytics.py`: 5개
- 기타 다수

**해결 방안**:
```python
# src/ui_helpers.py에 추가
def safe_get_first_row(df: pd.DataFrame, default=None):
    """안전하게 첫 번째 행 가져오기"""
    if df.empty:
        return default if default is not None else pd.Series()
    return df.iloc[0]

# 모든 사용처 변경
# 기존: menu_info = menu_df[menu_df['메뉴명'] == name].iloc[0]
# 수정: menu_info = safe_get_first_row(menu_df[menu_df['메뉴명'] == name])
```

#### 3. 트랜잭션 부재 (데이터 무결성 위험)
**위험도**: 🔴🔴🔴  
**위치**: `src/storage_supabase.py` - 모든 save 함수들  
**문제점**:
- `save_daily_close()`: 4개 테이블 저장 시 원자성 보장 없음
- 부분 실패 시 데이터 불일치 발생
- 복구 불가능한 상태 가능

**즉시 수정 필요 함수**:
- `save_daily_close()` - daily_close + sales + visitors + daily_sales_items
- `save_sales_entry()` - sales + naver_visitors 동기화
- `save_daily_sales_item()` - UPSERT + audit

**해결 방안**:
```python
# 이미 RPC 함수 존재: sql/save_daily_close_transaction.sql
# Python에서 호출만 변경 필요

def save_daily_close(...):
    """트랜잭션으로 daily_close 저장"""
    try:
        supabase.rpc('save_daily_close_transaction', {
            'p_date': date.isoformat(),
            'p_store_id': store_id,
            # ... 기타 파라미터
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Daily close 저장 실패: {e}")
        raise
```

#### 4. 과도한 st.rerun() 사용 (296회)
**위험도**: 🔴🔴  
**위치**: 전역 (296개 rerun 호출)  
**문제점**:
- 버튼 클릭마다 전체 페이지 리렌더링
- 성능 저하 (특히 데이터 로딩 많은 페이지)
- 사용자 경험 저하 (깜빡임, 느린 반응)

**주요 발생 위치**:
- `ui_pages/home/home_page.py`: 20개
- `ui_pages/home/home_v3_zones.py`: 15개
- `app.py`: 30개
- `ui_pages/strategy/strategy_board.py`: 4개
- 기타 다수

**해결 방안**:
- 상태 변경만으로 반영되는 경우 rerun 제거
- 캐시 무효화만 하고 rerun 생략
- 필요한 경우에만 선택적 rerun

#### 5. 예외 처리 불일치 (에러 삼킴)
**위험도**: 🔴🔴  
**위치**: 전역 (20개 이상 `except: pass`)  
**문제점**:
- 에러를 삼켜버려 사용자가 문제 인지 못함
- 디버깅 어려움
- 데이터 로드 실패 시 "데이터 없음"으로 오인

**해결 방안**:
- 모든 예외 로깅
- 사용자에게 명확한 에러 메시지
- 빈 DataFrame 반환 대신 에러 상태 명시

---

### 🟡 HIGH (출시 전 필수)

#### 6. session_state 오염 위험
**위험도**: 🟡🟡  
**위치**: 전역  
**문제점**:
- session_state 키 네이밍 불일치
- 페이지 간 상태 공유로 인한 충돌
- 온보딩 상태 캐싱 로직 복잡

**해결 방안**:
- session_state 키 네이밍 컨벤션 수립
- 페이지별 namespace 분리
- 상태 초기화 함수 표준화

#### 7. 동시성 문제 (Optimistic Locking 없음)
**위험도**: 🟡🟡  
**위치**: 모든 save 함수들  
**문제점**:
- 여러 사용자가 동시 수정 시 마지막 쓰기만 유지
- 데이터 손실 위험

**해결 방안**:
- `updated_at` 타임스탬프 기반 충돌 감지
- 수정 전 데이터 버전 체크
- 충돌 시 사용자에게 알림

#### 8. 캐시 전략 단순화
**위험도**: 🟡  
**위치**: `src/storage_supabase.py`  
**문제점**:
- 모든 데이터에 동일 TTL(60초) 적용
- 마스터 데이터(메뉴, 재료)와 트랜잭션 데이터(매출) 동일 처리

**해결 방안**:
- 마스터 데이터: TTL=3600 (1시간)
- 트랜잭션 데이터: TTL=60 (1분)

#### 9. 온보딩 프로세스 복잡도
**위험도**: 🟡  
**위치**: `app.py` 상단 (90줄 이상)  
**문제점**:
- 온보딩 체크 로직이 app.py에 직접 구현
- 세션 캐싱 로직 복잡
- 에러 처리 시 재체크 방지 로직 복잡

**해결 방안**:
- 온보딩 로직을 별도 모듈로 분리
- 상태 머신 패턴 적용
- 명확한 에러 복구 경로

#### 10. 데이터 로딩 전략 부재
**위험도**: 🟡  
**위치**: 전역  
**문제점**:
- 페이지 로드 시 모든 데이터 한 번에 로드
- 사용하지 않는 탭의 데이터도 로드
- 초기 로딩 시간 증가

**해결 방안**:
- 지연 로딩 (Lazy Loading) 적용
- 탭 진입 시에만 데이터 로드

---

### 🟢 MEDIUM (출시 후 개선)

#### 11. 코드 중복
**위험도**: 🟢  
**위치**: 전역  
**문제점**:
- 유사한 로직이 여러 곳에 반복
- DataFrame 처리 패턴 중복

#### 12. 로깅 시스템 부족
**위험도**: 🟢  
**위치**: 전역  
**문제점**:
- 에러 로깅은 있으나 비즈니스 로직 로깅 부족
- 구조화된 로깅 없음

#### 13. 테스트 코드 부재
**위험도**: 🟢  
**위치**: 전체 코드베이스  
**문제점**:
- 단위 테스트 없음
- 통합 테스트 없음

---

### 🔵 LOW (나중에)

#### 14. 벡터화 연산 미활용
#### 15. 에러 메시지 일관성 부족
#### 16. 사용자 매뉴얼 부재

---

## 3️⃣ 구조 리빌드 제안

### 현재 구조 문제점

```
app.py (3,352줄) ← 모든 것이 여기에
├── 라우팅
├── 사이드바
├── 30개 이상 페이지 렌더링
└── 공통 로직
```

### 제안하는 구조

```
app.py (200줄 이하)
├── 라우팅만
└── 페이지 모듈 import

ui_pages/
├── home/
│   ├── home_page.py (메인)
│   ├── home_data.py
│   ├── home_v3_zones.py
│   └── home_verdict.py
├── design_lab/
│   ├── design_center.py
│   ├── design_lab_frame.py
│   └── ...
├── strategy/
│   ├── strategy_board.py
│   ├── strategy_cards.py
│   └── ...
└── common/
    ├── routing.py (라우팅 로직)
    ├── sidebar.py (사이드바 구성)
    └── guards.py (가드 함수)

src/
├── storage_supabase.py (데이터 저장/로드)
├── analytics.py (분석 계산)
└── validators.py (입력 검증) ← 신규
```

### 파일 구조 재편안

#### Phase 1: app.py 분리
1. **라우팅 모듈 분리**
   ```python
   # ui_pages/common/routing.py
   def get_current_page():
       """현재 페이지 반환"""
       return st.session_state.get('current_page', '홈')
   
   def navigate_to(page: str):
       """페이지 이동"""
       st.session_state.current_page = page
       st.rerun()
   ```

2. **사이드바 모듈 분리**
   ```python
   # ui_pages/common/sidebar.py
   def render_sidebar():
       """사이드바 렌더링"""
       # 사이드바 구성 로직
   ```

3. **app.py 최소화**
   ```python
   # app.py (200줄 이하)
   from ui_pages.common.routing import get_current_page
   from ui_pages.common.sidebar import render_sidebar
   
   # 인증/온보딩 체크
   # 사이드바 렌더링
   # 페이지 라우팅만
   ```

#### Phase 2: 페이지 책임 분리
- 각 페이지는 독립적인 모듈
- 페이지 간 의존성 최소화
- 공통 컴포넌트는 `ui_pages/common/`에

#### Phase 3: 데이터 책임 분리
- 데이터 저장/로드: `src/storage_supabase.py`
- 분석 계산: `src/analytics.py`
- 입력 검증: `src/validators.py` (신규)

---

## 4️⃣ Phase 로드맵

### Phase 0: 안정화 (2-3주) ← **출시 전 필수**

**목표**: 크래시 방지, 데이터 무결성 보장

**해야 할 작업**:
1. ✅ **빈 DataFrame 안전 접근** (3일)
   - `safe_get_first_row()` 함수 생성
   - 모든 `.iloc[0]` 사용처 변경 (50개)
   - 테스트: 빈 데이터 상태에서 모든 페이지 접근

2. ✅ **트랜잭션 함수 적용** (3일)
   - `save_daily_close()` RPC 함수 호출로 변경
   - `save_sales_entry()` 트랜잭션 래핑
   - 테스트: 부분 실패 시나리오

3. ✅ **app.py 모듈 분리** (5일)
   - 라우팅 모듈 분리
   - 사이드바 모듈 분리
   - app.py 200줄 이하로 축소
   - 테스트: 모든 페이지 정상 동작 확인

4. ✅ **rerun 최적화** (3일)
   - 불필요한 rerun 제거 (50% 이상 감소)
   - 상태 변경만으로 반영되는 경우 rerun 생략
   - 테스트: 버튼 클릭 반응 속도 확인

5. ✅ **예외 처리 개선** (2일)
   - `except: pass` 제거
   - 모든 예외 로깅
   - 사용자 친화적 에러 메시지

**확인 사항**:
- [ ] 빈 데이터 상태에서 모든 페이지 접근 가능
- [ ] 부분 저장 실패 시 데이터 불일치 없음
- [ ] app.py 200줄 이하
- [ ] rerun 호출 150개 이하
- [ ] 모든 예외가 로깅됨

---

### Phase 1: 사장 MVP 완성 (1-2주)

**목표**: 사장이 매일 사용할 수 있는 최소 기능 완성

**해야 할 작업**:
1. **홈 페이지 안정화**
   - 전략 카드 로딩 실패 시 graceful fallback
   - 데이터 부족 시 안내 메시지

2. **일일 입력 통합 안정화**
   - 저장 실패 시 복구 가이드
   - 부분 저장 방지

3. **온보딩 프로세스 개선**
   - 온보딩 로직 모듈 분리
   - 명확한 에러 복구 경로

4. **성능 최적화**
   - 캐시 TTL 분리
   - 지연 로딩 적용

**확인 사항**:
- [ ] 신규 사용자가 5분 안에 첫 입력 완료
- [ ] 홈 페이지 3초 이내 로딩
- [ ] 일일 입력 저장 실패 없음

---

### Phase 2: 제품화 (2-3주)

**목표**: SaaS 수준의 완성도

**해야 할 작업**:
1. **동시성 제어**
   - Optimistic Locking 도입
   - 충돌 감지 및 알림

2. **에러 복구 메커니즘**
   - 저장 실패 시 "다시 시도" 버튼
   - 부분 실패 시 상태 표시

3. **로깅 시스템 강화**
   - 구조화된 로깅
   - 비즈니스 이벤트 로깅

4. **모니터링 구축**
   - 에러 추적
   - 성능 모니터링

**확인 사항**:
- [ ] 동시 수정 시 충돌 감지
- [ ] 모든 에러가 추적됨
- [ ] 성능 지표 수집

---

### Phase 3: SaaS화 (1-2개월)

**목표**: 멀티 테넌시, 확장성, 운영 자동화

**해야 할 작업**:
1. **멀티 테넌시 강화**
   - RLS 정책 최적화
   - 데이터 격리 검증

2. **확장성 개선**
   - 데이터베이스 인덱스 최적화
   - 쿼리 성능 개선

3. **운영 자동화**
   - CI/CD 파이프라인
   - 자동 배포

4. **사용자 지원**
   - 사용자 매뉴얼
   - 온보딩 튜토리얼

**확인 사항**:
- [ ] 100개 이상 매장 동시 운영 가능
- [ ] 자동 배포 파이프라인 구축
- [ ] 사용자 매뉴얼 완성

---

## 5️⃣ 바로 실행할 "첫 5개 수정 작업"

### 작업 1: safe_get_first_row() 함수 생성
**파일**: `src/ui_helpers.py`  
**수정 목적**: 빈 DataFrame 접근 위험 제거  
**상태**: ✅ **이미 구현됨**

**현재 상태 확인**:
- `safe_get_first_row()` 함수가 이미 `src/ui_helpers.py`에 존재
- `safe_get_value()`, `safe_get_row_by_condition()` 함수도 함께 구현됨
- 추가 작업: 모든 `.iloc[0]` 사용처를 이 함수로 변경 필요 (50개 이상)

**다음 단계**:
- [ ] 모든 `.iloc[0]` 사용처를 `safe_get_first_row()`로 변경
- [ ] 빈 데이터 상태에서 모든 페이지 접근 테스트

---

### 작업 2: save_daily_close() 트랜잭션 적용
**파일**: `src/storage_supabase.py`  
**수정 목적**: 데이터 무결성 보장  
**상태**: ✅ **이미 구현됨** (RPC 함수 사용 중)

**현재 상태 확인**:
- `save_daily_close()` 함수는 이미 `save_daily_close_transaction` RPC 함수를 사용
- 트랜잭션 보장됨
- 추가 작업 불필요

**확인 사항**:
- [x] RPC 함수 호출 확인
- [x] 트랜잭션 보장 확인
- [ ] 부분 실패 시나리오 테스트 필요

---

### 작업 3: app.py 라우팅 모듈 분리
**파일**: `ui_pages/common/routing.py` (신규), `app.py` (수정)  
**수정 목적**: app.py 비대화 해결  
**성공 기준**: app.py 500줄 이하, 모든 페이지 정상 동작

```python
# ui_pages/common/routing.py (신규)
def get_current_page():
    """현재 페이지 반환"""
    return st.session_state.get('current_page', '홈')

def navigate_to(page: str):
    """페이지 이동"""
    st.session_state.current_page = page
    st.rerun()

# app.py 수정 (라우팅만)
from ui_pages.common.routing import get_current_page, navigate_to

page = get_current_page()
if page == "홈":
    from ui_pages.home.home_page import render_home_page
    render_home_page()
elif page == "일일 입력(통합)":
    from ui_pages.daily_input_hub import render_daily_input_hub
    render_daily_input_hub()
# ...
```

---

### 작업 4: rerun 최적화 (홈 페이지)
**파일**: `ui_pages/home/home_v3_zones.py`  
**수정 목적**: 성능 개선, UX 개선  
**성공 기준**: 버튼 클릭 반응 속도 50% 이상 개선

```python
# 불필요한 rerun 제거
# 상태 변경만으로 반영되는 경우 rerun 생략

# 기존
if st.button("실행하기"):
    # 상태 변경
    st.session_state.some_state = value
    st.rerun()  # ← 제거 가능

# 수정
if st.button("실행하기"):
    # 상태 변경만 (rerun 없이 자동 반영)
    st.session_state.some_state = value
    # 필요한 경우에만 rerun
```

---

### 작업 5: 예외 처리 개선 (storage_supabase.py)
**파일**: `src/storage_supabase.py`  
**수정 목적**: 에러 추적 가능하도록  
**상태**: ✅ **부분 완료** (2개 수정)

**수정 완료**:
- `save_sales()` 함수의 `except: pass` → `logger.warning()` 변경
- 성능 스냅샷 예외 처리 개선

**추가 작업 필요**:
- [ ] 다른 파일의 `except: pass` 패턴 검색 및 수정
- [ ] 모든 예외가 로깅되는지 확인

---

## 📊 제품 관점 평가

### A. 첫인상 구조

**현재 상태**: 🟡 **부분적 양호**

**긍정적**:
- 홈 페이지 "오늘의 운영 지시" 중심 구조 좋음
- 사이드바 카테고리 구조 직관적
- 일일 입력 통합으로 사용 편의성 향상

**문제점**:
- 신규 사용자 데이터 입력 전 홈 접근 시 크래시
- 온보딩 프로세스 복잡 (90줄 이상 로직)
- 첫 사용 시 가이드 부재

**개선 필요**:
- 빈 데이터 상태 graceful fallback
- 온보딩 튜토리얼 추가
- 첫 방문 가이드

---

### B. 기능 레벨 평가

**현재 상태**: 🟢 **MVP 기준 충분**

**핵심 기능 완성도**:
- ✅ 일일 입력: 완성
- ✅ 홈 (운영 지시): 완성
- ✅ 전략 보드: 완성
- ✅ 설계실 4개: 완성
- ✅ 매출 하락 원인 찾기: 완성

**불필요하게 복잡한 곳**:
- 온보딩 로직 (app.py에 90줄)
- session_state 관리 (네이밍 불일치)

**비어있는 핵심 가치**:
- 없음 (모든 핵심 기능 구현됨)

---

### C. 제품 리스크

**사장이 쓰다 포기할 지점**:
1. **빈 데이터 접근 시 크래시** ← 최우선 해결
2. **저장 실패 시 복구 불가** ← 트랜잭션 적용 필요
3. **느린 반응 속도** ← rerun 최적화 필요

**설명 없으면 못 쓰는 구조**:
- 없음 (UI가 직관적)

**숫자 코치 컨셉과 어긋난 부분**:
- 없음 (컨셉 잘 구현됨)

---

## 🎯 최종 권장사항

### 즉시 실행 (1주일 내)
1. ✅ 빈 DataFrame 안전 접근 (작업 1)
2. ✅ 트랜잭션 함수 적용 (작업 2)
3. ✅ app.py 모듈 분리 시작 (작업 3)

### 단기 개선 (2-3주 내)
4. ✅ rerun 최적화
5. ✅ 예외 처리 개선
6. ✅ 온보딩 프로세스 개선

### 중기 개선 (1-2개월 내)
7. ✅ 동시성 제어
8. ✅ 성능 최적화
9. ✅ 모니터링 구축

---

**리포트 작성자**: 프로덕션 감리 엔지니어  
**다음 리뷰**: Phase 0 완료 후
