# Community Clients

- `fgi_api.py`: 태웅님 커뮤니티 데이터 서버(`/reaction`, `/fgi`) HTTP 호출. 네트워크·인증 오류를 `FGIAPIError`(Timeout·Unavailable·Unauthorized)로 감싸서 올린다. 계약 형식 변환은 여기서 하지 않고 services가 맡는다.
