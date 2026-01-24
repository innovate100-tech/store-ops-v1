"""
Action Plan Engine v1 - 실행 플랜 생성
전략 타입별 이번 주 실행 체크리스트 생성
"""
from typing import Dict, List


def build_action_plan(strategy_type: str, context: Dict) -> Dict:
    """
    전략별 실행 플랜 생성
    
    Args:
        strategy_type: "SURVIVAL" | "MARGIN" | "COST" | "PORTFOLIO" | "ACQUISITION" | "OPERATIONS"
        context: {
            "store_id": ...,
            "period": {"year":..., "month":...},
            ...
        }
    
    Returns:
        {
            "time_horizon": "1주"|"2주"|"즉시",
            "difficulty": "낮음"|"중간"|"높음",
            "steps": [
                {"text": "...", "eta_min": 20, "done_when": "..."},
                ...
            ],
            "watchouts": ["...", "..."],
            "required_pages": [{"label":"...", "page_key":"..."}]
        }
    """
    if strategy_type == "SURVIVAL":
        return _build_survival_plan(context)
    elif strategy_type == "MARGIN":
        return _build_margin_plan(context)
    elif strategy_type == "COST":
        return _build_cost_plan(context)
    elif strategy_type == "PORTFOLIO":
        return _build_portfolio_plan(context)
    elif strategy_type == "ACQUISITION":
        return _build_acquisition_plan(context)
    elif strategy_type == "OPERATIONS":
        return _build_operations_plan(context)
    else:
        return _get_empty_plan()


def _build_survival_plan(context: Dict) -> Dict:
    """SURVIVAL 전략 실행 플랜"""
    return {
        "time_horizon": "1주",
        "difficulty": "중간",
        "steps": [
            {
                "text": "손익분기점 계산 확인 (수익 구조 설계실)",
                "eta_min": 10,
                "done_when": "손익분기점과 예상 매출 차이 확인"
            },
            {
                "text": "고정비 항목 Top3 점검 (임차료/인건비/공과금)",
                "eta_min": 20,
                "done_when": "고정비 절감 가능 항목 1개 이상 식별"
            },
            {
                "text": "변동비율 확인 및 목표 매출 재설정",
                "eta_min": 15,
                "done_when": "목표 매출이 손익분기점을 넘도록 설정"
            },
            {
                "text": "매출 증대 방안 3안 작성 (단기/중기/장기)",
                "eta_min": 30,
                "done_when": "3가지 방안 문서화 완료"
            }
        ],
        "watchouts": [
            "고정비 절감만으로 해결하려 하지 말 것",
            "매출 증대와 비용 절감의 균형 필요",
            "단기 해결책보다 구조 개선 우선"
        ],
        "required_pages": [
            {"label": "수익 구조 설계실", "page_key": "수익 구조 설계실"},
            {"label": "월간 성적표", "page_key": "실제정산"}
        ]
    }


def _build_margin_plan(context: Dict) -> Dict:
    """MARGIN 전략 실행 플랜"""
    return {
        "time_horizon": "1주",
        "difficulty": "중간",
        "steps": [
            {
                "text": "원가율 상위 메뉴 Top5 확인 (메뉴 수익 구조 설계실)",
                "eta_min": 15,
                "done_when": "원가율 35% 이상 메뉴 5개 식별"
            },
            {
                "text": "가격/구성 2안 시뮬레이터 적용",
                "eta_min": 30,
                "done_when": "각 메뉴별 2가지 개선안 작성"
            },
            {
                "text": "마진 메뉴 후보 3개 선정",
                "eta_min": 20,
                "done_when": "마진 메뉴로 지정할 후보 3개 결정"
            },
            {
                "text": "메뉴판 내 '유인/볼륨/마진' 균형 점검",
                "eta_min": 25,
                "done_when": "메뉴 역할 분류 완료 및 균형 확인"
            }
        ],
        "watchouts": [
            "가격 인상만으로 해결하려 하지 말 것",
            "고객 반응을 고려한 점진적 조정",
            "원가 절감과 가격 조정 병행"
        ],
        "required_pages": [
            {"label": "메뉴 수익 구조 설계실", "page_key": "메뉴 수익 구조 설계실"},
            {"label": "메뉴 등록", "page_key": "메뉴 등록"}
        ]
    }


