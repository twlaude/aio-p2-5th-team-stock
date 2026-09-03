# 살래? 말래? frontend

React 19, Vite 8, TypeScript 기반 프론트엔드다. 현재 item 1 범위는 기존 Python UI 제거, 목 API 계약, 기본 라우팅, auth/search 상태, Home/Login JSON 확인 화면까지다.

## 실행

```bash
npm install
npm run dev
```

기본 dev/preview 포트는 `8501`이다.

## 환경 변수

- `VITE_API_MODE=mock|live`: 기본값은 `mock`
- `VITE_BACKEND_URL=http://localhost:8000`: live 모드 백엔드 주소
- `VITE_DEMO_MODE=true`: 데모 표시 플래그

## 검증

```bash
npm run lint
npm run build
npm test
```

`npm run shots`와 Dockerfile은 마감 항목에서 추가한다.
