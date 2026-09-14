# Community MCP Tool 계약

> **한눈에**
> 반응과 공포탐욕 지수를 조회합니다.
> 표본 수로 상태를 나눕니다.
> 집계·주제·짧은 근거만 전달합니다.

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

원문 100개 전체는 MCP Client·LLM(언어 모델)에 보내지 않습니다.

`activity`의 `ratio` = 최근 7일 글 수(`posts_7d`) / 직전 28일 주간 평균(`weekly_avg_prev_28d`). 기준선 없음은 `null`, `baseline_days`는 `28` 고정입니다.
상류에 `activity`가 없으면 생략하고 소비자는 미가용(`null`)으로 봅니다.

## Tool: get_fear_greed_index

15분 단위 지수입니다. 최근 28일 분위수(분포 내 위치)로 `공포`·`중립`·`탐욕` 계열을 정합니다. 표본·기준선 부족: `warnings`.

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

원본 `status:"empty"` → `no_data`. 인증 실패·장애·타임아웃 → `status:"error"` + `error` 객체.
