"""
홈화면 리뉴얼 테스트 페이지 2
링크 버튼 8가지 디자인 변형
"""
import streamlit as st


def render_header_unified_test2():
    """링크 버튼 8가지 디자인 변형 테스트"""
    
    st.title("🎨 링크 버튼 디자인 변형 테스트")
    st.caption("8가지 다른 스타일과 효과를 적용한 버튼 디자인")
    
    # 8가지 디자인 변형 CSS
    css = """
    <style>
    /* 공통 스타일 */
    .btn-variant-section {
        margin-bottom: 4rem;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%);
        border-radius: 24px;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .btn-variant-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .btn-variant-desc {
        font-size: 0.9rem;
        color: #94A3B8;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .btn-group {
        display: flex;
        gap: 1.5rem;
        justify-content: center;
        flex-wrap: wrap;
    }
    
    /* 버튼 공통 기본 스타일 */
    .link-btn {
        min-width: 150px;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 600;
        color: white;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        text-align: center;
    }
    
    /* 변형 1: 네온 글로우 효과 */
    .btn-neon-1 {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5),
                    0 0 40px rgba(59, 130, 246, 0.3),
                    0 0 60px rgba(59, 130, 246, 0.1);
    }
    
    .btn-neon-1:hover {
        box-shadow: 0 0 30px rgba(59, 130, 246, 0.8),
                    0 0 60px rgba(59, 130, 246, 0.5),
                    0 0 90px rgba(59, 130, 246, 0.3);
        transform: translateY(-2px);
    }
    
    .btn-neon-2 {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.5),
                    0 0 40px rgba(16, 185, 129, 0.3),
                    0 0 60px rgba(16, 185, 129, 0.1);
    }
    
    .btn-neon-2:hover {
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.8),
                    0 0 60px rgba(16, 185, 129, 0.5),
                    0 0 90px rgba(16, 185, 129, 0.3);
        transform: translateY(-2px);
    }
    
    .btn-neon-3 {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%);
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.5),
                    0 0 40px rgba(168, 85, 247, 0.3),
                    0 0 60px rgba(168, 85, 247, 0.1);
    }
    
    .btn-neon-3:hover {
        box-shadow: 0 0 30px rgba(168, 85, 247, 0.8),
                    0 0 60px rgba(168, 85, 247, 0.5),
                    0 0 90px rgba(168, 85, 247, 0.3);
        transform: translateY(-2px);
    }
    
    /* 변형 2: 그라데이션 애니메이션 */
    .btn-gradient-1 {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 50%, #1D4ED8 100%);
        background-size: 200% 200%;
        animation: gradient-shift 3s ease infinite;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }
    
    .btn-gradient-2 {
        background: linear-gradient(135deg, #10B981 0%, #059669 50%, #047857 100%);
        background-size: 200% 200%;
        animation: gradient-shift 3s ease infinite;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
    }
    
    .btn-gradient-3 {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 50%, #7E22CE 100%);
        background-size: 200% 200%;
        animation: gradient-shift 3s ease infinite;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
    }
    
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    /* 변형 3: 3D 입체 효과 */
    .btn-3d-1 {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        box-shadow: 0 8px 0 #1E40AF,
                    0 12px 20px rgba(0, 0, 0, 0.3);
        transform: perspective(1000px) rotateX(0deg);
    }
    
    .btn-3d-1:hover {
        transform: perspective(1000px) rotateX(5deg) translateY(2px);
        box-shadow: 0 4px 0 #1E40AF,
                    0 8px 15px rgba(0, 0, 0, 0.3);
    }
    
    .btn-3d-1:active {
        transform: perspective(1000px) rotateX(10deg) translateY(4px);
        box-shadow: 0 2px 0 #1E40AF,
                    0 4px 10px rgba(0, 0, 0, 0.3);
    }
    
    .btn-3d-2 {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        box-shadow: 0 8px 0 #047857,
                    0 12px 20px rgba(0, 0, 0, 0.3);
        transform: perspective(1000px) rotateX(0deg);
    }
    
    .btn-3d-2:hover {
        transform: perspective(1000px) rotateX(5deg) translateY(2px);
        box-shadow: 0 4px 0 #047857,
                    0 8px 15px rgba(0, 0, 0, 0.3);
    }
    
    .btn-3d-2:active {
        transform: perspective(1000px) rotateX(10deg) translateY(4px);
        box-shadow: 0 2px 0 #047857,
                    0 4px 10px rgba(0, 0, 0, 0.3);
    }
    
    .btn-3d-3 {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%);
        box-shadow: 0 8px 0 #7E22CE,
                    0 12px 20px rgba(0, 0, 0, 0.3);
        transform: perspective(1000px) rotateX(0deg);
    }
    
    .btn-3d-3:hover {
        transform: perspective(1000px) rotateX(5deg) translateY(2px);
        box-shadow: 0 4px 0 #7E22CE,
                    0 8px 15px rgba(0, 0, 0, 0.3);
    }
    
    .btn-3d-3:active {
        transform: perspective(1000px) rotateX(10deg) translateY(4px);
        box-shadow: 0 2px 0 #7E22CE,
                    0 4px 10px rgba(0, 0, 0, 0.3);
    }
    
    /* 변형 4: 글래스모피즘 */
    .btn-glass-1 {
        background: rgba(59, 130, 246, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .btn-glass-1:hover {
        background: rgba(59, 130, 246, 0.3);
        border-color: rgba(59, 130, 246, 0.5);
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    .btn-glass-2 {
        background: rgba(16, 185, 129, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(16, 185, 129, 0.3);
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .btn-glass-2:hover {
        background: rgba(16, 185, 129, 0.3);
        border-color: rgba(16, 185, 129, 0.5);
        box-shadow: 0 12px 40px rgba(16, 185, 129, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    .btn-glass-3 {
        background: rgba(168, 85, 247, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(168, 85, 247, 0.3);
        box-shadow: 0 8px 32px rgba(168, 85, 247, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .btn-glass-3:hover {
        background: rgba(168, 85, 247, 0.3);
        border-color: rgba(168, 85, 247, 0.5);
        box-shadow: 0 12px 40px rgba(168, 85, 247, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    /* 변형 5: 홀로그램 효과 */
    .btn-holo-1 {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.9) 0%, rgba(37, 99, 235, 0.9) 100%);
        position: relative;
        overflow: hidden;
    }
    
    .btn-holo-1::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        animation: holo-shine 2s infinite;
    }
    
    .btn-holo-2 {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.9) 0%, rgba(5, 150, 105, 0.9) 100%);
        position: relative;
        overflow: hidden;
    }
    
    .btn-holo-2::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        animation: holo-shine 2s infinite;
    }
    
    .btn-holo-3 {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.9) 0%, rgba(147, 51, 234, 0.9) 100%);
        position: relative;
        overflow: hidden;
    }
    
    .btn-holo-3::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        animation: holo-shine 2s infinite;
    }
    
    @keyframes holo-shine {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    /* 변형 6: 파티클 효과 */
    .btn-particle-1 {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        position: relative;
        overflow: hidden;
    }
    
    .btn-particle-1::before {
        content: "";
        position: absolute;
        width: 4px;
        height: 4px;
        background: white;
        border-radius: 50%;
        top: 20%;
        left: 20%;
        animation: particle-float 3s ease-in-out infinite;
        opacity: 0.6;
    }
    
    .btn-particle-1::after {
        content: "";
        position: absolute;
        width: 3px;
        height: 3px;
        background: white;
        border-radius: 50%;
        top: 60%;
        left: 70%;
        animation: particle-float 2.5s ease-in-out infinite 0.5s;
        opacity: 0.6;
    }
    
    .btn-particle-2 {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        position: relative;
        overflow: hidden;
    }
    
    .btn-particle-2::before {
        content: "";
        position: absolute;
        width: 4px;
        height: 4px;
        background: white;
        border-radius: 50%;
        top: 20%;
        left: 20%;
        animation: particle-float 3s ease-in-out infinite;
        opacity: 0.6;
    }
    
    .btn-particle-2::after {
        content: "";
        position: absolute;
        width: 3px;
        height: 3px;
        background: white;
        border-radius: 50%;
        top: 60%;
        left: 70%;
        animation: particle-float 2.5s ease-in-out infinite 0.5s;
        opacity: 0.6;
    }
    
    .btn-particle-3 {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%);
        position: relative;
        overflow: hidden;
    }
    
    .btn-particle-3::before {
        content: "";
        position: absolute;
        width: 4px;
        height: 4px;
        background: white;
        border-radius: 50%;
        top: 20%;
        left: 20%;
        animation: particle-float 3s ease-in-out infinite;
        opacity: 0.6;
    }
    
    .btn-particle-3::after {
        content: "";
        position: absolute;
        width: 3px;
        height: 3px;
        background: white;
        border-radius: 50%;
        top: 60%;
        left: 70%;
        animation: particle-float 2.5s ease-in-out infinite 0.5s;
        opacity: 0.6;
    }
    
    @keyframes particle-float {
        0%, 100% { transform: translateY(0) translateX(0); opacity: 0.6; }
        50% { transform: translateY(-10px) translateX(10px); opacity: 1; }
    }
    
    /* 변형 7: 마이크로 인터랙션 */
    .btn-micro-1 {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        position: relative;
    }
    
    .btn-micro-1::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s ease, height 0.6s ease;
    }
    
    .btn-micro-1:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .btn-micro-1:hover {
        transform: scale(1.05);
    }
    
    .btn-micro-2 {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        position: relative;
    }
    
    .btn-micro-2::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s ease, height 0.6s ease;
    }
    
    .btn-micro-2:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .btn-micro-2:hover {
        transform: scale(1.05);
    }
    
    .btn-micro-3 {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%);
        position: relative;
    }
    
    .btn-micro-3::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s ease, height 0.6s ease;
    }
    
    .btn-micro-3:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .btn-micro-3:hover {
        transform: scale(1.05);
    }
    
    /* 변형 8: 미니멀 라인 아트 */
    .btn-minimal-1 {
        background: transparent;
        border: 2px solid #3B82F6;
        color: #3B82F6;
        position: relative;
    }
    
    .btn-minimal-1::before,
    .btn-minimal-1::after {
        content: "";
        position: absolute;
        width: 0;
        height: 0;
        border: 2px solid #3B82F6;
        transition: all 0.3s ease;
    }
    
    .btn-minimal-1::before {
        top: 0;
        left: 0;
        border-right: none;
        border-bottom: none;
    }
    
    .btn-minimal-1::after {
        bottom: 0;
        right: 0;
        border-left: none;
        border-top: none;
    }
    
    .btn-minimal-1:hover {
        background: rgba(59, 130, 246, 0.1);
        color: #60A5FA;
    }
    
    .btn-minimal-1:hover::before,
    .btn-minimal-1:hover::after {
        width: 100%;
        height: 100%;
    }
    
    .btn-minimal-2 {
        background: transparent;
        border: 2px solid #10B981;
        color: #10B981;
        position: relative;
    }
    
    .btn-minimal-2::before,
    .btn-minimal-2::after {
        content: "";
        position: absolute;
        width: 0;
        height: 0;
        border: 2px solid #10B981;
        transition: all 0.3s ease;
    }
    
    .btn-minimal-2::before {
        top: 0;
        left: 0;
        border-right: none;
        border-bottom: none;
    }
    
    .btn-minimal-2::after {
        bottom: 0;
        right: 0;
        border-left: none;
        border-top: none;
    }
    
    .btn-minimal-2:hover {
        background: rgba(16, 185, 129, 0.1);
        color: #34D399;
    }
    
    .btn-minimal-2:hover::before,
    .btn-minimal-2:hover::after {
        width: 100%;
        height: 100%;
    }
    
    .btn-minimal-3 {
        background: transparent;
        border: 2px solid #A855F7;
        color: #A855F7;
        position: relative;
    }
    
    .btn-minimal-3::before,
    .btn-minimal-3::after {
        content: "";
        position: absolute;
        width: 0;
        height: 0;
        border: 2px solid #A855F7;
        transition: all 0.3s ease;
    }
    
    .btn-minimal-3::before {
        top: 0;
        left: 0;
        border-right: none;
        border-bottom: none;
    }
    
    .btn-minimal-3::after {
        bottom: 0;
        right: 0;
        border-left: none;
        border-top: none;
    }
    
    .btn-minimal-3:hover {
        background: rgba(168, 85, 247, 0.1);
        color: #C084FC;
    }
    
    .btn-minimal-3:hover::before,
    .btn-minimal-3:hover::after {
        width: 100%;
        height: 100%;
    }
    
    /* 버튼 텍스트 z-index */
    .link-btn span {
        position: relative;
        z-index: 1;
    }
    
    /* 반응형 */
    @media (max-width: 768px) {
        .btn-group {
            flex-direction: column;
            align-items: center;
        }
        
        .link-btn {
            width: 100%;
            max-width: 300px;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    # 변형 1: 네온 글로우 효과
    st.markdown('<div class="btn-variant-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-title">변형 1: 네온 글로우 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-desc">강렬한 네온 빛 효과로 시선을 끄는 버튼</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-group">', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-neon-1"><span>▶ 입력하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-neon-2"><span>▶ 분석하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-neon-3"><span>▶ 설계하기</span></button>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 2: 그라데이션 애니메이션
    st.markdown('<div class="btn-variant-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-title">변형 2: 그라데이션 애니메이션</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-desc">움직이는 그라데이션으로 생동감 있는 버튼</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-group">', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-gradient-1"><span>▶ 입력하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-gradient-2"><span>▶ 분석하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-gradient-3"><span>▶ 설계하기</span></button>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 3: 3D 입체 효과
    st.markdown('<div class="btn-variant-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-title">변형 3: 3D 입체 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-desc">눌리는 듯한 입체감을 주는 3D 버튼</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-group">', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-3d-1"><span>▶ 입력하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-3d-2"><span>▶ 분석하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-3d-3"><span>▶ 설계하기</span></button>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 4: 글래스모피즘
    st.markdown('<div class="btn-variant-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-title">변형 4: 글래스모피즘</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-desc">반투명 유리 효과의 세련된 버튼</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-group">', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-glass-1"><span>▶ 입력하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-glass-2"><span>▶ 분석하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-glass-3"><span>▶ 설계하기</span></button>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 5: 홀로그램 효과
    st.markdown('<div class="btn-variant-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-title">변형 5: 홀로그램 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-desc">빛이 지나가는 홀로그램 스타일 버튼</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-group">', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-holo-1"><span>▶ 입력하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-holo-2"><span>▶ 분석하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-holo-3"><span>▶ 설계하기</span></button>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 6: 파티클 효과
    st.markdown('<div class="btn-variant-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-title">변형 6: 파티클 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-desc">떠다니는 파티클로 역동적인 버튼</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-group">', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-particle-1"><span>▶ 입력하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-particle-2"><span>▶ 분석하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-particle-3"><span>▶ 설계하기</span></button>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 7: 마이크로 인터랙션
    st.markdown('<div class="btn-variant-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-title">변형 7: 마이크로 인터랙션</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-desc">호버 시 리플 효과가 퍼지는 버튼</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-group">', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-micro-1"><span>▶ 입력하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-micro-2"><span>▶ 분석하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-micro-3"><span>▶ 설계하기</span></button>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 변형 8: 미니멀 라인 아트
    st.markdown('<div class="btn-variant-section">', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-title">변형 8: 미니멀 라인 아트</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-variant-desc">깔끔한 라인으로 구성된 미니멀 버튼</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-group">', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-minimal-1"><span>▶ 입력하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-minimal-2"><span>▶ 분석하기</span></button>', unsafe_allow_html=True)
    st.markdown('<button class="link-btn btn-minimal-3"><span>▶ 설계하기</span></button>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
