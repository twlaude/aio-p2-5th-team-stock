"""색인된 정기보고서의 관련 원문 청크 검색 서비스."""

from .annual_report_service import AnnualReportService


class ReportSearchService(AnnualReportService):
    """미색인 정기보고서는 ``ingest_periodic_report``로 수집한 뒤 검색한다."""
