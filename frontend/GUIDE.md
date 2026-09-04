# GUIDE

## 역할

`frontend/`는 살래? 말래? React 단일 페이지 앱이다. 검색 전 화면에서 지원 기업을 탐색하고, 검색 후 같은 화면에서 공개 결과, 로그인 게이트, 회원 근거, 개인화 확인 포인트를 이어서 표시한다. 백엔드가 준비되기 전까지 mock 모드로 계약 응답을 완성하며, live 모드는 같은 타입을 유지한 채 실제 API 경로로 전환한다.

## 확정 화면과 상태

- 검색 전: `/` 초기 상태. 마스코트 idle, 검색바, 인기 기업 칩, 지원 20종목 시트를 표시한다.
- 검색 중: 지원 종목 제출 뒤 loading 상태. 마스코트 thinking, 진행 칩, 스켈레톤을 표시한다.
- 공개 결과: 비회원과 회원 모두 회사명, 가격, 스파크라인, 한줄 결론, Why 버튼을 본다.
- 비회원 게이트: 비회원이 Why를 누르면 근거 영역을 blur 처리하고 Mock 계정 로그인 버튼을 표시한다.
- 로그인: `/login`에서 데모 계정 10개를 5x2 카드로 표시한다. 모바일은 2열이다.
- 회원 상세: 로그인 후 보류된 검색어가 있으면 홈으로 돌아와 자동 재분석하고 근거, 개인화, 푸터를 표시한다.
- 미지원: `status:"unsupported_company"` 응답에서 안내 카드와 지원 기업 20개 리스트를 표시한다.
- 부분 실패: `status:"partial_completed"` 응답에서 커뮤니티 실패 안내와 실패 카드 재시도 버튼을 표시한다.
- 전체 실패: 네트워크 또는 서버 오류를 ErrorNotice로 표시하고 재시도 버튼을 제공한다.
- 모바일: 390px 기준 가로 스크롤 없이 검색바, 게이지, 카드, 게이트, 로그인 카드, 빼꼼 마스코트가 재배치된다.

## 폴더 트리

```text
frontend/
├─ src/
│  ├─ pages/
│  │  ├─ home/
│  │  └─ login/
│  ├─ components/
│  │  ├─ common/
│  │  ├─ stock/
│  │  ├─ analysis/
│  │  └─ mascot/
│  ├─ services/backend_api/
│  ├─ state/
│  ├─ mocks/
│  │  └─ analyses/
│  ├─ styles/
│  └─ assets/
├─ tests/
│  └─ shots.mjs
├─ index.html
├─ vite.config.ts
├─ tsconfig.json
├─ tsconfig.app.json
├─ tsconfig.node.json
├─ package.json
├─ .env.example
├─ Dockerfile
├─ GUIDE.md
└─ README.md
```

## 실행

```bash
npm ci
npm run dev
```

dev server는 기본 `0.0.0.0:8501`로 뜬다. 통합 스크린샷 스크립트는 독립 dev server를 `127.0.0.1:8519`에 띄우고 종료한다.

```bash
npm run build
npm run preview
```

`npm run build`는 `tsc -b`와 `vite build`를 순서대로 실행한다. `npm run preview`는 `vite preview --host 0.0.0.0 --port 8501`로 빌드 산출물을 제공한다.

```bash
docker build -t sallae-frontend .
docker run --rm -p 8501:8501 --env-file .env.example sallae-frontend
```

Dockerfile은 `node:22-alpine`에서 `npm ci`, `npm run build`를 수행하고 Vite preview로 `8501` 포트를 연다.

## 반응형 규칙

| 사이즈 클래스 | 범위 | 페이지 껍데기 용도 |
|---|---:|---|
| compact | `<600px` | 모바일 나브, 섹션 패딩, 단일 컬럼 |
| medium | `600~839px` | 축소 패딩, 중간 컬럼 |
| expanded | `>=840px` | 중앙 데스크톱 컬럼 |

