"""모든 조건(A~D)에서 똑같이 쓰는 판단 프롬프트와 출력 JSON 스키마.

조건마다 달라지는 것은 CODE 블록과 '보이지 않는 호출' 목록뿐이다.
"""

PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """You review Python code for object-level authorization (access control on a specific object).
You are given an access policy, the name of a target function, and some source code.
Decide whether the target function, as written, lets a requester obtain or disclose an object's data in a way the policy forbids.

Rules:
- Judge only from the code shown. Do not assume authorization logic that is not visible.
- An `if` statement, or a name containing words such as "owner", "check", "guard" or "auth", is not evidence by itself. Confirm what is actually compared, with which values, and what happens when the comparison fails.
- A call whose return value is ignored does not block anything unless the called code itself raises or stops execution.
- Data that is returned, yielded, written, appended or sent before a failing check has already been disclosed.
- If deciding requires code that is not shown (for example a called function whose body is missing), answer "insufficient_context" and name what is missing.
- If the policy allows the access, it is not a problem.

Verdict values:
- "vulnerable": the visible code lets a requester access or disclose data against the policy.
- "no_issue_found": the visible code enforces the policy for the target function.
- "insufficient_context": the decision depends on code that is not shown.

Reply with JSON only: {"verdict": ..., "evidence": ..., "missing_context": [...]}.
"evidence" quotes the relevant code lines and explains them briefly. "missing_context" lists the missing information (empty list if none)."""

# Ollama `format`에 넘기는 JSON 스키마. 모델 출력 형식을 고정한다.
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["vulnerable", "no_issue_found", "insufficient_context"]},
        "evidence": {"type": "string"},
        "missing_context": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["verdict", "evidence", "missing_context"],
}


def _not_shown_section(ctx):
    """추출기가 보여주지 못한 호출을 사실대로 나열한다. builtin 호출은 생략한다."""
    if ctx["condition"] == "A_full":
        return "The entire source file is shown."
    lines = []
    for name in ctx["excluded_by_depth"]:
        lines.append(f"- {name}(...): defined in this file but not shown (call depth limit)")
    for u in ctx["unresolved"]:
        if u["kind"] == "builtin":
            continue
        lines.append(f"- {u['call']}(...) called in {u['in']}: not resolved by the extractor ({u['kind']}), body not shown")
    header = "Only selected functions from the file are shown. Module-level variables and classes are not shown."
    if not lines:
        return header + "\nCalls not shown: none."
    return header + "\nCalls not shown:\n" + "\n".join(lines)


def build_user_prompt(policy, target, ctx):
    """정책 + 대상 함수 + 조건별 코드로 사용자 프롬프트를 만든다."""
    return (
        f"ACCESS POLICY:\n{policy}\n\n"
        f"TARGET FUNCTION: {target}\n\n"
        f"CODE:\n```python\n{ctx['code']}```\n\n"
        f"CONTEXT NOTE:\n{_not_shown_section(ctx)}\n\n"
        "Return the JSON object."
    )
