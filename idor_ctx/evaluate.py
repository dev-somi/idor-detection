"""평가 단계: 예측(predictions.jsonl)과 정답표(ground_truth/labels.json)를 비교해 지표를 만든다.

양성(positive) = vulnerable.
- 주 지표: insufficient_context와 parse_error를 혼동행렬에서 제외하고, 판단 가능 비율을 따로 보고한다.
- 보조 지표(보수적): insufficient_context를 '사람 검토 필요'로 보아 양성으로 센다. parse_error는 여전히 제외한다.
분모가 0이면 N/A로 표시한다.
사용: python3 -m idor_ctx.evaluate runs/<run_id>
"""

import csv
import json
import sys
from pathlib import Path
from statistics import mean

from .extract import CONDITIONS

ROOT = Path(__file__).resolve().parent.parent
LABELS_PATH = ROOT / "ground_truth" / "labels.json"


def ratio(num, den):
    """분모가 0이면 None(N/A)을 돌려준다."""
    return None if den == 0 else num / den


def fmt(value, digits=3):
    """None은 'N/A'로, 실수는 소수점 자리수를 맞춰 문자열로 만든다."""
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}" if isinstance(value, float) else str(value)


def context_sufficient(record, label):
    """추출된 코드에 판단에 필요한 함수가 모두 들어 있는지 (LLM과 무관한 결정적 값)."""
    if record["condition"] == "A_full":
        return True
    if label["out_of_scope"]:
        return False
    return set(label["required_functions"]) <= set(record["included_functions"])


def confusion(pairs):
    """(정답, 예측양성여부) 목록으로 TP/FP/FN/TN과 precision/recall/accuracy를 계산한다."""
    tp = sum(1 for gold, pos in pairs if gold and pos)
    fp = sum(1 for gold, pos in pairs if not gold and pos)
    fn = sum(1 for gold, pos in pairs if gold and not pos)
    tn = sum(1 for gold, pos in pairs if not gold and not pos)
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": ratio(tp, tp + fp), "recall": ratio(tp, tp + fn),
            "accuracy": ratio(tp + tn, len(pairs))}


def evaluate(records, labels):
    """조건별 지표 사전 목록을 돌려준다."""
    rows = []
    for cond in CONDITIONS:
        recs = [r for r in records if r["condition"] == cond]
        if not recs:
            continue
        gold = {r["case_id"]: labels[r["case_id"]]["expected"] == "vulnerable" for r in recs}
        decided = [r for r in recs if r["verdict"] in ("vulnerable", "no_issue_found")]
        insufficient = [r for r in recs if r["verdict"] == "insufficient_context"]
        parse_errors = [r for r in recs if r["verdict"] == "parse_error"]
        primary = confusion([(gold[r["case_id"]], r["verdict"] == "vulnerable") for r in decided])
        conservative = confusion([(gold[r["case_id"]], r["verdict"] != "no_issue_found")
                                  for r in recs if r["verdict"] != "parse_error"])
        suff = [context_sufficient(r, labels[r["case_id"]]) for r in recs]
        unsupported_ok = sum(1 for r, s in zip(recs, suff) if not s and r["verdict"] == "no_issue_found")
        # 확정 판정을 내렸는데 스스로 누락 정보를 적은 경우 (판정과 근거의 불일치)
        decided_with_missing = sum(1 for r in decided if r.get("missing_context"))
        # 사례별로 반복 실행의 판정이 모두 같은지
        by_case = {}
        for r in recs:
            by_case.setdefault(r["case_id"], set()).add(r["verdict"])
        consistent = sum(1 for v in by_case.values() if len(v) == 1)
        tokens = [r["prompt_tokens"] for r in recs if r["prompt_tokens"] is not None]
        rows.append({
            "condition": cond, "n": len(recs),
            **primary,
            "decided": len(decided), "insufficient_context": len(insufficient), "parse_error": len(parse_errors),
            "decidable_ratio": ratio(len(decided), len(recs)),
            "cons_TP": conservative["TP"], "cons_FP": conservative["FP"],
            "cons_FN": conservative["FN"], "cons_TN": conservative["TN"],
            "cons_precision": conservative["precision"], "cons_recall": conservative["recall"],
            "extraction_sufficient": sum(suff),
            "no_issue_without_needed_code": unsupported_ok,
            "decided_with_missing_context": decided_with_missing,
            "cases_consistent_across_repeats": f"{consistent}/{len(by_case)}",
            "context_overflow": sum(1 for r in recs if r["context_overflow"]),
            "mean_prompt_tokens": mean(tokens) if tokens else None,
            "mean_code_chars": mean(r["code_chars"] for r in recs),
            "mean_extract_ms": mean(r["extract_seconds"] for r in recs) * 1000,
            "mean_inference_s": mean(r["inference_wall_seconds"] for r in recs),
            "total_inference_s": sum(r["inference_wall_seconds"] for r in recs),
            "mean_output_tokens": mean(r["output_tokens"] or 0 for r in recs),
        })
    return rows