- 짧은 화면은 `(max-height: 520px)`, 초대형은 `1600px`과 `2000px` 단계만 예외로 둔다.
- 큰 글자는 `tokens.css`의 `--fs-display`부터 `--fs-caption`까지 clamp 토큰을 쓴다.
- 나브·히어로·섹션 패딩·페이지 컬럼 수만 뷰포트 쿼리로 바꾼다.
- 카드·리스트 행처럼 재사용되는 UI는 `container-type: inline-size`와 `@container`로 부모 폭에 반응시킨다.
- 그리드는 우선 `auto-fit`과 `minmax()`로 구성하고, 칩은 `flex-wrap`으로 줄바꿈한다.
- 포인터가 coarse면 탭 타깃을 최소 44px로 만들고, hover 효과는 `(hover: hover)` 안에만 둔다.
- 전체 매트릭스는 `node tests/responsive.mjs`로 10개 뷰포트 × 3개 상태를 headless 검증한다.

## Env

```text
VITE_API_MODE=mock
VITE_BACKEND_URL=http://localhost:8000
VITE_DEMO_MODE=true
```

- `VITE_API_MODE`: `mock` 또는 `live`를 지정한다. 기본값은 `mock`이다.
- `VITE_BACKEND_URL`: dev proxy가 전달할 백엔드 주소다. 기본값은 `http://localhost:8000`이다.
- `VITE_DEMO_MODE`: 데모 표시 플래그다. 현재 화면 카피와 mock 로그인을 유지한다.

## Mock 시나리오

- 기본 검색: 초기 화면에서 자동 제출하지 않는다.
- `?scenario=slow`: `삼성전자`를 자동 제출하고 loading 상태를 2.2초 유지한다.
- `?scenario=partial`: `삼성전자`를 자동 제출한다. 로그인 세션이 있으면 부분 실패 회원 응답을 표시한다.
- `?scenario=unsupported`: `NAVER`를 자동 제출하고 미지원 응답을 표시한다.
- `?scenario=error`: `삼성전자`를 자동 제출하고 ErrorNotice를 표시한다.

회원 상태 캡처는 `/login`에서 `demo001` 계정으로 mock 로그인 API를 호출해 `localStorage`의 `sallae.auth.session`을 만든 뒤 홈으로 진입한다.

## 백엔드 연결

live 모드는 상대경로로 API를 호출한다.

```text
POST /api/v1/auth/login
GET  /api/v1/companies
GET  /api/v1/profile
PUT  /api/v1/profile
POST /api/v1/analyses
```

개발 서버에서는 `vite.config.ts`의 `/api` proxy가 `VITE_BACKEND_URL`로 요청을 넘긴다. preview 서버는 proxy를 적용하지 않으므로 live preview에서 백엔드가 같은 origin에 없으면 `/api/v1/...` 요청은 실패하고 ErrorNotice로 떨어진다.

배포 시 백엔드는 프론트 호스트를 CORS 허용해야 한다. 예: `allow_origins=["http://<프론트호스트>:8501"]`.

## 완료 기준

1. 비회원이 로그인 없이 지원 종목을 검색하면 공개 결과가 표시된다.
2. Why 버튼은 로그인 여부에 따라 비회원 게이트 또는 회원 근거 섹션으로 분기한다.
3. Mock 로그인 후 원래 검색 종목으로 복귀해 회원 분석을 자동 실행한다.
4. 회원 화면은 공통 근거와 개인화 확인 포인트를 구분해 표시하고, 유저를 바꾸면 개인화만 달라진다.
5. 미지원 기업, 부분 실패, 전체 실패 상태가 각각 전용 안내로 표시된다.
6. `npm run lint`, `npm run build`, `npm test`, `npm run shots`가 통과하고 `tests/shots/`에 9장 스크린샷이 생성된다.
