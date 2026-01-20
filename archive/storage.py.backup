"""
CSV 파일 저장/로드 공통 모듈
"""
import pandas as pd
import os
import logging
from pathlib import Path
from datetime import datetime


def get_data_dir():
    """data 디렉토리 경로 반환"""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_log_dir():
    """logs 디렉토리 경로 반환"""
    base_dir = Path(__file__).parent.parent
    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir


def get_backup_dir():
    """backups 디렉토리 경로 반환"""
    base_dir = Path(__file__).parent.parent
    backup_dir = base_dir / "backups"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def setup_logger():
    """로깅 시스템 설정"""
    log_dir = get_log_dir()
    log_file = log_dir / f"store_ops_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger('store_ops')
    logger.setLevel(logging.INFO)
    
    # 파일 핸들러
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def load_csv(filename, default_columns=None):
    """
    CSV 파일 로드 (없으면 빈 DataFrame 반환)
    
    Args:
        filename: 파일명 (예: "sales.csv")
        default_columns: 기본 컬럼 리스트 (파일이 없을 때 사용)
    
    Returns:
        pandas.DataFrame
    """
    data_dir = get_data_dir()
    filepath = data_dir / filename
    
    if filepath.exists():
        try:
            df = pd.read_csv(filepath)
            if '날짜' in df.columns:
                df['날짜'] = pd.to_datetime(df['날짜'])
            return df
        except Exception as e:
            print(f"파일 로드 오류: {e}")
            return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    else:
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()


def backup_file(filename):
    """
    파일 백업 생성
    
    Args:
        filename: 백업할 파일명
    """
    logger = setup_logger()
    data_dir = get_data_dir()
    backup_dir = get_backup_dir()
    
    source_file = data_dir / filename
    if not source_file.exists():
        return
    
    # 백업 파일명: 원본이름_YYYYMMDD_HHMMSS.csv
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"{filename.replace('.csv', '')}_{timestamp}.csv"
    backup_path = backup_dir / backup_filename
    
    try:
        import shutil
        shutil.copy2(source_file, backup_path)
        logger.info(f"백업 생성: {filename} -> {backup_filename}")
    except Exception as e:
        logger.error(f"백업 생성 오류: {filename} - {e}")
        raise


def create_backup():
    """
    전체 데이터 백업 생성
    
    Returns:
        tuple: (성공 여부, 백업 경로)
    """
    logger = setup_logger()
    data_dir = get_data_dir()
    backup_dir = get_backup_dir()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder = backup_dir / f"backup_{timestamp}"
    backup_folder.mkdir(exist_ok=True)
    
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        return False, "백업할 파일이 없습니다."
    
    try:
        import shutil
        for csv_file in csv_files:
            shutil.copy2(csv_file, backup_folder / csv_file.name)
        logger.info(f"전체 백업 생성: {backup_folder}")
        return True, str(backup_folder)
    except Exception as e:
        logger.error(f"전체 백업 생성 오류: {e}")
        return False, str(e)


def save_csv(df, filename, mode='append'):
    """
    CSV 파일 저장
    
    Args:
        df: 저장할 DataFrame
        filename: 파일명
        mode: 'append' (추가) 또는 'overwrite' (덮어쓰기)
    """
    logger = setup_logger()
    data_dir = get_data_dir()
    filepath = data_dir / filename
    
    # 백업 생성 (기존 파일이 있는 경우)
    if filepath.exists() and mode == 'overwrite':
        try:
            backup_file(filename)
        except Exception as e:
            logger.warning(f"백업 생성 실패: {e}")
    
    if mode == 'append' and filepath.exists():
        try:
            existing_df = pd.read_csv(filepath)
            # 날짜 컬럼이 있으면 datetime으로 변환
            if '날짜' in existing_df.columns:
                existing_df['날짜'] = pd.to_datetime(existing_df['날짜'])
            df = pd.concat([existing_df, df], ignore_index=True)
            # 중복 제거 (날짜 기준)
            if '날짜' in df.columns:
                df = df.drop_duplicates(subset=['날짜'], keep='last')
        except Exception as e:
            logger.error(f"기존 파일 로드 오류: {e}")
            print(f"기존 파일 로드 오류: {e}")
    
    # 날짜 컬럼을 문자열로 변환하여 저장
    df_to_save = df.copy()
    if '날짜' in df_to_save.columns:
        df_to_save['날짜'] = df_to_save['날짜'].dt.strftime('%Y-%m-%d')
    
    try:
        df_to_save.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f"파일 저장 성공: {filename} (mode: {mode})")
    except Exception as e:
        logger.error(f"파일 저장 오류: {filename} - {e}")
        raise


