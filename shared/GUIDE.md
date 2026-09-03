# 공통 입출력 계약 가이드

## 목적

팀원들이 서로 다른 서버를 개발해도 마지막에 연결할 수 있도록 공통 요청·응답 형식을 한곳에서 관리한다.

코드를 공유하기 위한 폴더라기보다 처음에는 계약 문서를 공유하기 위한 폴더로 사용한다.

## 확정 계약

```text
shared/
├─ CONNECTION_CONTRACT.md
└─ contracts/
   ├─ frontend_backend
   ├─ analysis
   ├─ user_profile
   ├─ price
   ├─ news
   ├─ disclosure
   ├─ community
   └─ errors
```

각 폴더의 `README.md`에 확정 Endpoint, Tool 이름, JSON 예시와 상태값을 기록했다. 구현은 이 계약을 기준으로 시작한다.

## 공통 필드 원칙

모든 근거 데이터에는 가능한 한 다음 항목을 포함한다.

```text
source_type
source_name
source_url
published_at
collected_at
status
summary
```

## 공통 분석과 개인화 분리

최종 Backend 응답에서 다음 두 영역을 분리한다.

```text
common_analysis
personalized_checkpoints
```

`common_analysis`는 MCP Client가 만든 결과이며 사용자와 관계없이 동일해야 한다. `personalized_checkpoints`도 MCP Client가 만들지만, Backend가 전달한 투자 성향 네 값만 사용한다. Backend는 사용자와 Memory를 관리하고 MCP Client 응답을 검증해 Frontend에 전달한다.

## 오류 상태

```text
success
no_data
partial_success
external_api_error
timeout
invalid_request
```

오류 메시지만 전달하지 말고 어느 서버와 어느 데이터에서 문제가 발생했는지 구분한다.

## 계약 변경 규칙

1. 필드를 추가할 때 의미와 예시를 함께 기록한다.
2. 기존 필드 이름을 임의로 바꾸지 않는다.
3. 필수 필드와 선택 필드를 구분한다.
4. 날짜와 시간 형식을 통일한다.
5. Mock Data도 실제 계약과 같은 형식을 사용한다.
