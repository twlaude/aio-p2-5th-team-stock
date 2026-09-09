"""Compute paired off/on metrics from the complete original JSONL observations."""
import argparse
from collections import Counter
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def metrics(rows):
    eligible = [row for row in rows if not row["excluded_from_metrics"]]
    completed = [row for row in eligible if row["termination_reason"] == "completed"]
    selection = [row for row in eligible if row["selection"]["eligible"]]
    return {
        "completion": (len(completed), len(eligible)),
        "selection": (sum(row["selection"]["correct"] for row in selection), len(selection)),
        "consistency": (sum(row["verifier"]["passed"] for row in completed), len(completed)),
        "reflections": (sum(row["reflection_calls"] for row in eligible), len(eligible)),
        "llm": (sum(row["llm_calls"] for row in eligible), len(eligible)),
        "http": (sum(row["http_attempts"] for row in eligible), len(eligible)),
    }


def ratio(pair, percent=True):
    numerator, denominator = pair
    if not denominator:
        return f"N/A ({numerator}/{denominator})"
    return (f"{100 * numerator / denominator:.2f}%" if percent else f"{numerator / denominator:.3f}회") + f" ({numerator}/{denominator})"


def error_counts(rows, kind):
    occurred = resolved = events = resolved_events = 0
    for row in rows:
        reflections = [item for item in row["reflections"] if item["kind"] == kind]
        detected = [*reflections, *row["selection"]["violations"], *row["verifier"]["violations"]]
        found = any(item["kind"] == kind for item in detected)
        found |= kind == "schema_mismatch" and any(turn.get("error", {}).get("schema_mismatch") for turn in row["turns"])
        occurred += bool(found)
        resolved += bool(reflections and all(item["resolved"] for item in reflections))
        events += len(reflections)
        resolved_events += sum(item["resolved"] for item in reflections)
    return f"{occurred}/{resolved}건; 이벤트 {events}/{resolved_events}건"


def load_rows(directory, cases, repeat):
    rows = []
    expected = {(case["case_id"], mode, number) for case in cases
                for mode in ("off", "on") for number in range(1, repeat + 1)}
    seen, fingerprints = set(), {}
    for mode in ("off", "on"):
        for line in (directory / f"{mode}.jsonl").read_text().splitlines():
            row = json.loads(line)
            key = (row["case_id"], row["mode"], row["repeat"])
            if row["mode"] != mode or key in seen or key not in expected:
                raise ValueError(f"Unexpected/duplicate observation: {key}")
            seen.add(key)
            fingerprint = (row["fixture_sha256"], row["input_sha256"])
            prior = fingerprints.setdefault(row["case_id"], fingerprint)
            if prior != fingerprint:
                raise ValueError(f"Unpaired fixture/input: {row['case_id']}")
            rows.append(row)
    if seen != expected:
        raise ValueError(f"Missing {len(expected - seen)} observations")
    return rows