def save_sales(date, store, card_sales, cash_sales, total_sales=None):
    """
    매출 데이터 저장 (날짜+매장 기준 중복 처리)
    
    Args:
        date: 날짜
        store: 매장명
        card_sales: 카드매출
        cash_sales: 현금매출
        total_sales: 총매출 (None이면 card_sales + cash_sales로 자동 계산)
    """
    logger = setup_logger()
    if total_sales is None:
        total_sales = card_sales + cash_sales
    
    # 기존 매출 데이터 로드
    existing_df = load_csv('sales.csv', default_columns=['날짜', '매장', '카드매출', '현금매출', '총매출'])
    
    # 날짜를 datetime으로 변환
    new_date = pd.to_datetime(date)
    
    # 같은 날짜+매장이 있으면 업데이트, 없으면 추가
    if not existing_df.empty:
        existing_df['날짜'] = pd.to_datetime(existing_df['날짜'])
        mask = (existing_df['날짜'] == new_date) & (existing_df['매장'] == store)
        
        if mask.any():
            # 기존 데이터 업데이트
            existing_df.loc[mask, '카드매출'] = card_sales
            existing_df.loc[mask, '현금매출'] = cash_sales
            existing_df.loc[mask, '총매출'] = total_sales
            df = existing_df
            logger.info(f"매출 데이터 업데이트: {date}, {store}")
        else:
            # 새 데이터 추가
            new_row = pd.DataFrame({
                '날짜': [date],
                '매장': [store],
                '카드매출': [card_sales],
                '현금매출': [cash_sales],
                '총매출': [total_sales]
            })
            df = pd.concat([existing_df, new_row], ignore_index=True)
            logger.info(f"매출 데이터 추가: {date}, {store}")
    else:
        # 첫 번째 데이터
        df = pd.DataFrame({
            '날짜': [date],
            '매장': [store],
            '카드매출': [card_sales],
            '현금매출': [cash_sales],
            '총매출': [total_sales]
        })
        logger.info(f"매출 데이터 최초 저장: {date}, {store}")
    
    save_csv(df, 'sales.csv', mode='overwrite')
    return True


def save_visitor(date, visitors):
    """
    방문자 데이터 저장 (날짜 기준 중복 처리)
    
    Args:
        date: 날짜
        visitors: 방문자수
    """
    logger = setup_logger()
    
    # 기존 방문자 데이터 로드
    existing_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
    
    # 날짜를 datetime으로 변환
    new_date = pd.to_datetime(date)
    
    # 같은 날짜가 있으면 업데이트, 없으면 추가
    if not existing_df.empty:
        existing_df['날짜'] = pd.to_datetime(existing_df['날짜'])
        mask = existing_df['날짜'] == new_date
        
        if mask.any():
            # 기존 데이터 업데이트
            existing_df.loc[mask, '방문자수'] = visitors
            df = existing_df
            logger.info(f"방문자 데이터 업데이트: {date}")
        else:
            # 새 데이터 추가
            new_row = pd.DataFrame({
                '날짜': [date],
                '방문자수': [visitors]
            })
            df = pd.concat([existing_df, new_row], ignore_index=True)
            logger.info(f"방문자 데이터 추가: {date}")
    else:
        # 첫 번째 데이터
        df = pd.DataFrame({
            '날짜': [date],
            '방문자수': [visitors]
        })
        logger.info(f"방문자 데이터 최초 저장: {date}")
    
    save_csv(df, 'naver_visitors.csv', mode='overwrite')
    return True


