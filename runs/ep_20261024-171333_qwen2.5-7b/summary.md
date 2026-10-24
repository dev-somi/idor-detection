# 실험 요약: ep_20261024-171333_qwen2.5-7b

> 자동 생성 파일(idor_ctx/evaluate.py). 자체 구성 벤치마크의 엔드포인트 항목 39개에서 얻은 결과이며, 실제 프로젝트 전반으로 일반화할 수 없다.
> 반복 횟수: 3

## 실행 설정
- 모델: `qwen2.5:7b` (family qwen2, 7.6B, 양자화 Q4_K_M, format gguf, digest 845dbda0ea48), 모델 최대 문맥 32768
- 생성 설정: `{"temperature": 0, "seed": 42, "num_ctx": 16384, "num_predict": 768}`, 출력은 JSON 스키마로 고정, 프롬프트 ep-v1
- 장비: Apple M5, RAM 16.0GB, macOS-26.5.1-arm64-arm-64bit, Python 3.11.15, Ollama 서버 0.40.9
- 모델 로딩 시간(본 지표와 별도): 1.81s (워밍업 요청 벽시계 2.16s)
- 실행 시각: 2026-10-24T17:13:33 ~ 2026-10-24T17:59:13

## 판단 불가 처리 방식
- **주 지표**: `insufficient_context`와 `parse_error`는 TP/FP/FN/TN에서 제외하고, 판단 가능 비율(decided/n)을 따로 적었다.
- **보수적 지표(cons_)**: `insufficient_context`를 양성(사람 검토 필요)으로 셌다. `parse_error`는 제외했다.
- 양성 = vulnerable. 분모가 0이면 N/A로 표시했다.

## 조건별 탐지 지표 — campus 전체
| 조건 | n | TP | FP | FN | TN | precision | recall | 판단 불가 | parse_error | 판단 가능 비율 | cons precision | cons recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 75 | 9 | 3 | 21 | 42 | 0.750 | 0.300 | 0 | 0 | 1.000 | 0.750 | 0.300 |
| B_handler | 75 | 15 | 6 | 3 | 33 | 0.714 | 0.833 | 18 | 0 | 0.760 | 0.692 | 0.900 |
| C_depth1 | 75 | 9 | 6 | 6 | 36 | 0.600 | 0.600 | 18 | 0 | 0.760 | 0.727 | 0.800 |
| D_depth2 | 75 | 6 | 6 | 6 | 39 | 0.500 | 0.500 | 18 | 0 | 0.760 | 0.800 | 0.800 |

## 조건별 탐지 지표 — campus 원본 엔드포인트(e01~e17)
| 조건 | n | TP | FP | FN | TN | precision | recall | 판단 불가 | parse_error | 판단 가능 비율 | cons precision | cons recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 51 | 6 | 0 | 12 | 33 | 1.000 | 0.333 | 0 | 0 | 1.000 | 1.000 | 0.333 |
| B_handler | 51 | 12 | 6 | 0 | 27 | 0.667 | 1.000 | 6 | 0 | 0.882 | 0.750 | 1.000 |
| C_depth1 | 51 | 3 | 6 | 3 | 27 | 0.333 | 0.500 | 12 | 0 | 0.765 | 0.714 | 0.833 |
| D_depth2 | 51 | 3 | 6 | 3 | 27 | 0.333 | 0.500 | 12 | 0 | 0.765 | 0.714 | 0.833 |

## 조건별 탐지 지표 — campus 추가 위임형 엔드포인트(e18~e25)
| 조건 | n | TP | FP | FN | TN | precision | recall | 판단 불가 | parse_error | 판단 가능 비율 | cons precision | cons recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 24 | 3 | 3 | 9 | 9 | 0.500 | 0.250 | 0 | 0 | 1.000 | 0.500 | 0.250 |
| B_handler | 24 | 3 | 0 | 3 | 6 | 1.000 | 0.500 | 12 | 0 | 0.500 | 0.600 | 0.750 |
| C_depth1 | 24 | 6 | 0 | 3 | 9 | 1.000 | 0.667 | 6 | 0 | 0.750 | 0.750 | 0.750 |
| D_depth2 | 24 | 3 | 0 | 3 | 12 | 1.000 | 0.500 | 6 | 0 | 0.750 | 1.000 | 0.750 |

