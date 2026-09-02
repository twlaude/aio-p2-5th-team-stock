# Community MCP Tool 계약

## 연결과 Tool

- MCP 주소: `http://COMMUNITY_MCP_HOST:8023/mcp`
- Tool 이름: `get_community_reaction`
- 원본 제공처: 태웅님 커뮤니티 데이터 서버
- 기본 범위: 최근 7일, 최대 100개 게시글

## 입력

```json
{
  "company_name": "삼성전자",
  "stock_code": "005930",
  "lookback_days": 7,
  "limit": 100
}
```

## 출력

```json
{
  "status": "success",
  "sample_status": "sufficient",
  "period": {
    "from": "2026-08-26T00:00:00Z",
    "to": "2026-09-01T09:00:00Z"
  },
  "sample_size": 100,
  "sentiment": {
    "positive_count": 35,
    "neutral_count": 40,
    "negative_count": 25
  },
  "top_topics": {
    "expectations": ["기대 주제"],
    "concerns": ["우려 주제"]
  },
  "representative_evidence": [
    {
      "text": "개인정보를 제거한 짧은 대표 문장",
      "posted_at": "2026-09-01T01:00:00Z"
    }
  ],
  "source_name": "태웅님 커뮤니티 서버",
  "collected_at": "2026-09-01T09:00:00Z"
}
```

표본 규칙:

| 표본 수 | `status` | `sample_status` |
|---:|---|---|
| 0 | `no_data` | `no_data` |
| 1~9 | `success` | `insufficient_sample` |
| 10 이상 | `success` | `sufficient` |

원문 100개 전체를 MCP Client와 LLM에 전달하지 않는다. 집계값, 주요 주제와 짧은 대표 근거만 전달한다.
