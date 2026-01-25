# P4: 입력 컴포넌트 제품화 + 시각 스펙 통합 문서

## 📌 목적

입력센터 전 페이지의 모든 입력 UI를  
**"사장 전용 숫자 코치" 앱에 맞는 제품급 입력 컴포넌트 시스템(FormKit v2)** 으로 통합

---

## 🎯 최종 목표

입력센터의 모든 숫자는  
"그냥 input"이 아니라  
👉 **'계기판'처럼 보이고, '의미 단위'처럼 느껴지게 한다.**

---

## 🧱 FormKit v2 컴포넌트 등급 체계

### ✅ A. Primary Input (핵심 수치)

**대상**:
- 매출
- 비용
- 목표 매출/비용
- 판매량
- 사용량
- 재고 수량

**컴포넌트**:
- `ps_primary_money_input()` - 금액 입력
- `ps_primary_quantity_input()` - 수량 입력
- `ps_primary_ratio_input()` - 비율 입력

**특징**:
- 가장 크고 진하게 (height: 56px, font-size: 22px, font-weight: 600)
- 단위가 시각적으로 분리됨 (우측 고정 단위 박스)
- 입력 즉시 "의미"가 느껴져야 함
- 포커스 시 테두리 + 글로우
- 0 / 음수 / 비정상값 시 상태 표시 (warn/danger)

---

### ✅ B. Secondary Input (조정/조건 입력)

**대상**:
- 날짜/월 선택
- 카테고리
- 상태
- 옵션

**컴포넌트**:
- `ps_secondary_select()` - 선택 입력
- `ps_secondary_date()` - 날짜 입력
- `ps_secondary_toggle()` - 토글 입력

**특징**:
- 높이 통일 (height: 40px)
- Primary보다 명도/대비 낮음
- 한 줄 정렬 기본

---

### ✅ C. Tertiary Input (설명/보조)

**대상**:
- 메모
- 조리법
- 비고
- 참고 입력

**컴포넌트**:
- `ps_note_input()` - 메모 입력
- `ps_text_block()` - 텍스트 블록

**특징**:
- 시각적 우선순위 가장 낮음
- 접히거나 카드 하단
- Primary 입력을 방해하지 않음

---

## 🎨 시각 스펙

### Primary Input 시각 스펙

**크기**:
- height: 56px
- font-size: 22px
- font-weight: 600

**색**:
- text: #F8FAFC
- placeholder: rgba(248,250,252,0.35)

**배경**:
- 기본: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03))
- 포커스: 
  - border: 1px solid rgba(96,165,250,0.9)
  - box-shadow: 0 0 0 3px rgba(59,130,246,0.25), 0 6px 20px rgba(0,0,0,0.4)

**단위 박스**:
- 우측 고정
- background: rgba(255,255,255,0.06)
- font-size: 13px
- padding: 0 10px
- border-left: 1px solid rgba(255,255,255,0.12)

**상태 표현**:
- 정상: blue glow
- 경고(0, 부족): amber border
- 위험(초과, 음수): red glow

---

### Secondary Input 시각 스펙

- height: 40px
- font-size: 14px
- background: rgba(255,255,255,0.04)
- border: 1px solid rgba(255,255,255,0.12)
- focus 시 outline만 표시

---

### Input Block 스펙

**구조**:
```
[ 제목 ]
[ 설명 ]
[ 🔢 PRIMARY INPUT ][ 단위 ]
[ 즉시 피드백 / 상태 ]
[ 경고 / 참고 ]
```

**시각 규칙**:
- 블록 간 간격: 16px
- 내부 패딩: 16px
- 라벨 font-size: 13px
- 설명 opacity: 0.65
- 카드 배경: rgba(255,255,255,0.02)
- border: 1px solid rgba(255,255,255,0.08)
- radius: 14px

---

## 🔁 입력 리듬 시스템

### 공통 컴포넌트

- `ps_input_block()` - 입력 블록 컨테이너
- `ps_inline_feedback()` - 즉시 피드백
- `ps_inline_warning()` - 인라인 경고
- `ps_input_status_badge()` - 입력 상태 배지

### 저장 리듬 규칙

- 페이지 내 저장 버튼 전면 금지
- 저장 CTA는 Action Bar만 사용
- 입력 영역은 "작성", 하단은 "결정"

---

## 📦 파일 구조

```
src/ui/components/
├── form_kit.py (기존 v1)
└── form_kit_v2.py (신규 v2)
```

---

## ✅ 완료 기준

**구조**:
- FormKit v2 파일 생성 ✅
- Primary/Secondary/Tertiary 구분 존재 ✅

**시각**:
- 핵심 숫자가 가장 먼저 보임
- 단위가 입력칸과 분리됨
- 입력 시 상태가 즉시 보임

**코드**:
- 페이지는 컴포넌트 호출만
- 스타일은 입력 전용 스코프
- rerun 후 유지 확인

---

## 🧪 파일럿 적용 페이지

**settlement_actual.py** (파일럿)

**적용 내용**:
- 총매출 입력 → `ps_primary_money_input` 교체 ✅
- 비용 항목 금액 입력 → `ps_primary_money_input` 교체 ✅
- 비용 항목 비율 입력 → `ps_primary_ratio_input` 교체 ✅
- 새 항목 금액 입력 → `ps_primary_money_input` 교체 ✅
- 새 항목 비율 입력 → `ps_primary_ratio_input` 교체 ✅
- KPI 카드 → `ps_inline_feedback` 적용 ✅
- 계산 금액 피드백 → `ps_inline_feedback` 적용 ✅

---

## 🎯 최종 제품 문장

"이 앱은  
입력하는 순간부터  
이미 분석이 시작된 느낌이 나야 한다."
