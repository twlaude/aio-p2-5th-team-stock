# 설계 문서 읽는 순서

팀원이 개발을 시작할 때는 아래 순서로 읽는다.

1. 루트 `README.md`
2. 루트 `실행_폴더_구분.md`
3. `shared/CONNECTION_CONTRACT.md`
4. 자신이 담당한 서비스의 `GUIDE.md`
5. `shared/contracts/`의 담당 계약
6. `guide/06_CONFIRMED_LOCAL_STRUCTURE.md`
7. `guide/07_AGENT_WORKFLOW_GUIDE.md`

`guide/00`부터 `guide/05`까지는 아이디어와 구조를 잡는 과정에서 작성한 보관용 초기 문서이며 구현 지시서가 아니다. 자유 질문, Streamlit, 과거 역할처럼 현재 결정과 다른 내용이 남아 있으므로 개발에는 사용하지 않는다. 최신 기준의 우선순위는 `shared` 계약 → 각 실행 폴더의 `GUIDE.md` → 루트 문서 → `guide/06`, `guide/07`이다.
