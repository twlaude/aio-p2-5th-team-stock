# 문서 색인
> **한눈에** — 구조·계약·검증·실행 문서를 찾습니다.
> 서비스 실행은 [README 바로 실행](../README.md#1-바로-실행-docker)을 봅니다.
> 소스 빌드와 서비스별 실행은 [개발 환경](operations/DEVELOPMENT.md)을 봅니다.

| 폴더 | 문서·내용 |
|---|---|
| `architecture/` | [SERVICE_OVERVIEW.md](architecture/SERVICE_OVERVIEW.md): 책임·요청 흐름·설계 의도·기술·폴더 구조 / [FINAL_ARCHITECTURE.md](architecture/FINAL_ARCHITECTURE.md): 책임·확정 연결 / [agent-architecture.md](architecture/agent-architecture.md): Profile(역할)·노드·분기·안전장치 / [diagrams/](architecture/diagrams/): 시스템·서비스·DB·Agent Mermaid 원본·SVG |
| `specs/` | [API명세서.md](specs/API명세서.md)·[DB설계서.md](specs/DB설계서.md)·[화면설계서.md](specs/화면설계서.md): 제출 3종 / [FRONTEND_FLOW.md](specs/FRONTEND_FLOW.md): 검색·로그인·근거·개인화 / [CONNECTION_CONTRACT.md](specs/CONNECTION_CONTRACT.md)·[contracts/](specs/contracts/): 포트·필드·오류 |
| `reports/` | [agent-test-report.md](reports/agent-test-report.md): off/on 비교 / [agent-test-result-report_narrative-source.md](reports/agent-test-result-report_narrative-source.md): Backend 서술 채택 / [BACKEND_CONCURRENCY_FINDINGS.md](reports/BACKEND_CONCURRENCY_FINDINGS.md): 동시성 병목 재현·개선 |
| `planning/` | [plan.md](planning/plan.md): 팀·역할·일정·제출 |
| `operations/` | [DEVELOPMENT.md](operations/DEVELOPMENT.md): `compose.yml` 소스 빌드·Docker 없이 서비스별 실행 / [LOCAL_RUN_ENV_CHECKLIST.md](operations/LOCAL_RUN_ENV_CHECKLIST.md): 환경변수 / [DEPLOYMENT_AND_PRESENTATION.md](operations/DEPLOYMENT_AND_PRESENTATION.md): 분산 실행·발표 |
