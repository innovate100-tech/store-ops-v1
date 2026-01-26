"""
Streamlit 버튼 디자인 갤러리
다양한 CSS 스타일을 적용한 Streamlit 버튼 디자인 모음
"""
import streamlit as st


def render_header_unified_test2():
    """Streamlit 버튼 디자인 갤러리"""
    
    st.title("🎨 Streamlit 버튼 디자인 갤러리")
    st.caption("CSS와 JavaScript로 스타일링한 다양한 Streamlit 버튼 디자인")
    
    # CSS 스타일 정의 - 더 강력한 선택자 사용
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
    
    /* Streamlit 버튼 기본 스타일 오버라이드 - 모든 가능한 선택자 */
    .btn-gallery-section .stButton > button,
    .btn-gallery-section button[data-testid],
    .btn-gallery-section button,
    .btn-gallery-section .stButton button,
    .btn-gallery-section [class*="stButton"] button,
    .btn-gallery-section [data-testid*="button"] {
        width: 100% !important;
        min-width: 150px !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
        cursor: pointer !important;
        border: none !important;
    }
    
    /* Streamlit 기본 버튼 스타일 강제 오버라이드 */
    .btn-gallery-section button {
        background-color: transparent !important;
        border-color: transparent !important;
    }
    
    /* 애니메이션 키프레임 */
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes pulse-glow {
        0%, 100% {
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.5), 0 0 40px rgba(59, 130, 246, 0.3);
            transform: scale(1);
        }
        50% {
            box-shadow: 0 0 30px rgba(59, 130, 246, 0.8), 0 0 60px rgba(59, 130, 246, 0.5);
            transform: scale(1.02);
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    # JavaScript로 버튼 스타일 적용 - 더 강력한 방법
    style_js = """
    <script>
    (function() {
        'use strict';
        
        function applyButtonStyles() {
            // 모든 가능한 방법으로 버튼 찾기
            const gallerySections = document.querySelectorAll('.btn-gallery-section');
            let allButtons = [];
            
            gallerySections.forEach(section => {
                // 여러 선택자로 버튼 찾기
                const selectors = [
                    '.stButton > button',
                    '.stButton button',
                    'button[data-testid]',
                    'button'
                ];
                
                selectors.forEach(selector => {
                    const buttons = section.querySelectorAll(selector);
                    buttons.forEach(btn => {
                        // 중복 제거
                        if (!allButtons.includes(btn) && btn.textContent.trim().includes('입력하기') || 
                            btn.textContent.trim().includes('분석하기') || 
                            btn.textContent.trim().includes('설계하기')) {
                            allButtons.push(btn);
                        }
                    });
                });
            });
            
            const buttons = allButtons;
            console.log('Found buttons:', buttons.length);
            
            if (buttons.length === 0) {
                console.warn('No buttons found!');
                return;
            }
            
            // 버튼 스타일 맵핑
            const buttonStyles = {
                'btn_neon_1': {
                    background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
                    color: 'white',
                    boxShadow: '0 0 20px rgba(59, 130, 246, 0.5), 0 0 40px rgba(59, 130, 246, 0.3), 0 0 60px rgba(59, 130, 246, 0.1)',
                    border: 'none'
                },
                'btn_neon_2': {
                    background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                    color: 'white',
                    boxShadow: '0 0 20px rgba(16, 185, 129, 0.5), 0 0 40px rgba(16, 185, 129, 0.3), 0 0 60px rgba(16, 185, 129, 0.1)',
                    border: 'none'
                },
                'btn_neon_3': {
                    background: 'linear-gradient(135deg, #A855F7 0%, #9333EA 100%)',
                    color: 'white',
                    boxShadow: '0 0 20px rgba(168, 85, 247, 0.5), 0 0 40px rgba(168, 85, 247, 0.3), 0 0 60px rgba(168, 85, 247, 0.1)',
                    border: 'none'
                },
                'btn_gradient_1': {
                    background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 50%, #1D4ED8 100%)',
                    backgroundSize: '200% 200%',
                    color: 'white',
                    boxShadow: '0 4px 15px rgba(59, 130, 246, 0.4)',
                    border: 'none',
                    animation: 'gradient-shift 3s ease infinite'
                },
                'btn_gradient_2': {
                    background: 'linear-gradient(135deg, #10B981 0%, #059669 50%, #047857 100%)',
                    backgroundSize: '200% 200%',
                    color: 'white',
                    boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)',
                    border: 'none',
                    animation: 'gradient-shift 3s ease infinite'
                },
                'btn_gradient_3': {
                    background: 'linear-gradient(135deg, #A855F7 0%, #9333EA 50%, #7E22CE 100%)',
                    backgroundSize: '200% 200%',
                    color: 'white',
                    boxShadow: '0 4px 15px rgba(168, 85, 247, 0.4)',
                    border: 'none',
                    animation: 'gradient-shift 3s ease infinite'
                },
                'btn_3d_1': {
                    background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
                    color: 'white',
                    boxShadow: '0 8px 0 #1E40AF, 0 12px 20px rgba(0, 0, 0, 0.3)',
                    border: 'none'
                },
                'btn_3d_2': {
                    background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                    color: 'white',
                    boxShadow: '0 8px 0 #047857, 0 12px 20px rgba(0, 0, 0, 0.3)',
                    border: 'none'
                },
                'btn_3d_3': {
                    background: 'linear-gradient(135deg, #A855F7 0%, #9333EA 100%)',
                    color: 'white',
                    boxShadow: '0 8px 0 #7E22CE, 0 12px 20px rgba(0, 0, 0, 0.3)',
                    border: 'none'
                },
                'btn_glass_1': {
                    background: 'rgba(59, 130, 246, 0.2)',
                    backdropFilter: 'blur(10px)',
                    color: 'white',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    boxShadow: '0 8px 32px rgba(59, 130, 246, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
                },
                'btn_glass_2': {
                    background: 'rgba(16, 185, 129, 0.2)',
                    backdropFilter: 'blur(10px)',
                    color: 'white',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    boxShadow: '0 8px 32px rgba(16, 185, 129, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
                },
                'btn_glass_3': {
                    background: 'rgba(168, 85, 247, 0.2)',
                    backdropFilter: 'blur(10px)',
                    color: 'white',
                    border: '1px solid rgba(168, 85, 247, 0.3)',
                    boxShadow: '0 8px 32px rgba(168, 85, 247, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
                },
                'btn_holo_1': {
                    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.9) 0%, rgba(37, 99, 235, 0.9) 100%)',
                    color: 'white',
                    border: 'none'
                },
                'btn_holo_2': {
                    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.9) 0%, rgba(5, 150, 105, 0.9) 100%)',
                    color: 'white',
                    border: 'none'
                },
                'btn_holo_3': {
                    background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.9) 0%, rgba(147, 51, 234, 0.9) 100%)',
                    color: 'white',
                    border: 'none'
                },
                'btn_minimal_1': {
                    background: 'transparent',
                    color: '#3B82F6',
                    border: '2px solid #3B82F6'
                },
                'btn_minimal_2': {
                    background: 'transparent',
                    color: '#10B981',
                    border: '2px solid #10B981'
                },
                'btn_minimal_3': {
                    background: 'transparent',
                    color: '#A855F7',
                    border: '2px solid #A855F7'
                },
                'btn_pulse_1': {
                    background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
                    color: 'white',
                    border: 'none',
                    animation: 'pulse-glow 2s ease-in-out infinite'
                },
                'btn_pulse_2': {
                    background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                    color: 'white',
                    border: 'none',
                    animation: 'pulse-glow 2s ease-in-out infinite'
                },
                'btn_pulse_3': {
                    background: 'linear-gradient(135deg, #A855F7 0%, #9333EA 100%)',
                    color: 'white',
                    border: 'none',
                    animation: 'pulse-glow 2s ease-in-out infinite'
                },
                'btn_metallic_1': {
                    background: 'linear-gradient(135deg, #64748B 0%, #475569 50%, #334155 100%)',
                    color: 'white',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: 'inset 0 2px 4px rgba(255, 255, 255, 0.2), 0 4px 8px rgba(0, 0, 0, 0.3), inset 0 -2px 4px rgba(0, 0, 0, 0.3)'
                },
                'btn_metallic_2': {
                    background: 'linear-gradient(135deg, #64748B 0%, #475569 50%, #334155 100%)',
                    color: 'white',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: 'inset 0 2px 4px rgba(255, 255, 255, 0.2), 0 4px 8px rgba(0, 0, 0, 0.3), inset 0 -2px 4px rgba(0, 0, 0, 0.3)'
                },
                'btn_metallic_3': {
                    background: 'linear-gradient(135deg, #64748B 0%, #475569 50%, #334155 100%)',
                    color: 'white',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: 'inset 0 2px 4px rgba(255, 255, 255, 0.2), 0 4px 8px rgba(0, 0, 0, 0.3), inset 0 -2px 4px rgba(0, 0, 0, 0.3)'
                },
                'btn_stroke_1': {
                    background: 'transparent',
                    color: '#3B82F6',
                    border: '3px solid #3B82F6'
                },
                'btn_stroke_2': {
                    background: 'transparent',
                    color: '#10B981',
                    border: '3px solid #10B981'
                },
                'btn_stroke_3': {
                    background: 'transparent',
                    color: '#A855F7',
                    border: '3px solid #A855F7'
                },
                'btn_radial_1': {
                    background: 'radial-gradient(circle at center, #3B82F6 0%, #2563EB 100%)',
                    color: 'white',
                    border: 'none'
                },
                'btn_radial_2': {
                    background: 'radial-gradient(circle at center, #10B981 0%, #059669 100%)',
                    color: 'white',
                    border: 'none'
                },
                'btn_radial_3': {
                    background: 'radial-gradient(circle at center, #A855F7 0%, #9333EA 100%)',
                    color: 'white',
                    border: 'none'
                }
            };
            
            // 섹션별로 버튼 스타일 적용
            const styleMap = [
                // 섹션 1: 네온
                [
                    { bg: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)', shadow: '0 0 20px rgba(59, 130, 246, 0.5), 0 0 40px rgba(59, 130, 246, 0.3), 0 0 60px rgba(59, 130, 246, 0.1)' },
                    { bg: 'linear-gradient(135deg, #10B981 0%, #059669 100%)', shadow: '0 0 20px rgba(16, 185, 129, 0.5), 0 0 40px rgba(16, 185, 129, 0.3), 0 0 60px rgba(16, 185, 129, 0.1)' },
                    { bg: 'linear-gradient(135deg, #A855F7 0%, #9333EA 100%)', shadow: '0 0 20px rgba(168, 85, 247, 0.5), 0 0 40px rgba(168, 85, 247, 0.3), 0 0 60px rgba(168, 85, 247, 0.1)' }
                ],
                // 섹션 2: 그라데이션
                [
                    { bg: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 50%, #1D4ED8 100%)', shadow: '0 4px 15px rgba(59, 130, 246, 0.4)', anim: 'gradient-shift 3s ease infinite', bgSize: '200% 200%' },
                    { bg: 'linear-gradient(135deg, #10B981 0%, #059669 50%, #047857 100%)', shadow: '0 4px 15px rgba(16, 185, 129, 0.4)', anim: 'gradient-shift 3s ease infinite', bgSize: '200% 200%' },
                    { bg: 'linear-gradient(135deg, #A855F7 0%, #9333EA 50%, #7E22CE 100%)', shadow: '0 4px 15px rgba(168, 85, 247, 0.4)', anim: 'gradient-shift 3s ease infinite', bgSize: '200% 200%' }
                ],
                // 섹션 3: 3D
                [
                    { bg: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)', shadow: '0 8px 0 #1E40AF, 0 12px 20px rgba(0, 0, 0, 0.3)' },
                    { bg: 'linear-gradient(135deg, #10B981 0%, #059669 100%)', shadow: '0 8px 0 #047857, 0 12px 20px rgba(0, 0, 0, 0.3)' },
                    { bg: 'linear-gradient(135deg, #A855F7 0%, #9333EA 100%)', shadow: '0 8px 0 #7E22CE, 0 12px 20px rgba(0, 0, 0, 0.3)' }
                ],
                // 섹션 4: 글래스
                [
                    { bg: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.3)', shadow: '0 8px 32px rgba(59, 130, 246, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)', blur: 'blur(10px)' },
                    { bg: 'rgba(16, 185, 129, 0.2)', border: '1px solid rgba(16, 185, 129, 0.3)', shadow: '0 8px 32px rgba(16, 185, 129, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)', blur: 'blur(10px)' },
                    { bg: 'rgba(168, 85, 247, 0.2)', border: '1px solid rgba(168, 85, 247, 0.3)', shadow: '0 8px 32px rgba(168, 85, 247, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)', blur: 'blur(10px)' }
                ],
                // 섹션 5: 홀로그램
                [
                    { bg: 'linear-gradient(135deg, rgba(59, 130, 246, 0.9) 0%, rgba(37, 99, 235, 0.9) 100%)' },
                    { bg: 'linear-gradient(135deg, rgba(16, 185, 129, 0.9) 0%, rgba(5, 150, 105, 0.9) 100%)' },
                    { bg: 'linear-gradient(135deg, rgba(168, 85, 247, 0.9) 0%, rgba(147, 51, 234, 0.9) 100%)' }
                ],
                // 섹션 6: 미니멀
                [
                    { bg: 'transparent', color: '#3B82F6', border: '2px solid #3B82F6' },
                    { bg: 'transparent', color: '#10B981', border: '2px solid #10B981' },
                    { bg: 'transparent', color: '#A855F7', border: '2px solid #A855F7' }
                ],
                // 섹션 7: 펄스
                [
                    { bg: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)', anim: 'pulse-glow 2s ease-in-out infinite' },
                    { bg: 'linear-gradient(135deg, #10B981 0%, #059669 100%)', anim: 'pulse-glow 2s ease-in-out infinite' },
                    { bg: 'linear-gradient(135deg, #A855F7 0%, #9333EA 100%)', anim: 'pulse-glow 2s ease-in-out infinite' }
                ],
                // 섹션 8: 메탈릭
                [
                    { bg: 'linear-gradient(135deg, #64748B 0%, #475569 50%, #334155 100%)', border: '1px solid rgba(255, 255, 255, 0.1)', shadow: 'inset 0 2px 4px rgba(255, 255, 255, 0.2), 0 4px 8px rgba(0, 0, 0, 0.3), inset 0 -2px 4px rgba(0, 0, 0, 0.3)' },
                    { bg: 'linear-gradient(135deg, #64748B 0%, #475569 50%, #334155 100%)', border: '1px solid rgba(255, 255, 255, 0.1)', shadow: 'inset 0 2px 4px rgba(255, 255, 255, 0.2), 0 4px 8px rgba(0, 0, 0, 0.3), inset 0 -2px 4px rgba(0, 0, 0, 0.3)' },
                    { bg: 'linear-gradient(135deg, #64748B 0%, #475569 50%, #334155 100%)', border: '1px solid rgba(255, 255, 255, 0.1)', shadow: 'inset 0 2px 4px rgba(255, 255, 255, 0.2), 0 4px 8px rgba(0, 0, 0, 0.3), inset 0 -2px 4px rgba(0, 0, 0, 0.3)' }
                ],
                // 섹션 9: 스트로크
                [
                    { bg: 'transparent', color: '#3B82F6', border: '3px solid #3B82F6' },
                    { bg: 'transparent', color: '#10B981', border: '3px solid #10B981' },
                    { bg: 'transparent', color: '#A855F7', border: '3px solid #A855F7' }
                ],
                // 섹션 10: 라디얼
                [
                    { bg: 'radial-gradient(circle at center, #3B82F6 0%, #2563EB 100%)' },
                    { bg: 'radial-gradient(circle at center, #10B981 0%, #059669 100%)' },
                    { bg: 'radial-gradient(circle at center, #A855F7 0%, #9333EA 100%)' }
                ]
            ];
            
            // 섹션별로 버튼 스타일 적용
            gallerySections.forEach((section, sectionIndex) => {
                if (sectionIndex >= styleMap.length) return;
                
                const sectionStyles = styleMap[sectionIndex];
                const sectionButtons = Array.from(section.querySelectorAll('.stButton > button, button')).slice(0, 3);
                
                sectionButtons.forEach((btn, btnIndex) => {
                    if (btnIndex >= sectionStyles.length) return;
                    
                    const style = sectionStyles[btnIndex];
                    console.log('Applying style to button', sectionIndex, btnIndex, style);
                    
                    // 기본 스타일 강제 적용
                    if (style.bg) btn.style.setProperty('background', style.bg, 'important');
                    if (style.color) btn.style.setProperty('color', style.color, 'important');
                    if (style.border) btn.style.setProperty('border', style.border, 'important');
                    if (style.shadow) btn.style.setProperty('box-shadow', style.shadow, 'important');
                    if (style.anim) btn.style.setProperty('animation', style.anim, 'important');
                    if (style.bgSize) btn.style.setProperty('background-size', style.bgSize, 'important');
                    if (style.blur) btn.style.setProperty('backdrop-filter', style.blur, 'important');
                    
                    // 기본 속성 강제 설정
                    if (!style.color) btn.style.setProperty('color', 'white', 'important');
                    if (!style.border) btn.style.setProperty('border', 'none', 'important');
                    
                    btn.style.setProperty('min-width', '150px', 'important');
                    btn.style.setProperty('padding', '1rem 2rem', 'important');
                    btn.style.setProperty('border-radius', '12px', 'important');
                    btn.style.setProperty('font-size', '1rem', 'important');
                    btn.style.setProperty('font-weight', '600', 'important');
                    btn.style.setProperty('transition', 'all 0.3s ease', 'important');
                    btn.style.setProperty('position', 'relative', 'important');
                    btn.style.setProperty('overflow', 'hidden', 'important');
                    btn.style.setProperty('cursor', 'pointer', 'important');
                    btn.style.setProperty('width', '100%', 'important');
                });
            });
        }
        
        // 즉시 여러 번 실행 (Streamlit의 동적 렌더링 대응)
        function runMultipleTimes() {
            applyButtonStyles();
            setTimeout(applyButtonStyles, 100);
            setTimeout(applyButtonStyles, 300);
            setTimeout(applyButtonStyles, 500);
            setTimeout(applyButtonStyles, 1000);
            setTimeout(applyButtonStyles, 2000);
        }
        
        // 즉시 실행
        runMultipleTimes();
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', runMultipleTimes);
        }
        
        // DOM 변경 감지
        const observer = new MutationObserver(function() {
            setTimeout(applyButtonStyles, 100);
        });
        
        if (document.body) {
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['class', 'style']
            });
        }
        
        // 주기적 확인 (매우 자주)
        setInterval(applyButtonStyles, 300);
        
        // 페이지 로드 후에도 실행
        window.addEventListener('load', runMultipleTimes);
        
        // Streamlit의 rerun 대응
        if (window.parent !== window) {
            window.parent.addEventListener('load', runMultipleTimes);
        }
    })();
    </script>
    """
    st.markdown(style_js, unsafe_allow_html=True)
    
    # 변형 1: 네온 글로우 효과
    st.markdown('<div class="btn-gallery-section" data-section="neon">', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-title">변형 1: 네온 글로우 효과</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-gallery-desc">강렬한 네온 빛 효과로 시선을 끄는 버튼</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div data-btn-key="btn_neon_1">', unsafe_allow_html=True)
        if st.button("▶ 입력하기", key="btn_neon_1", use_container_width=True):
            st.info("네온 글로우 버튼 1 클릭됨")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div data-btn-key="btn_neon_2">', unsafe_allow_html=True)
        if st.button("▶ 분석하기", key="btn_neon_2", use_container_width=True):
            st.info("네온 글로우 버튼 2 클릭됨")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div data-btn-key="btn_neon_3">', unsafe_allow_html=True)
        if st.button("▶ 설계하기", key="btn_neon_3", use_container_width=True):
            st.info("네온 글로우 버튼 3 클릭됨")
        st.markdown('</div>', unsafe_allow_html=True)
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
