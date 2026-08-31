# scripts/ — 수집·임베딩 배치

API 서버와 별개로 미리 돌려두는 작업들. backend의 .env / requirements를 그대로 쓴다.
- (예정) ingest_news.py : 뉴스 수집 → rag_chunks 적재
- (예정) embed_chunks.py : 미임베딩 청크 임베딩 생성
- (예정) ingest_user_notes.py : 사용자 투자 메모 적재
