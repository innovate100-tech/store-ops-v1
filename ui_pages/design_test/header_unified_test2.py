"""
Streamlit 버튼 디자인 갤러리
다양한 CSS 스타일을 적용한 Streamlit 버튼 디자인 모음
"""
import streamlit as st


def render_header_unified_test2():
    """Streamlit 버튼 디자인 갤러리"""
    
    st.title("🎨 Streamlit 버튼 디자인 갤러리")
    st.caption("CSS로 스타일링한 다양한 Streamlit 버튼 디자인")
    
    # CSS 스타일 정의
    css = """
    <style>
    /* 공통 스타일 */
    .btn-gallery-section {
        margin-bottom: 4rem;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%);
        border-radius: 24px;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .btn-gallery-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .btn-gallery-desc {
        font-size: 0.9rem;
        color: #94A3B8;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .btn-row {
        display: flex;
        gap: 1.5rem;
        justify-content: center;
        flex-wrap: wrap;
        margin-bottom: 1rem;
    }
    
    /* Streamlit 버튼 스타일링 - 변형 1: 네온 글로우 */
    button[key="btn_neon_1"],
    button[key="btn_neon_2"],
    button[key="btn_neon_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    button[key="btn_neon_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5),
                    0 0 40px rgba(59, 130, 246, 0.3),
                    0 0 60px rgba(59, 130, 246, 0.1) !important;
    }
    
    button[key="btn_neon_1"]:hover {
        box-shadow: 0 0 30px rgba(59, 130, 246, 0.8),
                    0 0 60px rgba(59, 130, 246, 0.5),
                    0 0 90px rgba(59, 130, 246, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    button[key="btn_neon_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.5),
                    0 0 40px rgba(16, 185, 129, 0.3),
                    0 0 60px rgba(16, 185, 129, 0.1) !important;
    }
    
    button[key="btn_neon_2"]:hover {
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.8),
                    0 0 60px rgba(16, 185, 129, 0.5),
                    0 0 90px rgba(16, 185, 129, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    button[key="btn_neon_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.5),
                    0 0 40px rgba(168, 85, 247, 0.3),
                    0 0 60px rgba(168, 85, 247, 0.1) !important;
    }
    
    button[key="btn_neon_3"]:hover {
        box-shadow: 0 0 30px rgba(168, 85, 247, 0.8),
                    0 0 60px rgba(168, 85, 247, 0.5),
                    0 0 90px rgba(168, 85, 247, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    /* 변형 2: 그라데이션 애니메이션 */
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    button[key="btn_gradient_1"],
    button[key="btn_gradient_2"],
    button[key="btn_gradient_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        background-size: 200% 200% !important;
        animation: gradient-shift 3s ease infinite !important;
    }
    
    button[key="btn_gradient_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 50%, #1D4ED8 100%) !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    
    button[key="btn_gradient_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 50%, #047857 100%) !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
    }
    
    button[key="btn_gradient_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 50%, #7E22CE 100%) !important;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4) !important;
    }
    
    /* 변형 3: 3D 입체 효과 */
    button[key="btn_3d_1"],
    button[key="btn_3d_2"],
    button[key="btn_3d_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        transform: perspective(1000px) rotateX(0deg) !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_3d_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        box-shadow: 0 8px 0 #1E40AF,
                    0 12px 20px rgba(0, 0, 0, 0.3) !important;
    }
    
    button[key="btn_3d_1"]:hover {
        transform: perspective(1000px) rotateX(5deg) translateY(2px) !important;
        box-shadow: 0 4px 0 #1E40AF,
                    0 8px 15px rgba(0, 0, 0, 0.3) !important;
    }
    
    button[key="btn_3d_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        box-shadow: 0 8px 0 #047857,
                    0 12px 20px rgba(0, 0, 0, 0.3) !important;
    }
    
    button[key="btn_3d_2"]:hover {
        transform: perspective(1000px) rotateX(5deg) translateY(2px) !important;
        box-shadow: 0 4px 0 #047857,
                    0 8px 15px rgba(0, 0, 0, 0.3) !important;
    }
    
    button[key="btn_3d_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
        box-shadow: 0 8px 0 #7E22CE,
                    0 12px 20px rgba(0, 0, 0, 0.3) !important;
    }
    
    button[key="btn_3d_3"]:hover {
        transform: perspective(1000px) rotateX(5deg) translateY(2px) !important;
        box-shadow: 0 4px 0 #7E22CE,
                    0 8px 15px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* 변형 4: 글래스모피즘 */
    button[key="btn_glass_1"],
    button[key="btn_glass_2"],
    button[key="btn_glass_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_glass_1"] {
        background: rgba(59, 130, 246, 0.2) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    }
    
    button[key="btn_glass_1"]:hover {
        background: rgba(59, 130, 246, 0.3) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }
    
    button[key="btn_glass_2"] {
        background: rgba(16, 185, 129, 0.2) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    }
    
    button[key="btn_glass_2"]:hover {
        background: rgba(16, 185, 129, 0.3) !important;
        border-color: rgba(16, 185, 129, 0.5) !important;
        box-shadow: 0 12px 40px rgba(16, 185, 129, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }
    
    button[key="btn_glass_3"] {
        background: rgba(168, 85, 247, 0.2) !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
        box-shadow: 0 8px 32px rgba(168, 85, 247, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    }
    
    button[key="btn_glass_3"]:hover {
        background: rgba(168, 85, 247, 0.3) !important;
        border-color: rgba(168, 85, 247, 0.5) !important;
        box-shadow: 0 12px 40px rgba(168, 85, 247, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }
    
    /* 변형 5: 홀로그램 효과 */
    @keyframes holo-shine {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    button[key="btn_holo_1"],
    button[key="btn_holo_2"],
    button[key="btn_holo_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    button[key="btn_holo_1"]::before,
    button[key="btn_holo_2"]::before,
    button[key="btn_holo_3"]::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent) !important;
        animation: holo-shine 2s infinite !important;
    }
    
    button[key="btn_holo_1"] {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.9) 0%, rgba(37, 99, 235, 0.9) 100%) !important;
    }
    
    button[key="btn_holo_2"] {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.9) 0%, rgba(5, 150, 105, 0.9) 100%) !important;
    }
    
    button[key="btn_holo_3"] {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.9) 0%, rgba(147, 51, 234, 0.9) 100%) !important;
    }
    
    /* 변형 6: 미니멀 라인 아트 */
    button[key="btn_minimal_1"],
    button[key="btn_minimal_2"],
    button[key="btn_minimal_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        background: transparent !important;
        border: 2px solid !important;
        position: relative !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_minimal_1"] {
        border-color: #3B82F6 !important;
        color: #3B82F6 !important;
    }
    
    button[key="btn_minimal_1"]:hover {
        background: rgba(59, 130, 246, 0.1) !important;
        color: #60A5FA !important;
    }
    
    button[key="btn_minimal_2"] {
        border-color: #10B981 !important;
        color: #10B981 !important;
    }
    
    button[key="btn_minimal_2"]:hover {
        background: rgba(16, 185, 129, 0.1) !important;
        color: #34D399 !important;
    }
    
    button[key="btn_minimal_3"] {
        border-color: #A855F7 !important;
        color: #A855F7 !important;
    }
    
    button[key="btn_minimal_3"]:hover {
        background: rgba(168, 85, 247, 0.1) !important;
        color: #C084FC !important;
    }
    
    /* 변형 7: 펄스 효과 */
    @keyframes pulse-glow {
        0%, 100% {
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.5),
                        0 0 40px rgba(59, 130, 246, 0.3);
            transform: scale(1);
        }
        50% {
            box-shadow: 0 0 30px rgba(59, 130, 246, 0.8),
                        0 0 60px rgba(59, 130, 246, 0.5);
            transform: scale(1.02);
        }
    }
    
    button[key="btn_pulse_1"],
    button[key="btn_pulse_2"],
    button[key="btn_pulse_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        animation: pulse-glow 2s ease-in-out infinite !important;
    }
    
    button[key="btn_pulse_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    }
    
    button[key="btn_pulse_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    }
    
    button[key="btn_pulse_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
    }
    
    /* 변형 8: 메탈릭 효과 */
    button[key="btn_metallic_1"],
    button[key="btn_metallic_2"],
    button[key="btn_metallic_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_metallic_1"] {
        background: linear-gradient(135deg, #64748B 0%, #475569 50%, #334155 100%) !important;
        box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.2),
                    0 4px 8px rgba(0, 0, 0, 0.3),
                    inset 0 -2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    button[key="btn_metallic_1"]:hover {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 50%, #1E40AF 100%) !important;
        box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.3),
                    0 6px 12px rgba(59, 130, 246, 0.4),
                    inset 0 -2px 4px rgba(0, 0, 0, 0.2) !important;
    }
    
    button[key="btn_metallic_2"] {
        background: linear-gradient(135deg, #64748B 0%, #475569 50%, #334155 100%) !important;
        box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.2),
                    0 4px 8px rgba(0, 0, 0, 0.3),
                    inset 0 -2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    button[key="btn_metallic_2"]:hover {
        background: linear-gradient(135deg, #10B981 0%, #059669 50%, #047857 100%) !important;
        box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.3),
                    0 6px 12px rgba(16, 185, 129, 0.4),
                    inset 0 -2px 4px rgba(0, 0, 0, 0.2) !important;
    }
    
    button[key="btn_metallic_3"] {
        background: linear-gradient(135deg, #64748B 0%, #475569 50%, #334155 100%) !important;
        box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.2),
                    0 4px 8px rgba(0, 0, 0, 0.3),
                    inset 0 -2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    button[key="btn_metallic_3"]:hover {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 50%, #7E22CE 100%) !important;
        box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.3),
                    0 6px 12px rgba(168, 85, 247, 0.4),
                    inset 0 -2px 4px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* 변형 9: 스트로크 효과 */
    button[key="btn_stroke_1"],
    button[key="btn_stroke_2"],
    button[key="btn_stroke_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        background: transparent !important;
        border: 3px solid !important;
        position: relative !important;
        transition: all 0.4s ease !important;
    }
    
    button[key="btn_stroke_1"] {
        border-color: #3B82F6 !important;
        color: #3B82F6 !important;
    }
    
    button[key="btn_stroke_1"]:hover {
        color: white !important;
        background: #3B82F6 !important;
    }
    
    button[key="btn_stroke_2"] {
        border-color: #10B981 !important;
        color: #10B981 !important;
    }
    
    button[key="btn_stroke_2"]:hover {
        color: white !important;
        background: #10B981 !important;
    }
    
    button[key="btn_stroke_3"] {
        border-color: #A855F7 !important;
        color: #A855F7 !important;
    }
    
    button[key="btn_stroke_3"]:hover {
        color: white !important;
        background: #A855F7 !important;
    }
    
    /* 변형 10: 라디얼 그라데이션 */
    button[key="btn_radial_1"],
    button[key="btn_radial_2"],
    button[key="btn_radial_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_radial_1"] {
        background: radial-gradient(circle at center, #3B82F6 0%, #2563EB 100%) !important;
    }
    
    button[key="btn_radial_1"]:hover {
        background: radial-gradient(circle at center, #60A5FA 0%, #3B82F6 100%) !important;
        transform: scale(1.05) !important;
    }
    
    button[key="btn_radial_2"] {
        background: radial-gradient(circle at center, #10B981 0%, #059669 100%) !important;
    }
    
    button[key="btn_radial_2"]:hover {
        background: radial-gradient(circle at center, #34D399 0%, #10B981 100%) !important;
        transform: scale(1.05) !important;
    }
    
    button[key="btn_radial_3"] {
        background: radial-gradient(circle at center, #A855F7 0%, #9333EA 100%) !important;
    }
    
    button[key="btn_radial_3"]:hover {
        background: radial-gradient(circle at center, #C084FC 0%, #A855F7 100%) !important;
        transform: scale(1.05) !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    # 변형 1: 네온 글로우 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 1: 네온 글로우 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">강렬한 네온 빛 효과로 시선을 끄는 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_neon_1", use_container_width=True):
            st.info("네온 글로우 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_neon_2", use_container_width=True):
            st.info("네온 글로우 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_neon_3", use_container_width=True):
            st.info("네온 글로우 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 2: 그라데이션 애니메이션
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 2: 그라데이션 애니메이션</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">움직이는 그라데이션으로 생동감 있는 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_gradient_1", use_container_width=True):
            st.info("그라데이션 애니메이션 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_gradient_2", use_container_width=True):
            st.info("그라데이션 애니메이션 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_gradient_3", use_container_width=True):
            st.info("그라데이션 애니메이션 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 3: 3D 입체 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 3: 3D 입체 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">눌리는 듯한 입체감을 주는 3D 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_3d_1", use_container_width=True):
            st.info("3D 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_3d_2", use_container_width=True):
            st.info("3D 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_3d_3", use_container_width=True):
            st.info("3D 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 4: 글래스모피즘
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 4: 글래스모피즘</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">반투명 유리 효과의 세련된 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_glass_1", use_container_width=True):
            st.info("글래스모피즘 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_glass_2", use_container_width=True):
            st.info("글래스모피즘 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_glass_3", use_container_width=True):
            st.info("글래스모피즘 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 5: 홀로그램 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 5: 홀로그램 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">빛이 지나가는 홀로그램 스타일 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_holo_1", use_container_width=True):
            st.info("홀로그램 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_holo_2", use_container_width=True):
            st.info("홀로그램 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_holo_3", use_container_width=True):
            st.info("홀로그램 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 6: 미니멀 라인 아트
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 6: 미니멀 라인 아트</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">깔끔한 라인으로 구성된 미니멀 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_minimal_1", use_container_width=True):
            st.info("미니멀 라인 아트 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_minimal_2", use_container_width=True):
            st.info("미니멀 라인 아트 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_minimal_3", use_container_width=True):
            st.info("미니멀 라인 아트 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 7: 펄스 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 7: 펄스 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">지속적으로 맥박치는 듯한 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_pulse_1", use_container_width=True):
            st.info("펄스 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_pulse_2", use_container_width=True):
            st.info("펄스 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_pulse_3", use_container_width=True):
            st.info("펄스 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 8: 메탈릭 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 8: 메탈릭 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">금속 질감의 고급스러운 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_metallic_1", use_container_width=True):
            st.info("메탈릭 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_metallic_2", use_container_width=True):
            st.info("메탈릭 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_metallic_3", use_container_width=True):
            st.info("메탈릭 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 9: 스트로크 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 9: 스트로크 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">테두리에서 안쪽으로 채워지는 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_stroke_1", use_container_width=True):
            st.info("스트로크 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_stroke_2", use_container_width=True):
            st.info("스트로크 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_stroke_3", use_container_width=True):
            st.info("스트로크 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 10: 라디얼 그라데이션
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 10: 라디얼 그라데이션</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">중앙에서 퍼지는 원형 그라데이션 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_radial_1", use_container_width=True):
            st.info("라디얼 그라데이션 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_radial_2", use_container_width=True):
            st.info("라디얼 그라데이션 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_radial_3", use_container_width=True):
            st.info("라디얼 그라데이션 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 추가 CSS 스타일 (변형 11-20)
    additional_css = """
    <style>
    /* 변형 11: 슬라이드 효과 */
    button[key="btn_slide_1"],
    button[key="btn_slide_2"],
    button[key="btn_slide_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        position: relative !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_slide_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    }
    
    button[key="btn_slide_1"]:hover {
        transform: translateX(5px) !important;
    }
    
    button[key="btn_slide_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    }
    
    button[key="btn_slide_2"]:hover {
        transform: translateX(5px) !important;
    }
    
    button[key="btn_slide_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
    }
    
    button[key="btn_slide_3"]:hover {
        transform: translateX(5px) !important;
    }
    
    /* 변형 12: 스케치 효과 */
    button[key="btn_sketch_1"],
    button[key="btn_sketch_2"],
    button[key="btn_sketch_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        background: transparent !important;
        border: 2px dashed !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_sketch_1"] {
        border-color: #3B82F6 !important;
        color: #3B82F6 !important;
    }
    
    button[key="btn_sketch_1"]:hover {
        background: rgba(59, 130, 246, 0.1) !important;
        border-style: solid !important;
    }
    
    button[key="btn_sketch_2"] {
        border-color: #10B981 !important;
        color: #10B981 !important;
    }
    
    button[key="btn_sketch_2"]:hover {
        background: rgba(16, 185, 129, 0.1) !important;
        border-style: solid !important;
    }
    
    button[key="btn_sketch_3"] {
        border-color: #A855F7 !important;
        color: #A855F7 !important;
    }
    
    button[key="btn_sketch_3"]:hover {
        background: rgba(168, 85, 247, 0.1) !important;
        border-style: solid !important;
    }
    
    /* 변형 13: 글로우 펄스 */
    @keyframes glow-pulse {
        0%, 100% {
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.6),
                        0 0 40px rgba(59, 130, 246, 0.4);
        }
        50% {
            box-shadow: 0 0 30px rgba(59, 130, 246, 0.9),
                        0 0 60px rgba(59, 130, 246, 0.6),
                        0 0 90px rgba(59, 130, 246, 0.3);
        }
    }
    
    button[key="btn_glow_pulse_1"],
    button[key="btn_glow_pulse_2"],
    button[key="btn_glow_pulse_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        animation: glow-pulse 2s ease-in-out infinite !important;
    }
    
    button[key="btn_glow_pulse_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.6) !important;
    }
    
    button[key="btn_glow_pulse_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.6) !important;
    }
    
    button[key="btn_glow_pulse_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.6) !important;
    }
    
    /* 변형 14: 셔터 효과 */
    button[key="btn_shutter_1"],
    button[key="btn_shutter_2"],
    button[key="btn_shutter_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        position: relative !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_shutter_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    }
    
    button[key="btn_shutter_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    }
    
    button[key="btn_shutter_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
    }
    
    /* 변형 15: 다이아몬드 효과 */
    button[key="btn_diamond_1"],
    button[key="btn_diamond_2"],
    button[key="btn_diamond_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        clip-path: polygon(20% 0%, 80% 0%, 100% 20%, 100% 80%, 80% 100%, 20% 100%, 0% 80%, 0% 20%) !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_diamond_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    }
    
    button[key="btn_diamond_1"]:hover {
        clip-path: polygon(10% 0%, 90% 0%, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0% 90%, 0% 10%) !important;
        transform: rotate(5deg) scale(1.05) !important;
    }
    
    button[key="btn_diamond_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    }
    
    button[key="btn_diamond_2"]:hover {
        clip-path: polygon(10% 0%, 90% 0%, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0% 90%, 0% 10%) !important;
        transform: rotate(5deg) scale(1.05) !important;
    }
    
    button[key="btn_diamond_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
    }
    
    button[key="btn_diamond_3"]:hover {
        clip-path: polygon(10% 0%, 90% 0%, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0% 90%, 0% 10%) !important;
        transform: rotate(5deg) scale(1.05) !important;
    }
    
    /* 변형 16: 웨이브 효과 */
    button[key="btn_wave_1"],
    button[key="btn_wave_2"],
    button[key="btn_wave_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        position: relative !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_wave_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    }
    
    button[key="btn_wave_1"]:hover {
        transform: scale(1.05) !important;
    }
    
    button[key="btn_wave_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    }
    
    button[key="btn_wave_2"]:hover {
        transform: scale(1.05) !important;
    }
    
    button[key="btn_wave_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
    }
    
    button[key="btn_wave_3"]:hover {
        transform: scale(1.05) !important;
    }
    
    /* 변형 17: 스플릿 효과 */
    button[key="btn_split_1"],
    button[key="btn_split_2"],
    button[key="btn_split_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        position: relative !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_split_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    }
    
    button[key="btn_split_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    }
    
    button[key="btn_split_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
    }
    
    /* 변형 18: 매트릭스 효과 */
    @keyframes matrix-move {
        0% { transform: translateY(0); }
        100% { transform: translateY(20px); }
    }
    
    button[key="btn_matrix_1"],
    button[key="btn_matrix_2"],
    button[key="btn_matrix_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    button[key="btn_matrix_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    }
    
    button[key="btn_matrix_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    }
    
    button[key="btn_matrix_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
    }
    
    /* 변형 19: 그라데이션 보더 */
    button[key="btn_border_grad_1"],
    button[key="btn_border_grad_2"],
    button[key="btn_border_grad_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        background: transparent !important;
        border: 3px solid !important;
        position: relative !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_border_grad_1"] {
        border-image: linear-gradient(135deg, #3B82F6, #2563EB) 1 !important;
        color: #3B82F6 !important;
    }
    
    button[key="btn_border_grad_1"]:hover {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.1)) !important;
    }
    
    button[key="btn_border_grad_2"] {
        border-image: linear-gradient(135deg, #10B981, #059669) 1 !important;
        color: #10B981 !important;
    }
    
    button[key="btn_border_grad_2"]:hover {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1)) !important;
    }
    
    button[key="btn_border_grad_3"] {
        border-image: linear-gradient(135deg, #A855F7, #9333EA) 1 !important;
        color: #A855F7 !important;
    }
    
    button[key="btn_border_grad_3"]:hover {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(147, 51, 234, 0.1)) !important;
    }
    
    /* 변형 20: 반사 효과 */
    button[key="btn_reflect_1"],
    button[key="btn_reflect_2"],
    button[key="btn_reflect_3"] {
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: white !important;
        border: none !important;
        position: relative !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
    }
    
    button[key="btn_reflect_1"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }
    
    button[key="btn_reflect_1"]:hover {
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    button[key="btn_reflect_2"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }
    
    button[key="btn_reflect_2"]:hover {
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    button[key="btn_reflect_3"] {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    }
    
    button[key="btn_reflect_3"]:hover {
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.6),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """
    st.markdown(additional_css, unsafe_allow_html=True)
    
    # 변형 11: 슬라이드 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 11: 슬라이드 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">호버 시 이동하는 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_slide_1", use_container_width=True):
            st.info("슬라이드 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_slide_2", use_container_width=True):
            st.info("슬라이드 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_slide_3", use_container_width=True):
            st.info("슬라이드 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 12: 스케치 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 12: 스케치 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">손그림 느낌의 스케치 스타일 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_sketch_1", use_container_width=True):
            st.info("스케치 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_sketch_2", use_container_width=True):
            st.info("스케치 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_sketch_3", use_container_width=True):
            st.info("스케치 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 13: 글로우 펄스
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 13: 글로우 펄스</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">빛이 맥박치듯 강해지는 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_glow_pulse_1", use_container_width=True):
            st.info("글로우 펄스 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_glow_pulse_2", use_container_width=True):
            st.info("글로우 펄스 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_glow_pulse_3", use_container_width=True):
            st.info("글로우 펄스 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 14: 셔터 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 14: 셔터 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">위에서 아래로 내려오는 셔터 효과</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_shutter_1", use_container_width=True):
            st.info("셔터 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_shutter_2", use_container_width=True):
            st.info("셔터 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_shutter_3", use_container_width=True):
            st.info("셔터 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 15: 다이아몬드 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 15: 다이아몬드 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">다이아몬드 모양으로 변형되는 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_diamond_1", use_container_width=True):
            st.info("다이아몬드 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_diamond_2", use_container_width=True):
            st.info("다이아몬드 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_diamond_3", use_container_width=True):
            st.info("다이아몬드 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 16: 웨이브 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 16: 웨이브 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">호버 시 파도처럼 퍼지는 효과</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_wave_1", use_container_width=True):
            st.info("웨이브 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_wave_2", use_container_width=True):
            st.info("웨이브 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_wave_3", use_container_width=True):
            st.info("웨이브 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 17: 스플릿 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 17: 스플릿 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">중앙에서 양쪽으로 퍼지는 빛 효과</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_split_1", use_container_width=True):
            st.info("스플릿 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_split_2", use_container_width=True):
            st.info("스플릿 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_split_3", use_container_width=True):
            st.info("스플릿 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 18: 매트릭스 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 18: 매트릭스 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">호버 시 매트릭스 코드가 흐르는 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_matrix_1", use_container_width=True):
            st.info("매트릭스 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_matrix_2", use_container_width=True):
            st.info("매트릭스 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_matrix_3", use_container_width=True):
            st.info("매트릭스 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 19: 그라데이션 보더
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 19: 그라데이션 보더</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">그라데이션 테두리를 가진 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_border_grad_1", use_container_width=True):
            st.info("그라데이션 보더 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_border_grad_2", use_container_width=True):
            st.info("그라데이션 보더 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_border_grad_3", use_container_width=True):
            st.info("그라데이션 보더 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 20: 반사 효과
    st.markdown('<div class="btn-gallery-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 20: 반사 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">유리처럼 반사되는 효과의 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ 입력하기", key="btn_reflect_1", use_container_width=True):
            st.info("반사 효과 버튼 1 클릭됨")
    with col2:
        if st.button("▶ 분석하기", key="btn_reflect_2", use_container_width=True):
            st.info("반사 효과 버튼 2 클릭됨")
    with col3:
        if st.button("▶ 설계하기", key="btn_reflect_3", use_container_width=True):
            st.info("반사 효과 버튼 3 클릭됨")
    st.markdown('</div>', unsafe_allow_html=True)