def _build_cost_plan(context: Dict) -> Dict:
    """COST 전략 실행 플랜"""
    return {
        "time_horizon": "2주",
        "difficulty": "높음",
        "steps": [
            {
                "text": "재료 집중도 Top3 확인 (재료 구조 설계실)",
                "eta_min": 15,
                "done_when": "TOP3 재료와 집중도 % 확인"
            },
            {
                "text": "고위험 재료 대체 가능성 체크",
                "eta_min": 30,
                "done_when": "대체재 후보 1개 이상 식별"
            },
            {
                "text": "발주 유형 정리 (단일/복수 공급업체)",
                "eta_min": 20,
                "done_when": "각 재료별 발주 전략 수립"
            },
            {
                "text": "레시피 사용량 상위 재료 개선",
                "eta_min": 25,
                "done_when": "사용량 최적화 방안 3개 작성"
            },
            {
                "text": "대체재 테스트 및 레시피 업데이트",
                "eta_min": 40,
                "done_when": "대체재 적용 레시피 1개 이상 완료"
            }
        ],
        "watchouts": [
            "품질 저하 없이 원가 절감",
            "대체재는 충분한 테스트 후 적용",
            "공급업체와의 관계 고려"
        ],
        "required_pages": [
            {"label": "재료 등록", "page_key": "재료 등록"},
            {"label": "레시피 등록", "page_key": "레시피 등록"}
        ]
    }


def _build_portfolio_plan(context: Dict) -> Dict:
    """PORTFOLIO 전략 실행 플랜"""
    return {
        "time_horizon": "1주",
        "difficulty": "중간",
        "steps": [
            {
                "text": "메뉴 역할 분류 확인 (유인/볼륨/마진)",
                "eta_min": 20,
                "done_when": "모든 메뉴 역할 분류 완료"
            },
            {
                "text": "유인 메뉴 후보 2~3개 선정",
                "eta_min": 15,
                "done_when": "유인 메뉴로 지정할 후보 결정"
            },
            {
                "text": "마진 메뉴 비율 30% 이상 목표 설정",
                "eta_min": 10,
                "done_when": "마진 메뉴 목표 개수 설정"
            },
            {
                "text": "메뉴판 구성 균형 점검",
                "eta_min": 20,
                "done_when": "유인/볼륨/마진 균형 확인"
            }
        ],
        "watchouts": [
            "유인 메뉴만 늘리지 말 것",
            "마진 메뉴 비율 유지 중요",
            "고객 선호도와 수익성 균형"
        ],
        "required_pages": [
            {"label": "메뉴 등록", "page_key": "메뉴 등록"},
            {"label": "메뉴 포트폴리오 설계실", "page_key": "메뉴 등록"}
        ]
    }


def _build_acquisition_plan(context: Dict) -> Dict:
    """ACQUISITION 전략 실행 플랜"""
    return {
        "time_horizon": "2주",
        "difficulty": "중간",
        "steps": [
            {
                "text": "지난 14일 유입/객단가/판매량 분해 분석",
                "eta_min": 20,
                "done_when": "매출 하락 원인 1차 파악"
            },
            {
                "text": "리뷰/콘텐츠 1회 실행 (SNS 또는 리뷰 응답)",
                "eta_min": 30,
                "done_when": "리뷰 응답 또는 콘텐츠 게시 1건 완료"
            },
            {
                "text": "유인 메뉴/사진 포인트 점검",
                "eta_min": 15,
                "done_when": "유인 메뉴 사진/설명 개선 1건"
            },
            {
                "text": "프로모션 기획 (단기/중기)",
                "eta_min": 25,
                "done_when": "프로모션 계획 1개 작성"
            }
        ],
        "watchouts": [
            "단기 프로모션에만 의존하지 말 것",
            "브랜드 이미지와 일관성 유지",
            "ROI 측정 가능한 활동 우선"
        ],
        "required_pages": [
            {"label": "분석총평", "page_key": "분석총평"},
            {"label": "매출 분석", "page_key": "매출 관리"}
        ]
    }


def _build_operations_plan(context: Dict) -> Dict:
    """OPERATIONS 전략 실행 플랜"""
    return {
        "time_horizon": "즉시",
        "difficulty": "낮음",
        "steps": [
            {
                "text": "건강검진 결과 확인 (종합 건강검진)",
                "eta_min": 10,
                "done_when": "건강검진 리포트 확인 완료"
            },
            {
                "text": "주요 병목 영역 1개 선택",
                "eta_min": 5,
                "done_when": "개선할 영역 1개 결정"
            },
            {
                "text": "해당 영역 체크리스트 작성",
                "eta_min": 20,
                "done_when": "체크리스트 5개 항목 작성"
            },
            {
                "text": "1주일 실행 후 재검진 계획",
                "eta_min": 10,
                "done_when": "재검진 일정 설정"
            }
        ],
        "watchouts": [
            "한 번에 모든 영역 개선하려 하지 말 것",
            "지속 가능한 개선 우선",
            "직원과의 소통 중요"
        ],
        "required_pages": [
            {"label": "종합 건강검진", "page_key": "종합 건강검진"}
        ]
    }


def _get_empty_plan() -> Dict:
    """빈 플랜 반환"""
    return {
        "time_horizon": "1주",
        "difficulty": "중간",
        "steps": [
            {
                "text": "가게 전략 센터에서 시작",
                "eta_min": 30,
                "done_when": "설계 데이터 입력 완료"
            }
        ],
        "watchouts": ["데이터 부족 시 설계부터 시작"],
        "required_pages": [
            {"label": "가게 전략 센터", "page_key": "가게 전략 센터"}
        ]
    }
