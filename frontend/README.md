# 살래? 말래? frontend

React 19, Vite 8, TypeScript 기반의 한 페이지 주식 정보 프론트엔드다. 기본은 mock 모드로 동작하며, `VITE_API_MODE=live`로 전환하면 같은 프론트 계약 타입으로 백엔드 API를 호출한다.

## 실행

```bash
npm ci
npm run dev
```

기본 dev/preview 포트는 `8501`이다. 통합 검증 스크립트는 충돌을 피하기 위해 dev 서버를 `8519`에 별도로 띄운다.

## 환경 변수

```text
VITE_API_MODE=mock
VITE_BACKEND_URL=http://localhost:8000
VITE_DEMO_MODE=true
```

`mock`은 fixture 기반으로 비회원, 회원, 미지원, 부분 실패, 전체 실패를 재현한다. `live`는 상대경로 `/api/v1/...`를 호출하며 개발 서버에서는 Vite proxy가 `VITE_BACKEND_URL`로 전달한다.

## 검증

```bash
npm run lint
npm run build
npm test
npm run shots
```

`npm run shots`는 headless Chrome(`/opt/google/chrome/chrome --no-sandbox`)으로 데스크톱 7상태와 모바일 2상태를 `tests/shots/*.png`에 생성한다.

## Docker

```bash
docker build -t sallae-frontend .
docker run --rm -p 8501:8501 --env-file .env.example sallae-frontend
```

컨테이너는 `npm ci`, `npm run build`를 수행한 뒤 `vite preview --host 0.0.0.0 --port 8501`로 정적 빌드를 제공한다.
