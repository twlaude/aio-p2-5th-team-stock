# GUIDE

## 역할

`frontend/`는 살래? 말래? React 단일 페이지 앱이다. 백엔드가 준비되기 전까지 `VITE_API_MODE=mock`으로 계약 응답을 완성하고, `VITE_API_MODE=live`로 전환하면 같은 타입으로 실제 API를 호출한다.

## 화면

- `/`: Home. 지원 기업 목록과 분석 응답 JSON을 호출해 표시한다.
- `/login`: Login. 데모 계정 fixture를 보여주고 목 로그인 API 결과를 표시한다.

## 구조

```text
src/pages/home
src/pages/login
src/components/common
src/components/stock
src/components/analysis
src/components/mascot
src/services/backend_api
src/state
src/mocks
src/styles
src/assets
tests
```

## Env

`.env.example` 기준으로 시작한다.

```text
VITE_API_MODE=mock
VITE_BACKEND_URL=http://localhost:8000
VITE_DEMO_MODE=true
```

## 실행

```bash
npm install
npm run dev
```

Vite dev server는 `0.0.0.0:8501`로 뜬다.

## 완료 기준

item 1 기준 완료 조건은 다음과 같다.

- 기존 Python UI 파일과 관련 호출이 없다.
- React 19 + Vite 8 + TypeScript 프로젝트가 빌드된다.
- `/`와 `/login` 라우트가 동작한다.
- 목 API가 `companies`, guest/member/unsupported/partial 분석 계약 필드를 반환한다.
- `npm run lint`, `npm run build`, `npm test`가 통과한다.
