# QSC 입력 페이지 리디자인 기획안

**작업 일자**: 2026-01-24  
**목적**: QSC 입력 페이지를 빠르고 안정적이며 사용하기 편하게 업그레이드

---

## 🎯 현재 문제점 분석

### 사용 패턴
- **빈도**: 월 2-3회
- **작업 특성**: 9개 영역, 각 10문항씩 총 90문항을 7-10분 내에 입력
- **중요도**: 매우 높음 (HOME/전략엔진에 반영)

### 현재 UI의 문제점
1. ❌ **느린 입력**: 라디오 버튼이 많아서 렌더링이 느림
2. ❌ **에러 발생**: session_state 관리 복잡, dirty tracking 오류
3. ❌ **불편한 네비게이션**: 9개 탭을 하나씩 클릭해야 함
4. ❌ **저장 불안정**: 임시 저장이 제대로 작동하지 않을 수 있음
5. ❌ **진행 상황 불명확**: 진행률이 정확하지 않을 수 있음
6. ❌ **복잡한 상태 관리**: session_state 키가 너무 많고 복잡함

---

## 🚀 개선 방향

### 핵심 원칙
1. **빠른 입력**: 클릭 한 번으로 답변 가능
2. **안정적인 저장**: 자동 저장 또는 더 나은 저장 방식
3. **명확한 진행 상황**: 실시간 진행률 및 완료 상태 표시
4. **에러 방지**: 단순한 상태 관리, 명확한 에러 처리
5. **직관적인 네비게이션**: 한 화면에서 모든 질문을 볼 수 있도록

---

## 📋 개선안: 3-Zone 구조 (빠른 입력 중심)

### **ZONE A: 대시보드 & 진행 상황**
**목적**: 전체 진행 상황을 한눈에 파악

#### 구성 요소
1. **핵심 지표 카드 (4열)**
   - 전체 문항 수 (90개)
   - 완료 문항 수
   - 미완료 문항 수
   - 완료율 (%)

2. **진행률 바**
   - 전체 진행률: `완료 문항 / 전체 문항 × 100%`
   - 영역별 진행률 (9개 영역)

3. **스마트 알림**
   - 미완료 영역이 있으면 안내 표시
   - 저장되지 않은 변경이 있으면 경고 표시

---

### **ZONE B: 빠른 입력 테이블 (핵심)**
**목적**: 모든 질문을 한 화면에서 빠르게 입력

#### 입력 방식 개선
**옵션 1: 버튼 그리드 방식 (권장)**
- 각 질문마다 3개 버튼 (예/애매함/아니다)
- 클릭 한 번으로 즉시 답변 및 저장
- 선택된 버튼은 색상으로 강조
- 스크롤 가능한 컨테이너

**옵션 2: 체크박스 방식 (대안)**
- 각 질문마다 3개 체크박스 (단일 선택)
- 체크박스 클릭으로 즉시 답변

#### 레이아웃
- **영역별 섹션**: 9개 영역을 섹션으로 구분
- **질문 그리드**: 각 질문을 카드 형태로 표시
- **페이지네이션**: 한 페이지에 20-30개 질문씩 표시 (선택적)

#### 성능 최적화
1. **지연 렌더링**: 보이는 영역만 렌더링
2. **버튼 최적화**: 각 질문마다 독립적인 버튼 키
3. **자동 저장**: 답변 변경 시 즉시 저장 (debounce 적용)

---

### **ZONE C: 저장 & 완료**
**목적**: 저장 상태 확인 및 완료 처리

#### 구성 요소
1. **저장 상태 표시**
   - 저장되지 않은 변경 개수
   - 마지막 저장 시간
   - 저장 성공/실패 표시

2. **완료 버튼**
   - 최소 60개 이상 답변 시 활성화
   - 완료 전 최종 저장 확인
   - 완료 후 결과 페이지로 이동

3. **빠른 액션**
   - 💾 수동 저장 버튼
   - 🔄 초기화 버튼
   - 📊 결과 미리보기

---

## 🎨 UI/UX 디자인

