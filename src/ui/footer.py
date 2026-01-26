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
        /* 본질적 해결: 푸터를 완전히 독립적인 구조로 */
        .ps-cause-footer-wrapper {
            width: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-end !important;
            justify-content: flex-end !important;
            margin-top: 4rem !important;
            padding: 2.5rem 0 1.5rem 0 !important;
            border-top: 1px solid rgba(148, 163, 184, 0.12) !important;
            position: relative !important;
        }
        
        .ps-cause-footer {
            width: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-end !important;
            justify-content: flex-end !important;
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
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-end !important;
            justify-content: flex-end !important;
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
            display: inline-block !important;
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
        
        /* Streamlit 기본 스타일 완전 오버라이드 */
        [data-testid="stMarkdownContainer"] .ps-cause-footer-wrapper,
        [data-testid="stMarkdownContainer"] .ps-cause-footer-wrapper *,
        .stMarkdown .ps-cause-footer-wrapper,
        .stMarkdown .ps-cause-footer-wrapper *,
        .ps-cause-footer-wrapper,
        .ps-cause-footer-wrapper *,
        .ps-cause-footer,
        .ps-cause-footer * {
            text-align: right !important;
            direction: ltr !important;
            align-items: flex-end !important;
            justify-content: flex-end !important;
        }
        
        /* 부모 컨테이너도 오른쪽 정렬 */
        [data-testid="stMarkdownContainer"]:has(.ps-cause-footer-wrapper),
        .stMarkdown:has(.ps-cause-footer-wrapper),
        [data-testid="stAppViewContainer"]:has(.ps-cause-footer-wrapper) {
            text-align: right !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-end !important;
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
                    // Flexbox로 강제 오른쪽 정렬
                    wrapper.style.setProperty('display', 'flex', 'important');
                    wrapper.style.setProperty('flex-direction', 'column', 'important');
                    wrapper.style.setProperty('align-items', 'flex-end', 'important');
                    wrapper.style.setProperty('justify-content', 'flex-end', 'important');
                    wrapper.style.setProperty('width', '100%', 'important');
                    wrapper.style.setProperty('text-align', 'right', 'important');
                    wrapper.style.setProperty('direction', 'ltr', 'important');
                    
                    var footer = wrapper.querySelector('.ps-cause-footer');
                    if (footer) {
                        footer.style.setProperty('display', 'flex', 'important');
                        footer.style.setProperty('flex-direction', 'column', 'important');
                        footer.style.setProperty('align-items', 'flex-end', 'important');
                        footer.style.setProperty('justify-content', 'flex-end', 'important');
                        footer.style.setProperty('width', '100%', 'important');
                        footer.style.setProperty('text-align', 'right', 'important');
                        footer.style.setProperty('direction', 'ltr', 'important');
                        
                        // 모든 자식 요소
                        var children = footer.querySelectorAll('*');
                        children.forEach(function(child) {
                            child.style.setProperty('text-align', 'right', 'important');
                            child.style.setProperty('direction', 'ltr', 'important');
                        });
                    }
                    
                    // 부모 컨테이너도 강제
                    var parent = wrapper.parentElement;
                    if (parent) {
                        parent.style.setProperty('text-align', 'right', 'important');
                        var computed = window.getComputedStyle(parent);
                        if (computed.display !== 'flex') {
                            parent.style.setProperty('display', 'flex', 'important');
                            parent.style.setProperty('flex-direction', 'column', 'important');
                            parent.style.setProperty('align-items', 'flex-end', 'important');
                        }
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
                });
            } else {
                setTimeout(forceFooterRightAlign, 50);
                setTimeout(forceFooterRightAlign, 200);
            }
            
            // load 이벤트
            window.addEventListener('load', function() {
                setTimeout(forceFooterRightAlign, 100);
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
                    }
                });
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            }
            
            // 주기적 확인
            setInterval(forceFooterRightAlign, 2000);
        })();
        </script>
        """
        st.markdown(css, unsafe_allow_html=True)
        st.session_state["_ps_footer_css_injected"] = True
    
    # 푸터 내용 렌더링 - Flexbox 구조로 변경
    if style == "brand":
        # 2안: 브랜드형
        st.markdown("""
        <div class="ps-cause-footer-wrapper">
            <div class="ps-cause-footer">
                <div>
                    <span class="ps-cause-footer-brand">CAUSE OS</span>
                    <span class="ps-cause-footer-separator">·</span>
                    <span class="ps-cause-footer-tagline">우리는 매출을 보지 않습니다. 원인을 봅니다.</span>
                </div>
                <div class="ps-cause-footer-copyright">by INNOVATION100</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 1안: 기본형
        st.markdown("""
        <div class="ps-cause-footer-wrapper">
            <div class="ps-cause-footer">
                <div>
                    <span class="ps-cause-footer-brand">CAUSE OS</span>
                    <span class="ps-cause-footer-separator">—</span>
                    <span>성공에는 이유가 있습니다</span>
                </div>
                <div class="ps-cause-footer-copyright">© 2026 INNOVATION100. All rights reserved.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
