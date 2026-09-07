# 문서 안내

문서는 주제별 폴더로 나눈다. 현재 구현과 연결 기준은 아래 문서와 실제 코드를 우선하며, `archive/`는 참고용이다.

| 폴더 | 문서 | 목적 |
|---|---|---|
| `architecture/` | `FINAL_ARCHITECTURE.md` | 서비스 책임과 확정 연결 구조 |
| | `agent-architecture.md` | 에이전트 아키텍처 설계서 (제출 산출물 1) |
| | `diagrams/` | 시스템 구성·서비스 흐름·Backend 계층·ERD·Agent 상태 흐름 Mermaid 원본과 라이트/다크 SVG |
| `specs/` | `API명세서.md` | Backend·MCP Client·MCP Tool Endpoint와 요청·응답·오류 |
| | `DB설계서.md` | Backend DB와 Disclosure DB의 테이블·인덱스·벡터 검색 |
| | `화면설계서.md` | 단일 페이지 상태, 로그인, 공개·회원 화면과 이동 흐름 |
| | `FRONTEND_FLOW.md` | 비회원·회원 화면 흐름 기준 |
| `planning/` | `plan.md` | 팀 구성·역할, 작업 범위, 협업 규칙, 일정과 제출 기준 |
| | `DEVELOPMENT_PLAN.md` | 개발 단계와 완료 기준 (현재 상태) |
| | `DECISIONS_2026-09-02.md` | 회의에서 확정한 결정 목록 |
| `operations/` | `RUNTIME_FOLDERS.md` | 실행 대상, 로컬 포트와 VPS 운영 상태 |
| | `LOCAL_RUN_ENV_CHECKLIST.md` | MCP 연결과 서비스별 환경변수·점검 명령 |
| | `DEPLOYMENT_AND_PRESENTATION.md` | 운영 배치, 시연 전 확인 순서, 발표 흐름 |
| `reports/` | `agent-test-report.md` | 에이전트 시험 결과 보고서 (제출 산출물 2) |
| | `agent-test-result-report_narrative-source.md` | Backend 서술 채택 분기 시험 |
| | `BACKEND_CONCURRENCY_FINDINGS.md` | Backend 동시 요청 점검 결과 |
| `archive/` | `initial-design/`, `image-prompts/`, `design-drafts/` | 구조 확정 전 아이디어, 이미지 생성 프롬프트, 초기 화면 시안 |

제출 필수 산출물은 `architecture/agent-architecture.md`와 `reports/agent-test-report.md`이며, 저장소 README 5절 문서표와 6절 팀별 작성 영역에서도 연결한다.
