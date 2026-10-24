"""엔드포인트 실험 예측 단계: bench/<이름>/의 코드·엔드포인트·정책만 읽어 조건 A~D별로 로컬 LLM 판단을 실행한다.

이 모듈은 정답 파일을 읽지 않는다 (평가는 evaluate.py --labels로 따로 한다).
사용: python3 -m idor_ctx.ep_predict --bench campus,vampi_vuln,vampi_secure --model qwen2.5:7b [--repeats 1] [--items campus:e01,...]
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from . import llm
from .ep_extract import EP_CONDITIONS, Codebase, build_endpoint_context, input_files
from .predict import RUNS_DIR, condition_order, measure_load_time, parse_response
from .prompt import EP_PROMPT_VERSION, OUTPUT_SCHEMA, SYSTEM_PROMPT, build_endpoint_prompt

ROOT = Path(__file__).resolve().parent.parent
BENCH_DIR = ROOT / "bench"


def load_items(benches, selected=None):
    """벤치별 Codebase와 엔드포인트 목록을 읽는다. 정답 정보는 여기에 없다."""
    items, codebases, index_seconds = [], {}, {}
    for name in benches:
        start = time.perf_counter()
        codebases[name] = Codebase(BENCH_DIR / name)
        index_seconds[name] = time.perf_counter() - start
        for e in json.loads((BENCH_DIR / name / "endpoints.json").read_text()):
            if not selected or e["item_id"] in selected:
                items.append({**e, "bench": name})
    return items, codebases, index_seconds


def run(model, repeats, benches, selected):
    """전체 실험 루프. runs/<run_id>/ 아래에 raw 응답, predictions.jsonl, run_meta.json을 남긴다."""
    items, codebases, index_seconds = load_items(benches, selected)
    run_id = "ep_" + datetime.now().strftime("%Y%m%d-%H%M%S") + "_" + model.replace(":", "-").replace("/", "-")
    out = RUNS_DIR / run_id
    (out / "raw").mkdir(parents=True)

    meta = {"run_id": run_id, "experiment": "endpoint", "started_at": datetime.now().isoformat(timespec="seconds"),
            "model": llm.model_info(model), "machine": llm.machine_info(),
            "generation_options": llm.GEN_OPTIONS, "output_schema": OUTPUT_SCHEMA,
            "prompt_version": EP_PROMPT_VERSION, "system_prompt": SYSTEM_PROMPT,
            "conditions": list(EP_CONDITIONS), "benches": benches,
            "input_files": {b: input_files(BENCH_DIR / b) for b in benches},
            "codebase_index_seconds": index_seconds,
            "repeats": repeats, "single_run": repeats == 1, "cases": [i["item_id"] for i in items]}
    meta["model_loading"] = measure_load_time(model)
    print(f"[run] {run_id}  load={meta['model_loading']['load_duration_s']:.2f}s  items={len(items)}")

    num_ctx = llm.GEN_OPTIONS["num_ctx"]
    num_predict = llm.GEN_OPTIONS["num_predict"]
    with open(out / "predictions.jsonl", "w") as pred_file:
        for rep in range(1, repeats + 1):
            for i, item in enumerate(items):
                for cond in condition_order(i, EP_CONDITIONS):
                    ctx = build_endpoint_context(codebases[item["bench"]], item, cond)
                    user_prompt = build_endpoint_prompt(item["policy"], item, ctx)
                    raw, wall = llm.generate(model, SYSTEM_PROMPT, user_prompt, OUTPUT_SCHEMA)
                    parsed = parse_response(raw.get("response", ""))
                    if raw.get("done_reason") == "length":
                        parsed["verdict"] = "parse_error"  # 출력 길이 한도에서 잘림
                    prompt_tokens = raw.get("prompt_eval_count")
                    record = {
                        "case_id": item["item_id"], "bench": item["bench"], "condition": cond, "repeat": rep,
                        "endpoint": f"{item['method']} {item['path']}", "target": ctx["target"], **parsed,
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
                    raw_name = item["item_id"].replace(":", "_")
                    (out / "raw" / f"{raw_name}_{cond}_r{rep}.json").write_text(
                        json.dumps({"system": SYSTEM_PROMPT, "prompt": user_prompt,
                                    "response_raw": raw, "record": record}, ensure_ascii=False, indent=2))
                    print(f"[{item['item_id']} {cond} r{rep}] {parsed['verdict']:<20} "
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
    ap.add_argument("--bench", default="campus,vampi_vuln,vampi_secure")
    ap.add_argument("--items", default="", help="쉼표로 구분한 item_id (기본: 전체)")
    args = ap.parse_args()
    selected = set(args.items.split(",")) if args.items else None
    run(args.model, args.repeats, args.bench.split(","), selected)


if __name__ == "__main__":
    main()
