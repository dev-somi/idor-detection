"""로컬 Ollama 서버 호출과 실행 환경 정보 수집. 표준 라이브러리(urllib)만 사용한다."""

import json
import platform
import subprocess
import time
import urllib.request

OLLAMA_URL = "http://localhost:11434"

# 모든 조건에 동일하게 적용하는 생성 설정
GEN_OPTIONS = {"temperature": 0, "seed": 42, "num_ctx": 16384, "num_predict": 768}


def _post(path, payload, timeout=600):
    """Ollama API에 JSON POST 요청을 보내고 응답 JSON을 돌려준다."""
    req = urllib.request.Request(OLLAMA_URL + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def generate(model, system, prompt, schema, options=GEN_OPTIONS):
    """한 번 생성한다. 원 응답 JSON과 측정한 벽시계 시간(초)을 돌려준다."""
    payload = {"model": model, "system": system, "prompt": prompt, "format": schema,
               "stream": False, "options": options, "keep_alive": "30m"}
    if model.startswith("qwen3"):
        payload["think"] = False  # thinking 모델은 사고 과정 출력을 끈다
    start = time.perf_counter()
    raw = _post("/api/generate", payload)
    return raw, time.perf_counter() - start


def unload(model):
    """모델을 메모리에서 내린다 (로딩 시간을 따로 측정하기 위해)."""
    _post("/api/generate", {"model": model, "keep_alive": 0})


def model_info(model):
    """/api/show에서 모델 상세(양자화, 파라미터 수, 문맥 길이 등)를 가져온다."""
    info = _post("/api/show", {"model": model})
    details = info.get("details", {})
    ctx_len = next((v for k, v in info.get("model_info", {}).items() if k.endswith("context_length")), None)
    tags = _post_get("/api/tags")
    digest = next((m["digest"] for m in tags.get("models", []) if m["name"] == model), None)
    return {"model": model, "digest": digest, "format": details.get("format"),
            "family": details.get("family"), "parameter_size": details.get("parameter_size"),
            "quantization_level": details.get("quantization_level"), "model_context_length": ctx_len}


def _post_get(path):
    """Ollama API GET 요청."""
    with urllib.request.urlopen(OLLAMA_URL + path, timeout=30) as resp:
        return json.loads(resp.read())


def _sh(cmd):
    """셸 명령 출력을 문자열로 돌려준다. 실패하면 None."""
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return None


def machine_info():
    """장비·OS·Python·Ollama 버전 정보를 모은다."""
    mem = _sh("sysctl -n hw.memsize")
    return {
        "os": platform.platform(),
        "cpu": _sh("sysctl -n machdep.cpu.brand_string"),
        "gpu": _sh("system_profiler SPDisplaysDataType | grep -E 'Chipset|Cores' | tr -s ' '"),
        "ram_gb": round(int(mem) / 1024**3, 1) if mem else None,
        "python": platform.python_version(),
        "ollama_server_version": _post_get("/api/version").get("version"),
    }
