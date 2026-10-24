"""OpenAPI 작업(method + path)을 소스 코드의 핸들러 함수에 자동으로 연결하는 모듈 (ADR 0007).

bench/*/endpoints.json에 사람이 적던 file·handler를 외부 소스에서도 얻기 위해 쓴다. 연결 규칙(우선순위 순):
1. operationId가 '모듈.함수' 키와 그대로 같다 (connexion 방식, 예: api_views.users.get_by_username).
2. 데코레이터 `@X.get('/p')`, `@X.api_route('/p', methods=[...])`, `@X.route('/p', methods=[...])`의 경로가 같다.
   `X = APIRouter(prefix='/a')`, `Blueprint(..., url_prefix='/a')`, `include_router(X, prefix='/b')`는 문자열 상수일 때만 반영한다.
3. FastAPI 기본 operationId(`{함수명}_{경로}_{메서드}`)가 함수 이름으로 시작한다 (이름이 하나뿐일 때만).
4. 모두 실패하면 how="unmapped"로 남긴다.
경로는 파라미터 이름을 무시하고 비교한다 ({id} = {user_id}, Flask <int:id> 포함).
"""

import ast
import re

from .ep_extract import _module_name, _resolve_from

HTTP_VERBS = {"get", "post", "put", "patch", "delete", "head", "options"}


def normalize_path(path):
    """경로를 비교용으로 바꾼다: 파라미터를 {}로, 끝 슬래시와 중복 슬래시를 없앤다."""
    path = re.sub(r"\{[^{}]*\}", "{}", str(path or ""))
    path = re.sub(r"<[^<>]*>", "{}", path)
    path = "/" + re.sub(r"/{2,}", "/", path).strip("/")
    return path


def _const_str(node):
    """문자열 상수 노드면 값을, 아니면 None을 돌려준다."""
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _kw(call, *names):
    """호출의 키워드 인자 중 이름이 맞는 첫 값 노드를 돌려준다."""
    for k in call.keywords:
        if k.arg in names:
            return k.value
    return None


def _router_prefixes(module, tree):
    """모듈 최상위 `X = APIRouter(prefix=...)` / `Blueprint(url_prefix=...)`에서 {변수: 접두어}를 모은다."""
    out = {}
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)):
            continue
        prefix = _const_str(_kw(node.value, "prefix", "url_prefix"))
        if prefix is None:
            continue
        for t in node.targets:
            if isinstance(t, ast.Name):
                out[(module, t.id)] = prefix
    return out


def _include_prefixes(module, tree):
    """`include_router(라우터, prefix='/p')` 호출에서 {(라우터가 정의된 모듈, 변수): 접두어}를 모은다."""
    imported_modules, imported_names = {}, {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            target = _resolve_from(module, node)
            for alias in node.names:
                local = alias.asname or alias.name
                imported_modules[local] = f"{target}.{alias.name}" if target else alias.name  # from pkg import mod
                imported_names[local] = (target, alias.name)                                  # from mod import router
    out = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "include_router" and node.args):
            continue
        prefix = _const_str(_kw(node, "prefix"))
        if prefix is None:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Attribute) and isinstance(arg.value, ast.Name) and arg.value.id in imported_modules:
            out[(imported_modules[arg.value.id], arg.attr)] = prefix
        elif isinstance(arg, ast.Name) and arg.id in imported_names:
            out[imported_names[arg.id]] = prefix
        elif isinstance(arg, ast.Name):
            out[(module, arg.id)] = prefix
    return out


def _decorator_routes_of(call):
    """데코레이터 호출 하나에서 (라우터 변수, [메서드], 경로)를 꺼낸다. 라우트 데코레이터가 아니면 None."""
    func = call.func
    if not (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)):
        return None
    path = _const_str(call.args[0]) if call.args else _const_str(_kw(call, "path", "rule"))
    if path is None:
        return None
    if func.attr in HTTP_VERBS:
        return func.value.id, [func.attr.upper()], path
    if func.attr in ("api_route", "route"):
        methods_node = _kw(call, "methods")
        if isinstance(methods_node, (ast.List, ast.Tuple, ast.Set)):
            methods = [m.upper() for m in (_const_str(e) for e in methods_node.elts) if m]
        else:
            methods = ["GET"]
        return func.value.id, methods, path
    return None


def decorator_routes(codebase):
    """코드베이스의 라우트 데코레이터를 모두 읽어 [{method, path, qual, file, handler}]로 돌려준다."""
    prefixes, includes = {}, {}
    for rel, tree in codebase.trees.items():
        module = _module_name(rel)
        prefixes.update(_router_prefixes(module, tree))
        includes.update(_include_prefixes(module, tree))
    routes = []
    for rel, tree in codebase.trees.items():
        module = _module_name(rel)
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                found = _decorator_routes_of(dec) if isinstance(dec, ast.Call) else None
                if not found:
                    continue
                var, methods, path = found
                full = includes.get((module, var), "") + prefixes.get((module, var), "") + path
                for m in methods:
                    routes.append({"method": m, "path": full, "qual": f"{module}.{node.name}",
                                   "file": rel, "handler": node.name})
    return routes


def _hit(codebase, qual, how):
    """연결 결과 한 건을 만든다."""
    return {"qual": qual, "file": codebase.func_file[qual], "handler": qual.rsplit(".", 1)[1], "how": how}


def map_routes(codebase, operations):
    """[{method, path, operationId?}] 각각에 file·handler·qual·how를 붙여 돌려준다 (입력 순서 유지)."""
    by_route = {}
    for r in decorator_routes(codebase):
        by_route.setdefault((r["method"], normalize_path(r["path"])), []).append(r["qual"])
    by_name = {}
    for qual in codebase.functions:
        by_name.setdefault(qual.rsplit(".", 1)[1], []).append(qual)
    out = []
    for op in operations:
        method = str(op.get("method", "")).upper()
        op_id = op.get("operationId") or ""
        hit = None
        if op_id in codebase.functions:
            hit = _hit(codebase, op_id, "operationId")
        if hit is None:
            quals = by_route.get((method, normalize_path(op.get("path"))), [])
            if len(quals) == 1:
                hit = _hit(codebase, quals[0], "decorator")
            elif len(quals) > 1:
                hit = {"qual": None, "file": None, "handler": None, "how": "ambiguous",
                       "candidates": quals}
        if hit is None and op_id:
            names = sorted((n for n in by_name if op_id.startswith(n + "_")), key=len, reverse=True)
            if names and len(by_name[names[0]]) == 1:
                hit = _hit(codebase, by_name[names[0]][0], "fastapi_operationId")
        if hit is None:
            hit = {"qual": None, "file": None, "handler": None, "how": "unmapped"}
        out.append({**op, "method": method, **hit})
    return out
