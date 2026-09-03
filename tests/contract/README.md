# Contract Tests

각 서비스의 실제 응답이 `shared/contracts`와 일치하는지 확인한다.

현재 `test_static_data_contracts.py`는 다음 두 기준을 먼저 검증한다.

- 지원 기업 Snapshot이 20개이고 종목 코드와 순위가 중복되지 않는가
- Mock 사용자 10명의 투자 성향 값이 공통 계약의 허용값과 일치하는가