def per_case_table(records, labels):
    """사례 × 조건 판정표. 반복 실행이면 판정을 '/'로 이어 붙인다."""
    table = []
    for case_id, label in labels.items():
        row = {"case_id": case_id, "type": label["type"], "expected": label["expected"]}
        for cond in CONDITIONS:
            recs = sorted((r for r in records if r["case_id"] == case_id and r["condition"] == cond),
                          key=lambda r: r["repeat"])
            if not recs:
                row[cond] = "-"
                continue
            mark = "" if context_sufficient(recs[0], label) else " (코드부족)"
            row[cond] = "/".join(r["verdict"] for r in recs) + mark
        table.append(row)
    return table


def write_summary(run_dir, meta, rows, table, labels):
    """요약 Markdown(summary.md)을 쓴다. 실측값만 쓰고 해석은 최소화한다."""
    m, mach = meta["model"], meta["machine"]
    lines = [
        f"# 실험 요약: {meta['run_id']}", "",
        "> 자동 생성 파일(idor_ctx/evaluate.py). 자체 제작 예제 "
        f"{len(labels)}개에서 얻은 결과이며, 실제 프로젝트 전반으로 일반화할 수 없다.",
        f"> 반복 횟수: {meta['repeats']}" + (" — **단일 실행 결과**" if meta["single_run"] else ""), "",
        "## 실행 설정",
        f"- 모델: `{m['model']}` (family {m['family']}, {m['parameter_size']}, 양자화 {m['quantization_level']}, "
        f"format {m['format']}, digest {str(m['digest'])[:12]}), 모델 최대 문맥 {m['model_context_length']}",
        f"- 생성 설정: `{json.dumps(meta['generation_options'])}`, 출력은 JSON 스키마로 고정, 프롬프트 {meta['prompt_version']}",
        f"- 장비: {mach['cpu']}, RAM {mach['ram_gb']}GB, {mach['os']}, Python {mach['python']}, "
        f"Ollama 서버 {mach['ollama_server_version']}",
        f"- 모델 로딩 시간(본 지표와 별도): {meta['model_loading']['load_duration_s']:.2f}s "
        f"(워밍업 요청 벽시계 {meta['model_loading']['warmup_wall_s']:.2f}s)",
        f"- 실행 시각: {meta['started_at']} ~ {meta.get('finished_at')}", "",
        "## 판단 불가 처리 방식",
        "- **주 지표**: `insufficient_context`와 `parse_error`는 TP/FP/FN/TN에서 제외하고, 판단 가능 비율(decided/n)을 따로 적었다.",
        "- **보수적 지표(cons_)**: `insufficient_context`를 양성(사람 검토 필요)으로 셌다. `parse_error`는 제외했다.",
        "- 양성 = vulnerable. 분모가 0이면 N/A로 표시했다.", "",
        "## 조건별 탐지 지표",
        "| 조건 | n | TP | FP | FN | TN | precision | recall | 판단 불가 | parse_error | 판단 가능 비율 | cons precision | cons recall |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['condition']} | {r['n']} | {r['TP']} | {r['FP']} | {r['FN']} | {r['TN']} | "
                     f"{fmt(r['precision'])} | {fmt(r['recall'])} | {r['insufficient_context']} | {r['parse_error']} | "
                     f"{fmt(r['decidable_ratio'])} | {fmt(r['cons_precision'])} | {fmt(r['cons_recall'])} |")
    lines += [
        "", "## 조건별 비용과 추출 커버리지",
        "토큰 수는 Ollama가 보고한 `prompt_eval_count`(시스템 프롬프트와 채팅 템플릿 포함, 실제 토크나이저 기준)이다. "
        "문자 수는 참고용 대체 지표다.", "",
        "| 조건 | 평균 입력 토큰 | 평균 코드 문자 수 | 평균 추출 시간(ms) | 평균 추론 시간(s) | 총 추론 시간(s) | 평균 출력 토큰 | 필요 코드 포함 | 필요 코드 없이 no_issue | 누락 정보를 적고도 확정 판정 | 반복 간 판정 일치 | 문맥 초과 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['condition']} | {fmt(r['mean_prompt_tokens'], 1)} | {fmt(r['mean_code_chars'], 1)} | "
                     f"{fmt(r['mean_extract_ms'], 3)} | {fmt(r['mean_inference_s'], 2)} | {fmt(r['total_inference_s'], 1)} | "
                     f"{fmt(r['mean_output_tokens'], 1)} | {r['extraction_sufficient']}/{r['n']} | "
                     f"{r['no_issue_without_needed_code']} | {r['decided_with_missing_context']} | "
                     f"{r['cases_consistent_across_repeats']} | {r['context_overflow']} |")
    lines += ["", "- `필요 코드 포함`: 정답표의 required_functions가 추출 결과에 모두 들어 있는 사례 수(LLM과 무관).",
              "- `필요 코드 없이 no_issue`: 필요한 코드가 입력에 없는데 no_issue_found로 답한 횟수(근거 없는 정상 판정).",
              "- `누락 정보를 적고도 확정 판정`: verdict가 vulnerable/no_issue_found인데 missing_context가 비어 있지 않은 횟수.",
              "- `반복 간 판정 일치`: 모든 반복에서 판정이 같은 사례 수. 모두 일치하면 반복은 시간 측정에만 의미가 있고, "
              "탐지 지표의 n은 사실상 사례 수(12)의 반복 배수다.",
              "- 추출 시간: A_full은 문법 확인용 파싱만, B~D는 파싱 + 호출 그래프 + BFS. 모두 ms 이하로, 추론 시간에 비해 무시할 수 있는 수준이다.", "",
              "## 사례별 판정", "(코드부족) = 해당 조건 입력에 판단에 필요한 함수가 빠짐", "",
              "| 사례 | 유형 | 정답 | " + " | ".join(CONDITIONS) + " |",
              "|---|---|---|" + "---|" * len(CONDITIONS)]
    for t in table:
        lines.append(f"| {t['case_id']} | {t['type']} | {t['expected']} | " + " | ".join(t[c] for c in CONDITIONS) + " |")
    lines += ["", "원본 프롬프트와 모델 응답: `raw/<case>_<condition>_r<repeat>.json`", ""]
    (run_dir / "summary.md").write_text("\n".join(lines))


