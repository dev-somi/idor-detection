"""엔드포인트 벤치 누출 방지 테스트: 모델 입력 코드·프롬프트에 정답 힌트가 없고, 예측 단계가 정답 파일을 읽지 않는지 확인한다."""

import ast
import io
import json
import re
import tokenize
import unittest
from pathlib import Path

from idor_ctx.ep_extract import EP_CONDITIONS, Codebase, build_endpoint_context, input_files
from idor_ctx.prompt import build_endpoint_prompt

ROOT = Path(__file__).resolve().parent.parent
BENCHES = ["campus", "vampi_vuln", "vampi_secure"]
# test_leakage의 금지어 중 safe·secure·bug·correct·expected 등은 앱 원문 어휘("_debug", "not correct" 등)와 겹쳐 뺐다.
FORBIDDEN = ["vulnerab", "vuln", "insecure", "idor", "bola", "exploit", "no_issue", "insufficient",
             "case_", "ground_truth", "attack"]


def _endpoints(bench):
    return json.loads((ROOT / "bench" / bench / "endpoints.json").read_text())


class BenchCleanTest(unittest.TestCase):
    """벤치 코드, 엔드포인트 목록, 프롬프트 구성을 검사한다."""

    def test_input_files_have_no_comments_docstrings_or_hint_words(self):
        for bench in BENCHES:
            for rel in input_files(ROOT / "bench" / bench):
                src = (ROOT / "bench" / bench / rel).read_text()
                with self.subTest(file=f"{bench}/{rel}"):
                    tokens = tokenize.generate_tokens(io.StringIO(src).readline)
                    self.assertFalse(any(t.type == tokenize.COMMENT for t in tokens))
                    for node in ast.walk(ast.parse(src)):
                        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
                            first = node.body[0]
                            self.assertFalse(isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                                             and isinstance(first.value.value, str))
                    for word in ["vuln", "idor", "bola", "exploit", "insecure"]:
                        self.assertNotIn(word, src.lower())

    def test_endpoint_files_have_no_label_fields(self):
        for bench in BENCHES:
            for e in _endpoints(bench):
                self.assertEqual(set(e), {"item_id", "method", "path", "file", "handler", "policy"})

    def test_prompts_have_no_answer_words(self):
        for bench in BENCHES:
            cb = Codebase(ROOT / "bench" / bench)
            for e in _endpoints(bench):
                for cond in EP_CONDITIONS:
                    text = build_endpoint_prompt(e["policy"], e, build_endpoint_context(cb, e, cond)).lower()
                    for word in FORBIDDEN:
                        with self.subTest(item=e["item_id"], cond=cond, word=word):
                            self.assertNotIn(word, text)

    def test_prompt_is_identical_across_conditions_except_code(self):
        # 조건 간 차이는 CODE와 CONTEXT NOTE 부분뿐이어야 한다
        cb = Codebase(ROOT / "bench" / "campus")
        e = _endpoints("campus")[0]
        heads = {build_endpoint_prompt(e["policy"], e, build_endpoint_context(cb, e, c)).split("CODE:")[0]
                 for c in EP_CONDITIONS}
        self.assertEqual(len(heads), 1)

    def test_prediction_code_does_not_reference_ground_truth(self):
        for name in ["ep_predict.py", "ep_extract.py", "prompt.py", "llm.py", "predict.py"]:
            src = (ROOT / "idor_ctx" / name).read_text()
            self.assertIsNone(re.search(r"ground_truth|labels\.json", src), name)

    def test_vampi_handlers_match_openapi_operation_ids(self):
        # VAmPI 라우팅은 openapi3.yml의 operationId로 정해진다. 엔드포인트 목록의 핸들러가 명세와 맞아야 한다
        for bench in ["vampi_vuln", "vampi_secure"]:
            spec = (ROOT / "bench" / bench / "openapi_specs" / "openapi3.yml").read_text()
            ops = set(re.findall(r"operationId:\s*(\S+)", spec))
            for e in _endpoints(bench):
                with self.subTest(item=e["item_id"]):
                    self.assertIn(e["file"][:-3].replace("/", ".") + "." + e["handler"], ops)

    def test_labels_cover_every_endpoint(self):
        labels = json.loads((ROOT / "ground_truth" / "endpoints.json").read_text())["items"]
        ids = {e["item_id"] for b in BENCHES for e in _endpoints(b)}
        self.assertEqual(ids, set(labels))


if __name__ == "__main__":
    unittest.main()
