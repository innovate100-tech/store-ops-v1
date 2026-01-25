"""
CSS 주입 지점 자동 수집 스크립트
프로젝트 전체에서 CSS 주입 위치를 찾아 리포트를 생성합니다.
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent

# 제외할 디렉토리/파일
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "*.pyc",
    "*.md",  # 마크다운 파일 제외 (실제 코드만)
]

# 검색할 패턴
PATTERNS = {
    "st.markdown_style": [
        r'st\.markdown\s*\([^)]*<style',
        r'st\.markdown\s*\([^)]*style\s*[=:]',
        r'unsafe_allow_html\s*=\s*True.*style',
    ],
    "inject_function": [
        r'def\s+inject.*css',
        r'def\s+inject.*style',
    ],
    "components_html": [
        r'components\.html\s*\(',
        r'components\.iframe\s*\(',
    ],
    "dangerous_properties": [
        r'opacity\s*:\s*0',
        r'visibility\s*:\s*hidden',
        r'display\s*:\s*none',
        r'overflow\s*:\s*hidden',
        r'backdrop-filter',
        r'transform\s*:',
        r'filter\s*:',
    ],
    "stMain_selectors": [
        r'\[data-testid\s*=\s*["\']stMain',
        r'\[data-testid\s*=\s*["\']stMainBlockContainer',
        r'\[data-testid\s*=\s*["\']stAppViewContainer',
    ],
    "fixed_overlay": [
        r'position\s*:\s*fixed.*inset',
        r'position\s*:\s*fixed.*z-index',
        r'z-index\s*:\s*[5-9]\d+',
        r'z-index\s*:\s*[1-9]\d{2,}',
    ],
    "animation_keywords": [
        r'ultra|mesh|overlay|animation|background.*animation',
    ],
}

def should_exclude(path: Path) -> bool:
    """파일/디렉토리를 제외할지 확인"""
    path_str = str(path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return True
    return False

def find_matches(file_path: Path, pattern: str) -> List[Tuple[int, str]]:
    """파일에서 패턴 매칭 라인 찾기"""
    matches = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append((line_num, line.strip()))
    except Exception:
        pass
    return matches

def scan_project() -> Dict[str, List[Dict]]:
    """프로젝트 전체 스캔"""
    results = defaultdict(list)
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_exclude(py_file):
            continue
        
        rel_path = py_file.relative_to(PROJECT_ROOT)
        
        for category, patterns in PATTERNS.items():
            for pattern in patterns:
                matches = find_matches(py_file, pattern)
                if matches:
                    results[category].append({
                        "file": str(rel_path),
                        "pattern": pattern,
                        "matches": matches,
                    })
    
    return results

def generate_report(results: Dict[str, List[Dict]]) -> str:
    """마크다운 리포트 생성"""
    report = []
    report.append("# CSS 주입 지점 자동 수집 리포트\n")
    report.append(f"생성일: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for category, items in results.items():
        report.append(f"## {category}\n")
        if not items:
            report.append("발견된 항목 없음.\n")
        else:
            for item in items:
                report.append(f"### {item['file']}\n")
                report.append(f"**패턴**: `{item['pattern']}`\n")
                report.append("**매칭 라인**:\n")
                for line_num, line_content in item['matches']:
                    report.append(f"- 라인 {line_num}: `{line_content[:100]}...`\n")
                report.append("\n")
    
    return "\n".join(report)

def main():
    """메인 실행"""
    print("CSS 주입 지점 스캔 중...")
    results = scan_project()
    
    print(f"발견된 항목:")
    for category, items in results.items():
        print(f"  {category}: {len(items)}개 파일")
    
    report = generate_report(results)
    
    # 리포트 저장
    output_path = PROJECT_ROOT / "docs" / "css_audit_report.md"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(report, encoding='utf-8')
    
    print(f"\n리포트 저장: {output_path}")
    print("\n=== 리포트 미리보기 ===\n")
    try:
        print(report[:2000])
    except UnicodeEncodeError:
        print("(리포트 생성 완료, 미리보기 생략)")

if __name__ == "__main__":
    main()
