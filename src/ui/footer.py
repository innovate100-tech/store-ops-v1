"""
CAUSE OS 전용 제품 푸터 컴포넌트
모든 페이지 하단에 표시되는 브랜드 시그니처
"""
import streamlit as st


def render_cause_os_footer(style="default"):
    """
    CAUSE OS 푸터 렌더링
    
    Args:
        style: "default" (기본형) 또는 "brand" (브랜드형)
    
    Note:
        - OS 명판 / 브랜드 시그니처 역할
        - 얇고 작은 폰트, 연한 톤
        - 페이지 맨 아래 마침표 역할
    """
    # CSS 주입 (1회만)
    if not st.session_state.get("_ps_footer_css_injected", False):
        css = """
        <style id="ps-footer-style">
        /* 본질적 해결: 모든 부모 요소까지 오른쪽 정렬 강제 */
        .ps-cause-footer-wrapper,
        .ps-cause-footer-wrapper *,
        .ps-cause-footer,
        .ps-cause-footer * {
            text-align: right !important;
            direction: ltr !important;
        }
        
        .ps-cause-footer-wrapper {
            width: 100% !important;
            display: block !important;
            margin-top: 4rem !important;
            padding: 2.5rem 0 1.5rem 0 !important;
            border-top: 1px solid rgba(148, 163, 184, 0.12) !important;
            position: relative !important;
            text-align: right !important;
            direction: ltr !important;
        }
        
        .ps-cause-footer {
            width: 100% !important;
            display: block !important;
            text-align: right !important;
            color: rgba(148, 163, 184, 0.65) !important;
            font-size: 0.8rem !important;
            line-height: 1.7 !important;
            font-weight: 400 !important;
            letter-spacing: 0.02em !important;
            direction: ltr !important;
        }
        
        .ps-cause-footer::before {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            width: 60px;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.3), transparent);
        }
        
        .ps-cause-footer > div {
            width: 100% !important;
            display: block !important;
            text-align: right !important;
            direction: ltr !important;
        }
        
        .ps-cause-footer > div:first-child {
            margin-bottom: 0.5rem !important;
        }
        
        .ps-cause-footer-brand,
        .ps-cause-footer-tagline,
        .ps-cause-footer-copyright,
        .ps-cause-footer-separator,
        .ps-cause-footer span {
            text-align: right !important;
            direction: ltr !important;
            display: inline !important;
        }
        
        .ps-cause-footer-brand {
            font-weight: 700 !important;
            color: rgba(148, 163, 184, 0.85) !important;
            letter-spacing: 0.08em !important;
            font-size: 0.85rem !important;
        }
        
        .ps-cause-footer-tagline {
            color: rgba(148, 163, 184, 0.55) !important;
            font-size: 0.75rem !important;
            font-weight: 400 !important;
            letter-spacing: 0.01em !important;
        }
        
        .ps-cause-footer-copyright {
            color: rgba(148, 163, 184, 0.45) !important;
            font-size: 0.7rem !important;
            margin-top: 0.75rem !important;
            font-weight: 300 !important;
            letter-spacing: 0.03em !important;
        }
        
        .ps-cause-footer-separator {
            color: rgba(148, 163, 184, 0.35) !important;
            margin: 0 0.6rem !important;
            font-weight: 300 !important;
        }
        
        /* Streamlit 마크다운 컨테이너 완전 오버라이드 */
        [data-testid="stMarkdownContainer"]:has(.ps-cause-footer-wrapper),
        [data-testid="stMarkdownContainer"] .ps-cause-footer-wrapper,
        .stMarkdown:has(.ps-cause-footer-wrapper),
        .stMarkdown .ps-cause-footer-wrapper {
            text-align: right !important;
            direction: ltr !important;
        }
        
        /* 전역 transition이 푸터에 영향을 주지 않도록 */
        .ps-cause-footer-wrapper,
        .ps-cause-footer-wrapper *,
        .ps-cause-footer,
        .ps-cause-footer * {
            transition: none !important;
        }
        
        /* 다크 모드 대응 */
        @media (prefers-color-scheme: dark) {
            .ps-cause-footer-wrapper {
                border-top-color: rgba(148, 163, 184, 0.15) !important;
            }
        }
        </style>
        <script>
        (function() {
            function forceFooterRightAlign() {
                var wrappers = document.querySelectorAll('.ps-cause-footer-wrapper');
                wrappers.forEach(function(wrapper) {
                    // 푸터 자체
                    wrapper.style.setProperty('text-align', 'right', 'important');
                    wrapper.style.setProperty('direction', 'ltr', 'important');
                    wrapper.style.setProperty('width', '100%', 'important');
                    wrapper.style.setProperty('display', 'block', 'important');
                    
                    // 모든 자식 요소
                    var allChildren = wrapper.querySelectorAll('*');
                    allChildren.forEach(function(child) {
                        child.style.setProperty('text-align', 'right', 'important');
                        child.style.setProperty('direction', 'ltr', 'important');
                    });
                    
                    // 모든 부모 요소를 찾아서 오른쪽 정렬 강제
                    var parent = wrapper.parentElement;
                    var depth = 0;
                    while (parent && depth < 10) { // 최대 10단계까지
                        parent.style.setProperty('text-align', 'right', 'important');
                        parent.style.setProperty('direction', 'ltr', 'important');
                        
                        // Streamlit 마크다운 컨테이너인 경우 특별 처리
                        if (parent.hasAttribute && parent.hasAttribute('data-testid')) {
                            var testid = parent.getAttribute('data-testid');
                            if (testid === 'stMarkdownContainer' || testid.includes('Markdown')) {
                                parent.style.setProperty('text-align', 'right', 'important');
                                parent.style.setProperty('direction', 'ltr', 'important');
                                parent.style.setProperty('display', 'block', 'important');
                            }
                        }
                        
                        // 클래스명으로도 확인
                        if (parent.classList && parent.classList.contains('stMarkdown')) {
                            parent.style.setProperty('text-align', 'right', 'important');
                            parent.style.setProperty('direction', 'ltr', 'important');
                        }
                        
                        parent = parent.parentElement;
                        depth++;
                    }
                });
            }
            
            // 즉시 실행
            forceFooterRightAlign();
            
            // DOM 로드 후 실행
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    forceFooterRightAlign();
                    setTimeout(forceFooterRightAlign, 50);
                    setTimeout(forceFooterRightAlign, 200);
                    setTimeout(forceFooterRightAlign, 500);
                });
            } else {
                setTimeout(forceFooterRightAlign, 50);
                setTimeout(forceFooterRightAlign, 200);
                setTimeout(forceFooterRightAlign, 500);
            }
            
            // load 이벤트
            window.addEventListener('load', function() {
                setTimeout(forceFooterRightAlign, 100);
                setTimeout(forceFooterRightAlign, 500);
            });
            
            // MutationObserver로 새로 추가된 푸터 감지
            if (window.MutationObserver) {
                var observer = new MutationObserver(function(mutations) {
                    var hasFooter = false;
                    mutations.forEach(function(mutation) {
                        if (mutation.addedNodes) {
                            mutation.addedNodes.forEach(function(node) {
                                if (node.nodeType === 1) {
                                    if (node.classList && (node.classList.contains('ps-cause-footer-wrapper') || node.classList.contains('ps-cause-footer'))) {
                                        hasFooter = true;
                                    } else if (node.querySelector && node.querySelector('.ps-cause-footer-wrapper, .ps-cause-footer')) {
                                        hasFooter = true;
                                    }
                                }
                            });
                        }
                    });
                    if (hasFooter) {
                        setTimeout(forceFooterRightAlign, 10);
                        setTimeout(forceFooterRightAlign, 100);
                    }
                });
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            }
            
            // 주기적 확인 (더 자주)
            setInterval(forceFooterRightAlign, 1000);
        })();
        </script>
        """
        st.markdown(css, unsafe_allow_html=True)
        st.session_state["_ps_footer_css_injected"] = True
    
    # 푸터 내용 렌더링 - 인라인 스타일로 강제
    if style == "brand":
        # 2안: 브랜드형
        st.markdown("""
        <div class="ps-cause-footer-wrapper" style="text-align: right !important; direction: ltr !important; width: 100% !important; display: block !important;">
            <div class="ps-cause-footer" style="text-align: right !important; direction: ltr !important; width: 100% !important; display: block !important;">
                <div style="text-align: right !important; direction: ltr !important; display: block !important;">
                    <span class="ps-cause-footer-brand" style="text-align: right !important;">CAUSE OS</span>
                    <span class="ps-cause-footer-separator">·</span>
                    <span class="ps-cause-footer-tagline" style="text-align: right !important;">우리는 매출을 보지 않습니다. 원인을 봅니다.</span>
                </div>
                <div class="ps-cause-footer-copyright" style="text-align: right !important; direction: ltr !important; display: block !important;">by INNOVATION100</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 1안: 기본형
        st.markdown("""
        <div class="ps-cause-footer-wrapper" style="text-align: right !important; direction: ltr !important; width: 100% !important; display: block !important;">
            <div class="ps-cause-footer" style="text-align: right !important; direction: ltr !important; width: 100% !important; display: block !important;">
                <div style="text-align: right !important; direction: ltr !important; display: block !important;">
                    <span class="ps-cause-footer-brand" style="text-align: right !important;">CAUSE OS</span>
                    <span class="ps-cause-footer-separator">—</span>
                    <span style="text-align: right !important;">성공에는 이유가 있습니다</span>
                </div>
                <div class="ps-cause-footer-copyright" style="text-align: right !important; direction: ltr !important; display: block !important;">© 2026 INNOVATION100. All rights reserved.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
