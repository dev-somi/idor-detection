"""LLM 없이 조건별 추출 결과를 정리하는 리포트 (모델 실행이 막혀도 만들 수 있는 산출물).

출력: runs/extraction/extraction.csv, extraction.md, 사례·조건별 실제 입력 프롬프트(prompts/*.txt)
사용: python3 -m idor_ctx.report_extraction
"""

import csv
import json
from pathlib import Path

from .extract import CONDITIONS, build_context
from .predict import load_cases
from .prompt import SYSTEM_PROMPT, build_user_prompt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "extraction"


def main():
    """모든 사례·조건의 추출 결과와 문자 수, 필요 함수 포함 여부를 기록한다."""
    (OUT / "prompts").mkdir(parents=True, exist_ok=True)
    # 커버리지 계산에만 정답표의 required_functions를 쓴다 (예측 단계와는 별개의 리포트)
    labels = json.loads((ROOT / "ground_truth" / "labels.json").read_text())["cases"]
    rows = []
    for case in load_cases():
        label = labels[case["case_id"]]
        for cond in CONDITIONS:
            ctx = build_context(case["source"], case["target"], cond)
            prompt = build_user_prompt(case["policy"], case["target"], ctx)
            (OUT / "prompts" / f"{case['case_id']}_{cond}.txt").write_text(
                "=== SYSTEM ===\n" + SYSTEM_PROMPT + "\n\n=== USER ===\n" + prompt)
            if cond == "A_full":
                sufficient = True
            else:
                sufficient = not label["out_of_scope"] and set(label["required_functions"]) <= set(ctx["included"])
            rows.append({
                "case_id": case["case_id"], "condition": cond, "target": case["target"],
                "included": " ".join(ctx["included"]),
                "excluded_by_depth": " ".join(ctx["excluded_by_depth"]),
                "unresolved_non_builtin": " ".join(u["call"] for u in ctx["unresolved"] if u["kind"] != "builtin"),
                "code_chars": len(ctx["code"]), "prompt_chars": len(SYSTEM_PROMPT) + len(prompt),
                "extract_ms": round(ctx["extract_seconds"] * 1000, 4),
                "needed_code_included": sufficient,
            })
    with open(OUT / "extraction.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = ["# 조건별 코드 추출 결과 (LLM 미사용)", "",
             "문자 수는 토큰 수의 대체 지표이며 실제 토큰 수가 아니다. 추출 시간은 단일 측정값이다.", "",
             "| 사례 | 조건 | 포함 함수 | 깊이 한도로 제외 | 미해석 호출(builtin 제외) | 코드 문자 수 | 필요 코드 포함 |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['case_id']} | {r['condition']} | {r['included']} | {r['excluded_by_depth'] or '-'} | "
                     f"{r['unresolved_non_builtin'] or '-'} | {r['code_chars']} | {'예' if r['needed_code_included'] else '아니오'} |")
    lines += ["", "## 조건별 합계", "", "| 조건 | 평균 코드 문자 수 | 필요 코드 포함 사례 |", "|---|---|---|"]
    for cond in CONDITIONS:
        sub = [r for r in rows if r["condition"] == cond]
        avg = sum(r["code_chars"] for r in sub) / len(sub)
        lines.append(f"| {cond} | {avg:.1f} | {sum(r['needed_code_included'] for r in sub)}/{len(sub)} |")
    (OUT / "extraction.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}/extraction.md")


if __name__ == "__main__":
    main()