## 조건별 탐지 지표 — vampi 주 지표(boundary 제외)
| 조건 | n | TP | FP | FN | TN | precision | recall | 판단 불가 | parse_error | 판단 가능 비율 | cons precision | cons recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 30 | 6 | 9 | 0 | 15 | 0.400 | 1.000 | 0 | 0 | 1.000 | 0.400 | 1.000 |
| B_handler | 30 | 6 | 18 | 0 | 6 | 0.250 | 1.000 | 0 | 0 | 1.000 | 0.250 | 1.000 |
| C_depth1 | 30 | 6 | 12 | 0 | 12 | 0.333 | 1.000 | 0 | 0 | 1.000 | 0.333 | 1.000 |
| D_depth2 | 30 | 6 | 12 | 0 | 12 | 0.333 | 1.000 | 0 | 0 | 1.000 | 0.333 | 1.000 |

## 조건별 탐지 지표 — vampi boundary 포함(민감도 분석)
| 조건 | n | TP | FP | FN | TN | precision | recall | 판단 불가 | parse_error | 판단 가능 비율 | cons precision | cons recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 42 | 12 | 15 | 0 | 15 | 0.444 | 1.000 | 0 | 0 | 1.000 | 0.444 | 1.000 |
| B_handler | 42 | 12 | 18 | 0 | 6 | 0.400 | 1.000 | 6 | 0 | 0.857 | 0.333 | 1.000 |
| C_depth1 | 42 | 12 | 12 | 0 | 18 | 0.500 | 1.000 | 0 | 0 | 1.000 | 0.500 | 1.000 |
| D_depth2 | 42 | 12 | 12 | 0 | 18 | 0.500 | 1.000 | 0 | 0 | 1.000 | 0.500 | 1.000 |

## 조건별 비용과 추출 커버리지
토큰 수는 Ollama가 보고한 `prompt_eval_count`(시스템 프롬프트와 채팅 템플릿 포함, 실제 토크나이저 기준)이다. 문자 수는 참고용 대체 지표다.

### campus 전체
| 조건 | 평균 입력 토큰 | 평균 코드 문자 수 | 평균 추출 시간(ms) | 평균 추론 시간(s) | 총 추론 시간(s) | 평균 출력 토큰 | 필요 코드 포함 | 필요 코드 없이 no_issue | 누락 정보를 적고도 확정 판정 | 반복 간 판정 일치 | 문맥 초과 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 6746.6 | 26111 | 0.205 | 16.08 | 1205.9 | 68.2 | 75/75 | 0 | 0 | 25/25 | 0 |
| B_handler | 656.4 | 350.0 | 0.118 | 3.11 | 233.1 | 58.8 | 27/75 | 30 | 30 | 25/25 | 0 |
| C_depth1 | 876.1 | 876.1 | 0.190 | 3.21 | 240.6 | 60.0 | 63/75 | 6 | 15 | 25/25 | 0 |
| D_depth2 | 900.8 | 943.2 | 0.141 | 2.81 | 211.0 | 62.4 | 75/75 | 0 | 12 | 25/25 | 0 |

### campus 원본 엔드포인트(e01~e17)
| 조건 | 평균 입력 토큰 | 평균 코드 문자 수 | 평균 추출 시간(ms) | 평균 추론 시간(s) | 총 추론 시간(s) | 평균 출력 토큰 | 필요 코드 포함 | 필요 코드 없이 no_issue | 누락 정보를 적고도 확정 판정 | 반복 간 판정 일치 | 문맥 초과 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 6746.6 | 26111 | 0.224 | 16.13 | 822.5 | 69.2 | 51/51 | 0 | 0 | 17/17 | 0 |
| B_handler | 682.2 | 374.4 | 0.140 | 3.10 | 158.3 | 59 | 27/51 | 21 | 21 | 17/17 | 0 |
| C_depth1 | 866.7 | 812.6 | 0.119 | 3.18 | 162.2 | 59.9 | 48/51 | 3 | 9 | 17/17 | 0 |
| D_depth2 | 877.4 | 837.8 | 0.144 | 2.65 | 135.3 | 60.6 | 51/51 | 0 | 9 | 17/17 | 0 |

### campus 추가 위임형 엔드포인트(e18~e25)
| 조건 | 평균 입력 토큰 | 평균 코드 문자 수 | 평균 추출 시간(ms) | 평균 추론 시간(s) | 총 추론 시간(s) | 평균 출력 토큰 | 필요 코드 포함 | 필요 코드 없이 no_issue | 누락 정보를 적고도 확정 판정 | 반복 간 판정 일치 | 문맥 초과 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 6746.6 | 26111 | 0.166 | 15.97 | 383.4 | 66.1 | 24/24 | 0 | 0 | 8/8 | 0 |
| B_handler | 601.6 | 298 | 0.072 | 3.12 | 74.8 | 58.2 | 0/24 | 9 | 9 | 8/8 | 0 |
| C_depth1 | 896 | 1011 | 0.340 | 3.27 | 78.4 | 60.4 | 15/24 | 3 | 6 | 8/8 | 0 |
| D_depth2 | 950.4 | 1167.4 | 0.134 | 3.15 | 75.7 | 66 | 24/24 | 0 | 3 | 8/8 | 0 |

