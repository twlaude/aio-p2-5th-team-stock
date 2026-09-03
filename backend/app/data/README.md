# Backend Data

Backend가 Mock 모드에서 사용하는 고정 데이터다.

- `mock_users.json`: 발표용 사용자 10명과 투자 성향

지원 기업의 공통 Snapshot은 `shared/supported_companies.json`이 기준이다. Backend 구현 시 해당 파일을 읽거나 Backend 이미지에 복사해 사용한다.

Mock 비밀번호는 JSON에 저장하지 않고 `DEMO_PASSWORD` 환경변수로 받는다.
