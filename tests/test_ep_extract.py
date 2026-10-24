"""엔드포인트 추출기(idor_ctx.ep_extract) 단위 테스트: 모듈 사이 import, Depends 간선, depth, 순환, 실제 벤치 커버리지."""

import json
import tempfile
import unittest
from pathlib import Path

from idor_ctx.ep_extract import EP_CONDITIONS, Codebase, build_endpoint_context

ROOT = Path(__file__).resolve().parent.parent

# 합성 패키지: 라우터 → (from-import) 서비스 → 헬퍼, Depends 의존성, 상대 import, 순환, 모듈 속성 호출
FILES = {
    "pkg/__init__.py": "",
    "pkg/auth.py": "def current():\n    return 1\n\ndef role(name):\n    def checker(u=Depends(current)):\n        return u\n    return checker\n",
    "pkg/helpers.py": "def check(x):\n    return ping(x)\n\ndef ping(x):\n    return check(x)\n",
    "pkg/service.py": "from .helpers import check\nimport pkg.helpers as h\n\ndef load(x):\n    h.ping(x)\n    return check(x)\n",
    "pkg/router.py": ("from pkg.auth import current, role\nfrom pkg.service import load\n\n"
                      "@router.get('/x/{x}')\ndef handler(x, u=Depends(current), v=Depends(role('a'))):\n    return load(x)\n"),
}


class EndpointExtractTest(unittest.TestCase):
    """합성 패키지로 간선 해석과 깊이별 포함 함수를 확인한다."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        for rel, text in FILES.items():
            path = Path(cls.tmp.name) / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        cls.cb = Codebase(cls.tmp.name)
        cls.endpoint = {"file": "pkg/router.py", "handler": "handler"}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def ctx(self, cond):
        return build_endpoint_context(self.cb, self.endpoint, cond)

    def test_edges_cross_module_and_depends(self):
        # from-import 호출, Depends(함수), Depends(팩토리(...))가 모두 간선이 된다
        calls = self.cb.functions["pkg.router.handler"].calls
        self.assertEqual(sorted(calls), ["pkg.auth.current", "pkg.auth.role", "pkg.service.load"])
        # 팩토리 안 중첩 함수의 Depends도 팩토리의 간선으로 잡힌다
        self.assertEqual(self.cb.functions["pkg.auth.role"].calls, ["pkg.auth.current"])
        # 상대 import(from .helpers import check)도 해석된다
        self.assertEqual(self.cb.functions["pkg.service.load"].calls, ["pkg.helpers.check"])

    def test_module_attribute_call_is_unresolved(self):
        # 모듈 속성 호출(h.ping)은 따라가지 않고 미해석으로 남긴다
        self.assertIn(("h.ping", "attribute_call"), self.cb.functions["pkg.service.load"].unresolved)

    def test_depths(self):
        # B는 핸들러만, C는 직접 간선, D는 두 단계까지. 순환(check ↔ ping)은 visited로 끝난다
        self.assertEqual(self.ctx("B_handler")["included"], ["pkg.router.handler"])
        self.assertEqual(sorted(self.ctx("C_depth1")["included"]),
                         ["pkg.auth.current", "pkg.auth.role", "pkg.router.handler", "pkg.service.load"])
        d = self.ctx("D_depth2")
        self.assertIn("pkg.helpers.check", d["included"])
        self.assertEqual(d["excluded_by_depth"], ["pkg.helpers.ping"])

    def test_handler_source_includes_decorator_and_file_header(self):
        # 핸들러 원문에 라우트 데코레이터가 들어가고, 파일마다 경로 헤더가 붙는다
        code = self.ctx("B_handler")["code"]
        self.assertTrue(code.startswith("# file: pkg/router.py\n@router.get('/x/{x}')"))

    def test_full_condition_has_every_file(self):
        code = self.ctx("A_full")["code"]
        for rel in FILES:
            self.assertIn(f"# file: {rel}", code)


class BenchCoverageTest(unittest.TestCase):
    """실제 벤치에서 정답표의 필요 함수가 설계한 조건에서 처음 들어오는지 확인한다 (LLM과 무관)."""

    def test_first_sufficient_condition(self):
        labels = json.loads((ROOT / "ground_truth" / "endpoints.json").read_text())["items"]
        expected_first = {"campus:e18": "C_depth1", "campus:e19": "C_depth1", "campus:e20": "D_depth2",
                          "campus:e21": "C_depth1", "campus:e22": "D_depth2", "campus:e23": "C_depth1",
                          "campus:e24": "D_depth2", "campus:e25": "C_depth1", "campus:e01": "B_handler",
                          "vampi_secure:e01": "C_depth1", "vampi_vuln:e01": "B_handler"}
        cbs = {}
        for item_id, want in expected_first.items():
            bench = item_id.split(":")[0]
            cbs.setdefault(bench, Codebase(ROOT / "bench" / bench))
            endpoint = next(e for e in json.loads((ROOT / "bench" / bench / "endpoints.json").read_text())
                            if e["item_id"] == item_id)
            need = set(labels[item_id]["required_functions"])
            first = next(c for c in list(EP_CONDITIONS)[1:]
                         if need <= set(build_endpoint_context(cbs[bench], endpoint, c)["included"]))
            with self.subTest(item=item_id):
                self.assertEqual(first, want)

    def test_every_endpoint_handler_resolves(self):
        # endpoints.json의 모든 핸들러가 색인에 있다
        for bench in ["campus", "vampi_vuln", "vampi_secure"]:
            cb = Codebase(ROOT / "bench" / bench)
            for e in json.loads((ROOT / "bench" / bench / "endpoints.json").read_text()):
                with self.subTest(item=e["item_id"]):
                    cb.handler_qual(e["file"], e["handler"])


if __name__ == "__main__":
    unittest.main()