### vampi 주 지표(boundary 제외)
| 조건 | 평균 입력 토큰 | 평균 코드 문자 수 | 평균 추출 시간(ms) | 평균 추론 시간(s) | 총 추론 시간(s) | 평균 출력 토큰 | 필요 코드 포함 | 필요 코드 없이 no_issue | 누락 정보를 적고도 확정 판정 | 반복 간 판정 일치 | 문맥 초과 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 3794.1 | 15158.5 | 0.146 | 9.84 | 295.3 | 72.6 | 30/30 | 0 | 0 | 10/10 | 0 |
| B_handler | 917.9 | 911 | 0.178 | 4.02 | 120.6 | 71.8 | 6/30 | 6 | 24 | 10/10 | 0 |
| C_depth1 | 1060.1 | 1468.8 | 0.090 | 4.11 | 123.4 | 76.3 | 30/30 | 0 | 15 | 10/10 | 0 |
| D_depth2 | 1060.1 | 1468.8 | 0.098 | 3.19 | 95.7 | 76.4 | 30/30 | 0 | 15 | 10/10 | 0 |

### vampi boundary 포함(민감도 분석)
| 조건 | 평균 입력 토큰 | 평균 코드 문자 수 | 평균 추출 시간(ms) | 평균 추론 시간(s) | 총 추론 시간(s) | 평균 출력 토큰 | 필요 코드 포함 | 필요 코드 없이 no_issue | 누락 정보를 적고도 확정 판정 | 반복 간 판정 일치 | 문맥 초과 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A_full | 3796.8 | 15158.5 | 0.171 | 9.81 | 412.0 | 72.2 | 42/42 | 0 | 0 | 14/14 | 0 |
| B_handler | 815.1 | 710.1 | 0.148 | 3.61 | 151.7 | 65.7 | 6/42 | 6 | 30 | 14/14 | 0 |
| C_depth1 | 921.5 | 1138.1 | 0.099 | 3.71 | 155.6 | 71.6 | 30/42 | 6 | 27 | 14/14 | 0 |
| D_depth2 | 921.5 | 1138.1 | 0.087 | 2.97 | 124.5 | 71.7 | 30/42 | 6 | 27 | 14/14 | 0 |

- `필요 코드 포함`: 정답표의 required_functions가 추출 결과에 모두 들어 있는 사례 수(LLM과 무관).
- `필요 코드 없이 no_issue`: 필요한 코드가 입력에 없는데 no_issue_found로 답한 횟수(근거 없는 정상 판정).
- `누락 정보를 적고도 확정 판정`: verdict가 vulnerable/no_issue_found인데 missing_context가 비어 있지 않은 횟수.
- `반복 간 판정 일치`: 모든 반복에서 판정이 같은 사례 수. 모두 일치하면 반복은 시간 측정에만 의미가 있고, 탐지 지표의 n은 사실상 사례 수의 반복 배수다.
- 추출 시간: 벤치 색인(파싱 + 호출 그래프)은 실행 시작 때 한 번만 하고 run_meta의 codebase_index_seconds에 따로 적었다. 표의 값은 BFS와 코드 조립 시간이다.

## VAmPI 짝 비교 (같은 엔드포인트의 vuln 빌드 / secure 빌드)
정답: vuln 빌드는 vulnerable, secure 빌드는 not_vulnerable. 양성이 2개뿐이라 비율 지표보다 이 표를 우선해서 본다.

| 엔드포인트 | 조건 | vuln 빌드 판정 | secure 빌드 판정 |
|---|---|---|---|
| e01 (P1) | A_full | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| e01 (P1) | B_handler | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| e01 (P1) | C_depth1 | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| e01 (P1) | D_depth2 | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| e02 (P2) | A_full | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| e02 (P2) | B_handler | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| e02 (P2) | C_depth1 | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| e02 (P2) | D_depth2 | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |

## 사례별 판정
(코드부족) = 해당 조건 입력에 판단에 필요한 함수가 빠짐

