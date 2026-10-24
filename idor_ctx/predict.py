"""예측 단계: cases/의 코드·정책만 읽어 조건 A~D별로 로컬 LLM 판단을 실행하고 원문을 저장한다.

이 모듈은 정답 파일을 읽지 않는다 (평가는 evaluate.py에서 따로 한다).
사용: python3 -m idor_ctx.predict --model qwen2.5:7b [--repeats 1] [--cases case_01,case_02]
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from . import llm
from .extract import CONDITIONS, build_context
from .prompt import OUTPUT_SCHEMA, PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "cases"
RUNS_DIR = ROOT / "runs"
VERDICTS = {"vulnerable", "no_issue_found", "insufficient_context"}


def load_cases(selected=None):
    """cases/*/meta.json과 app.py를 읽는다. 정답 정보는 여기에 없다."""
    cases = []
    for d in sorted(CASES_DIR.iterdir()):
        if not (d / "meta.json").exists() or (selected and d.name not in selected):
            continue
        meta = json.loads((d / "meta.json").read_text())
        meta["source"] = (d / "app.py").read_text()
        cases.append(meta)
    return cases


def parse_response(text):
    """모델 응답 문자열을 JSON으로 해석한다. 실패하거나 verdict가 이상하면 parse_error로 표시한다."""
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return {"verdict": "parse_error", "evidence": None, "missing_context": None}
    if obj.get("verdict") not in VERDICTS:
        return {"verdict": "parse_error", "evidence": obj.get("evidence"), "missing_context": obj.get("missing_context")}
    return {"verdict": obj["verdict"], "evidence": obj.get("evidence"), "missing_context": obj.get("missing_context")}


def condition_order(index):
    """사례마다 조건 실행 순서를 회전시켜 순서 효과(캐시 등)를 한 조건에 몰리지 않게 한다."""
    names = list(CONDITIONS)
    k = index % len(names)
    return names[k:] + names[:k]


def measure_load_time(model):
    """모델을 내린 뒤 짧은 요청으로 다시 올려 로딩 시간을 따로 기록한다 (본 실험 지표와 분리)."""
    llm.unload(model)
    time.sleep(1)
    raw, wall = llm.generate(model, "Reply with JSON.", "Return {\"ok\": true}.", {"type": "object"})
    return {"load_duration_s": raw.get("load_duration", 0) / 1e9, "warmup_wall_s": wall}


def run(model, repeats, selected):
    """전체 실험 루프. runs/<run_id>/ 아래에 raw 응답, predictions.jsonl, run_meta.json을 남긴다."""
    cases = load_cases(selected)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "_" + model.replace(":", "-").replace("/", "-")
    out = RUNS_DIR / run_id
    (out / "raw").mkdir(parents=True)

    meta = {"run_id": run_id, "started_at": datetime.now().isoformat(timespec="seconds"),
            "model": llm.model_info(model), "machine": llm.machine_info(),
            "generation_options": llm.GEN_OPTIONS, "output_schema": OUTPUT_SCHEMA,
            "prompt_version": PROMPT_VERSION, "system_prompt": SYSTEM_PROMPT,
            "repeats": repeats, "single_run": repeats == 1, "cases": [c["case_id"] for c in cases]}
    meta["model_loading"] = measure_load_time(model)
    print(f"[run] {run_id}  load={meta['model_loading']['load_duration_s']:.2f}s")

    num_ctx = llm.GEN_OPTIONS["num_ctx"]
    num_predict = llm.GEN_OPTIONS["num_predict"]
    with open(out / "predictions.jsonl", "w") as pred_file:
        for rep in range(1, repeats + 1):
            for i, case in enumerate(cases):
                for cond in condition_order(i):
                    ctx = build_context(case["source"], case["target"], cond)
                    user_prompt = build_user_prompt(case["policy"], case["target"], ctx)
                    raw, wall = llm.generate(model, SYSTEM_PROMPT, user_prompt, OUTPUT_SCHEMA)
                    parsed = parse_response(raw.get("response", ""))
                    if raw.get("done_reason") == "length":
                        parsed["verdict"] = "parse_error"  # 출력 길이 한도에서 잘림
                    prompt_tokens = raw.get("prompt_eval_count")
                    record = {
                        "case_id": case["case_id"], "condition": cond, "repeat": rep,
                        "target": case["target"], **parsed,
                        "included_functions": ctx["included"],
                        "excluded_by_depth": ctx["excluded_by_depth"],
                        "unresolved_calls": ctx["unresolved"],
                        "extract_warnings": ctx["warnings"],
                        "code_chars": len(ctx["code"]),
                        "prompt_chars": len(SYSTEM_PROMPT) + len(user_prompt),
                        "prompt_tokens": prompt_tokens,
                        "output_tokens": raw.get("eval_count"),
                        "context_overflow": prompt_tokens is not None and prompt_tokens >= num_ctx - num_predict,
                        "extract_seconds": ctx["extract_seconds"],
                        "inference_wall_seconds": wall,
                        "ollama_total_seconds": raw.get("total_duration", 0) / 1e9,
                        "ollama_prompt_eval_seconds": raw.get("prompt_eval_duration", 0) / 1e9,
                        "ollama_eval_seconds": raw.get("eval_duration", 0) / 1e9,
                        "ollama_load_seconds": raw.get("load_duration", 0) / 1e9,
                        "done_reason": raw.get("done_reason"),
                    }
                    pred_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                    pred_file.flush()
                    raw_path = out / "raw" / f"{case['case_id']}_{cond}_r{rep}.json"
                    raw_path.write_text(json.dumps({"system": SYSTEM_PROMPT, "prompt": user_prompt,
                                                    "response_raw": raw, "record": record},
                                                   ensure_ascii=False, indent=2))
                    print(f"[{case['case_id']} {cond} r{rep}] {parsed['verdict']:<20} "
                          f"tok={prompt_tokens} infer={wall:.1f}s")

    meta["finished_at"] = datetime.now().isoformat(timespec="seconds")
    (out / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"[done] {out}")
    return out


def main():
    """명령행 인자를 읽어 실험을 실행한다."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--cases", default="", help="쉼표로 구분한 case_id (기본: 전체)")
    args = ap.parse_args()
    selected = set(args.cases.split(",")) if args.cases else None
    run(args.model, args.repeats, selected)


if __name__ == "__main__":
    main()