### 레이아웃
```
┌─────────────────────────────────────────┐
│ ZONE A: 대시보드 & 진행 상황            │
│ [지표 카드 4개] [진행률 바] [알림]      │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│ 필터 & 네비게이션 (고정)                │
│ [영역 필터] [검색] [페이지네이션]       │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│ ZONE B: 빠른 입력 테이블 (핵심)        │
│ ┌─────────────────────────────────────┐ │
│ │ [영역 Q]                            │ │
│ │ 질문1 [예] [애매함] [아니다]        │ │
│ │ 질문2 [예] [애매함] [아니다]        │ │
│ │ ...                                 │ │
│ │ [영역 S]                            │ │
│ │ 질문1 [예] [애매함] [아니다]        │ │
│ │ ...                                 │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│ ZONE C: 저장 & 완료                   │
│ [저장 상태] [완료 버튼] [빠른 액션]   │
└─────────────────────────────────────────┘
```

### 색상 체계
- **예** (초록색): #22C55E
- **애매함** (노란색): #F59E0B
- **아니다** (빨간색): #EF4444
- **선택 안 함** (회색): #9CA3AF
- **선택됨** (강조): 파란색 배경 (#3B82F6)

---

## 🔄 데이터 흐름

### 1. 초기 로드
1. 세션 확인 (진행 중인 세션 또는 새 세션 생성)
2. 기존 답변 로드 (DB에서)
3. session_state 초기화
4. 화면 렌더링

### 2. 답변 입력
1. 사용자가 버튼 클릭
2. 즉시 session_state 업데이트
3. debounce 후 자동 저장 (또는 수동 저장)
4. 진행률 자동 업데이트

### 3. 저장
1. 변경된 답변만 추출
2. 배치 저장 (upsert_health_answers_batch)
3. 저장 성공 시 dirty 비우기
4. 저장 시간 업데이트

### 4. 완료
1. 최소 60개 이상 답변 확인
2. 마지막 저장 실행
3. finalize_health_session 호출
4. 결과 페이지로 이동

---

## 📊 구현 상세

### 버튼 그리드 방식 (권장)

```python
def render_question_buttons(store_id, session_id, category, question_code, question_text):
    """질문별 버튼 그리드 렌더링"""
    # 현재 답변 가져오기
    key = (category, question_code)
    current_value = st.session_state.get('hc_answers', {}).get(key)
    
    # 버튼 옵션
    options = [
        ("예", "yes", "#22C55E"),
        ("애매함", "maybe", "#F59E0B"),
        ("아니다", "no", "#EF4444")
    ]
    
    # 질문 텍스트
    st.markdown(f"**{question_code}** {question_text}")
    
    # 버튼 그리드
    cols = st.columns(3)
    for idx, (label, raw_value, color) in enumerate(options):
        with cols[idx]:
            is_selected = current_value == raw_value
            button_type = "primary" if is_selected else "secondary"
            
            if st.button(
                label,
                key=f"qsc_btn_{session_id}_{category}_{question_code}_{raw_value}",
                type=button_type,
                use_container_width=True
            ):
                # 답변 업데이트
                if 'hc_answers' not in st.session_state:
                    st.session_state['hc_answers'] = {}
                st.session_state['hc_answers'][key] = raw_value
                
                # dirty에 추가
                if 'hc_dirty' not in st.session_state:
                    st.session_state['hc_dirty'] = set()
                st.session_state['hc_dirty'].add(key)
                
                # 자동 저장 (debounce)
                st.session_state['qsc_auto_save_trigger'] = True
                st.rerun()
```

### 자동 저장 (debounce)

```python
def _auto_save_with_debounce(store_id, session_id):
    """자동 저장 (debounce 적용)"""
    if st.session_state.get('qsc_auto_save_trigger', False):
        # debounce: 1초 대기
        import time
        if 'qsc_last_save_time' not in st.session_state:
            st.session_state['qsc_last_save_time'] = time.time()
        
        current_time = time.time()
        if current_time - st.session_state['qsc_last_save_time'] > 1.0:
            # 저장 실행
            success, error_msg = _save_answers_batch(store_id, session_id)
            if success:
                st.session_state['qsc_last_save_time'] = current_time
                st.session_state['qsc_auto_save_trigger'] = False
```

### 페이지네이션 (선택적)

```python
def render_questions_with_pagination(store_id, session_id, all_questions):
    """질문 페이지네이션"""
    items_per_page = 20
    total_items = len(all_questions)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    current_page = st.session_state.get('qsc_page', 1)
    
    # 페이지네이션 컨트롤
    if total_pages > 1:
        col_prev, col_page, col_next = st.columns([1, 10, 1])
        with col_prev:
            if st.button("◀ 이전", key="qsc_page_prev", disabled=(current_page == 1)):
                st.session_state['qsc_page'] = current_page - 1
                st.rerun()
        with col_page:
            st.write(f"**페이지 {current_page} / {total_pages}**")
        with col_next:
            if st.button("다음 ▶", key="qsc_page_next", disabled=(current_page == total_pages)):
                st.session_state['qsc_page'] = current_page + 1
                st.rerun()
    
    # 현재 페이지 질문만 렌더링
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_questions = all_questions[start_idx:end_idx]
    
    for question in page_questions:
        render_question_buttons(store_id, session_id, question['category'], 
                                question['code'], question['text'])
```

---

## ⚡ 성능 최적화

### 1. 렌더링 최적화
- **지연 렌더링**: 보이는 영역만 렌더링
- **버튼 최적화**: 독립적인 키 사용
- **페이지네이션**: 한 번에 20-30개만 렌더링

### 2. 저장 최적화
- **자동 저장**: debounce 적용 (1초)
- **배치 저장**: 변경된 답변만 저장
- **비동기 저장**: 저장 중에도 입력 가능 (선택적)

### 3. 상태 관리 최적화
- **단순한 구조**: session_state 키 최소화
- **명확한 네이밍**: `qsc_` 접두사 사용
- **에러 방지**: try-except로 안전하게 처리

---

## 🔧 구현 체크리스트

### ZONE A: 대시보드 & 진행 상황
- [ ] 핵심 지표 카드 (4개)
- [ ] 전체 진행률 바
- [ ] 영역별 진행률 표시
- [ ] 스마트 알림

### ZONE B: 빠른 입력 테이블
- [ ] 영역별 섹션 구분
- [ ] 질문별 버튼 그리드 (3개 버튼)
- [ ] 선택 상태 시각적 피드백
- [ ] 페이지네이션 (선택적)
- [ ] 필터 & 검색

### ZONE C: 저장 & 완료
- [ ] 저장 상태 표시
- [ ] 자동 저장 (debounce)
- [ ] 수동 저장 버튼
- [ ] 완료 버튼
- [ ] 빠른 액션

### 성능 최적화
- [ ] 지연 렌더링
- [ ] 버튼 최적화
- [ ] 자동 저장 최적화
- [ ] 상태 관리 최적화

### 에러 방지
- [ ] try-except 블록 추가
- [ ] 명확한 에러 메시지
- [ ] 저장 실패 시 재시도
- [ ] 세션 상태 검증

---

## 🚀 향후 개선 사항

### Phase 2 (권장)
- [ ] 키보드 단축키 지원 (1/2/3 키로 답변)
- [ ] 진행 상황 저장 (브라우저 종료해도 유지)
- [ ] 답변 히스토리 (이전 답변과 비교)
- [ ] 빠른 답변 모드 (모든 질문에 동일 답변)

### Phase 3 (선택)
- [ ] 음성 입력 지원
- [ ] 모바일 최적화
- [ ] 오프라인 모드
- [ ] 답변 패턴 분석

---

## 📝 주의사항

1. **DB 연결 확인**
   - health_check_sessions 테이블 존재 확인
   - health_check_answers 테이블 존재 확인
   - 저장 함수 정상 작동 확인

2. **상태 관리 단순화**
   - session_state 키 최소화
   - 명확한 네이밍
   - 에러 방지 로직 추가

3. **성능 고려**
   - 90개 질문을 한 번에 렌더링하면 느릴 수 있음
   - 페이지네이션 또는 지연 렌더링 고려
   - 버튼 키 최적화

4. **자동 저장**
   - debounce 적용 (너무 자주 저장하지 않도록)
   - 저장 실패 시 재시도 로직
   - 저장 상태 명확히 표시

---

**작성일**: 2026-01-24  
**담당**: QSC 입력 페이지 리디자인 기획
