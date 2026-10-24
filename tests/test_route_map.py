"""주소→핸들러 자동 연결(idor_ctx.route_map) 테스트: 실제 벤치의 사람이 적은 연결과 일치하는지, 접두어·operationId 규칙."""

import json
import re
import tempfile
import unittest
from pathlib import Path

from idor_ctx.ep_extract import Codebase
from idor_ctx.route_map import map_routes, normalize_path

ROOT = Path(__file__).resolve().parent.parent


def ops_from_openapi_yml(path):
    """VAmPI openapi3.yml에서 (method, path, operationId)를 줄 단위로 읽는다 (표준 라이브러리만 쓰려고 YAML 파서 대신)."""
    ops, cur_path, cur_method = [], None, None
    for line in Path(path).read_text().splitlines():
        m = re.match(r"^  (/\S*):\s*$", line)
        if m:
            cur_path = m.group(1)
            continue
        m = re.match(r"^    (get|post|put|patch|delete):\s*$", line)
        if m:
            cur_method = m.group(1).upper()
            continue
        m = re.match(r"^\s+operationId:\s*(\S+)", line)
        if m and cur_path and cur_method:
            ops.append({"method": cur_method, "path": cur_path, "operationId": m.group(1)})
    return ops


class BenchMappingTest(unittest.TestCase):
    """자동 연결 결과가 bench/*/endpoints.json의 file·handler와 같은지 확인한다."""

    def check(self, name, ops, expected_how):
        """벤치 하나의 모든 엔드포인트가 기대한 규칙으로 정확히 연결되는지 본다."""
        cb = Codebase(ROOT / "bench" / name)
        got = {(r["method"], r["path"]): r for r in map_routes(cb, ops)}
        for e in json.loads((ROOT / "bench" / name / "endpoints.json").read_text()):
            r = got[(e["method"], e["path"])]
            self.assertEqual((r["file"], r["handler"]), (e["file"], e["handler"]), e["item_id"])
            self.assertEqual(r["how"], expected_how, e["item_id"])

    def test_campus_decorators(self):
        """FastAPI 캠퍼스: 데코레이터 경로만으로 25개 모두 연결된다."""
        eps = json.loads((ROOT / "bench/campus/endpoints.json").read_text())
        self.check("campus", [{"method": e["method"], "path": e["path"]} for e in eps], "decorator")

    def test_vampi_operation_ids(self):
        """connexion VAmPI: OpenAPI operationId가 '모듈.함수'와 같아서 그대로 연결된다."""
        for name in ("vampi_vuln", "vampi_secure"):
            self.check(name, ops_from_openapi_yml(ROOT / "bench" / name / "openapi_specs/openapi3.yml"), "operationId")


FILES = {
    "app/__init__.py": "",
    "app/routers/__init__.py": "",
    "app/routers/orders.py": ("router = APIRouter(prefix='/orders')\n\n"
                              "@router.get('/{order_id}')\ndef get_order(order_id):\n    return order_id\n\n"
                              "@router.api_route('/{order_id}', methods=['PUT', 'PATCH'])\ndef edit_order(order_id):\n    return 1\n"),
    "app/routers/legacy.py": ("bp = Blueprint('legacy', __name__, url_prefix='/old')\n\n"
                              "@bp.route('/items/<int:item_id>', methods=['DELETE'])\ndef drop_item(item_id):\n    return 1\n"),
    "app/routers/plain.py": "def list_invoices_v2(user):\n    return []\n",
    "app/main.py": ("from .routers import orders\n\n"
                    "app.include_router(orders.router, prefix='/api')\n"),
}


class SyntheticMappingTest(unittest.TestCase):
    """합성 코드로 접두어, methods 목록, Flask 경로 문법, FastAPI 기본 operationId, 실패 표시를 확인한다."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        for rel, text in FILES.items():
            p = Path(cls.tmp.name) / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        cls.cb = Codebase(cls.tmp.name, globs=["**/*.py"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def one(self, **op):
        """작업 하나를 연결해 결과를 돌려준다."""
        return map_routes(self.cb, [op])[0]

    def test_include_and_router_prefix(self):
        """include_router 접두어 + APIRouter 접두어 + 데코레이터 경로가 이어 붙고, 파라미터 이름은 무시된다."""
        r = self.one(method="GET", path="/api/orders/{id}")
        self.assertEqual((r["handler"], r["how"]), ("get_order", "decorator"))

    def test_methods_list(self):
        """api_route의 methods 목록에 있는 메서드마다 연결된다."""
        self.assertEqual(self.one(method="PATCH", path="/api/orders/{x}")["handler"], "edit_order")
        self.assertEqual(self.one(method="DELETE", path="/api/orders/{x}")["how"], "unmapped")

    def test_flask_blueprint(self):
        """Blueprint url_prefix와 Flask <int:id> 경로 문법을 처리한다."""
        self.assertEqual(self.one(method="DELETE", path="/old/items/{item_id}")["handler"], "drop_item")

    def test_fastapi_default_operation_id(self):
        """데코레이터가 없어도 FastAPI 기본 operationId가 함수 이름으로 시작하면 연결한다."""
        r = self.one(method="GET", path="/elsewhere", operationId="list_invoices_v2_invoices_get")
        self.assertEqual((r["handler"], r["how"]), ("list_invoices_v2", "fastapi_operationId"))

    def test_unmapped(self):
        """어느 규칙에도 맞지 않으면 버리지 않고 unmapped로 남긴다."""
        r = self.one(method="GET", path="/nowhere")
        self.assertEqual((r["how"], r["handler"]), ("unmapped", None))

    def test_normalize_path(self):
        """파라미터 이름, 끝 슬래시, 중복 슬래시를 무시한다."""
        self.assertEqual(normalize_path("/a//{x}/b/"), normalize_path("/a/<int:y>/b"))


if __name__ == "__main__":
    unittest.main()
