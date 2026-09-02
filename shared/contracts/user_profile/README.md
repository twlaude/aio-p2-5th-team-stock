# 사용자 투자 성향 계약

초기 개인화에는 다음 네 값만 사용한다.

```json
{
  "experience_level": "beginner",
  "risk_profile": "balanced",
  "investment_horizon": "long",
  "preferred_evidence": "news"
}
```

## 허용값

| 필드 | 허용값 | 개인화 적용 |
|---|---|---|
| `experience_level` | `beginner`, `intermediate`, `experienced` | 설명 난이도 |
| `risk_profile` | `conservative`, `balanced`, `aggressive` | 강조할 위험·기회 관점 |
| `investment_horizon` | `short`, `medium`, `long` | 확인할 시간 범위 |
| `preferred_evidence` | `market`, `news`, `financial`, `risk` | 먼저 보여줄 근거 |

네 값은 모두 필수다. 이 값은 매수·매도 적합도나 추천을 계산하는 데 사용하지 않는다.

개인화 결과는 다음 규격을 사용한다.

```json
{
  "personal_summary": "개인 관점의 한 줄 설명",
  "priority_checks": ["확인 항목 1", "확인 항목 2"],
  "caution": "주의할 점 1개"
}
```
