"""추출기(idor_ctx.extract) 단위 테스트: depth, 순환, 중복, 미해석 호출 표시, AST 덤프 미사용."""

import unittest

from idor_ctx.extract import build_context, extract, parse_functions

# 테스트용 합성 코드: a → b → c → d 사슬, b ↔ e 순환, a/b 모두 c 호출(다이아몬드), 여러 종류의 미해석 호출
SAMPLE = '''
import os
from helpers import imported_fn

class Box:
    def open(self):
        return 1

def d():
    return 4

def c():
    return d()

def e():
    return b()

def b():
    os.path.join("x")
    return c() + e()

def a(fn):
    fn()
    getattr(Box, "open")
    imported_fn()
    Box().open()
    len([1])
    return b() + c()

def a_dup():
    return 1

def a_dup():
    return 2
'''


class ExtractTest(unittest.TestCase):
    """깊이별 추출 결과를 확인한다."""

    def test_depth0_only_target(self):
        # depth 0은 대상 함수만 포함하고, 호출된 파일 내 함수는 '깊이 한도로 제외'로 표시한다
        ex = extract(SAMPLE, "a", 0)
        self.assertEqual(ex.included, ["a"])
        self.assertEqual(sorted(ex.excluded_by_depth), ["b", "c"])

    def test_depth1_and_depth2(self):
        # depth 1은 직접 호출(b, c), depth 2는 두 단계(d, e)까지 포함한다
        self.assertEqual(sorted(extract(SAMPLE, "a", 1).included), ["a", "b", "c"])
        ex2 = extract(SAMPLE, "a", 2)
        self.assertEqual(sorted(ex2.included), ["a", "b", "c", "d", "e"])
        self.assertEqual(ex2.excluded_by_depth, [])

    def test_cycle_terminates_and_no_duplicates(self):
        # b ↔ e 순환과 c로 가는 두 경로가 있어도 함수는 한 번씩만 들어간다
        ex = extract(SAMPLE, "b", 5)
        self.assertEqual(len(ex.included), len(set(ex.included)))
        self.assertEqual(ex.code.count("def c():"), 1)

    def test_self_recursion(self):
        # 자기 자신을 호출하는 함수도 끝난다
        src = "def f(n):\n    return f(n - 1) if n else 0\n"
        self.assertEqual(extract(src, "f", 2).included, ["f"])

    def test_unresolved_calls_are_marked(self):
        # 파일 내 최상위 함수가 아닌 호출은 따라가지 않고 종류별로 표시한다
        kinds = {u["call"]: u["kind"] for u in extract(SAMPLE, "a", 0).unresolved}
        self.assertEqual(kinds["fn"], "dynamic_local")
        self.assertEqual(kinds["getattr"], "dynamic_builtin")
        self.assertEqual(kinds["imported_fn"], "imported")
        self.assertEqual(kinds["Box"], "class_constructor")
        self.assertEqual(kinds["Box().open"], "attribute_call")
        self.assertEqual(kinds["len"], "builtin")

    def test_duplicate_definition_uses_last(self):
        # 같은 이름이 두 번 정의되면 런타임처럼 마지막 정의를 쓰고 경고를 남긴다
        funcs, warnings = parse_functions(SAMPLE)
        self.assertIn("return 2", funcs["a_dup"].source)
        self.assertTrue(any("duplicate" in w for w in warnings))

    def test_output_is_source_not_ast_dump(self):
        # LLM 입력은 함수 원문이어야 하고 ast.dump 형태가 아니어야 한다
        code = extract(SAMPLE, "a", 1).code
        self.assertIn("def a(fn):", code)
        self.assertNotIn("FunctionDef(", code)
        self.assertNotIn("Name(id=", code)

    def test_full_condition_is_file_verbatim(self):
        # 조건 A는 파일 원문을 그대로 쓴다 (잘라내지 않음)
        self.assertEqual(build_context(SAMPLE, "a", "A_full")["code"], SAMPLE)

    def test_missing_target_raises(self):
        # 없는 대상 함수는 조용히 넘어가지 않고 오류를 낸다
        with self.assertRaises(KeyError):
            extract(SAMPLE, "nope", 1)


if __name__ == "__main__":
    unittest.main()
