"""여러 파일로 된 웹 앱에서 엔드포인트 핸들러부터 호출 관계를 따라가 관련 함수 원문을 추출하는 모듈.

extract.py의 단일 파일 규칙을 패키지 단위로 넓힌다.
- 모든 모델 입력 .py의 최상위 def를 '모듈.함수' 키로 색인한다.
- `from 모듈 import 이름`(상대 import, `*` 포함)으로 들어온 함수 호출을 모듈 사이 간선으로 해석한다.
- 매개변수 기본값의 `Depends(함수)`를 간선으로 본다 (FastAPI 의존성 주입).
미지원(미해석으로 표시만 함): 메서드·속성 호출(모듈 속성 호출 포함), 클래스 생성, 동적 호출, 중첩 함수 분리.
"""

import ast
import time
from collections import deque
from pathlib import Path

from .extract import FunctionInfo, _classify_call, _local_names, _module_names

# 조건 이름과 depth의 대응. None은 앱 전체 코드를 뜻한다.
EP_CONDITIONS = {"A_full": None, "B_handler": 0, "C_depth1": 1, "D_depth2": 2}

# 벤치별 모델 입력 파일 (벤치 루트 기준 glob). tests/, 명세, 정답 파일은 넣지 않는다.
INPUT_GLOBS = {
    "campus": ["app/**/*.py"],
    "vampi": ["app.py", "config.py", "api_views/*.py", "models/*.py"],
}


# 외부 소스(globs를 직접 준 경우)에서 모델 입력으로 쓰지 않는 디렉터리 이름
EXTERNAL_EXCLUDE_DIRS = {"tests", "test", ".venv", "venv", "env", "migrations", "node_modules",
                         "site-packages", "__pycache__", ".git"}


def input_files(bench_dir, globs=None):
    """벤치 디렉터리에서 모델 입력이 되는 .py 경로(상대 경로 문자열) 목록을 정렬해서 돌려준다.

    globs를 주면 벤치 이름 규칙 대신 그 패턴을 쓰고, EXTERNAL_EXCLUDE_DIRS 아래 파일은 뺀다 (외부 소스용).
    """
    bench_dir = Path(bench_dir)
    external = globs is not None
    if not external:
        globs = INPUT_GLOBS.get(bench_dir.name.split("_")[0], ["**/*.py"])  # vampi_vuln → vampi, 그 밖은 전체
    files = {p.relative_to(bench_dir).as_posix() for g in globs for p in bench_dir.glob(g)}
    if external:
        files = {f for f in files if not EXTERNAL_EXCLUDE_DIRS.intersection(f.split("/")[:-1])}
    return sorted(files)