def delete_sales(date, store=None):
    """
    매출 데이터 삭제
    
    Args:
        date: 날짜
        store: 매장명 (None이면 해당 날짜의 모든 매출 삭제)
    
    Returns:
        tuple: (성공 여부, 메시지)
    """
    logger = setup_logger()
    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '카드매출', '현금매출', '총매출'])
    
    if sales_df.empty:
        return False, "삭제할 매출 데이터가 없습니다."
    
    sales_df['날짜'] = pd.to_datetime(sales_df['날짜'])
    date_obj = pd.to_datetime(date)
    
    if store:
        mask = (sales_df['날짜'] == date_obj) & (sales_df['매장'] == store)
        if not mask.any():
            return False, f"{date}, {store}의 매출 데이터를 찾을 수 없습니다."
        sales_df = sales_df[~mask]
        logger.info(f"매출 데이터 삭제: {date}, {store}")
    else:
        mask = sales_df['날짜'] == date_obj
        if not mask.any():
            return False, f"{date}의 매출 데이터를 찾을 수 없습니다."
        count = mask.sum()
        sales_df = sales_df[~mask]
        logger.info(f"매출 데이터 삭제: {date} ({count}건)")
    
    save_csv(sales_df, 'sales.csv', mode='overwrite')
    return True, "삭제 성공"


def delete_visitor(date):
    """
    방문자 데이터 삭제
    
    Args:
        date: 날짜
    
    Returns:
        tuple: (성공 여부, 메시지)
    """
    logger = setup_logger()
    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
    
    if visitors_df.empty:
        return False, "삭제할 방문자 데이터가 없습니다."
    
    visitors_df['날짜'] = pd.to_datetime(visitors_df['날짜'])
    date_obj = pd.to_datetime(date)
    
    mask = visitors_df['날짜'] == date_obj
    if not mask.any():
        return False, f"{date}의 방문자 데이터를 찾을 수 없습니다."
    
    visitors_df = visitors_df[~mask]
    save_csv(visitors_df, 'naver_visitors.csv', mode='overwrite')
    logger.info(f"방문자 데이터 삭제: {date}")
    return True, "삭제 성공"


def save_menu(menu_name, price):
    """
    메뉴 마스터 저장 (중복 체크 포함)
    
    Args:
        menu_name: 메뉴명
        price: 판매가
    
    Returns:
        tuple: (성공 여부, 메시지)
    """
    logger = setup_logger()
    
    # 중복 체크
    existing_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    if not existing_df.empty:
        if menu_name in existing_df['메뉴명'].values:
            logger.warning(f"중복 메뉴명 감지: {menu_name}")
            return False, f"'{menu_name}' 메뉴는 이미 등록되어 있습니다."
    
    df = pd.DataFrame({
        '메뉴명': [menu_name],
        '판매가': [price]
    })
    save_csv(df, 'menu_master.csv', mode='append')
    logger.info(f"메뉴 저장: {menu_name}, {price:,}원")
    return True, "저장 성공"


def update_menu(old_menu_name, new_menu_name, new_price):
    """
    메뉴 수정
    
    Args:
        old_menu_name: 기존 메뉴명
        new_menu_name: 새 메뉴명
        new_price: 새 판매가
    
    Returns:
        tuple: (성공 여부, 메시지)
    """
    logger = setup_logger()
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    
    if menu_df.empty:
        return False, "수정할 메뉴가 없습니다."
    
    if old_menu_name not in menu_df['메뉴명'].values:
        return False, f"'{old_menu_name}' 메뉴를 찾을 수 없습니다."
    
    # 새 메뉴명이 기존 메뉴명과 다르고, 이미 존재하면 오류
    if new_menu_name != old_menu_name:
        if new_menu_name in menu_df['메뉴명'].values:
            return False, f"'{new_menu_name}' 메뉴명은 이미 사용 중입니다."
    
    # 메뉴 수정
    menu_df.loc[menu_df['메뉴명'] == old_menu_name, '메뉴명'] = new_menu_name
    menu_df.loc[menu_df['메뉴명'] == new_menu_name, '판매가'] = new_price
    
    save_csv(menu_df, 'menu_master.csv', mode='overwrite')
    logger.info(f"메뉴 수정: {old_menu_name} -> {new_menu_name}, {new_price:,}원")
    return True, "수정 성공"


