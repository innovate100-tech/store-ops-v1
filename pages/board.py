"""
게시판 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
from datetime import datetime
from src.ui_helpers import render_page_header
from src.auth import get_current_store_name

# 공통 설정 적용
bootstrap(page_title="Board")


def render_board():
    """게시판 페이지 렌더링"""
    render_page_header("게시판", "📌")
    
    # 게시판 데이터 (임시 - 추후 DB 연결)
    if 'board_posts' not in st.session_state:
        st.session_state.board_posts = []
    
    # 게시글 작성
    with st.expander("✏️ 새 게시글 작성", expanded=False):
        post_title = st.text_input("제목", key="board_title")
        post_content = st.text_area("내용", key="board_content", height=200)
        if st.button("작성", key="board_submit", type="primary"):
            if post_title and post_content:
                new_post = {
                    'id': len(st.session_state.board_posts) + 1,
                    'title': post_title,
                    'content': post_content,
                    'author': get_current_store_name(),
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                }
                st.session_state.board_posts.insert(0, new_post)
                st.success("게시글이 작성되었습니다!")
                st.rerun()
            else:
                st.error("제목과 내용을 모두 입력해주세요.")
    
    # 게시글 목록
    if st.session_state.board_posts:
        st.markdown("**📌 게시글 목록**")
        for post in st.session_state.board_posts:
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 3px solid #667eea;">
                    <div style="font-weight: 600; font-size: 1.2rem; margin-bottom: 0.5rem; color: #ffffff;">{post['title']}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.95rem; margin-bottom: 0.8rem; line-height: 1.6; white-space: pre-wrap;">{post['content']}</div>
                    <div style="color: rgba(255,255,255,0.5); font-size: 0.85rem;">👤 {post['author']} • 📅 {post['date']}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("게시글이 없습니다. 첫 게시글을 작성해보세요!")


# Streamlit 멀티페이지에서 직접 실행될 때
render_board()
