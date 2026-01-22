"""
대시보드 데이터 로더
"""
from src.storage_supabase import load_csv, load_expense_structure


def _load_dashboard_data(ctx):
    """대시보드에 필요한 모든 데이터 로드"""
    expense_df = load_expense_structure(ctx['year'], ctx['month'])
    targets_df = load_csv('targets.csv', default_columns=[
        '연도', '월', '목표매출', '목표원가율', '목표인건비율',
        '목표임대료율', '목표기타비용율', '목표순이익률'
    ])
    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    return {
        'expense_df': expense_df,
        'targets_df': targets_df,
        'sales_df': sales_df,
        'visitors_df': visitors_df,
        'menu_df': menu_df,
        'daily_sales_df': daily_sales_df,
        'recipe_df': recipe_df,
        'ingredient_df': ingredient_df,
    }
