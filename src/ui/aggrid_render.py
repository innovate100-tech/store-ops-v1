"""
AgGrid 공통 렌더 함수
다크 테마 적용 가능한 표준 테이블 컴포넌트
안전장치: 패키지가 없어도 st.dataframe으로 fallback
"""
import streamlit as st
import pandas as pd

# 안전한 import: 실패 시 fallback 모드로 전환
_AGGRID_AVAILABLE = False
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    _AGGRID_AVAILABLE = True
except ImportError:
    # 패키지가 없으면 fallback 모드
    pass

# DEV 모드 확인 함수
def _is_dev_mode():
    """DEV 모드 여부 확인"""
    try:
        from src.auth import is_dev_mode
        return is_dev_mode()
    except:
        return False


def render_aggrid(
    df: pd.DataFrame,
    key: str = None,
    height: int = 400,
    selectable: bool = False,
    sortable: bool = True,
    filterable: bool = True,
    resizable: bool = True,
    theme: str = "alpine"
):
    """
    AgGrid를 사용하여 DataFrame을 렌더링합니다.
    패키지가 없으면 자동으로 st.dataframe으로 fallback합니다.
    
    Args:
        df: 표시할 DataFrame
        key: 고유 키 (같은 페이지에 여러 AgGrid가 있을 때 필수)
        height: 그리드 높이 (픽셀)
        selectable: 행 선택 가능 여부
        sortable: 정렬 가능 여부
        filterable: 필터 가능 여부
        resizable: 컬럼 크기 조정 가능 여부
        theme: 테마 ("streamlit", "alpine", "balham" 등)
    
    Returns:
        AgGrid 컴포넌트 또는 None (fallback 시)
    """
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return None
    
    # AgGrid 패키지가 없으면 fallback
    if not _AGGRID_AVAILABLE:
        st.caption(f"⚠️ AGGRID NOT INSTALLED -> fallback dataframe (key: {key or 'no-key'})")
        st.dataframe(df, use_container_width=True, hide_index=True)
        return None
    
    # GridOptionsBuilder로 설정 구성
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # 기본 옵션 설정
    # AgGrid는 filterable 파라미터를 지원하지 않음. filter 속성 사용
    default_column_config = {
        'sortable': sortable,
        'resizable': resizable,
        'editable': False
    }
    # filterable은 filter 속성으로 설정
    if filterable:
        default_column_config['filter'] = True  # 또는 'agTextColumnFilter' 등 필터 타입 지정 가능
    
    gb.configure_default_column(**default_column_config)
    
    # 그리드 기본 스타일 설정 (다크 테마 명확히 보이도록)
    # enableRangeSelection은 deprecated되었으므로 제거
    gb.configure_grid_options(
        headerHeight=40,
        rowHeight=35,
        suppressRowHoverHighlight=False
    )
    
    # 행 선택 설정
    if selectable:
        gb.configure_selection('single' if not selectable else 'multiple')
    
    # 그리드 옵션 생성
    grid_options = gb.build()
    
    # getRowId는 함수를 전달해야 하는데 JSON 직렬화가 안 되므로 제거
    # 이 경고는 기능에 영향을 주지 않으므로 무시해도 됨
    
    # 다크 테마 강제: custom_css 사용 (streamlit-aggrid가 iframe 내부에 주입)
    # 주의: custom_css는 CSS 문자열이어야 함
    custom_css = """
    .ag-theme-alpine {
        --ag-background-color: #0f1720 !important;
        --ag-foreground-color: #e8eef7 !important;
        --ag-secondary-foreground-color: rgba(232,238,247,0.62) !important;
        --ag-header-background-color: #101823 !important;
        --ag-header-foreground-color: #e8eef7 !important;
        --ag-border-color: rgba(232,238,247,0.12) !important;
        --ag-row-hover-color: rgba(255,255,255,0.04) !important;
        --ag-odd-row-background-color: #0f1720 !important;
        --ag-even-row-background-color: #0f1720 !important;
        --ag-selected-row-background-color: rgba(57,255,20,0.10) !important;
        --ag-input-background-color: #0f1720 !important;
        --ag-input-border-color: rgba(0,0,0,0.65) !important;
    }
    """
    
    # AgGrid 렌더링
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=height,
        theme=theme,
        custom_css=custom_css,
        update_mode=GridUpdateMode.SELECTION_CHANGED if selectable else GridUpdateMode.NO_UPDATE,
        key=key,
        allow_unsafe_jscode=False,
        enable_enterprise_modules=False
    )
    
    # JavaScript는 theme_manager.py에서 전역으로 주입하므로 여기서는 제거
    # (중복 주입 방지 및 전역 주입으로 더 안정적)
    
    return grid_response