def render(rows, cases, probes=(), previous=(), probe_prefix=""):
    modes = {mode: [row for row in rows if row["mode"] == mode] for mode in ("off", "on")}
    values = {mode: metrics(items) for mode, items in modes.items()}
    versions = {row["verifier"].get("version", "v1_substring") for row in rows}
    if len(versions) != 1:
        raise ValueError("Cannot compare observations graded with different verifier versions")
    rule = ("v1은 매수/매도 등을 문맥 구분 없이 부분문자열로 검사하여 수급·호가 사실도 위반으로 잡습니다."
            if versions == {"v1_substring"} else
            "v2는 매수/매도/보유의 지시·권유 어미와 가격 방향 예측 패턴을 검사합니다. "
            "매도벽·매수세·순매수·순매도·매수/매도 우위·기관 매수·외국인 매도 같은 수급 사실은 허용합니다.")
    lines = ["# 에이전트 자기 성찰 전후 실측 요약", "",
             f"측정 기간: {min(row['started_at'] for row in rows)} ~ {max(row['started_at'] for row in rows)} (UTC 시작 시각).",
             f"모델: `{rows[0]['model']}`, reasoning effort: `{rows[0]['reasoning_effort']}`. "
             f"케이스 {len(cases)}개, 모드별 {len(modes['off'])}회입니다.", "",
             "## 비교 지표", "", "| 지표 | off | on | 산식 |", "|---|---:|---:|---|"]
    definitions = [
        ("completion", "태스크 완료율", "Agent 종료 completed ÷ 현재가 실패 제외 전체", True),
        ("selection", "도구 선택 정확도", "허용 접수번호 호출 또는 정당한 미호출 ÷ 공시 목록이 있는 실행", True),
        ("consistency", "응답 일관성", "채택된 모델 서술이 검증기 4항목 모두 통과 ÷ 완료 건수", True),
        ("reflections", "평균 재시행 횟수", "성찰로 인한 추가 LLM 호출 합계 ÷ 현재가 실패 제외 전체", False),
        ("llm", "평균 LLM 호출 수", "실패 포함 Provider 호출 시도 합계 ÷ 현재가 실패 제외 전체", False),
        ("http", "평균 HTTP 요청 수", "SDK 내부 재시도 포함 HTTP 요청 합계 ÷ 현재가 실패 제외 전체", False),
    ]
    for key, name, formula, percent in definitions:
        lines.append(f"| {name} | {ratio(values['off'][key], percent)} | {ratio(values['on'][key], percent)} | {formula} |")
    lines += ["", "현재가 실패는 모든 비교 지표 분모에서 제외합니다. 도구 선택은 요청 전체 이력을 검사하며, "
              "목록 밖·중복·허용 외 도구·인자 오류는 이후 복구되어도 선택 정확도 실패입니다. "
              "정당한 미호출은 Tool 요청 없이 모델 서술이 채택된 경우입니다. "
              "API 오류로 응답을 받지 못한 미호출은 성공으로 세지 않습니다. "
              "서술 미채택 상태의 미호출도 분모에 남고 분자에는 포함하지 않으므로 이 지표는 "
              "도구 선택 오류 외에 서술 검증 실패의 영향도 받습니다. 실제 선택 오류 건수는 아래 유형별 표와 구분합니다.", "",
              "종료 사유와 narrative는 Workflow의 partial_completed 변환·투자 성향 후처리 전 AgentResult입니다. "
              "off는 런타임 입력과 동작을 유지합니다. 두 모드의 외부 검증에는 동일하게 기본/상세 조회 실패와 성공한 상세 근거를 포함합니다. "
              "검증 항목은 목록 밖 14자리 접수번호, 실패한 소스의 제한 문구, 추천·예측 금지어, 투자 성향/null 일치입니다.", "",
              rule + " "
              "목표주가 금지는 유지하며 인용·부정 문맥은 구분하지 않습니다. "
              "응답 일관성은 규칙 통과율이며, 위반 전체가 실제 투자 지시나 환각을 뜻하지는 않습니다.", "",
              "LLM 호출 수는 Provider 진입 횟수입니다. 기존 off의 runtime_llm_calls는 실패 시도를 누락할 수 있으므로 원본에 따로 남깁니다. "
              "성찰 이벤트 수와 실제 추가 호출 reflection_calls를 구분합니다.", "",
              "## 오류 유형별 발생·해소", "", "| 유형 | off 발생/해소 | on 발생/해소 |", "|---|---|---|"]
    for kind in ("tool_selection_error", "parameter_error", "schema_mismatch", "hallucination", "inconsistency"):
        lines.append(f"| {kind} | {error_counts(modes['off'], kind)} | {error_counts(modes['on'], kind)} |")
    lines += ["", "건수는 해당 유형을 감지한 실행 수와 런타임이 해당 유형의 성찰 이벤트를 모두 해소한 실행 수입니다. "
              "동일 실행의 중복 감지는 한 건으로 셉니다. 이벤트 열은 원본 ReflectionEvent 수입니다. "
              "off의 외부 검증 감지는 성찰 이벤트나 해소로 간주하지 않습니다.", "",
              "## 시험 데이터 구성", "", "| 유형 | 케이스 수 | 확인 항목 |", "|---|---:|---|"]
    for kind, count in Counter(case["kind"] for case in cases).items():
        check = next(case["check"] for case in cases if case["kind"] == kind)
        lines.append(f"| {kind} | {count} | {check} |")
    lines += ["", "## 관측 범위와 실행 종료", "", "| 모드 | 종료 사유 | 실행 수 |", "|---|---|---:|"]
    for mode, items in modes.items():
        for reason, count in sorted(Counter(row["termination_reason"] for row in items).items()):
            lines.append(f"| {mode} | {reason} | {count} |")
    for mode, items in modes.items():
        candidates = [row for row in items if row["kind"] == "detail_failure"]
        hit = sum(any(call["injected_failure"] for call in row["detail_calls"]) for row in candidates)
        lines += ["", f"{mode}: 상세 실패 주입이 실제 실행된 횟수는 {hit}/{len(candidates)}입니다. "
                  "미호출 실행에서는 상세 실패 복구를 검증하지 못했습니다.", ""]
        errors = Counter((turn["error"]["type"], turn["error"].get("status_code"))
                         for row in items for turn in row["turns"] if "error" in turn)
        lines.append(f"{mode}: Provider 오류 유형/HTTP 상태별 건수는 `{dict(errors)}`입니다.")
        incomplete = sum(row["termination_reason"] == "TimeoutError" for row in items)
        lines.append(f"{mode}: Workflow 시간 초과는 {incomplete}회입니다. 시간 초과에서도 실제 상세/성찰 호출 수는 "
                     "관측값을 유지합니다. runtime_result_available=false인 중도 종료에서는 Runtime 성찰 이벤트와 "
                     "최종 서술을 회수하지 못하므로 위 이벤트 발생 집계가 전체 감지를 포함하지 않을 수 있습니다.")
    lines += ["", "기본 조회는 실제 MCP 4개의 DataCollector 결과 20종목을 저장한 픽스처이며, "
              "측정 시 기본/상세 MCP 호출과 Backend 이벤트 전송은 없습니다. Agent만 실제 OpenAI를 호출합니다. "
              "프로필은 사용자 식별자가 없는 시험 입력입니다. 유혹 접수번호는 시험용 주입값입니다.", "",
              "off와 on의 모델 생성 시각이 다르므로 모델 비결정성과 시간 차이는 통제되지 않습니다. "
              "픽스처·주입 입력 SHA-256의 일치를 검사하며, 30일 공시 필터는 실행 시각을 사용하므로 "
              "나중에 재실행할 때에는 원본 context·receipt_numbers도 비교해야 합니다. "
              "현재 검증기는 지정된 규칙 4항목을 검사하며 모든 사실 정확성을 증명하지 않습니다."]
    if probes:
        lines += ["", "## 별도 Provider 후속 호출 실측", "",
                  "30개 Agent 시험에서 선택적 상세 호출이 발생하지 않아도 후속 요청 경로를 확인하기 위해 "
                  "tools=[]로 실제 첫 응답을 받은 뒤 사용자 재검토 메시지를 next_turn에 전달했습니다. "
                  "두 모드 모두 store=False를 유지하며 위 Agent 지표 분모에는 포함하지 않습니다.", "",
                  "| 모드 | 결과 | Provider 호출 수 | 원본 |", "|---|---|---:|---|"]
        for probe in probes:
            mode = probe["mode"]
            lines.append(f"| {mode} | {probe['outcome']} | {probe['llm_calls']} | "
                         f"[continuation_{mode}.jsonl]({probe_prefix}continuation_{mode}.jsonl) |")
        for probe in probes:
            for turn in probe["turns"]:
                if "error" in turn:
                    message = turn["error"]["message"].replace("\n", " ")
                    lines.append(f"\n{probe['mode']} {turn['method']} 실제 오류: `{message}`\n")
    if previous:
        lines += ["", "## 검증기 개선 이력 v1 → v2", "",
                  "v1의 원본 전체는 [round1/summary.md](round1/summary.md)에 보존했습니다. "
                  "v2 off는 round1/off.jsonl의 저장된 narrative/context만 오프라인 재채점했습니다. "
                  "재채점의 LLM·HTTP 호출은 0회이며, off 행의 호출 수·시각·소요 시간은 v1 관측값 그대로입니다. "
                  "verifier와 rescoring 메타데이터만 갱신하고 원본 파일 SHA-256을 기록했습니다. "
                  "v2 on은 같은 30케이스를 2회씩 새로 실행했습니다. 별도 Provider 후속 호출은 v1 측정입니다.", "",
                  "| 규칙/측정 | 완료율 | 도구 선택 정확도 | 응답 일관성 | 평균 성찰 호출 | 성찰 소진 |",
                  "|---|---:|---:|---:|---:|---:|"]
        for version, observations in (("v1 부분문자열", previous), ("v2 패턴", rows)):
            for mode in ("off", "on"):
                subset = [row for row in observations if row["mode"] == mode]
                measured = metrics(subset)
                cells = [ratio(measured[key], key != "reflections")
                         for key in ("completion", "selection", "consistency", "reflections")]
                exhausted = sum(row["termination_reason"] == "reflection_exhausted" for row in subset)
                lines.append(f"| {version} {mode} | " + " | ".join(cells) + f" | {exhausted}회 |")
        lines += ["", "off의 일관성 변화는 같은 응답을 새 규칙으로 평가한 결과이며 모델 개선이 아닙니다. "
                  "on의 변화에는 규칙 변경과 모델 비결정성이 함께 반영됩니다.", ""]
        for label, observations in (("v1 off", previous), ("v2 off", rows)):
            violations = [row["verifier"]["violations"] for row in observations if row["mode"] == "off"]
            prohibited = sum(any("추천·예측" in item["detail"] for item in items) for items in violations)
            limitation = sum(any("조회 실패 제한" in item["detail"] for item in items) for items in violations)
            lines.append(f"{label}: 금지어 검출 {prohibited}건, 소스 실패 제한 누락 {limitation}건입니다. "
                         "두 유형은 같은 실행에서 중복될 수 있습니다.")
    lines += ["", "## 케이스별 원본 결과", "", "| case_id | mode | 반복 | Agent 종료 | 검증 | LLM | 성찰 호출 | 상세 호출 | ms |",
              "|---|---|---:|---|---|---:|---:|---:|---:|"]
    for row in sorted(rows, key=lambda row: (row["case_id"], row["mode"], row["repeat"])):
        passed = row["verifier"]["passed"]
        lines.append(f"| {row['case_id']} | {row['mode']} | {row['repeat']} | {row['termination_reason']} | "
                     f"{'제외' if passed is None else '통과' if passed else '위반'} | {row['llm_calls']} | "
                     f"{row['reflection_calls']} | {row['tool_calls']} | {row['duration_ms']} |")
    lines += ["", "원본: [off.jsonl](off.jsonl), [on.jsonl](on.jsonl). "
              "각 행에 전체 서술, 정규화된 모델 응답·요청 도구·피드백·오류, 검증 결과, 입력 컨텍스트, "
              "기본 조회 실패, 실행 이벤트 및 픽스처 해시를 보존합니다. "
              "인증 헤더·키·내부 추론·암호화 reasoning 데이터는 저장하지 않습니다.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "results")
    parser.add_argument("--repeat", type=int, default=2)
    args = parser.parse_args()
    cases = json.loads((HERE / "cases.json").read_text())
    rows = load_rows(args.out, cases, args.repeat)
    archive = args.out / "round1"
    previous = load_rows(archive, cases, args.repeat) if archive.is_dir() else []
    probe_dir = archive if previous else args.out
    probes = [json.loads(path.read_text()) for path in sorted(probe_dir.glob("continuation_*.jsonl"))]
    (args.out / "summary.md").write_text(render(rows, cases, probes, previous, "round1/" if previous else ""))
    interrupted = args.out / "interrupted_on.jsonl"
    if interrupted.exists():
        with (args.out / "summary.md").open("a") as stream:
            stream.write(f"\n중단된 초안 규칙의 완료 관측 {len(interrupted.read_text().splitlines())}행은 "
                         "[interrupted_on.jsonl](interrupted_on.jsonl)에 보존하며 모든 지표에서 제외합니다. "
                         "중단 사유와 미완결 실행은 [하네스 안내](../README.md#검증기-v2-재측정)에 기록했습니다.\n")
    print(f"report rows={len(rows)} paired_inputs=ok summary={args.out / 'summary.md'}")