def delete_menu(menu_name, check_references=True):
    """
    메뉴 삭제 (참조 무결성 체크)
    
    Args:
        menu_name: 삭제할 메뉴명
        check_references: 참조 무결성 체크 여부
    
    Returns:
        tuple: (성공 여부, 메시지, 참조 정보)
    """
    logger = setup_logger()
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    
    if menu_df.empty or menu_name not in menu_df['메뉴명'].values:
        return False, f"'{menu_name}' 메뉴를 찾을 수 없습니다.", None
    
    references = {}
    
    if check_references:
        # 레시피 참조 확인
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        if not recipe_df.empty and menu_name in recipe_df['메뉴명'].values:
            references['레시피'] = recipe_df[recipe_df['메뉴명'] == menu_name].shape[0]
        
        # 판매 내역 참조 확인
        sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
        if not sales_df.empty and menu_name in sales_df['메뉴명'].values:
            references['판매내역'] = sales_df[sales_df['메뉴명'] == menu_name].shape[0]
    
    if references:
        ref_info = ", ".join([f"{k}: {v}개" for k, v in references.items()])
        return False, f"'{menu_name}' 메뉴는 다음 데이터에서 사용 중입니다: {ref_info}", references
    
    # 메뉴 삭제
    menu_df = menu_df[menu_df['메뉴명'] != menu_name]
    save_csv(menu_df, 'menu_master.csv', mode='overwrite')
    logger.info(f"메뉴 삭제: {menu_name}")
    return True, "삭제 성공", None


def save_ingredient(ingredient_name, unit, unit_price):
    """
    재료 마스터 저장 (중복 체크 포함)
    
    Args:
        ingredient_name: 재료명
        unit: 단위
        unit_price: 단가
    
    Returns:
        tuple: (성공 여부, 메시지)
    """
    logger = setup_logger()
    
    # 중복 체크
    existing_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    if not existing_df.empty:
        if ingredient_name in existing_df['재료명'].values:
            logger.warning(f"중복 재료명 감지: {ingredient_name}")
            return False, f"'{ingredient_name}' 재료는 이미 등록되어 있습니다."
    
    df = pd.DataFrame({
        '재료명': [ingredient_name],
        '단위': [unit],
        '단가': [unit_price]
    })
    save_csv(df, 'ingredient_master.csv', mode='append')
    logger.info(f"재료 저장: {ingredient_name}, {unit_price:,.2f}원/{unit}")
    return True, "저장 성공"


def update_ingredient(old_ingredient_name, new_ingredient_name, new_unit, new_unit_price):
    """
    재료 수정
    
    Args:
        old_ingredient_name: 기존 재료명
        new_ingredient_name: 새 재료명
        new_unit: 새 단위
        new_unit_price: 새 단가
    
    Returns:
        tuple: (성공 여부, 메시지)
    """
    logger = setup_logger()
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    if ingredient_df.empty or old_ingredient_name not in ingredient_df['재료명'].values:
        return False, f"'{old_ingredient_name}' 재료를 찾을 수 없습니다."
    
    # 새 재료명이 기존 재료명과 다르고, 이미 존재하면 오류
    if new_ingredient_name != old_ingredient_name:
        if new_ingredient_name in ingredient_df['재료명'].values:
            return False, f"'{new_ingredient_name}' 재료명은 이미 사용 중입니다."
    
    # 재료 수정
    ingredient_df.loc[ingredient_df['재료명'] == old_ingredient_name, '재료명'] = new_ingredient_name
    ingredient_df.loc[ingredient_df['재료명'] == new_ingredient_name, '단위'] = new_unit
    ingredient_df.loc[ingredient_df['재료명'] == new_ingredient_name, '단가'] = new_unit_price
    
    save_csv(ingredient_df, 'ingredient_master.csv', mode='overwrite')
    logger.info(f"재료 수정: {old_ingredient_name} -> {new_ingredient_name}")
    return True, "수정 성공"


