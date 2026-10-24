# 조건별 코드 추출 결과 (LLM 미사용)

문자 수는 토큰 수의 대체 지표이며 실제 토큰 수가 아니다. 추출 시간은 단일 측정값이다.

| 사례 | 조건 | 포함 함수 | 깊이 한도로 제외 | 미해석 호출(builtin 제외) | 코드 문자 수 | 필요 코드 포함 |
|---|---|---|---|---|---|---|
| case_01 | A_full | <entire file> | - | - | 1182 | 예 |
| case_01 | B_depth0 | get_record | load_record normalize_id to_view | - | 118 | 아니오 |
| case_01 | C_depth1 | normalize_id load_record to_view get_record | - | raw.strip().lower raw.strip RECORDS.get | 403 | 예 |
| case_01 | D_depth2 | normalize_id load_record to_view get_record | - | raw.strip().lower raw.strip RECORDS.get | 403 | 예 |
| case_02 | A_full | <entire file> | - | - | 1172 | 예 |
| case_02 | B_depth0 | fetch_invoice | _load _render | - | 192 | 예 |
| case_02 | C_depth1 | _load _render fetch_invoice | - | INVOICES.get | 427 | 예 |
| case_02 | D_depth2 | _load _render fetch_invoice | - | INVOICES.get | 427 | 예 |
| case_03 | A_full | <entire file> | - | - | 1161 | 예 |
| case_03 | B_depth0 | read_message | _lookup _ensure_owner _present | - | 148 | 아니오 |
| case_03 | C_depth1 | _lookup _ensure_owner _present read_message | - | MESSAGES.get | 519 | 예 |
| case_03 | D_depth2 | _lookup _ensure_owner _present read_message | - | MESSAGES.get | 519 | 예 |
| case_04 | A_full | <entire file> | - | - | 1260 | 예 |
| case_04 | B_depth0 | order_detail | _guard _get_order _shape | - | 122 | 아니오 |
| case_04 | C_depth1 | _get_order _guard _shape order_detail | _require_match | ORDERS.get | 455 | 아니오 |
| case_04 | D_depth2 | _get_order _require_match _guard _shape order_detail | - | ORDERS.get | 567 | 예 |
| case_05 | A_full | <entire file> | - | - | 1225 | 예 |
| case_05 | B_depth0 | view_product | _find _card | - | 102 | 아니오 |
| case_05 | C_depth1 | _find _card view_product | - | PRODUCTS.get | 345 | 예 |
| case_05 | D_depth2 | _find _card view_product | - | PRODUCTS.get | 345 | 예 |
| case_06 | A_full | <entire file> | - | - | 1097 | 예 |
| case_06 | B_depth0 | download_document | _read is_owner _payload | - | 141 | 아니오 |
| case_06 | C_depth1 | _read is_owner _payload download_document | - | DOCUMENTS.get | 462 | 예 |
| case_06 | D_depth2 | _read is_owner _payload download_document | - | DOCUMENTS.get | 462 | 예 |
| case_07 | A_full | <entire file> | - | - | 1011 | 예 |
| case_07 | B_depth0 | export_report | _get _serialize | channel.append HISTORY.append | 283 | 아니오 |
| case_07 | C_depth1 | _get _serialize export_report | - | REPORTS.get channel.append HISTORY.append | 499 | 예 |
| case_07 | D_depth2 | _get _serialize export_report | - | REPORTS.get channel.append HISTORY.append | 499 | 예 |
| case_08 | A_full | <entire file> | - | - | 1135 | 예 |
| case_08 | B_depth0 | open_entry | _fetch | entry.get | 326 | 아니오 |
| case_08 | C_depth1 | _fetch open_entry | - | ENTRIES.get entry.get | 459 | 예 |
| case_08 | D_depth2 | _fetch open_entry | - | ENTRIES.get entry.get | 459 | 예 |
| case_09 | A_full | <entire file> | - | - | 1119 | 예 |
| case_09 | B_depth0 | show_note | _note _can_view | - | 183 | 아니오 |
| case_09 | C_depth1 | _note _can_view show_note | - | NOTES.get USERS.get | 459 | 예 |
| case_09 | D_depth2 | _note _can_view show_note | - | NOTES.get USERS.get | 459 | 예 |
| case_10 | A_full | <entire file> | - | - | 1257 | 예 |
| case_10 | B_depth0 | get_file | _file _authorize | - | 132 | 아니오 |
| case_10 | C_depth1 | _file _authorize get_file | _root_owner | FILES.get | 389 | 아니오 |
| case_10 | D_depth2 | _file _root_owner _authorize get_file | - | FILES.get | 559 | 예 |
| case_11 | A_full | <entire file> | - | - | 980 | 예 |
| case_11 | B_depth0 | photo_meta | _photo | ACL.allows | 228 | 아니오 |
| case_11 | C_depth1 | _photo photo_meta | - | PHOTOS.get ACL.allows | 360 | 아니오 |
| case_11 | D_depth2 | _photo photo_meta | - | PHOTOS.get ACL.allows | 360 | 아니오 |
| case_12 | A_full | <entire file> | - | - | 1241 | 예 |
| case_12 | B_depth0 | ticket_detail | _prepare | - | 159 | 아니오 |
| case_12 | C_depth1 | _prepare ticket_detail | _load_ticket _validate | AUDIT.append | 335 | 아니오 |
| case_12 | D_depth2 | _load_ticket _validate _prepare ticket_detail | _match_owner | TICKETS.get AUDIT.append | 652 | 아니오 |

## 조건별 합계

| 조건 | 평균 코드 문자 수 | 필요 코드 포함 사례 |
|---|---|---|
| A_full | 1153.3 | 12/12 |
| B_depth0 | 177.8 | 1/12 |
| C_depth1 | 426.0 | 8/12 |
| D_depth2 | 475.9 | 10/12 |
