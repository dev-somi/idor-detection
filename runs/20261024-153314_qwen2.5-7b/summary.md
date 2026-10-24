# 실험 요약: 20261024-153314_qwen2.5-7b

> 자동 생성 파일(idor_ctx/evaluate.py). 자체 제작 예제 12개에서 얻은 결과이며, 실제 프로젝트 전반으로 일반화할 수 없다.
> 반복 횟수: 3

## 실행 설정
- 모델: `qwen2.5:7b` (family qwen2, 7.6B, 양자화 Q4_K_M, format gguf, digest 845dbda0ea48), 모델 최대 문맥 32768
- 생성 설정: `{"temperature": 0, "seed": 42, "num_ctx": 16384, "num_predict": 768}`, 출력은 JSON 스키마로 고정, 프롬프트 v1
- 장비: Apple M5, RAM 16.0GB, macOS-26.5.1-arm64-arm-64bit, Python 3.11.15, Ollama 서버 0.40.9
- 모델 로딩 시간(본 지표와 별도): 0.82s (워밍업 요청 벽시계 1.16s)
- 실행 시각: 2026-10-24T15:33:14 ~ 2026-10-24T15:39:29

## 판단 불가 처리 방식
- **주 지표**: `insufficient_context`와 `parse_error`는 TP/FP/FN/TN에서 제외하고, 판단 가능 비율(decided/n)을 따로 적었다.
- **보수적 지표(cons_)**: `insufficient_context`를 양성(사람 검토 필요)으로 셌다. `parse_error`는 제외했다.
- 양성 = vulnerable. 분모가 0이면 N/A로 표시했다.

## 조건별 탐지 지표
| 조건 | n | TP | FP | FN | TN | precision | recall | 판단 불가 | parse_error | 판단 가능 비율 | cons precision | cons recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 36 | 9 | 0 | 6 | 21 | 1.000 | 0.600 | 0 | 0 | 1.000 | 1.000 | 0.600 |
| B_depth0 | 36 | 9 | 3 | 3 | 9 | 0.750 | 0.750 | 12 | 0 | 0.667 | 0.500 | 0.800 |
| C_depth1 | 36 | 6 | 6 | 9 | 15 | 0.500 | 0.400 | 0 | 0 | 1.000 | 0.500 | 0.400 |
| D_depth2 | 36 | 6 | 3 | 9 | 18 | 0.667 | 0.400 | 0 | 0 | 1.000 | 0.667 | 0.400 |

## 조건별 비용과 추출 커버리지
토큰 수는 Ollama가 보고한 `prompt_eval_count`(시스템 프롬프트와 채팅 템플릿 포함, 실제 토크나이저 기준)이다. 문자 수는 참고용 대체 지표다.

| 조건 | 평균 입력 토큰 | 평균 코드 문자 수 | 평균 추출 시간(ms) | 평균 추론 시간(s) | 총 추론 시간(s) | 평균 출력 토큰 | 필요 코드 포함 | 필요 코드 없이 no_issue | 누락 정보를 적고도 확정 판정 | 반복 간 판정 일치 | 문맥 초과 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 707.3 | 1153.3 | 0.537 | 2.91 | 104.9 | 59.3 | 36/36 | 0 | 0 | 12/12 | 0 |
| B_depth0 | 501.4 | 177.8 | 2.828 | 2.38 | 85.8 | 55.4 | 3/36 | 9 | 15 | 12/12 | 0 |
| C_depth1 | 559.3 | 426 | 2.695 | 2.67 | 96.0 | 58.7 | 24/36 | 6 | 12 | 12/12 | 0 |
| D_depth2 | 568.6 | 475.9 | 2.938 | 2.36 | 85.0 | 57.2 | 30/36 | 3 | 9 | 12/12 | 0 |

- `필요 코드 포함`: 정답표의 required_functions가 추출 결과에 모두 들어 있는 사례 수(LLM과 무관).
- `필요 코드 없이 no_issue`: 필요한 코드가 입력에 없는데 no_issue_found로 답한 횟수(근거 없는 정상 판정).
- `누락 정보를 적고도 확정 판정`: verdict가 vulnerable/no_issue_found인데 missing_context가 비어 있지 않은 횟수.
- `반복 간 판정 일치`: 모든 반복에서 판정이 같은 사례 수. 모두 일치하면 반복은 시간 측정에만 의미가 있고, 탐지 지표의 n은 사실상 사례 수(12)의 반복 배수다.
- 추출 시간: A_full은 문법 확인용 파싱만, B~D는 파싱 + 호출 그래프 + BFS. 모두 ms 이하로, 추론 시간에 비해 무시할 수 있는 수준이다.

## 사례별 판정
(코드부족) = 해당 조건 입력에 판단에 필요한 함수가 빠짐

| 사례 | 유형 | 정답 | A_full | B_depth0 | C_depth1 | D_depth2 |
|---|---|---|---|---|---|---|
| case_01 | 소유자 전용, 인가 검사 없음 | vulnerable | vulnerable/vulnerable/vulnerable | insufficient_context/insufficient_context/insufficient_context (코드부족) | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| case_02 | 함수 안에서 올바른 소유권 검사 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| case_03 | 보조 함수(1단계) 안에서 검사 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | insufficient_context/insufficient_context/insufficient_context (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| case_04 | 두 단계 보조 함수 안에서 검사 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | insufficient_context/insufficient_context/insufficient_context (코드부족) | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found |
| case_05 | 공개 조회 허용, 소유권 검사 불필요 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| case_06 | 검사 함수를 호출하지만 반환값을 무시 | vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| case_07 | 정보를 내보낸 뒤에 검사 | vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| case_08 | if문과 owner 이름은 있지만 요청자와 비교하지 않음 | vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| case_09 | 보조 함수가 정책과 다른 조건(조직)을 검사 | vulnerable | no_issue_found/no_issue_found/no_issue_found | vulnerable/vulnerable/vulnerable (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| case_10 | 재귀(순환) 호출을 포함한 2단계 검사 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | insufficient_context/insufficient_context/insufficient_context (코드부족) | vulnerable/vulnerable/vulnerable (코드부족) | no_issue_found/no_issue_found/no_issue_found |
| case_11 | 검사가 클래스 메서드에 있음(추출기 미지원 범위) | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found (코드부족) |
| case_12 | 3단계 깊이의 검사(depth 2 밖) | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable (코드부족) |

원본 프롬프트와 모델 응답: `raw/<case>_<condition>_r<repeat>.json`
