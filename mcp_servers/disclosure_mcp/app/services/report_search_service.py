"""색인된 정기보고서의 관련 원문 청크 검색 서비스."""

from .annual_report_service import AnnualReportService


class ReportSearchService(AnnualReportService):
    """정기보고서 검색을 제공하는 서비스.

    색인되지 않은 보고서는 검색 전에 ``ingest_periodic_report``로 수집한다.
    """
