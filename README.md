# 호출 관계 기반 코드 문맥 축소가 로컬 LLM IDOR 판단에 미치는 영향 (최소 프로토타입)

같은 로컬 LLM에 (A) 전체 파일, (B) 대상 함수만, (C) 직접 호출 함수까지, (D) 두 단계 호출 함수까지를 넣고
IDOR(객체 수준 인가) 판단 결과, 입력 토큰 수, 실행 시간을 비교한다.
성능 개선은 아직 검증되지 않은 가설이다. 결과는 `runs/` 아래의 실측 파일만 근거로 삼는다.

> 예제 12개는 직접 만든 작은 코드다. 실제 프로젝트에서 같은 결과가 나온다는 증거가 아니다.

## 요구 환경
- Python 3.11 이상 (표준 라이브러리만 사용, 별도 패키지 설치 없음)
- 로컬 [Ollama](https://ollama.com) 서버 (`http://localhost:11434`)와 모델 (기본값 `qwen2.5:7b`)
- 측정 장비: Apple M5 / RAM 16GB / macOS 26.5.1 / Ollama 0.40.9

## 구조
```
cases/case_XX/app.py      예제 코드 (모델 입력, 주석 없음)
cases/case_XX/meta.json   case_id, 분석 대상 함수, 접근 정책 (모델 입력)
ground_truth/labels.json  정답, 이유, 판단에 필요한 함수, 실행 확인용 probe (예측 단계에서 읽지 않음)
idor_ctx/extract.py       ast 기반 함수·호출 추출, depth별 원문 추출
idor_ctx/prompt.py        고정 판단 프롬프트와 출력 JSON 스키마
idor_ctx/llm.py           Ollama 호출, 모델·장비 정보 수집
idor_ctx/predict.py       예측 실행 → runs/<run_id>/
idor_ctx/evaluate.py      지표 계산 → metrics.csv/json, per_case.csv, summary.md
idor_ctx/report_extraction.py  LLM 없이 추출 결과만 정리 → runs/extraction/
tests/                    추출기·정답 실행·누출 방지·지표 테스트
docs/adr/                 설계 변경 기록
```

## 실행 명령
```bash
# 1) 테스트 (추출기, 정답 실행 확인, 정답 누출 방지, 지표 계산)
python3 -m unittest discover -s tests -t . -v

# 2) LLM 없이 조건별 추출 결과 보기
python3 -m idor_ctx.report_extraction        # → runs/extraction/extraction.md, prompts/*.txt

# 3) 예측 (정답 파일을 읽지 않음)
python3 -m idor_ctx.predict --model qwen2.5:7b --repeats 3
#   일부 사례만: --cases case_01,case_06

# 4) 평가
python3 -m idor_ctx.evaluate runs/<run_id>   # → summary.md, metrics.csv, metrics.json, per_case.csv
```

## 방법 요약
- **추출**: 모듈 최상위 `def`와 `이름(...)` 형태의 직접 호출로 호출 그래프를 만들고, 대상 함수에서 BFS로 depth만큼 따라간다. visited 집합으로 순환과 중복을 처리하고, `ast.get_source_segment`로 함수 원문만 꺼낸다. AST 덤프는 넣지 않는다.
- **미해석 호출 표시**: 속성·메서드 호출, import, 클래스 생성, 지역 변수로 받은 함수, `getattr` 같은 동적 호출은 따라가지 않는다. 대신 프롬프트의 "Calls not shown" 목록에 종류와 함께 적는다. depth 한도 때문에 빠진 파일 내 함수도 같은 목록에 적는다.
- **판단**: 정책 + 대상 함수명 + 조건별 코드 → `{"verdict": vulnerable|no_issue_found|insufficient_context, "evidence", "missing_context"}`. 시스템 프롬프트, 출력 스키마, 생성 설정(temperature 0, seed 42, num_ctx 16384, num_predict 768)은 모든 조건에서 같다.
- **평가**: 양성은 vulnerable이다. 주 지표에서는 insufficient_context를 혼동행렬에서 제외하고 판단 가능 비율을 따로 보고한다. 보수적 지표에서는 insufficient_context를 양성으로 센다. 분모가 0이면 N/A로 표시한다.
- **토큰**: Ollama `prompt_eval_count`(실제 토크나이저 기준, 시스템 프롬프트와 템플릿 포함). 문자 수는 대체 지표로 따로 둔다.

## 측정 결과 위치
- `runs/extraction/`: LLM 없이 만든 조건별 추출 결과와 실제 입력 프롬프트
- `runs/20261024-153314_qwen2.5-7b/`: 주 실험(qwen2.5:7b, 12사례 × 4조건 × 3회)
- `runs/20261024-154012_qwen3-8b/`: 보조 실험(qwen3:8b, 같은 설정)
- `runs/smoke_*`: 2사례 스모크 실행 (흐름 확인용, 분석에는 쓰지 않음)
- 회의용 정리: `회의자료.md`

## 한계 (구현 범위 밖)
- import 추적, 메서드·클래스 타입 추론, 동적 호출, 데코레이터, 중첩 함수 분리, 전역 변수와 클래스 정의 추출은 지원하지 않는다. B~D 조건에는 전역 데이터가 들어가지 않는다.
- 파일 하나만 다룬다. 웹 프레임워크 라우팅이나 세션 처리는 다루지 않는다.
- 예제가 작아서 전체 파일도 약 1,100자 수준이다. 큰 파일에서 생기는 문맥 한도 문제는 이번 데이터로 확인할 수 없다.
- Ollama 프롬프트 캐시 때문에 추론 시간 측정에 순서 효과가 있을 수 있다. 사례마다 조건 순서를 회전해 완화했다(ADR 0003).
