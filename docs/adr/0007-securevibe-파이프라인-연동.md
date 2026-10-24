# 0007. SecureVibe 파이프라인 연동용 코드 심사 CLI 추가

- 날짜: 2026-10-24
- 상태: 채택

## 맥락
SecureVibe(`../idor-explainable-web`)는 OpenAPI 명세와 HTTP 응답만 보는 블랙박스 도구다. 명세에는 소유권 검사 코드가 드러나지 않아서 정적 후보가 부풀려지고 설명 근거가 약하다. 이 저장소의 문맥 축소 + LLM 판단을 SecureVibe의 정적 후보에 적용하려면 두 가지가 필요했다.
- 엔드포인트 → 핸들러 연결. 지금까지는 `bench/*/endpoints.json`에 사람이 적었다.
- 벤치가 아닌 외부 소스를 읽는 입구.

## 결정
- **`idor_ctx/route_map.py`** (신규): OpenAPI 작업을 핸들러에 자동 연결한다. 우선순위는 다음과 같다.
  1. operationId = '모듈.함수' (connexion)
  2. 라우트 데코레이터 경로. `APIRouter(prefix)`, `Blueprint(url_prefix)`, `include_router(prefix)`는 문자열 상수일 때만 반영한다.
  3. FastAPI 기본 operationId의 함수명 접두어
  4. 연결 실패(unmapped). 경로가 둘 이상에 맞으면 ambiguous로 둔다.
- **`idor_ctx/review.py`** (신규 CLI): 소스 폴더 + 후보 JSON → 후보별 판정 JSON.
  - (method, 경로) 중복 제거 후 정적 심각도순으로 처리한다.
  - `build_endpoint_context` / `build_endpoint_prompt`(ep-v1) / `parse_response` / `GEN_OPTIONS`를 그대로 쓴다.
  - 정책은 기본 문장 하나(`DEFAULT_POLICY`)이고, `--policy`로 엔드포인트별 덮어쓰기를 받는다.
  - `--dry-run`은 LLM 없이 연결·문맥만 낸다. 모의 판정은 만들지 않고 verdict를 `not-run`으로 둔다.
  - HTTP 결과는 입력으로 받지 않는다. 두 검사의 독립성을 지키려는 것으로, 취합은 SecureVibe가 한다.
- **`ep_extract.py` 소폭 변경**
  - `input_files(bench_dir, globs=None)`, `Codebase(bench_dir, globs=None)`. globs를 주면 외부 소스 모드로 동작하고 `tests/`, `.venv/`, `migrations/` 등은 뺀다.
  - 문법 오류 파일은 경고를 남기고 건너뛴다.
  - 파싱한 트리를 `Codebase.trees`로 보관한다(데코레이터 읽기용).
- 실험 모듈(predict/ep_predict/evaluate)과 프롬프트 v1·ep-v1은 바꾸지 않았다.

## 결과(영향)
- globs를 생략하면 기존 동작과 같다. 기존 테스트가 모두 통과했다.
- 자동 연결 결과가 사람이 적은 연결과 모두 일치했다(`tests/test_route_map.py`). campus 25/25는 decorator 규칙, vampi_vuln·vampi_secure 7/7은 operationId 규칙으로 연결됐다.
- 한계
  - 변수나 함수로 만든 경로·접두어는 따라가지 않는다.
  - `register_blueprint(url_prefix=...)`는 반영하지 않는다.
  - 클래스 기반 뷰는 지원하지 않는다.
  - 기본 정책 문장은 엔드포인트별 정책보다 정보가 적어서, 판정 품질이 벤치 실험과 다를 수 있다.
