# MCP 서버 공통 가이드

## 구성

```text
mcp_servers/
├─ price_mcp/
├─ news_mcp/
├─ disclosure_mcp/
└─ community_mcp/
```

각 MCP 서버는 독립 폴더, 독립 가상환경, 독립 `.env`, 독립 `requirements.txt`, 독립 실행 포트를 가진다.

## 공통 내부 구조

```text
각_mcp/
├─ server.py                # 진입점: FastMCP 생성 + Tool 등록만 (로직 없음). 실행 `python server.py`
├─ app/
│  ├─ tools/                # MCP Tool 공개 규격
│  ├─ services/             # 정제·검색·계산 규칙
│  ├─ clients/              # 외부 API·DB 연결
│  ├─ schemas/              # Tool 입력·출력 형식
│  └─ core/                 # 설정·로그
├─ tests/
├─ .env.example
├─ requirements.txt
├─ Dockerfile               # 실행 코드 완성 후 추가
└─ GUIDE.md
```

## 계층별 책임

- `tools`: MCP Client가 호출할 Tool 이름, 설명, 입출력
- `services`: 수집 결과 정제, 중복 제거, 분석 규칙
- `clients`: 주가 API, 뉴스 API, DART, 태웅님 서버, DB 등 각 서버의 실제 원본 연결
- `schemas`: 필드 이름과 자료형
- `core`: 환경변수, 포트, 로그, 공통 오류
- `server.py`: 폴더 루트에 둔다. 교재 05장과 FastMCP의 대표 예제 구조를 따라 `python server.py`로 바로 실행한다. FastAPI 쪽 `app/main.py`와 구분하고 네 MCP의 실행법을 통일하기 위한 팀 규칙이다.

## 기준 구현

`community_mcp`는 현재 Tool, Schema, Service, 외부 Client, Mock, 오류 처리와 테스트가 구현되어 있다. 나머지 세 MCP는 Community MCP의 책임 분리와 테스트 방식을 기준으로 개발하되, Community 전용 코드를 복사하지 않는다.

## 모든 MCP 응답에 필요한 정보

```text
source_type
company_name
stock_code
collected_at
published_at
status
summary
evidence
source_url
error
```

## 공통 원칙

- 확인하지 못한 사실을 채워 넣지 않는다.
- 원문과 요약을 구분한다.
- 데이터 출처와 기준 시각을 반환한다.
- 중복 데이터 제거 기준을 정한다.
- 외부 API 장애와 검색 결과 없음은 다른 상태로 반환한다.
- 사용자 인증 정보와 투자 성향을 받지 않는다.

## 이전 단일 MCP 골격

초기 단일 서버 골격은 `archive/legacy/stock_mcp`에 보관한다. 현재 구현 대상으로 사용하지 않는다.
