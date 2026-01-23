# 홈 Step 9 UI 위계 정리 완료 요약

## 목표
홈 화면을 더 짧고 덜 피로하게 만들기 (정보는 유지, 시각적 위계만 정리)

## 구현 완료 사항

### 1. 첫 화면 구성 고정 (스크롤 0~1회)
✅ **구성 순서**:
1. 빠른 이동 (3개 버튼)
2. 상태 요약 (5 KPI 카드)
3. 이상 징후 (최대 2개)
4. 문제 TOP1 / 잘한 점 TOP1

✅ **Coach Only 섹션은 첫 화면 이후로 이동**:
- 성장 단계 메시지 (DAY1/DAY3/DAY7)
- 코치 모드 환영
- 시작 미션 3개
- 오늘 코치의 한 가지 제안

### 2. 색상 정책 단순화

#### KPI 카드 (중립 톤)
- **Before**: 각 카드마다 다른 그라데이션 (보라, 핑크, 파랑, 초록 등)
- **After**: 통일된 중립 톤
  - 배경: `#ffffff` (흰색)
  - 테두리: `1px solid #e9ecef` (연한 회색)
  - 텍스트: `#212529` (진한 회색), `#6c757d` (중간 회색)
  - 그라데이션 제거

#### 경고/이상징후/문제 (강조색 유지)
- **문제**: `#fff5f5` 배경, `#fecaca` 테두리, `#dc3545` 왼쪽 강조선
- **이상 징후**: `#fffbeb` 배경, `#fef3c7` 테두리, `#ffc107` 왼쪽 강조선
- **색상 강조 유지** (시각적 중요도 표현)

#### 잘한 점 (긍정 강조 유지)
- **잘한 점**: `#f0fdf4` 배경, `#bbf7d0` 테두리, `#28a745` 왼쪽 강조선
- **긍정 강조 유지**

### 3. 카드 레이아웃 정렬

#### KPI 카드 통일 스타일
```css
- 높이: 120px 고정
- 패딩: 1.2rem
- 폰트 크기:
  - Label: 0.85rem, color: #6c757d, font-weight: 500
  - Value: 1.4rem, color: #212529, font-weight: 700
  - Subtitle: 0.75rem, color: #6c757d
- 배경: #ffffff
- 테두리: 1px solid #e9ecef
- border-radius: 8px
- 정렬: 중앙, flexbox (세로 중앙 정렬)
```

#### 금액/단위 표기 통일
- 모든 금액: 천단위 콤마 + "원" (예: `1,234,567원`)
- 마감률: 백분율 + "일" 정보 (예: `85%`, subtitle: `15/18일 🔥3일`)
- 빈 값: "-" 표시

#### 문제/잘한 점/이상 징후 카드
```css
- 패딩: 1rem (기본), 0.8rem (확장 영역)
- 배경: 연한 색상 (문제: #fff5f5, 잘한점: #f0fdf4, 이상징후: #fffbeb)
- 테두리: 1px solid + 왼쪽 강조선 4px
- border-radius: 8px
- 폰트: 0.95rem (기본), 0.9rem (확장)
- margin-bottom: 0.5rem
```

### 4. 버튼 스타일 일관성
- 모든 버튼: `use_container_width=True` (일관된 너비)
- Primary 버튼: 빠른 이동, 주요 액션
- 일반 버튼: "보러가기", "자세히 보기"

### 5. Lazy/expander 구조 유지
- ✅ 기능 변경 없음
- "인사이트 더보기" expander 유지
- "자세히 보기" expander 유지

---

## 변경한 CSS/컴포넌트 요약

### 1. `_kpi_card_unified()` 함수 (신규)
**위치**: `ui_pages/home/home_page.py`

**스타일**:
```css
padding: 1.2rem;
background: #ffffff;
border: 1px solid #e9ecef;
border-radius: 8px;
height: 120px;
display: flex;
flex-direction: column;
justify-content: center;
```

**폰트**:
- Label: `0.85rem, color: #6c757d, font-weight: 500`
- Value: `1.4rem, color: #212529, font-weight: 700`
- Subtitle: `0.75rem, color: #6c757d`

### 2. 문제 카드 스타일 변경
**Before**:
```css
background: #f8d7da;
border-left: 4px solid #dc3545;
```

**After**:
```css
background: #fff5f5;
border: 1px solid #fecaca;
border-left: 4px solid #dc3545;
font-size: 0.95rem;
```

### 3. 잘한 점 카드 스타일 변경
**Before**:
```css
background: #d4edda;
border-left: 4px solid #28a745;
```

**After**:
```css
background: #f0fdf4;
border: 1px solid #bbf7d0;
border-left: 4px solid #28a745;
font-size: 0.95rem;
```

### 4. 이상 징후 카드 스타일 변경
**Before**:
```css
background: #fff3cd;
border-left: 4px solid #ffc107;
```

**After**:
```css
background: #fffbeb;
border: 1px solid #fef3c7;
border-left: 4px solid #ffc107;
font-size: 0.95rem;
color: #92400e (텍스트);
```

### 5. 상태 요약 섹션
- **Before**: "상태판" (2개 카드, 큰 그라데이션) + "핵심 숫자 카드" (4개 카드, 각각 다른 그라데이션)
- **After**: "상태 요약" (5개 KPI 카드, 통일된 중립 톤)
  - 이번 달 매출
  - 마감률 (subtitle: 일수/연속일)
  - 오늘 매출
  - 객단가
  - 이번 달 이익

---

## 변경 파일 목록

### 수정 파일
1. `ui_pages/home/home_page.py`
   - `_render_home_body()`: 첫 화면 구성 재배치
   - `_kpi_card_unified()`: 통일된 KPI 카드 스타일 함수 추가
   - `_render_problems_good_points()`: 카드 스타일 단순화
   - `_render_anomaly_signals()`: 카드 스타일 단순화

---

## 첫 화면 구성 (최종)

### 즉시 표시 (스크롤 0~1회)
1. **빠른 이동** (3개 버튼)
2. **상태 요약** (5 KPI 카드 - 중립 톤)
   - 이번 달 매출
   - 마감률
   - 오늘 매출
   - 객단가
   - 이번 달 이익
3. **이상 징후** (최대 2개 - 경량 버전)
4. **문제 TOP1 / 잘한 점 TOP1**

### 첫 화면 이후 (스크롤 필요)
- Coach Only: 성장 단계 메시지, 환영, 미션, 오늘 제안
- Lazy 영역: 미니 차트, 인사이트 더보기 (expander)

---

## 시각적 개선 효과

### Before
- 각 카드마다 다른 그라데이션 (시각적 혼란)
- 상태판과 핵심 숫자 카드 분리 (중복 느낌)
- Coach Only 섹션이 첫 화면에 섞임 (정보 과부하)

### After
- 통일된 중립 톤 KPI 카드 (시각적 일관성)
- 5개 KPI 카드로 통합 (간결함)
- 첫 화면에 핵심 정보만 (명확한 위계)
- Coach Only는 첫 화면 이후 (정보 분리)

---

## 참고사항

- 모든 기능은 변경 없음 (Lazy/expander 구조 유지)
- 색상 강조는 경고/이상징후/문제/잘한점에만 적용
- KPI 카드는 중립 톤으로 통일하여 정보 전달에 집중
- 카드 높이/패딩/폰트 크기 일관성으로 시각적 피로 감소
