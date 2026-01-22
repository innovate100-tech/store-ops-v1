"""
데이터 버전 토큰 시스템
캐시 무효화를 위한 버전 관리 유틸리티
"""
import streamlit as st
from typing import Dict, List


def get_data_version(name: str) -> int:
    """
    데이터 버전 토큰 조회
    
    Args:
        name: 데이터 이름 (예: "sales", "visitors", "menus", "cost")
    
    Returns:
        int: 버전 번호 (기본값: 0)
    """
    if "data_version" not in st.session_state:
        st.session_state["data_version"] = {}
    
    return st.session_state["data_version"].get(name, 0)


def bump_data_version(name: str) -> None:
    """
    데이터 버전 토큰 증가 (캐시 무효화)
    
    Args:
        name: 데이터 이름 (예: "sales", "visitors", "menus", "cost")
    """
    if "data_version" not in st.session_state:
        st.session_state["data_version"] = {}
    
    current_version = st.session_state["data_version"].get(name, 0)
    st.session_state["data_version"][name] = current_version + 1


def bump_versions(names: List[str]) -> None:
    """
    여러 데이터 버전 토큰을 한 번에 증가
    
    Args:
        names: 데이터 이름 리스트 (예: ["sales", "visitors"])
    """
    for name in names:
        bump_data_version(name)


def get_all_versions() -> Dict[str, int]:
    """
    모든 데이터 버전 토큰 조회
    
    Returns:
        dict: {name: version} 형태의 딕셔너리
    """
    if "data_version" not in st.session_state:
        st.session_state["data_version"] = {}
    
    return st.session_state["data_version"].copy()


def reset_all_versions() -> None:
    """모든 데이터 버전 토큰 초기화 (디버깅용)"""
    st.session_state["data_version"] = {}
