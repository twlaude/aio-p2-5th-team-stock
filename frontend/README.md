# frontend — 사용자 화면 (React + Vite, 포트 8501)

검색, 로그인, 공개 결과, 근거 카드, 성향별 확인 포인트를 보여주는 단일 페이지 앱입니다. 서버는 Backend 하나만 호출하고, `/api` 요청은 Vite가 `VITE_BACKEND_URL`로 프록시합니다.

## 실행

```bash
npm ci
cp .env.example .env            # VITE_API_MODE=mock|live, VITE_BACKEND_URL
npm run dev                     # http://localhost:8501
npm test                        # Vitest 단위 테스트
npm run build && npm run preview   # 배포와 같은 방식
node tests/responsive.mjs       # 뷰포트 10종 스크린샷 (Playwright Core)
```

`VITE_API_MODE=mock`이면 `src/mocks/`의 고정 응답으로 Backend 없이 화면을 볼 수 있습니다.

## 폴더 지도

| 경로 | 역할 |
|---|---|
| `src/App.tsx` | 라우팅. `/intro`(랜딩) · `/`(검색·결과) · `/login` |
| `src/pages/intro/` | 랜딩 페이지 (히어로·단계 설명·종목 레일·폰 목업) |
| `src/pages/home/` | 메인. 검색 히어로 → 결과 → 근거 → 개인화 섹션 |
| `src/pages/login/` | 데모 계정 로그인 |
| `src/components/stock/` | 검색창, 가격 헤더, 스파크라인, 한 줄 결론, 비회원 안내, 미지원·오류 안내 |
| `src/components/analysis/` | 관심 온도 게이지, 분위기 vs 근거 카드, 근거 카드, 성향별 확인 포인트, 부분 실패 알림 |
| `src/components/mascot/` · `common/` | 마스코트 상태 머신, 내비, 타이핑·카운트업 효과 |
| `src/services/backend_api/` | Backend 호출. `live.ts`(실제) / `mock.ts`(고정 응답)를 `index.ts`에서 모드에 따라 선택 |
| `src/state/` | 로그인 세션(`auth.ts`), 검색 상태와 재시도·복구(`searchStore.tsx`) |
| `src/styles/` | 디자인 토큰, 기본 스타일, 모션 |
| `tests/` | Vitest 단위 테스트 + 반응형 스크린샷 스크립트(`responsive.mjs`, `shots.mjs`) |
