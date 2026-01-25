"""
홈 패키지를 레거시로 이동하는 스크립트
"""
import os
import shutil
from pathlib import Path

# 경로 설정
base_dir = Path(__file__).parent.parent
home_dir = base_dir / "ui_pages" / "home"
legacy_dir = base_dir / "ui_pages" / "_legacy" / "home_pkg_20260126"
home_legacy_file = base_dir / "ui_pages" / "home_legacy.py"
legacy_old_file = base_dir / "ui_pages" / "_legacy" / "home_legacy_old.py"

# 레거시 디렉토리 생성
legacy_dir.mkdir(parents=True, exist_ok=True)

# home 폴더 내용 복사
if home_dir.exists():
    print(f"복사 중: {home_dir} -> {legacy_dir}")
    for item in home_dir.iterdir():
        if item.is_file() and item.suffix == ".py":
            dest = legacy_dir / item.name
            shutil.copy2(item, dest)
            print(f"  복사됨: {item.name}")
        elif item.is_dir() and item.name != "__pycache__":
            dest = legacy_dir / item.name
            shutil.copytree(item, dest, dirs_exist_ok=True)
            print(f"  복사됨: {item.name}/")
    print(f"완료: {len(list(legacy_dir.glob('*.py')))} 파일 복사됨")
else:
    print(f"경고: {home_dir}가 존재하지 않습니다.")

# home_legacy.py 이동
if home_legacy_file.exists():
    print(f"이동 중: {home_legacy_file} -> {legacy_old_file}")
    shutil.copy2(home_legacy_file, legacy_old_file)
    print(f"완료: {home_legacy_file.name} 복사됨")
else:
    print(f"경고: {home_legacy_file}가 존재하지 않습니다.")

print("\n수동으로 다음을 수행하세요:")
print("1. ui_pages/home/ 폴더 삭제")
print("2. ui_pages/home_legacy.py 파일 삭제")
