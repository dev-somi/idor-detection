"""SecureVibe 파이프라인용 코드 심사 CLI (ADR 0007). 외부 소스 + 후보 목록 → 후보별 LLM 판정 JSON.

SecureVibe가 subprocess로 부른다. HTTP 결과는 받지 않는다 (두 검사를 독립으로 두기 위해).
실험 모듈(predict/ep_predict)의 추출·프롬프트·파싱 함수를 그대로 재사용하고, 그 모듈들은 바꾸지 않는다.
사용:
  python3 -m idor_ctx.review --source DIR --candidates cand.json --out review.json \
      [--model qwen2.5:7b] [--condition D_depth2] [--policy policy.json] [--dry-run]
cand.json: [{"method": "GET", "path": "/orders/{id}", "operationId": "...", "severity": "High"}, ...]
"""

import argparse
import json
import time
from pathlib import Path

from . import llm
from .ep_extract import EP_CONDITIONS, Codebase, build_endpoint_context
from .predict import parse_response
from .prompt import EP_PROMPT_VERSION, OUTPUT_SCHEMA, SYSTEM_PROMPT, build_endpoint_prompt
from .route_map import map_routes, normalize_path

# 엔드포인트별 정책이 없을 때 쓰는 기본 정책 (영어: 실험 프롬프트와 같은 언어)
DEFAULT_POLICY = ("An object identified by a request parameter (path, query, header or body) may be read or "
                  "modified only by its owner, unless the API explicitly makes it public.")
SEVERITY_ORDER = {"High": 0, "Medium": 1}


def unique_candidates(candidates):
    """(method, 정규화 경로) 기준으로 중복을 없애고 정적 심각도 순으로 정렬한다. 같은 키면 더 높은 심각도를 남긴다."""
    best = {}
    for c in candidates:
        key = (str(c.get("method", "")).upper(), normalize_path(c.get("path")))
        rank = SEVERITY_ORDER.get(c.get("severity"), 2)
        if key not in best or rank < best[key][0]:
            best[key] = (rank, c)
    return [c for _, c in sorted(best.values(), key=lambda x: x[0])]


def review_one(codebase, cand, condition, model, policies, dry_run):
    """후보 하나를 핸들러에 연결하고 조건별 문맥을 만들어 LLM 판정을 받는다. 연결 실패면 LLM을 부르지 않는다."""
    key = f"{cand['method']} {cand['path']}"
    base = {"method": cand["method"], "path": cand["path"], "operationId": cand.get("operationId"),
            "handler": cand.get("qual"), "mapping_how": cand["how"]}
    if not cand.get("qual"):
        return {**base, "verdict": "unmapped", "evidence": None, "missing_context": None,
                "mapping_candidates": cand.get("candidates")}
    ctx = build_endpoint_context(codebase, cand, condition)
    prompt = build_endpoint_prompt(policies.get(key, DEFAULT_POLICY), cand, ctx)
    info = {**base, "policy_source": "override" if key in policies else "default",
            "included_functions": ctx["included"], "excluded_by_depth": ctx["excluded_by_depth"],
            "unresolved_calls": ctx["unresolved"], "code_chars": len(ctx["code"]),
            "extract_seconds": ctx["extract_seconds"]}
    if dry_run:
        return {**info, "verdict": "not-run", "evidence": None, "missing_context": None, "prompt": prompt}
    raw, wall = llm.generate(model, SYSTEM_PROMPT, prompt, OUTPUT_SCHEMA)
    parsed = parse_response(raw.get("response", ""))
    if raw.get("done_reason") == "length":
        parsed["verdict"] = "parse_error"  # 출력 길이 한도에서 잘림
    tokens = raw.get("prompt_eval_count")
    limit = llm.GEN_OPTIONS["num_ctx"] - llm.GEN_OPTIONS["num_predict"]
    return {**info, **parsed, "prompt_tokens": tokens, "output_tokens": raw.get("eval_count"),
            "context_overflow": tokens is not None and tokens >= limit, "inference_wall_seconds": wall}


def run(source, candidates, condition, model, policies, dry_run):
    """후보 전체를 심사해 결과 dict를 돌려준다 (합계 토큰·시간 포함)."""
    start = time.perf_counter()
    codebase = Codebase(source, globs=["**/*.py"])
    mapped = map_routes(codebase, unique_candidates(candidates))
    reviews = [review_one(codebase, c, condition, model, policies, dry_run) for c in mapped]
    tokens = [r["prompt_tokens"] for r in reviews if r.get("prompt_tokens") is not None]
    return {"status": "dry-run" if dry_run else "ok", "model": None if dry_run else model,
            "condition": condition, "prompt_version": EP_PROMPT_VERSION,
            "generation_options": llm.GEN_OPTIONS, "candidates_in": len(candidates),
            "candidates_reviewed": len(reviews), "source_files": len(codebase.files),
            "extract_warnings": codebase.warnings,
            "unmapped": [f"{r['method']} {r['path']}" for r in reviews if r["verdict"] == "unmapped"],
            "total_prompt_tokens": sum(tokens),
            "total_inference_seconds": sum(r.get("inference_wall_seconds", 0) for r in reviews),
            "wall_seconds": time.perf_counter() - start, "reviews": reviews}


def main():
    """명령행 인자를 읽어 심사를 실행하고 결과를 --out 파일에 쓴다."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="심사할 소스 코드 폴더")
    ap.add_argument("--candidates", required=True, help="후보 목록 JSON 파일")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--condition", default="D_depth2", choices=list(EP_CONDITIONS))
    ap.add_argument("--policy", default="", help='엔드포인트별 정책 JSON: {"GET /path": "..."}')
    ap.add_argument("--dry-run", action="store_true", help="LLM 없이 연결과 추출 문맥만 낸다")
    args = ap.parse_args()
    candidates = json.loads(Path(args.candidates).read_text())
    policies = json.loads(Path(args.policy).read_text()) if args.policy else {}
    result = run(args.source, candidates, args.condition, args.model, policies, args.dry_run)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[review] {result['candidates_reviewed']} reviewed, {len(result['unmapped'])} unmapped, "
          f"tokens={result['total_prompt_tokens']} -> {args.out}")


if __name__ == "__main__":
    main()
