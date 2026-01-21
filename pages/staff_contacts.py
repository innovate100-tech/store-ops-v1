"""
직원 연락망 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header

# 공통 설정 적용
bootstrap(page_title="Staff Contacts")


def render_staff_contacts():
    """직원 연락망 페이지 렌더링"""
    render_page_header("직원 연락망", "👤")
    
    # 직원 데이터 (임시 - 추후 DB 연결)
    if 'employees' not in st.session_state:
        st.session_state.employees = []
    
    # 직원 추가
    with st.expander("➕ 직원 추가", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            emp_name = st.text_input("이름", key="emp_name")
        with col2:
            emp_role = st.text_input("역할", key="emp_role", placeholder="예: 주방장, 서버 등")
        with col3:
            emp_phone = st.text_input("연락처", key="emp_phone", placeholder="010-0000-0000")
        
        col4, col5 = st.columns(2)
        with col4:
            emp_worktime = st.text_input("근무시간", key="emp_worktime", placeholder="예: 평일 09:00-18:00")
        with col5:
            st.write("")
            st.write("")
            if st.button("추가", key="emp_add", type="primary"):
                if emp_name and emp_phone:
                    new_emp = {
                        'id': len(st.session_state.employees) + 1,
                        'name': emp_name,
                        'role': emp_role,
                        'phone': emp_phone,
                        'worktime': emp_worktime,
                    }
                    st.session_state.employees.append(new_emp)
                    st.success(f"{emp_name} 직원이 추가되었습니다!")
                    st.rerun()
                else:
                    st.error("이름과 연락처는 필수입니다.")
    
    # 직원 목록
    if st.session_state.employees:
        st.markdown("**👥 직원 목록**")
        for idx, emp in enumerate(st.session_state.employees):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.write(f"**{emp['name']}**")
                if emp['role']:
                    st.caption(f"역할: {emp['role']}")
            with col2:
                st.write(f"📞 {emp['phone']}")
            with col3:
                if emp['worktime']:
                    st.caption(f"⏰ {emp['worktime']}")
            with col4:
                if st.button("🗑️", key=f"del_emp_{idx}", help="삭제"):
                    st.session_state.employees.pop(idx)
                    st.rerun()
            st.markdown("---")
    else:
        st.info("등록된 직원이 없습니다. 직원을 추가해주세요.")


# Streamlit 멀티페이지에서 직접 실행될 때
render_staff_contacts()
