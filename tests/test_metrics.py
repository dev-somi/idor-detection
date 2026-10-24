"""평가 지표 계산 테스트: 혼동행렬, 판단 불가 처리, 분모 0일 때 N/A."""

import unittest

from idor_ctx.evaluate import confusion, evaluate, fmt

LABELS = {
    "c1": {"expected": "vulnerable", "required_functions": ["h"], "out_of_scope": []},
    "c2": {"expected": "not_vulnerable", "required_functions": [], "out_of_scope": []},
    "c3": {"expected": "vulnerable", "required_functions": [], "out_of_scope": []},
}


def rec(case_id, verdict, included=("t",)):
    """테스트용 예측 레코드 하나를 만든다."""
    return {"case_id": case_id, "condition": "B_depth0", "repeat": 1, "verdict": verdict,
            "included_functions": list(included), "prompt_tokens": 100, "code_chars": 10,
            "extract_seconds": 0.001, "inference_wall_seconds": 1.0, "output_tokens": 5,
            "context_overflow": False}


class MetricsTest(unittest.TestCase):
    """지표 계산 규칙을 확인한다."""

    def test_confusion_counts(self):
        # (정답 양성, 예측 양성) 조합이 올바른 칸에 들어가는지
        m = confusion([(True, True), (False, True), (True, False), (False, False)])
        self.assertEqual((m["TP"], m["FP"], m["FN"], m["TN"]), (1, 1, 1, 1))
        self.assertEqual(m["precision"], 0.5)

    def test_zero_denominator_is_na(self):
        # 양성 예측이 없으면 precision 분모가 0 → N/A
        m = confusion([(True, False), (False, False)])
        self.assertIsNone(m["precision"])
        self.assertEqual(fmt(m["precision"]), "N/A")
        self.assertIsNone(confusion([])["recall"])

    def test_insufficient_excluded_in_primary_and_positive_in_conservative(self):
        # 주 지표는 판단 불가를 빼고, 보수적 지표는 양성으로 센다
        rows = evaluate([rec("c1", "insufficient_context"), rec("c2", "no_issue_found"),
                         rec("c3", "vulnerable")], LABELS)
        r = rows[0]
        self.assertEqual((r["TP"], r["FN"], r["TN"]), (1, 0, 1))
        self.assertEqual(r["insufficient_context"], 1)
        self.assertAlmostEqual(r["decidable_ratio"], 2 / 3)
        self.assertEqual(r["cons_TP"], 2)

    def test_unsupported_no_issue_counted(self):
        # 필요한 함수가 입력에 없는데 no_issue_found면 '근거 없는 정상 판정'으로 센다
        rows = evaluate([rec("c1", "no_issue_found")], LABELS)
        self.assertEqual(rows[0]["no_issue_without_needed_code"], 1)
        rows = evaluate([rec("c1", "no_issue_found", included=("t", "h"))], LABELS)
        self.assertEqual(rows[0]["no_issue_without_needed_code"], 0)

    def test_decided_with_missing_context_counted(self):
        # 확정 판정인데 missing_context를 적은 경우를 따로 센다
        r = rec("c1", "vulnerable")
        r["missing_context"] = ["h body"]
        self.assertEqual(evaluate([r], LABELS)[0]["decided_with_missing_context"], 1)

    def test_parse_error_excluded_everywhere(self):
        # 파싱 실패는 두 지표 모두에서 제외되고 따로 센다
        r = evaluate([rec("c1", "parse_error")], LABELS)[0]
        self.assertEqual(r["parse_error"], 1)
        self.assertEqual(r["cons_TP"] + r["cons_FN"], 0)


if __name__ == "__main__":
    unittest.main()
