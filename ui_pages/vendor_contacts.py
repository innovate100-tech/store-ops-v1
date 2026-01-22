"""
협력사 연락망 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header

# 공통 설정 적용
bootstrap(page_title="Vendor Contacts")


def render_vendor_contacts():
    """협력사 연락망 페이지 렌더링"""
    render_page_header("협력사 연락망", "🤝")
    
    # 협력사 데이터 (임시 - 추후 DB 연결)
    if 'partners' not in st.session_state:
        st.session_state.partners = []
    
    # 협력사 추가
    with st.expander("➕ 협력사 추가", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            partner_name = st.text_input("업체명", key="vendor_contacts_partner_name")
            partner_contact = st.text_input("담당자", key="vendor_contacts_partner_contact")
        with col2:
            partner_phone = st.text_input("연락처", key="vendor_contacts_partner_phone", placeholder="010-0000-0000")
            partner_type = st.selectbox("유형", ["재료 공급", "배달", "기타"], key="vendor_contacts_partner_type")
        
        partner_memo = st.text_area("메모", key="vendor_contacts_partner_memo", placeholder="거래 내역, 특이사항 등")
        
        if st.button("추가", key="vendor_contacts_partner_add", type="primary"):
            if partner_name and partner_phone:
                new_partner = {
                    'id': len(st.session_state.partners) + 1,
                    'name': partner_name,
                    'contact': partner_contact,
                    'phone': partner_phone,
                    'type': partner_type,
                    'memo': partner_memo,
                }
                st.session_state.partners.append(new_partner)
                st.success(f"{partner_name} 협력사가 추가되었습니다!")
                st.rerun()
            else:
                st.error("업체명과 연락처는 필수입니다.")
    
    # 협력사 목록
    if st.session_state.partners:
        st.markdown("**🤝 협력사 목록**")
        for idx, partner in enumerate(st.session_state.partners):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.write(f"**{partner['name']}**")
                if partner['contact']:
                    st.caption(f"담당자: {partner['contact']}")
            with col2:
                st.write(f"📞 {partner['phone']}")
                st.caption(f"유형: {partner['type']}")
            with col3:
                if partner['memo']:
                    st.caption(f"📝 {partner['memo']}")
            with col4:
                if st.button("🗑️", key=f"del_partner_{idx}", help="삭제"):
                    st.session_state.partners.pop(idx)
                    st.rerun()
            st.markdown("---")
    else:
        st.info("등록된 협력사가 없습니다. 협력사를 추가해주세요.")


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_vendor_contacts()
