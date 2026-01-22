"""
실제정산 페이지 (리빌드 예정)
현재는 MVP 설계 전 스텁 상태입니다.
"""
from src.bootstrap import bootstrap
import streamlit as st

# 공통 설정 적용
bootstrap(page_title="Settlement Actual")


def render_settlement_actual():
    """
    실제정산 페이지 렌더링 (스텁)
    
    현재 상태:
    - 페이지는 라우팅만 유지
    - 기능은 MVP 설계 후 새로 구현 예정
    """
    # 페이지 제목
    st.title("🧾 실제정산 (리빌드 예정)")
    
    # 안내 메시지
    st.info("""
    **현재 페이지는 MVP 설계 후 새로 구현합니다.**
    
    기존 기능은 제거되었으며, 향후 아래 기능들이 포함될 예정입니다.
    """)
    
    # MVP 체크리스트
    st.markdown("### 📋 향후 MVP 체크리스트")
    
    checklist_items = [
        "연/월 선택 UI",
        "실제매출 입력/표시",
        "실제원가 입력/표시",
        "실제이익 계산 및 표시",
        "데이터 저장 (upsert)",
        "이력 보기 (월별)",
        "대시보드 반영",
    ]
    
    for idx, item in enumerate(checklist_items, 1):
        st.markdown(f"- [ ] {idx}. {item}")
    
    # 추가 안내
    st.markdown("---")
    st.markdown("""
    **참고:**
    - 기존 코드는 `archive/settlement_actual_old.py`에 보관되어 있습니다.
    - 라우팅 및 페이지 구조는 유지되어 있어 다른 페이지에 영향을 주지 않습니다.
    """)