def _module_name(rel):
    """상대 경로 'app/routers/x.py'를 모듈 이름 'app.routers.x'로 바꾼다 (__init__은 패키지 이름)."""
    parts = rel[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_from(module, node):
    """ImportFrom 노드의 대상 모듈 이름을 돌려준다 (상대 import 처리)."""
    if not node.level:
        return node.module or ""
    base = module.split(".")[: -node.level] if node.level else []
    return ".".join(base + ([node.module] if node.module else []))


class Codebase:
    """벤치 하나의 함수 색인. functions: {'모듈.함수': FunctionInfo}, files: {상대경로: 원문}."""

    def __init__(self, bench_dir, globs=None):
        self.bench_dir = Path(bench_dir)
        self.files = {rel: (self.bench_dir / rel).read_text(errors="replace") for rel in input_files(bench_dir, globs)}
        self.functions, self.warnings = {}, []
        self.func_file = {}
        trees = {}
        for rel, src in list(self.files.items()):
            try:
                trees[rel] = ast.parse(src)
            except SyntaxError as exc:
                self.warnings.append(f"syntax error in {rel}: skipped ({exc.msg}, line {exc.lineno})")
                del self.files[rel]
        self.trees = trees  # route_map이 데코레이터를 읽을 때 다시 쓴다
        defs_by_module = {}
        for rel, tree in trees.items():
            defs_by_module[_module_name(rel)] = [n.name for n in tree.body
                                                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for rel, tree in trees.items():
            self._index_module(rel, tree, defs_by_module)

    def _index_module(self, rel, tree, defs_by_module):
        """모듈 하나의 최상위 함수와 호출(직접 호출, from-import 호출, Depends 인자)을 기록한다."""
        module = _module_name(rel)
        source = self.files[rel]
        lines = source.splitlines()
        classes, imports, assigned = _module_names(tree)
        # 이 모듈에서 이름 하나로 부를 수 있는 함수: 지역 정의 + from-import로 들어온 함수
        callable_names = {name: f"{module}.{name}" for name in defs_by_module[module]}
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            target = _resolve_from(module, node)
            for alias in node.names:
                if alias.name == "*":
                    for name in defs_by_module.get(target, []):
                        callable_names[name] = f"{target}.{name}"
                elif alias.name in defs_by_module.get(target, []):
                    callable_names[alias.asname or alias.name] = f"{target}.{alias.name}"
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            qual = f"{module}.{node.name}"
            if qual in self.functions:
                self.warnings.append(f"duplicate definition of {qual}: using the later one (line {node.lineno})")
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            info = FunctionInfo(qual, "\n".join(lines[start - 1:node.end_lineno]), start, node.end_lineno)
            local_names = _local_names(node)
            roots = list(node.body) + list(node.args.defaults) + list(node.args.kw_defaults or [])
            for root in roots:
                if root is None:
                    continue
                for sub in ast.walk(root):
                    if isinstance(sub, ast.Call):
                        self._add_call(info, sub, callable_names, local_names, classes, imports, assigned)
            self.functions[qual] = info
            self.func_file[qual] = rel

    def _add_call(self, info, call, callable_names, local_names, classes, imports, assigned):
        """호출 하나를 해석해 info.calls 또는 info.unresolved에 넣는다. Depends(f)는 f로의 간선으로 본다."""
        func = call.func
        if isinstance(func, ast.Name) and func.id == "Depends" and call.args:
            arg = call.args[0]
            if isinstance(arg, ast.Name) and arg.id in callable_names and arg.id not in local_names:
                self._link(info, callable_names[arg.id])
            elif isinstance(arg, ast.Name):
                self._unresolved(info, arg.id, "depends_unresolved")  # 프레임워크가 호출하는 의존성 객체
            return  # Depends(팩토리(...))의 안쪽 호출은 ast.walk가 따로 방문한다
        kind, value = _classify_call(call, set(callable_names), local_names, classes, imports, assigned)
        if kind == "resolved":
            self._link(info, callable_names[value])
        else:
            self._unresolved(info, value, kind)

    @staticmethod
    def _link(info, qual):
        """해석된 호출 대상을 중복 없이 기록한다."""
        if qual not in info.calls and qual != info.name:
            info.calls.append(qual)

    @staticmethod
    def _unresolved(info, text, kind):
        """미해석 호출을 중복 없이 기록한다."""
        if (text, kind) not in info.unresolved:
            info.unresolved.append((text, kind))

    def full_code(self):
        """A_full 입력: 모든 입력 파일을 경로 헤더와 함께 이어 붙인다."""
        return "\n\n".join(f"# file: {rel}\n{src.rstrip()}" for rel, src in self.files.items()) + "\n"

    def handler_qual(self, rel, handler):
        """엔드포인트의 파일과 핸들러 이름으로 '모듈.함수' 키를 만든다."""
        qual = f"{_module_name(rel)}.{handler}"
        if qual not in self.functions:
            raise KeyError(f"handler not found: {qual}")
        return qual


def build_endpoint_context(codebase, endpoint, condition):
    """조건별로 LLM에 넣을 코드와 메타데이터를 만든다 (predict.build_context와 같은 키)."""
    start = time.perf_counter()
    target = codebase.handler_qual(endpoint["file"], endpoint["handler"])
    depth = EP_CONDITIONS[condition]
    if depth is None:
        return {"condition": condition, "code": codebase.full_code(), "included": ["<entire codebase>"],
                "excluded_by_depth": [], "unresolved": [], "warnings": list(codebase.warnings),
                "target": target, "extract_seconds": time.perf_counter() - start}
    functions = codebase.functions
    level = {target: 0}
    queue = deque([target])
    excluded = []
    while queue:
        name = queue.popleft()
        for callee in functions[name].calls:
            if callee in level:
                continue  # 이미 방문함: 순환 호출이나 여러 경로로 만나는 함수
            if level[name] + 1 > depth:
                if callee not in excluded:
                    excluded.append(callee)
                continue
            level[callee] = level[name] + 1
            queue.append(callee)
    excluded = [n for n in excluded if n not in level]
    included = sorted(level, key=lambda n: (codebase.func_file[n], functions[n].lineno))
    unresolved = [{"in": n, "call": call, "kind": kind} for n in included for call, kind in functions[n].unresolved]
    blocks, current = [], None
    for n in included:
        rel = codebase.func_file[n]
        header = f"# file: {rel}\n" if rel != current else ""
        current = rel
        blocks.append(header + functions[n].source)
    return {"condition": condition, "code": "\n\n".join(blocks) + "\n", "included": included,
            "excluded_by_depth": excluded, "unresolved": unresolved, "warnings": list(codebase.warnings),
            "target": target, "extract_seconds": time.perf_counter() - start}