def main():
    """runs/<run_id> 디렉터리를 받아 metrics.csv, metrics.json, per_case.csv, summary.md를 쓴다."""
    run_dir = Path(sys.argv[1]).resolve()
    labels = json.loads(LABELS_PATH.read_text())["cases"]
    meta = json.loads((run_dir / "run_meta.json").read_text())
    records = [json.loads(line) for line in (run_dir / "predictions.jsonl").read_text().splitlines() if line]
    labels = {k: v for k, v in labels.items() if k in set(meta["cases"])}
    rows = evaluate(records, labels)
    table = per_case_table(records, labels)

    with open(run_dir / "metrics.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({k: fmt(v, 6) if v is None or isinstance(v, float) else v for k, v in row.items()} for row in rows)
    with open(run_dir / "per_case.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    (run_dir / "metrics.json").write_text(json.dumps(
        {"run_id": meta["run_id"], "single_run": meta["single_run"], "positive_class": "vulnerable",
         "insufficient_handling": {"primary": "excluded from confusion matrix; decidable_ratio reported",
                                   "conservative": "insufficient_context counted as positive"},
         "na_rule": "null when denominator is 0", "conditions": rows, "per_case": table},
        ensure_ascii=False, indent=2))
    write_summary(run_dir, meta, rows, table, labels)
    print(f"wrote {run_dir}/summary.md")


if __name__ == "__main__":
    main()