def delete_ingredient(ingredient_name, check_references=True):
    """
    재료 삭제 (참조 무결성 체크)
    
    Args:
        ingredient_name: 삭제할 재료명
        check_references: 참조 무결성 체크 여부
    
    Returns:
        tuple: (성공 여부, 메시지, 참조 정보)
    """
    logger = setup_logger()
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    if ingredient_df.empty or ingredient_name not in ingredient_df['재료명'].values:
        return False, f"'{ingredient_name}' 재료를 찾을 수 없습니다.", None
    
    references = {}
    
    if check_references:
        # 레시피 참조 확인
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        if not recipe_df.empty and ingredient_name in recipe_df['재료명'].values:
            references['레시피'] = recipe_df[recipe_df['재료명'] == ingredient_name].shape[0]
        
        # 재고 정보 참조 확인
        inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
        if not inventory_df.empty and ingredient_name in inventory_df['재료명'].values:
            references['재고정보'] = 1
    
    if references:
        ref_info = ", ".join([f"{k}: {v}개" for k, v in references.items()])
        return False, f"'{ingredient_name}' 재료는 다음 데이터에서 사용 중입니다: {ref_info}", references
    
    # 재료 삭제
    ingredient_df = ingredient_df[ingredient_df['재료명'] != ingredient_name]
    save_csv(ingredient_df, 'ingredient_master.csv', mode='overwrite')
    logger.info(f"재료 삭제: {ingredient_name}")
    return True, "삭제 성공", None


def save_recipe(menu_name, ingredient_name, quantity):
    """레시피 저장 (메뉴-재료 매핑)"""
    logger = setup_logger()
    df = pd.DataFrame({
        '메뉴명': [menu_name],
        '재료명': [ingredient_name],
        '사용량': [quantity]
    })
    save_csv(df, 'recipes.csv', mode='append')
    logger.info(f"레시피 저장: {menu_name} - {ingredient_name}")
    return True


def delete_recipe(menu_name, ingredient_name):
    """
    레시피 삭제
    
    Args:
        menu_name: 메뉴명
        ingredient_name: 재료명
    
    Returns:
        tuple: (성공 여부, 메시지)
    """
    logger = setup_logger()
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    
    if recipe_df.empty:
        return False, "삭제할 레시피가 없습니다."
    
    mask = (recipe_df['메뉴명'] == menu_name) & (recipe_df['재료명'] == ingredient_name)
    if not mask.any():
        return False, f"'{menu_name} - {ingredient_name}' 레시피를 찾을 수 없습니다."
    
    recipe_df = recipe_df[~mask]
    save_csv(recipe_df, 'recipes.csv', mode='overwrite')
    logger.info(f"레시피 삭제: {menu_name} - {ingredient_name}")
    return True, "삭제 성공"


def save_daily_sales_item(date, menu_name, quantity):
    """일일 판매 아이템 저장 (같은 날짜/메뉴가 있으면 수량 합산)"""
    # 기존 판매 데이터 로드
    existing_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    
    # 날짜를 datetime으로 변환하여 비교
    new_date = pd.to_datetime(date)
    
    # 같은 날짜와 메뉴명이 있는지 확인
    if not existing_df.empty:
        existing_df['날짜'] = pd.to_datetime(existing_df['날짜'])
        mask = (existing_df['날짜'] == new_date) & (existing_df['메뉴명'] == menu_name)
        
        if mask.any():
            # 기존 수량에 추가
            existing_df.loc[mask, '판매수량'] += quantity
            df = existing_df
        else:
            # 새 행 추가
            new_row = pd.DataFrame({
                '날짜': [date],
                '메뉴명': [menu_name],
                '판매수량': [quantity]
            })
            df = pd.concat([existing_df, new_row], ignore_index=True)
    else:
        # 첫 번째 데이터
        df = pd.DataFrame({
            '날짜': [date],
            '메뉴명': [menu_name],
            '판매수량': [quantity]
        })
    
    save_csv(df, 'daily_sales_items.csv', mode='overwrite')
    return True


