"""Python ast로 같은 파일 안의 직접 함수 호출을 따라가며 관련 함수 원문을 추출하는 모듈.

지원 범위: 모듈 최상위 def/async def와 `이름(...)` 형태의 직접 호출.
미지원(미해석으로 표시만 함): 속성·메서드 호출, import된 이름, 클래스 생성,
지역 변수에 담긴 함수, 데코레이터, getattr 같은 동적 호출.
"""

import ast
import builtins
import time
from collections import deque
from dataclasses import dataclass, field

# 조건 이름과 depth의 대응. None은 전체 파일을 뜻한다.
CONDITIONS = {"A_full": None, "B_depth0": 0, "C_depth1": 1, "D_depth2": 2}

BUILTIN_NAMES = set(dir(builtins))
DYNAMIC_BUILTINS = {"getattr", "eval", "exec", "globals", "locals", "__import__"}


@dataclass
class FunctionInfo:
    """최상위 함수 하나의 이름, 원문, 위치, 호출 목록."""
    name: str
    source: str
    lineno: int
    end_lineno: int
    calls: list = field(default_factory=list)       # 파일 내 함수로 해석된 호출 이름 (등장 순서, 중복 제거)
    unresolved: list = field(default_factory=list)  # (호출 텍스트, 분류) 목록


@dataclass
class Extraction:
    """한 조건(depth)에 대한 추출 결과."""
    target: str
    depth: int
    included: list            # 포함된 함수 이름 (파일 내 등장 순서)
    excluded_by_depth: list   # 파일 내 함수지만 depth 한도로 빠진 호출 대상
    unresolved: list          # 포함된 함수 안의 미해석 호출 [{"in", "call", "kind"}]
    code: str                 # LLM에 넣을 함수 원문 묶음
    warnings: list
    extract_seconds: float


def _local_names(func_node):
    """함수의 매개변수와 함수 안에서 대입된 이름을 모은다 (지역 변수 호출 판별용)."""
    names = {a.arg for a in ast.walk(func_node.args) if isinstance(a, ast.arg)}
    for node in ast.walk(func_node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
    return names


def _module_names(tree):
    """모듈 최상위의 클래스, import, 전역 변수 이름을 분류해서 돌려준다."""
    classes, imports, assigned = set(), set(), set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                imports.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        assigned.add(n.id)
    return classes, imports, assigned


def _classify_call(call, func_names, local_names, classes, imports, assigned):
    """호출 하나를 ('resolved', 이름) 또는 (분류, 텍스트)로 나눈다."""
    func = call.func
    text = ast.unparse(func)
    if isinstance(func, ast.Name):
        name = func.id
        if name in local_names:
            return "dynamic_local", text      # 매개변수·지역 변수로 받은 함수
        if name in func_names:
            return "resolved", name
        if name in DYNAMIC_BUILTINS:
            return "dynamic_builtin", text
        if name in classes:
            return "class_constructor", text
        if name in imports:
            return "imported", text
        if name in assigned:
            return "module_variable", text
        if name in BUILTIN_NAMES:
            return "builtin", text
        return "unknown_name", text
    if isinstance(func, ast.Attribute):
        return "attribute_call", text         # 메서드 타입 추론은 하지 않는다
    return "dynamic_expression", text         # f()(), d[k]() 등


def parse_functions(source):
    """파일 원문에서 최상위 함수 정보를 모은다. 같은 이름이 두 번 정의되면 마지막 정의를 쓴다."""
    tree = ast.parse(source)
    classes, imports, assigned = _module_names(tree)
    defs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    func_names = {d.name for d in defs}
    functions, warnings = {}, []
    for node in defs:
        if node.name in functions:
            warnings.append(f"duplicate definition of {node.name}: using the later one (line {node.lineno})")
        if node.decorator_list:
            warnings.append(f"decorators on {node.name} are not analyzed")
        info = FunctionInfo(node.name, ast.get_source_segment(source, node), node.lineno, node.end_lineno)
        local_names = _local_names(node)
        # 데코레이터는 분석하지 않으므로 본문과 기본값만 순회한다.
        roots = list(node.body) + list(node.args.defaults) + list(node.args.kw_defaults or [])
        for root in roots:
            if root is None:
                continue
            for sub in ast.walk(root):
                if not isinstance(sub, ast.Call):
                    continue
                kind, value = _classify_call(sub, func_names, local_names, classes, imports, assigned)
                if kind == "resolved":
                    if value not in info.calls:
                        info.calls.append(value)
                elif (value, kind) not in info.unresolved:
                    info.unresolved.append((value, kind))
        functions[node.name] = info
    return functions, warnings


def extract(source, target, depth):
    """대상 함수에서 호출 간선을 depth개까지 따라가 관련 함수 원문을 모은다 (BFS, 순환·중복은 visited로 처리)."""
    start = time.perf_counter()
    functions, warnings = parse_functions(source)
    if target not in functions:
        raise KeyError(f"target function not found: {target}")

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

    included = sorted(level, key=lambda n: functions[n].lineno)
    unresolved = [
        {"in": n, "call": call, "kind": kind}
        for n in included for call, kind in functions[n].unresolved
    ]
    code = "\n\n\n".join(functions[n].source for n in included) + "\n"
    elapsed = time.perf_counter() - start
    return Extraction(target, depth, included, excluded, unresolved, code, warnings, elapsed)


def build_context(source, target, condition):
    """조건별로 LLM에 넣을 코드와 메타데이터를 만든다. A_full은 파일 원문을 그대로 쓴다."""
    depth = CONDITIONS[condition]
    if depth is None:
        start = time.perf_counter()
        ast.parse(source)  # 다른 조건과 같은 파싱 비용을 포함하도록 문법 확인만 한다
        elapsed = time.perf_counter() - start
        return {"condition": condition, "code": source, "included": ["<entire file>"],
                "excluded_by_depth": [], "unresolved": [], "warnings": [], "extract_seconds": elapsed}
    ex = extract(source, target, depth)
    return {"condition": condition, "code": ex.code, "included": ex.included,
            "excluded_by_depth": ex.excluded_by_depth, "unresolved": ex.unresolved,
            "warnings": ex.warnings, "extract_seconds": ex.extract_seconds}
