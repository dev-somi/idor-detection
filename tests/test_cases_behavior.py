"""정답 확인용 실행 테스트: 각 사례 코드를 실제로 실행해 labels.json의 정답과 일치하는지 본다.

판정: 공격자(다른 사용자) 호출에서 비공개 값이 반환되거나 channel에 기록되고,
정책상 허용된 접근이 아니면 vulnerable이다.
"""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LABELS = json.loads((ROOT / "ground_truth" / "labels.json").read_text())["cases"]


def load_module(case_id):
    """사례 app.py를 매번 새 모듈로 불러온다 (사례 간 상태 공유 방지)."""
    spec = importlib.util.spec_from_file_location(f"{case_id}_app", ROOT / "cases" / case_id / "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call_and_observe(case_id, args, private_value):
    """대상 함수를 호출하고, 비공개 값이 반환값이나 sink에 노출되었는지와 거부 여부를 돌려준다."""
    module = load_module(case_id)
    meta = json.loads((ROOT / "cases" / case_id / "meta.json").read_text())
    sink = []
    real_args = [sink if a == "$SINK" else a for a in args]
    try:
        result = getattr(module, meta["target"])(*real_args)
        denied = False
    except PermissionError:
        result, denied = None, True
    leaked = private_value in repr(result) or private_value in repr(sink)
    return leaked, denied


class CaseBehaviorTest(unittest.TestCase):
    """사례별로 실제 실행 결과와 정답표를 대조한다."""

    def test_owner_can_access(self):
        # 소유자는 항상 자기 데이터를 얻어야 한다 (예제 자체가 정상 동작하는지 확인)
        for case_id, label in LABELS.items():
            with self.subTest(case=case_id):
                probe = label["probe"]
                leaked, denied = call_and_observe(case_id, probe["owner"], probe["private_value"])
                self.assertTrue(leaked and not denied)

    def test_attacker_outcome_matches_label(self):
        # 다른 사용자의 접근 결과가 정답(vulnerable / not_vulnerable)과 일치해야 한다
        for case_id, label in LABELS.items():
            with self.subTest(case=case_id):
                probe = label["probe"]
                leaked, _ = call_and_observe(case_id, probe["attacker"], probe["private_value"])
                observed = "vulnerable" if leaked and not probe["attacker_allowed_by_policy"] else "not_vulnerable"
                self.assertEqual(observed, label["expected"])

    def test_required_type_coverage(self):
        # 필수 유형(검사 없음, 함수 내 검사, 1·2단계 보조 함수, 공개, 반환값 무시, 노출 후 검사)이 모두 있어야 한다
        needed = ["인가 검사 없음", "함수 안에서", "보조 함수(1단계)", "두 단계", "공개", "반환값을 무시", "내보낸 뒤"]
        types = " | ".join(label["type"] for label in LABELS.values())
        for word in needed:
            self.assertIn(word, types)


if __name__ == "__main__":
    unittest.main()
