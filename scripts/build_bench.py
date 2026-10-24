"""엔드포인트 실험용 벤치마크(bench/)를 원본 저장소에서 다시 만드는 스크립트.

- 모든 모델 입력 .py는 ast.parse → docstring 제거 → ast.unparse로 정규화한다 (주석이 모두 사라진다).
- campus: idor-test-codebase-main의 app/만 복사하고 bench_src/campus_extra를 덮어쓴다. 정답 문서는 가져오지 않는다.
- vampi_vuln / vampi_secure: VAmPI의 `if vuln:` 분기를 True/False로 접고, 취약 여부를 드러내는 이름·문구를 중립화한다.
- 엔드포인트 목록과 정책은 bench_src/<이름>/endpoints.json에서 복사한다. 실행 테스트는 bench_src의 tests를 복사한다.
사용: python3 scripts/build_bench.py [--campus-src DIR] [--vampi-src DIR]
"""

import argparse
import ast
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "bench"
SRC = ROOT / "bench_src"
WORKSPACE = ROOT.parent

# VAmPI 원본 app.py는 취약 스위치(vuln)를 정의하므로 쓰지 않고, 토큰 수명만 남긴 파일로 바꾼다.
VAMPI_APP_PY = '''import os
from config import api_app
alive = int(os.getenv('tokentimetolive', 60))
if __name__ == '__main__':
    api_app.run(host='0.0.0.0', port=5000)
'''
# GET / 응답 문구에 "Vulnerable API"라는 설명이 들어 있어 중립 문구로 바꾼다.
VAMPI_HOME_TEXT = '{ "message": "Book API home" }'


class _StripDocstrings(ast.NodeTransformer):
    """모듈·클래스·함수 본문 첫 문장이 문자열 상수이면 지운다."""

    def _strip(self, node):
        self.generic_visit(node)
        body = node.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
        return node

    visit_Module = visit_ClassDef = visit_FunctionDef = visit_AsyncFunctionDef = _strip


class _FoldSwitch(ast.NodeTransformer):
    """VAmPI의 전역 스위치 `vuln`을 상수로 바꾸고, 그 결과 상수가 된 if/and를 접는다. vuln_app 이름도 바꾼다."""

    def __init__(self, value):
        self.value = value

    def visit_Name(self, node):
        if node.id == "vuln":
            return ast.copy_location(ast.Constant(self.value), node)
        if node.id == "vuln_app":
            node.id = "api_app"
        return node

    def visit_alias(self, node):
        if node.name == "vuln_app":
            node.name = "api_app"
        return node

    def visit_ImportFrom(self, node):
        node.names = [a for a in node.names if a.name != "vuln"]
        self.generic_visit(node)
        return node if node.names else None

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if not isinstance(node.op, ast.And):
            return node
        rest = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                if not v.value:
                    return ast.Constant(False)
                continue
            rest.append(v)
        if not rest:
            return ast.Constant(True)
        return rest[0] if len(rest) == 1 else ast.BoolOp(ast.And(), rest)

    def visit_If(self, node):
        self.generic_visit(node)
        if isinstance(node.test, ast.Constant):
            return (node.body if node.test.value else node.orelse) or [ast.Pass()]
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        if node.name == "basic":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and ast.unparse(stmt.targets[0]) == "response_text":
                    stmt.value = ast.Constant(VAMPI_HOME_TEXT)
        return node


def normalize(source, switch=None):
    """원문을 정규화한 코드 문자열로 바꾼다. switch가 있으면 VAmPI 스위치를 그 값으로 접는다."""
    tree = ast.parse(source)
    if switch is not None:
        tree = _FoldSwitch(switch).visit(tree)
    tree = _StripDocstrings().visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def _write(path, text):
    """상위 디렉터리를 만들고 파일을 쓴다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def build_campus(src):
    """캠퍼스 서비스 벤치를 만든다. 원본 app/ + 추가 엔드포인트, 원본·추가 실행 테스트."""
    out = BENCH / "campus"
    sources = {p.relative_to(src): p for p in (src / "app").rglob("*.py")}
    extra = SRC / "campus_extra"
    sources.update({p.relative_to(extra): p for p in (extra / "app").rglob("*.py")})
    for rel, path in sorted(sources.items()):
        _write(out / rel, normalize(path.read_text()))
    for path in [*(src / "tests").glob("*.py"), *(extra / "tests").glob("*.py")]:
        _copy(path, out / "tests" / path.name)
    shutil.copy(src / "requirements.txt", out / "requirements.txt")
    _copy(SRC / "campus" / "endpoints.json", out / "endpoints.json")


def _copy(src, dst):
    """상위 디렉터리를 만들고 파일을 복사한다."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)


def build_vampi(src, name, switch):
    """VAmPI 벤치 하나(switch=1 취약 빌드, 0 수정 빌드)를 만든다."""
    out = BENCH / name
    files = [src / "config.py", *sorted((src / "api_views").glob("*.py")), *sorted((src / "models").glob("*.py"))]
    for path in files:
        _write(out / path.relative_to(src), normalize(path.read_text(), switch))
    _write(out / "app.py", normalize(VAMPI_APP_PY))
    _write(out / "database" / "__init__.py", "")
    _copy(src / "openapi_specs" / "openapi3.yml", out / "openapi_specs" / "openapi3.yml")
    _copy(src / "requirements.txt", out / "requirements.txt")
    _copy(SRC / "vampi_tests" / "conftest.py", out / "tests" / "conftest.py")
    _copy(SRC / "vampi_tests" / f"test_{name}.py", out / "tests" / f"test_{name}.py")
    endpoints = json.loads((SRC / "vampi" / "endpoints.json").read_text())
    for e in endpoints:
        e["item_id"] = f"{name}:{e['item_id']}"
    _write(out / "endpoints.json", json.dumps(endpoints, ensure_ascii=False, indent=2) + "\n")


def main():
    """명령행 인자를 읽어 bench/를 지우고 다시 만든다."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--campus-src", type=Path, default=WORKSPACE / "idor-test-codebase-main")
    ap.add_argument("--vampi-src", type=Path, default=WORKSPACE / "VAmPI-master")
    args = ap.parse_args()
    if BENCH.exists():
        shutil.rmtree(BENCH)
    build_campus(args.campus_src)
    build_vampi(args.vampi_src, "vampi_vuln", 1)
    build_vampi(args.vampi_src, "vampi_secure", 0)
    print(f"built {BENCH}")


if __name__ == "__main__":
    main()