| 사례 | 유형 | 정답 | A_full | B_handler | C_depth1 | D_depth2 |
|---|---|---|---|---|---|---|
| campus:e01 | 원본 VULN-001 | vulnerable | no_issue_found/no_issue_found/no_issue_found | insufficient_context/insufficient_context/insufficient_context | insufficient_context/insufficient_context/insufficient_context | insufficient_context/insufficient_context/insufficient_context |
| campus:e02 | 원본 SAFE-001 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e03 | 원본 VULN-002 | vulnerable | no_issue_found/no_issue_found/no_issue_found | vulnerable/vulnerable/vulnerable | insufficient_context/insufficient_context/insufficient_context | insufficient_context/insufficient_context/insufficient_context |
| campus:e04 | 원본 SAFE-002 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e05 | 원본 SAFE-008 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e06 | 원본 VULN-003 | vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable | insufficient_context/insufficient_context/insufficient_context | insufficient_context/insufficient_context/insufficient_context |
| campus:e07 | 원본 SAFE-003 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| campus:e08 | 원본 VULN-004 | vulnerable | no_issue_found/no_issue_found/no_issue_found | insufficient_context/insufficient_context/insufficient_context | insufficient_context/insufficient_context/insufficient_context | insufficient_context/insufficient_context/insufficient_context |
| campus:e09 | 원본 SAFE-004 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e10 | 원본 SAFE-005 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e11 | 원본 SAFE-011 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e12 | 원본 SAFE-010 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e13 | 원본 VULN-005 | vulnerable | no_issue_found/no_issue_found/no_issue_found | vulnerable/vulnerable/vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e14 | 원본 VULN-006 | vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| campus:e15 | 원본 SAFE-006 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e16 | 원본 SAFE-007 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found |
| campus:e17 | 원본 SAFE-009 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| campus:e18 | 추가: 서비스 함수(depth1)가 검사 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | insufficient_context/insufficient_context/insufficient_context (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e19 | 추가: 서비스 함수(depth1)가 검사하지 않음 | vulnerable | vulnerable/vulnerable/vulnerable | insufficient_context/insufficient_context/insufficient_context (코드부족) | insufficient_context/insufficient_context/insufficient_context | insufficient_context/insufficient_context/insufficient_context |
| campus:e20 | 추가: depth2 헬퍼가 정책과 다른 기준(학과)을 검사 | vulnerable | no_issue_found/no_issue_found/no_issue_found | insufficient_context/insufficient_context/insufficient_context (코드부족) | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable |
| campus:e21 | 추가: 서비스를 거치는 공개 정보 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e22 | 추가: Depends 의존성(depth1)이 검사 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found |
| campus:e23 | 추가: 검사 함수 반환값 무시 | vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| campus:e24 | 추가: depth2 헬퍼가 검사 | not_vulnerable | vulnerable/vulnerable/vulnerable | insufficient_context/insufficient_context/insufficient_context (코드부족) | insufficient_context/insufficient_context/insufficient_context (코드부족) | no_issue_found/no_issue_found/no_issue_found |
| campus:e25 | 추가: Depends 의존성이 존재 여부만 확인 | vulnerable | no_issue_found/no_issue_found/no_issue_found | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable | insufficient_context/insufficient_context/insufficient_context |
| vampi_vuln:e01 | P1 | vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| vampi_secure:e01 | P1 짝 | not_vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| vampi_vuln:e02 | P2 | vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| vampi_secure:e02 | P2 짝 | not_vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| vampi_vuln:e03 | N1 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| vampi_secure:e03 | N1 | not_vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable |
| vampi_vuln:e04 | N2 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | vulnerable/vulnerable/vulnerable (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| vampi_secure:e04 | N2 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | vulnerable/vulnerable/vulnerable (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| vampi_vuln:e05 | N3 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| vampi_secure:e05 | N3 | not_vulnerable | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found | no_issue_found/no_issue_found/no_issue_found |
| vampi_vuln:e06 | B1 | not_vulnerable | vulnerable/vulnerable/vulnerable | insufficient_context/insufficient_context/insufficient_context (코드부족) | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found (코드부족) |
| vampi_secure:e06 | B1 | not_vulnerable | vulnerable/vulnerable/vulnerable | insufficient_context/insufficient_context/insufficient_context (코드부족) | no_issue_found/no_issue_found/no_issue_found (코드부족) | no_issue_found/no_issue_found/no_issue_found (코드부족) |
| vampi_vuln:e07 | B2 | vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable (코드부족) |
| vampi_secure:e07 | B2 | vulnerable | vulnerable/vulnerable/vulnerable | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable (코드부족) | vulnerable/vulnerable/vulnerable (코드부족) |

원본 프롬프트와 모델 응답: `raw/<case>_<condition>_r<repeat>.json`
