# Disclosure MCP

## 실행 순서

```powershell
pip install -r requirements.txt
python scripts/init_db.py
python scripts/sync_companies.py
python scripts/ingest_annual_reports.py --stock 005930 --years 2024 2025
python server.py
```

별도 터미널에서 서버와 지원 종목 전체를 점검한다.

```powershell
python scripts/smoke.py --skip-search
```

`--skip-search`를 빼면 미색인 사업보고서가 자동 수집·임베딩되어 OpenAI 비용과 시간이 든다.