def save_inventory(ingredient_name, current_stock, safety_stock):
    """재고 정보 저장 (현재고, 안전재고)"""
    # 기존 재고 정보 로드
    inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
    
    # 동일 재료명이 있으면 업데이트, 없으면 추가
    if not inventory_df.empty and ingredient_name in inventory_df['재료명'].values:
        inventory_df.loc[inventory_df['재료명'] == ingredient_name, '현재고'] = current_stock
        inventory_df.loc[inventory_df['재료명'] == ingredient_name, '안전재고'] = safety_stock
        df = inventory_df
        mode = 'overwrite'
    else:
        # 새로운 재고 정보 추가
        new_row = pd.DataFrame({
            '재료명': [ingredient_name],
            '현재고': [current_stock],
            '안전재고': [safety_stock]
        })
        if inventory_df.empty:
            df = new_row
        else:
            df = pd.concat([inventory_df, new_row], ignore_index=True)
        mode = 'overwrite'
    
    save_csv(df, 'inventory.csv', mode=mode)
    return True


def save_targets(year, month, target_sales, target_cost_rate, target_labor_rate, 
                 target_rent_rate, target_other_rate, target_profit_rate):
    """
    목표 매출/비용 구조 저장 (월별)
    
    Args:
        year: 연도
        month: 월
        target_sales: 목표 매출
        target_cost_rate: 목표 원가율 (%)
        target_labor_rate: 목표 인건비율 (%)
        target_rent_rate: 목표 임대료율 (%)
        target_other_rate: 목표 기타비용율 (%)
        target_profit_rate: 목표 순이익률 (%)
    """
    # 기존 목표 데이터 로드
    targets_df = load_csv('targets.csv', default_columns=[
        '연도', '월', '목표매출', '목표원가율', '목표인건비율', 
        '목표임대료율', '목표기타비용율', '목표순이익률'
    ])
    
    # 동일 연도/월이 있으면 업데이트, 없으면 추가
    if not targets_df.empty:
        mask = (targets_df['연도'] == year) & (targets_df['월'] == month)
        if mask.any():
            targets_df.loc[mask, '목표매출'] = target_sales
            targets_df.loc[mask, '목표원가율'] = target_cost_rate
            targets_df.loc[mask, '목표인건비율'] = target_labor_rate
            targets_df.loc[mask, '목표임대료율'] = target_rent_rate
            targets_df.loc[mask, '목표기타비용율'] = target_other_rate
            targets_df.loc[mask, '목표순이익률'] = target_profit_rate
            df = targets_df
        else:
            new_row = pd.DataFrame({
                '연도': [year],
                '월': [month],
                '목표매출': [target_sales],
                '목표원가율': [target_cost_rate],
                '목표인건비율': [target_labor_rate],
                '목표임대료율': [target_rent_rate],
                '목표기타비용율': [target_other_rate],
                '목표순이익률': [target_profit_rate]
            })
            df = pd.concat([targets_df, new_row], ignore_index=True)
    else:
        df = pd.DataFrame({
            '연도': [year],
            '월': [month],
            '목표매출': [target_sales],
            '목표원가율': [target_cost_rate],
            '목표인건비율': [target_labor_rate],
            '목표임대료율': [target_rent_rate],
            '목표기타비용율': [target_other_rate],
            '목표순이익률': [target_profit_rate]
        })
    
    save_csv(df, 'targets.csv', mode='overwrite')
    return True


def save_abc_history(year, month, abc_df):
    """
    ABC 분석 히스토리 저장 (월별 스냅샷)
    
    Args:
        year: 연도
        month: 월
        abc_df: ABC 분석 결과 DataFrame (메뉴명, 판매량, 매출, 공헌이익, 판매량비중, 매출비중, 공헌이익비중, ABC등급)
    """
    # 연도, 월 컬럼 추가
    abc_df = abc_df.copy()
    abc_df['연도'] = year
    abc_df['월'] = month
    
    # 기존 히스토리 로드
    history_df = load_csv('abc_history.csv', default_columns=[
        '연도', '월', '메뉴명', '판매량', '매출', '공헌이익', 
        '판매량비중', '매출비중', '공헌이익비중', 'ABC등급'
    ])
    
    # 동일 연도/월 데이터가 있으면 삭제 후 추가
    if not history_df.empty:
        history_df = history_df[
            ~((history_df['연도'] == year) & (history_df['월'] == month))
        ]
    
    # 새 데이터 추가
    if history_df.empty:
        df = abc_df
    else:
        df = pd.concat([history_df, abc_df], ignore_index=True)
    
    save_csv(df, 'abc_history.csv', mode='overwrite')
    return True


