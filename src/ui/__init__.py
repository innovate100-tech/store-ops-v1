"""
UI 컴포넌트 모듈
"""
# src/ui.py 모듈의 함수들을 re-export하여 기존 import 호환성 유지
# 주의: src/ui.py는 모듈이고, src/ui/는 패키지이므로 importlib을 사용
import sys
import importlib.util

# src/ui.py 모듈을 동적으로 로드
_ui_module_path = None
for path in sys.path:
    potential_path = __import__('pathlib').Path(path) / 'src' / 'ui.py'
    if potential_path.exists():
        _ui_module_path = potential_path
        break

# src/ui.py에서 export할 모든 함수 목록
_EXPORTED_FUNCTIONS = [
    'render_manager_closing_input',
    'render_daily_closing_input',
    'render_sales_input',
    'render_sales_batch_input',
    'render_visitor_input',
    'render_visitor_batch_input',
    'render_menu_input',
    'render_menu_batch_input',
    'render_ingredient_input',
    'render_inventory_input',
    'render_cost_analysis',
    'render_report_input',
    'render_abc_analysis',
    'render_daily_sales_input',
    'render_target_input',
    'render_target_dashboard',
    'render_sales_chart',
    'render_correlation_info',
    'render_recipe_input',
]

if _ui_module_path:
    spec = importlib.util.spec_from_file_location("src_ui_module", _ui_module_path)
    _ui_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_ui_module)
    
    # 모든 함수들을 re-export
    for func_name in _EXPORTED_FUNCTIONS:
        globals()[func_name] = getattr(_ui_module, func_name, None)
else:
    # src/ui.py를 찾을 수 없는 경우 (fallback)
    try:
        import importlib
        _ui_module = importlib.import_module('src.ui')
        for func_name in _EXPORTED_FUNCTIONS:
            globals()[func_name] = getattr(_ui_module, func_name, None)
    except ImportError:
        # 모듈을 찾을 수 없으면 None으로 설정
        for func_name in _EXPORTED_FUNCTIONS:
            globals()[func_name] = None

__all__ = _EXPORTED_FUNCTIONS
