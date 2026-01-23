"""
코치 판결 표준 스키마 (헌법)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Evidence:
    """근거 항목"""
    label: str
    value: str
    note: Optional[str] = None


@dataclass
class Action:
    """액션 항목"""
    label: str
    page: str
    intent: Optional[str] = None


@dataclass
class CoachVerdict:
    """코치 판결 표준 스키마"""
    level: str  # "OK" | "WARN" | "RISK"
    title: str  # 한줄 결론 제목
    summary: str  # 결론 문장 (숫자 포함)
    evidence: List[Evidence]  # 근거 2~4개
    actions: List[Action]  # CTA 1~3개
    source: str  # "home" | "design_center" | "menu_portfolio" ...
    as_of: str  # "YYYY-MM-DD" (표시용)
    
    def __post_init__(self):
        """검증"""
        if self.level not in ["OK", "WARN", "RISK"]:
            raise ValueError(f"Invalid level: {self.level}")
        if not self.evidence:
            raise ValueError("Evidence list cannot be empty")
        if not self.actions:
            raise ValueError("Actions list cannot be empty")


# Level별 기본 아이콘/색상 매핑
LEVEL_CONFIG = {
    "OK": {
        "icon": "✅",
        "color": "green",
        "emoji": "✅",
    },
    "WARN": {
        "icon": "⚠️",
        "color": "orange",
        "emoji": "⚠️",
    },
    "RISK": {
        "icon": "🔴",
        "color": "red",
        "emoji": "🔴",
    },
}


def get_level_config(level: str) -> dict:
    """Level별 설정 반환"""
    return LEVEL_CONFIG.get(level, LEVEL_CONFIG["OK"])