def load_key_menus():
    """
    핵심 메뉴 목록 로드
    
    Returns:
        list: 핵심 메뉴명 리스트
    """
    key_menus_df = load_csv('key_menus.csv', default_columns=['메뉴명'])
    if key_menus_df.empty:
        return []
    return key_menus_df['메뉴명'].tolist()


def save_key_menus(menu_list):
    """
    핵심 메뉴 목록 저장
    
    Args:
        menu_list: 메뉴명 리스트
    """
    logger = setup_logger()
    df = pd.DataFrame({'메뉴명': menu_list})
    save_csv(df, 'key_menus.csv', mode='overwrite')
    logger.info(f"핵심 메뉴 저장: {len(menu_list)}개")
    return True


def save_daily_close(date, store, card_sales, cash_sales, total_sales, 
                     visitors, sales_items, issues, memo):
    """
    일일 마감 데이터 통합 저장 (daily_close.csv)
    
    Args:
        date: 날짜
        store: 매장명
        card_sales: 카드매출
        cash_sales: 현금매출
        total_sales: 총매출
        visitors: 방문자수
        sales_items: 판매 아이템 리스트 [(메뉴명, 수량), ...]
        issues: 특이사항 체크박스 딕셔너리 {'품절': bool, '컴플레인': bool, ...}
        memo: 메모 텍스트
    """
    logger = setup_logger()
    
    # 기존 마감 데이터 로드
    existing_df = load_csv('daily_close.csv', default_columns=[
        '날짜', '매장', '카드매출', '현금매출', '총매출', '방문자수',
        '품절발생', '컴플레인발생', '단체손님', '직원이슈', '메모'
    ])
    
    # 날짜를 datetime으로 변환
    new_date = pd.to_datetime(date)
    
    # 판매 아이템을 JSON 문자열로 변환
    import json
    sales_items_json = json.dumps(sales_items, ensure_ascii=False)
    
    # 새로운 행 데이터
    new_row_data = {
        '날짜': [date],
        '매장': [store],
        '카드매출': [card_sales],
        '현금매출': [cash_sales],
        '총매출': [total_sales],
        '방문자수': [visitors],
        '품절발생': [issues.get('품절', False)],
        '컴플레인발생': [issues.get('컴플레인', False)],
        '단체손님': [issues.get('단체손님', False)],
        '직원이슈': [issues.get('직원이슈', False)],
        '메모': [memo],
        '판매내역': [sales_items_json]
    }
    
    # 같은 날짜+매장이 있으면 업데이트, 없으면 추가
    if not existing_df.empty:
        existing_df['날짜'] = pd.to_datetime(existing_df['날짜'])
        mask = (existing_df['날짜'] == new_date) & (existing_df['매장'] == store)
        
        if mask.any():
            # 기존 데이터 업데이트
            for col, val in new_row_data.items():
                existing_df.loc[mask, col] = val[0]
            df = existing_df
            logger.info(f"마감 데이터 업데이트: {date}, {store}")
        else:
            # 새 데이터 추가
            new_row = pd.DataFrame(new_row_data)
            df = pd.concat([existing_df, new_row], ignore_index=True)
            logger.info(f"마감 데이터 추가: {date}, {store}")
    else:
        # 첫 번째 데이터
        df = pd.DataFrame(new_row_data)
        logger.info(f"마감 데이터 최초 저장: {date}, {store}")
    
    save_csv(df, 'daily_close.csv', mode='overwrite')
    
    # 기존 매출, 방문자, 판매 데이터에도 저장 (호환성 유지)
    if total_sales > 0:
        save_sales(date, store, card_sales, cash_sales, total_sales)
    if visitors > 0:
        save_visitor(date, visitors)
    for menu_name, quantity in sales_items:
        if quantity > 0:
            save_daily_sales_item(date, menu_name, quantity)
    
    return True