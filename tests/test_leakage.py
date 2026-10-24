"""정답 누출 방지 테스트: 모델 입력에 정답 힌트가 없고, 예측 단계가 정답 파일을 읽지 않는지 확인한다."""

import io
import json
import re
import tokenize
import unittest
from pathlib import Path

from idor_ctx.extract import CONDITIONS, build_context
from idor_ctx.predict import load_cases
from idor_ctx.prompt import SYSTEM_PROMPT, build_user_prompt

ROOT = Path(__file__).resolve().parent.parent
# 사용자 프롬프트(정책 + 코드)에 나오면 안 되는 단어. verdict 단어는 시스템 프롬프트의 출력 형식 설명에만 있다.
FORBIDDEN = ["vulnerab", "insecure", "secure", "safe", "idor", "bola", "bug", "exploit",
             "no_issue", "insufficient", "expected", "correct", "wrong", "leak", "case_"]


class LeakageTest(unittest.TestCase):
    """입력 구성과 단계 분리를 검사한다."""

    def test_case_files_have_no_comments_or_docstrings(self):
        # 예제 코드는 그대로 모델 입력이 되므로 주석과 docstring이 없어야 한다
        for path in sorted((ROOT / "cases").glob("*/app.py")):
            with self.subTest(path=path.parent.name):
                src = path.read_text()
                tokens = tokenize.generate_tokens(io.StringIO(src).readline)
                self.assertFalse(any(t.type == tokenize.COMMENT for t in tokens))
                self.assertNotIn('"""', src)

    def test_user_prompts_have_no_answer_words(self):
        # 모든 사례·조건의 사용자 프롬프트에 금지어가 없어야 한다
        for case in load_cases():
            for cond in CONDITIONS:
                ctx = build_context(case["source"], case["target"], cond)
                text = build_user_prompt(case["policy"], case["target"], ctx).lower()
                for word in FORBIDDEN:
                    with self.subTest(case=case["case_id"], cond=cond, word=word):
                        self.assertNotIn(word, text)

    def test_case_meta_has_no_label_fields(self):
        # 모델 입력용 meta.json에는 case_id, target, policy만 있어야 한다
        for path in sorted((ROOT / "cases").glob("*/meta.json")):
            self.assertEqual(set(json.loads(path.read_text())), {"case_id", "target", "policy"})

    def test_prediction_code_does_not_reference_ground_truth(self):
        # 예측 경로의 모듈은 ground_truth 디렉터리를 참조하지 않는다
        for name in ["predict.py", "prompt.py", "extract.py", "llm.py"]:
            src = (ROOT / "idor_ctx" / name).read_text()
            self.assertIsNone(re.search(r"ground_truth|labels\.json", src), name)

    def test_prompt_is_identical_across_conditions_except_code(self):
        # 조건 간 차이는 CODE와 CONTEXT NOTE 부분뿐이어야 한다 (정책·대상·지시문 동일)
        case = load_cases()[0]
        heads = set()
        for cond in CONDITIONS:
            prompt = build_user_prompt(case["policy"], case["target"],
                                       build_context(case["source"], case["target"], cond))
            heads.add(prompt.split("CODE:")[0])
        self.assertEqual(len(heads), 1)
        self.assertIn("insufficient_context", SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
