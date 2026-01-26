"""
제목 박스 + 가이드 박스 통합 디자인 테스트 페이지
4가지 옵션을 모두 구현하여 비교할 수 있게 함
"""
import streamlit as st

def render_header_unified_test():
    """4가지 통합 옵션을 모두 보여주는 테스트 페이지"""
    
    st.title("🎨 제목 박스 + 가이드 박스 통합 디자인 테스트")
    st.caption("4가지 옵션을 비교해보세요. 원하는 옵션을 선택하면 실제 페이지에 적용됩니다.")
    
    # 테스트용 데이터
    score = 75
    status_color = "#3B82F6"
    
    # 공통 CSS
    common_css = """
    <style>
    @keyframes wave-move {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(0%); }
    }
    
    @keyframes pulse-ring {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
    }
    
    .test-section {
        margin-bottom: 3rem;
        padding: 2rem;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .test-section h2 {
        color: #F8FAFC;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    /* 반응형: 옵션 1 좌우 분할 */
    @media (max-width: 768px) {
        .option1-grid {
            grid-template-columns: 1fr !important;
            gap: 1.5rem !important;
            padding: 1.5rem !important;
        }
    }
    </style>
    """
    st.markdown(common_css, unsafe_allow_html=True)
    
    # 옵션 1: 좌우 분할 레이아웃
    st.markdown('<div class="test-section">', unsafe_allow_html=True)
    st.markdown("### 옵션 1: 좌우 분할 레이아웃 ⭐⭐⭐⭐⭐")
    st.caption("제목은 왼쪽(40%), 가이드는 오른쪽(60%)으로 배치")
    
    # 옵션 1: 문자열 연결로 구성
    option1_html = '<div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(30, 41, 59, 0.8) 100%); border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.3); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); margin-bottom: 2rem; overflow: hidden; position: relative;">'
    option1_html += '<div style="height: 6px; background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 50%, #3B82F6 100%); box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);"></div>'
    option1_html += '<div class="option1-grid" style="display: grid; grid-template-columns: 1fr 1.5fr; gap: 2rem; padding: 2rem;">'
    option1_html += '<div style="display: flex; flex-direction: column; gap: 0.5rem;">'
    option1_html += '<div style="font-size: 3rem; margin-bottom: 0.5rem;">📝</div>'
    option1_html += '<h1 style="font-size: 1.6rem; font-weight: 800; color: #F8FAFC; margin: 0; white-space: nowrap;">데이터 입력 센터</h1>'
    option1_html += '<p style="font-size: 0.9rem; color: #94A3B8; margin: 0;">매장 운영 OS 조종석</p>'
    option1_html += '</div>'
    option1_html += '<div style="display: flex; flex-direction: column; gap: 1rem;">'
    option1_html += '<h2 style="font-size: 1.2rem; font-weight: 700; color: #F8FAFC; margin: 0;">💡 데이터 자산 가이드</h2>'
    option1_html += '<p style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5; margin: 0;">이 앱은 \'감\'이 아니라 데이터 자산으로 매장을 운영하게 만듭니다.<br>아래 항목들이 채워질수록, 매장 운영이 시스템이 됩니다.</p>'
    option1_html += '<div style="margin: 0.5rem 0;">'
    option1_html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">'
    option1_html += '<span style="font-size: 0.75rem; color: #94A3B8; font-weight: 600;">MATURITY LEVEL</span>'
    option1_html += f'<span style="font-size: 1rem; color: #3B82F6; font-weight: 700;">{score}%</span>'
    option1_html += '</div>'
    option1_html += '<div style="width: 100%; height: 8px; background: rgba(255, 255, 255, 0.05); border-radius: 4px; overflow: hidden;">'
    option1_html += f'<div style="height: 100%; background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%); width: {score}%; box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);"></div>'
    option1_html += '</div>'
    option1_html += '</div>'
    option1_html += '<ul style="list-style: none; padding: 0; margin: 0.5rem 0;">'
    option1_html += '<li style="font-size: 0.8rem; color: #94A3B8; line-height: 1.4; margin-bottom: 0.5rem; padding-left: 1.5rem; position: relative;"><span style="position: absolute; left: 0; color: #3B82F6; font-size: 1.2rem;">•</span>비어 있는 데이터를 채우면 정밀 리포트/전략 기능이 단계적으로 열립니다.</li>'
    option1_html += '<li style="font-size: 0.8rem; color: #94A3B8; line-height: 1.4; margin-bottom: 0.5rem; padding-left: 1.5rem; position: relative;"><span style="position: absolute; left: 0; color: #3B82F6; font-size: 1.2rem;">•</span>입력은 일이 아니라, 매장의 운영 시스템을 만드는 과정입니다.</li>'
    option1_html += '</ul>'
    option1_html += '<p style="font-size: 0.75rem; color: #64748B; margin-top: 0.5rem; font-style: italic; margin: 0;">아래 패널들은 현재 매장이 보유한 \'데이터 자산\' 상태입니다.</p>'
    option1_html += '</div>'
    option1_html += '</div>'
    option1_html += '</div>'
    st.markdown(option1_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 옵션 2: 상하 압축형
    st.markdown('<div class="test-section">', unsafe_allow_html=True)
    st.markdown("### 옵션 2: 상하 압축형 ⭐⭐⭐⭐")
    st.caption("제목과 가이드를 하나의 박스에 세로로 압축 배치")
    
    # 옵션 2: 문자열 연결로 구성
    option2_html = '<div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(30, 41, 59, 0.8) 100%); border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.3); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); margin-bottom: 2rem; overflow: hidden; position: relative;">'
    option2_html += '<div style="height: 6px; background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 50%, #3B82F6 100%); box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);"></div>'
    option2_html += '<div style="padding: 1.5rem 2rem;">'
    option2_html += '<div style="margin-bottom: 1.5rem;">'
    option2_html += '<div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.5rem;">'
    option2_html += '<div style="font-size: 2.5rem;">📝</div>'
    option2_html += '<div><h1 style="font-size: 1.8rem; font-weight: 800; color: #F8FAFC; margin: 0; white-space: nowrap;">데이터 입력 센터</h1><p style="font-size: 0.9rem; color: #94A3B8; margin: 0.3rem 0 0 0;">매장 운영 OS 조종석</p></div>'
    option2_html += '</div></div>'
    option2_html += '<div style="height: 1px; background: rgba(148, 163, 184, 0.2); margin: 1.5rem 0;"></div>'
    option2_html += '<div>'
    option2_html += '<h2 style="font-size: 1.2rem; font-weight: 700; color: #F8FAFC; margin: 0 0 0.8rem 0;">💡 데이터 자산 가이드</h2>'
    option2_html += '<p style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5; margin: 0 0 1rem 0;">이 앱은 \'감\'이 아니라 데이터 자산으로 매장을 운영하게 만듭니다.<br>아래 항목들이 채워질수록, 매장 운영이 시스템이 됩니다.</p>'
    option2_html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">'
    option2_html += '<span style="font-size: 0.75rem; color: #94A3B8; font-weight: 600;">MATURITY LEVEL</span>'
    option2_html += f'<span style="font-size: 1rem; color: #3B82F6; font-weight: 700;">{score}%</span>'
    option2_html += '</div>'
    option2_html += '<div style="width: 100%; height: 8px; background: rgba(255, 255, 255, 0.05); border-radius: 4px; overflow: hidden; margin-bottom: 1rem;">'
    option2_html += f'<div style="height: 100%; background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%); width: {score}%; box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);"></div>'
    option2_html += '</div>'
    option2_html += '<ul style="list-style: none; padding: 0; margin: 0.5rem 0;">'
    option2_html += '<li style="font-size: 0.8rem; color: #94A3B8; line-height: 1.4; margin-bottom: 0.5rem; padding-left: 1.5rem; position: relative;"><span style="position: absolute; left: 0; color: #3B82F6; font-size: 1.2rem;">•</span>비어 있는 데이터를 채우면 정밀 리포트/전략 기능이 단계적으로 열립니다.</li>'
    option2_html += '<li style="font-size: 0.8rem; color: #94A3B8; line-height: 1.4; margin-bottom: 0.5rem; padding-left: 1.5rem; position: relative;"><span style="position: absolute; left: 0; color: #3B82F6; font-size: 1.2rem;">•</span>입력은 일이 아니라, 매장의 운영 시스템을 만드는 과정입니다.</li>'
    option2_html += '</ul>'
    option2_html += '<p style="font-size: 0.75rem; color: #64748B; margin-top: 1rem; font-style: italic; margin: 0;">아래 패널들은 현재 매장이 보유한 \'데이터 자산\' 상태입니다.</p>'
    option2_html += '</div></div></div>'
    st.markdown(option2_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 옵션 3: 탭/토글 방식
    st.markdown('<div class="test-section">', unsafe_allow_html=True)
    st.markdown("### 옵션 3: 탭/토글 방식 ⭐⭐⭐")
    st.caption("제목은 항상 보이고, 가이드는 토글로 접었다 펼 수 있게")
    
    # 옵션 3: 문자열 연결로 구성
    option3_title_html = '<div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(30, 41, 59, 0.8) 100%); border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.3); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); margin-bottom: 1rem; overflow: hidden; position: relative;">'
    option3_title_html += '<div style="height: 6px; background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 50%, #3B82F6 100%); box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);"></div>'
    option3_title_html += '<div style="padding: 1.5rem 2rem;">'
    option3_title_html += '<div style="display: flex; align-items: center; gap: 0.8rem;">'
    option3_title_html += '<div style="font-size: 2.5rem;">📝</div>'
    option3_title_html += '<div><h1 style="font-size: 1.8rem; font-weight: 800; color: #F8FAFC; margin: 0; white-space: nowrap;">데이터 입력 센터</h1><p style="font-size: 0.9rem; color: #94A3B8; margin: 0.3rem 0 0 0;">매장 운영 OS 조종석</p></div>'
    option3_title_html += '</div></div></div>'
    st.markdown(option3_title_html, unsafe_allow_html=True)
    
    with st.expander("💡 데이터 자산 가이드 보기", expanded=False):
        option3_guide_html = '<div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(30, 41, 59, 0.8) 100%); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.3); padding: 1.5rem; margin-top: 1rem;">'
        option3_guide_html += '<h2 style="font-size: 1.2rem; font-weight: 700; color: #F8FAFC; margin: 0 0 0.8rem 0;">💡 데이터 자산 가이드</h2>'
        option3_guide_html += '<p style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5; margin: 0 0 1rem 0;">이 앱은 \'감\'이 아니라 데이터 자산으로 매장을 운영하게 만듭니다.<br>아래 항목들이 채워질수록, 매장 운영이 시스템이 됩니다.</p>'
        option3_guide_html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">'
        option3_guide_html += '<span style="font-size: 0.75rem; color: #94A3B8; font-weight: 600;">MATURITY LEVEL</span>'
        option3_guide_html += f'<span style="font-size: 1rem; color: #3B82F6; font-weight: 700;">{score}%</span>'
        option3_guide_html += '</div>'
        option3_guide_html += '<div style="width: 100%; height: 8px; background: rgba(255, 255, 255, 0.05); border-radius: 4px; overflow: hidden; margin-bottom: 1rem;">'
        option3_guide_html += f'<div style="height: 100%; background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%); width: {score}%; box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);"></div>'
        option3_guide_html += '</div>'
        option3_guide_html += '<ul style="list-style: none; padding: 0; margin: 0.5rem 0;">'
        option3_guide_html += '<li style="font-size: 0.8rem; color: #94A3B8; line-height: 1.4; margin-bottom: 0.5rem; padding-left: 1.5rem; position: relative;"><span style="position: absolute; left: 0; color: #3B82F6; font-size: 1.2rem;">•</span>비어 있는 데이터를 채우면 정밀 리포트/전략 기능이 단계적으로 열립니다.</li>'
        option3_guide_html += '<li style="font-size: 0.8rem; color: #94A3B8; line-height: 1.4; margin-bottom: 0.5rem; padding-left: 1.5rem; position: relative;"><span style="position: absolute; left: 0; color: #3B82F6; font-size: 1.2rem;">•</span>입력은 일이 아니라, 매장의 운영 시스템을 만드는 과정입니다.</li>'
        option3_guide_html += '</ul>'
        option3_guide_html += '<p style="font-size: 0.75rem; color: #64748B; margin-top: 1rem; font-style: italic; margin: 0;">아래 패널들은 현재 매장이 보유한 \'데이터 자산\' 상태입니다.</p>'
        option3_guide_html += '</div>'
        st.markdown(option3_guide_html, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 옵션 4: 인라인 통합형
    st.markdown('<div class="test-section">', unsafe_allow_html=True)
    st.markdown("### 옵션 4: 인라인 통합형 ⭐⭐⭐⭐")
    st.caption("제목과 가이드를 자연스럽게 하나의 흐름으로 통합")
    
    # 옵션 4: 문자열 연결로 구성
    option4_html = '<div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(30, 41, 59, 0.8) 100%); border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.3); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); margin-bottom: 2rem; overflow: hidden; position: relative;">'
    option4_html += '<div style="height: 6px; background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 50%, #3B82F6 100%); box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);"></div>'
    option4_html += '<div style="padding: 2rem;">'
    option4_html += '<div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1.5rem;">'
    option4_html += '<div style="font-size: 2.5rem;">📝</div>'
    option4_html += '<div><h1 style="font-size: 1.8rem; font-weight: 800; color: #F8FAFC; margin: 0; white-space: nowrap;">데이터 입력 센터</h1><p style="font-size: 0.9rem; color: #94A3B8; margin: 0.3rem 0 0 0;">매장 운영 OS 조종석</p></div>'
    option4_html += '</div>'
    option4_html += '<p style="font-size: 0.9rem; color: #94A3B8; line-height: 1.6; margin: 0 0 1.5rem 0;">이 앱은 \'감\'이 아니라 데이터 자산으로 매장을 운영하게 만듭니다.<br>아래 항목들이 채워질수록, 매장 운영이 시스템이 됩니다.</p>'
    option4_html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">'
    option4_html += '<span style="font-size: 0.75rem; color: #94A3B8; font-weight: 600;">MATURITY LEVEL</span>'
    option4_html += f'<span style="font-size: 1rem; color: #3B82F6; font-weight: 700;">{score}%</span>'
    option4_html += '</div>'
    option4_html += '<div style="width: 100%; height: 8px; background: rgba(255, 255, 255, 0.05); border-radius: 4px; overflow: hidden; margin-bottom: 1.5rem;">'
    option4_html += f'<div style="height: 100%; background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%); width: {score}%; box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);"></div>'
    option4_html += '</div>'
    option4_html += '<ul style="list-style: none; padding: 0; margin: 0.5rem 0 1.5rem 0;">'
    option4_html += '<li style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5; margin-bottom: 0.8rem; padding-left: 1.5rem; position: relative;"><span style="position: absolute; left: 0; color: #3B82F6; font-size: 1.2rem;">•</span>비어 있는 데이터를 채우면 정밀 리포트/전략 기능이 단계적으로 열립니다.</li>'
    option4_html += '<li style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5; margin-bottom: 0.8rem; padding-left: 1.5rem; position: relative;"><span style="position: absolute; left: 0; color: #3B82F6; font-size: 1.2rem;">•</span>입력은 일이 아니라, 매장의 운영 시스템을 만드는 과정입니다.</li>'
    option4_html += '</ul>'
    option4_html += '<p style="font-size: 0.75rem; color: #64748B; margin-top: 1rem; font-style: italic; margin: 0; border-top: 1px solid rgba(148, 163, 184, 0.1); padding-top: 1rem;">아래 패널들은 현재 매장이 보유한 \'데이터 자산\' 상태입니다.</p>'
    option4_html += '</div></div>'
    st.markdown(option4_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 선택 안내
    st.markdown("---")
    st.info("💡 **원하는 옵션을 선택하시면 실제 '데이터 입력 센터' 페이지에 적용됩니다.**")
    
    selected_option = st.radio(
        "어떤 옵션을 적용하시겠습니까?",
        ["옵션 1: 좌우 분할", "옵션 2: 상하 압축형", "옵션 3: 탭/토글 방식", "옵션 4: 인라인 통합형", "아직 결정 안함"],
        horizontal=False
    )
    
    if selected_option != "아직 결정 안함":
        st.success(f"✅ **{selected_option}** 선택 완료! 실제 적용은 개발자가 진행하겠습니다.")
        st.caption("선택하신 옵션을 `input_hub.py`에 적용하시면 됩니다.")
    
    # ============================================
    # CAUSE OS 푸터 (테스트)
    # ============================================
    from src.ui.footer import render_cause_os_footer
    
    st.markdown("---")
    st.markdown("### 🧪 CAUSE OS 푸터 테스트")
    st.caption("아래에 CAUSE OS 전용 제품 푸터가 표시됩니다.")
    
    # 푸터 스타일 선택
    footer_style = st.radio(
        "푸터 스타일 선택",
        ["기본형 (1안)", "브랜드형 (2안)"],
        horizontal=True,
        key="footer_style_radio"
    )
    
    # 푸터 렌더링
    render_cause_os_footer(style="brand" if footer_style == "브랜드형 (2안)" else "default")
