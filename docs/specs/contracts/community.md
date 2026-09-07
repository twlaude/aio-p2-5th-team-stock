# Community MCP Tool 계약

## 연결과 Tool

- MCP 주소: `http://COMMUNITY_MCP_HOST:8023/mcp`
- Tool 이름: `get_community_reaction`, `get_fear_greed_index`
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
  "activity": {
    "posts_7d": 100,
    "weekly_avg_prev_28d": 70.0,
    "ratio": 1.43,
    "baseline_days": 28
  },
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
  "fgi_latest": {
    "fgi": 52.5,
    "label": "중립",
    "as_of": "2026-09-01T09:00:00Z",
    "post_count": 12,
    "valence_percentile": 51
  },
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

`activity`는 최근 7일 글 수(`posts_7d`)를 직전 28일의 주간 평균
(`weekly_avg_prev_28d`)과 비교한 활동량이다. `ratio`는 두 값의 비율이며 기준선이
없으면 `null`이다. `baseline_days`는 `28`로 고정된다. 상류 응답에 `activity`가
없으면 이 필드는 생략되며, 소비자는 미가용(`null`)으로 취급한다.

## Tool: get_fear_greed_index

15분 버킷 공포탐욕 지수를 반환한다. 라벨은 최근 28일 분위수 기준선으로 `공포`, `중립`, `탐욕` 계열을 산출하며, 표본 부족이나 기준선 부족은 `warnings`에 포함한다.

### 입력

```json
{
  "company_name": "삼성전자",
  "stock_code": "005930"
}
```

### 출력

```json
{
  "request_id": "9b4b0c7b-0b5a-4a86-b92d-2f6f89c59a19",
  "status": "success",
  "company_name": "삼성전자",
  "stock_code": "005930",
  "fgi": 52.5,
  "label": "중립",
  "as_of": "2026-09-01T09:00:00Z",
  "post_count": 12,
  "warnings": [],
  "source_name": "태웅님 커뮤니티 서버",
  "collected_at": "2026-09-01T09:00:00Z"
}
```

`status:"empty"` 원본 응답은 `no_data`로 변환한다. 원본 서버 인증 실패, 장애, 타임아웃은 `status:"error"`와 `error` 객체로 반환한다.
