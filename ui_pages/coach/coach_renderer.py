"""
코치 판결 표준 렌더러
"""
import streamlit as st
from ui_pages.coach.coach_contract import CoachVerdict, get_level_config


def render_verdict_card(verdict: CoachVerdict, *, compact: bool = False):
    """판결 카드 렌더링"""
    config = get_level_config(verdict.level)
    
    if compact:
        # 컴팩트 버전 (한 줄)
        st.markdown(f"""
        <div style="padding: 0.5rem; border-left: 4px solid {config['color']}; background: rgba(0,0,0,0.02); border-radius: 4px; margin: 0.5rem 0;">
            <strong>{config['emoji']} {verdict.title}</strong><br>
            <small>{verdict.summary}</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 전체 버전
        st.markdown(f"""
        <div style="padding: 1rem; border-left: 4px solid {config['color']}; background: rgba(0,0,0,0.02); border-radius: 4px; margin: 1rem 0;">
            <h4 style="margin: 0 0 0.5rem 0; color: {config['color']};">
                {config['emoji']} {verdict.title}
            </h4>
            <p style="margin: 0 0 1rem 0; color: #333;">
                {verdict.summary}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 근거 그리드
        render_evidence_grid(verdict.evidence)
        
        # 액션 버튼
        render_actions(verdict.actions)


def render_verdict_strip(verdict: CoachVerdict):
    """홈/상단 스트립용 한줄 렌더링"""
    config = get_level_config(verdict.level)
    
    st.markdown(f"""
    <div style="padding: 0.75rem; background: rgba(0,0,0,0.03); border-radius: 4px; margin: 0.5rem 0;">
        <strong>{config['emoji']} {verdict.title}</strong> — {verdict.summary}
    </div>
    """, unsafe_allow_html=True)


def render_evidence_grid(evidence_list):
    """근거 그리드 렌더링"""
    if not evidence_list:
        return
    
    cols = st.columns(min(len(evidence_list), 4))
    for idx, evidence in enumerate(evidence_list):
        with cols[idx % len(cols)]:
            st.markdown(f"""
            <div style="padding: 0.75rem; background: rgba(0,0,0,0.02); border-radius: 4px; margin: 0.25rem 0;">
                <strong>{evidence.label}</strong><br>
                <span style="color: #666; font-size: 0.9em;">{evidence.value}</span>
                {f'<br><small style="color: #999;">{evidence.note}</small>' if evidence.note else ''}
            </div>
            """, unsafe_allow_html=True)


def render_actions(actions_list):
    """액션 버튼 렌더링"""
    if not actions_list:
        return
    
    cols = st.columns(min(len(actions_list), 3))
    for idx, action in enumerate(actions_list):
        with cols[idx % len(cols)]:
            if st.button(
                action.label,
                key=f"coach_action_{action.page}_{idx}",
                use_container_width=True,
                type="primary" if idx == 0 else "secondary"
            ):
                st.session_state.current_page = action.page
                st.rerun()
