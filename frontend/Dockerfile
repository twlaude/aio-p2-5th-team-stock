FROM node:22-alpine

# Root context includes the company list imported by CompanyRail.tsx.
WORKDIR /app/frontend

# VITE_* 는 build 시점에 번들에 박힌다. 컨테이너 실행 시 --env-file 로는 못 바꾸므로 build-arg 로 넘긴다.
#   docker build --build-arg VITE_API_MODE=live --build-arg VITE_BACKEND_URL=http://backend:8000 -f frontend/Dockerfile -t sallae-frontend .
ARG VITE_API_MODE=live
ARG VITE_BACKEND_URL=http://localhost:8000
ENV VITE_API_MODE=$VITE_API_MODE
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ .
COPY shared/supported_companies.json /app/shared/supported_companies.json
RUN npm run build

EXPOSE 8501

# preview 서버가 /api 를 VITE_BACKEND_URL 로 프록시한다 (vite.config.ts preview.proxy)
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "8501"]
