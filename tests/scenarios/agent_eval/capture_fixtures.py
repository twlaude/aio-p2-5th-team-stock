"""Capture public MCP data through the production DataCollector, without event delivery."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "mcp_client"))

from app.clients.base import MCPClientError
from app.core.config import Settings
from app.schemas.analysis import CompanyRef
from app.services.analysis_builder import calculate_evidence_level, calculate_market_temperature
from app.services.progress_reporter import ProgressReporter
from app.workflows.factory import build_workflow


def settings_for(mode="off"):
    return Settings(
        _env_file=ROOT / "mcp_client/.env", llm_provider="openai",
        openai_model="gpt-5.6-luna", agent_reflection_enabled=mode == "on",
        backend_event_url="", backend_internal_token="",
        **{f"{name}_mcp_url": f"http://localhost:{port}/mcp"
           for name, port in zip(("price", "news", "disclosure", "community"), range(8020, 8024))},
    )


def clean(value, secrets=()):
    """Keep public source content; remove credentials and individual account identifiers."""
    if isinstance(value, dict):
        private = {"api_key", "access_token", "authorization", "password", "email",
                   "username", "user_id", "author", "author_id", "nickname", "phone"}
        return {key: clean(item, secrets) for key, item in value.items() if key.lower() not in private}
    if isinstance(value, list):
        return [clean(item, secrets) for item in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        value = re.sub(r"\bsk-[A-Za-z0-9_-]{12,}", "[REDACTED]", value)
        return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", value)
    return value


def required_receipts(fixture, cases):
    from run_eval import FixtureCollector
    receipts = list(fixture["receipt_numbers"])
    for case in cases:
        if case["stock_code"] != fixture["company"]["stock_code"]:
            continue
        data = FixtureCollector(fixture, case).data
        temperature = calculate_market_temperature(data)
        evidence = calculate_evidence_level(data, temperature.data_coverage)
        from app.workflows.analysis import AnalysisWorkflow
        receipts.extend(AnalysisWorkflow._receipt_numbers(data, evidence))
    return list(dict.fromkeys(receipts))


async def capture(out, complete_details=False):
    settings = settings_for()
    workflow = build_workflow(settings)
    out.mkdir(parents=True, exist_ok=True)
    companies = json.loads((ROOT / "shared/supported_companies.json").read_text())["companies"]
    cases = json.loads((HERE / "cases.json").read_text())
    for index, item in enumerate(companies, 1):
        company = CompanyRef(company_name=item["company_name"], stock_code=item["stock_code"])
        reporter = ProgressReporter(settings, f"test-capture-{company.stock_code}", "test-capture")
        started = datetime.now(timezone.utc).isoformat()
        target = out / f"{company.stock_code}.json"
        if complete_details:
            payload = json.loads(target.read_text())
        else:
            data = await workflow.collector.collect(company, reporter)
            temperature = calculate_market_temperature(data)
            evidence = calculate_evidence_level(data, temperature.data_coverage)
            payload = {"company": company.model_dump(), "captured_at": started,
                       "data": data.model_dump(), "details": {}, "events": reporter.events,
                       "receipt_numbers": workflow._receipt_numbers(data, evidence)}
        receipts = required_receipts(payload, cases)
        details = payload["details"]
        for receipt in receipts:
            if receipt in details:
                continue
            try:
                details[receipt] = {"data": await workflow.collector.disclosure.get_disclosure_detail(receipt)}
            except MCPClientError as error:
                details[receipt] = {"error": {"service": error.service, "code": error.code,
                                            "message": error.message, "retryable": error.retryable}}
        payload.update(capture_finished_at=datetime.now(timezone.utc).isoformat(),
                       privacy="Credential and individual account fields/emails are removed.")
        payload = clean(payload, (settings.openai_api_key,))
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        print(f"[TEST] capture {index}/{len(companies)} {company.stock_code} "
              f"price={payload['data']['price'].get('status')} "
              f"failures={len(payload['data']['failures'])} details={len(details)}", flush=True)
    await workflow.agent.provider._client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "fixtures")
    parser.add_argument("--complete-details", action="store_true", help="Only capture missing case-specific detail candidates")
    args = parser.parse_args()
    asyncio.run(capture(args.out, args.complete_details))
