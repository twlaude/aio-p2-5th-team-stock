"""OpenDART 원본 응답 스키마.

이 파일의 필드명은 OpenDART 응답과 동일하다. MCP Tool 공개 응답용 모델은
``search.py``에 두며, 서비스 계층이 이 원본 값을 공개 계약 형태로 변환한다.
"""

from typing import Literal, NotRequired, TypedDict


DartStatus = Literal["000", "010", "011", "012", "013", "014", "020", "021", "100", "800", "900", "901"]
DartPeriodicReportType = Literal["annual", "semi_annual", "quarterly"]


class DartResponse(TypedDict):
    """모든 JSON 응답이 공통으로 갖는 상태와 메시지."""

    status: DartStatus | str
    message: str


class DartCorpCode(TypedDict):
    """``corpCode.xml`` ZIP 안의 ``<list>`` 한 건."""

    corp_code: str
    corp_name: str
    corp_eng_name: str
    stock_code: str
    modify_date: str


class DartDisclosureRecord(TypedDict):
    """``list.json``의 공시 목록 한 건."""

    corp_code: str
    corp_name: str
    stock_code: str
    corp_cls: str
    report_nm: str
    rcept_no: str
    flr_nm: str
    rcept_dt: str
    rm: str


class DartDisclosureListResponse(DartResponse, total=False):
    """``list.json`` 원본 응답.

    ``status == '013'``일 때 ``list``와 페이지 메타데이터는 존재하지 않을 수 있다.
    """

    page_no: NotRequired[int]
    page_count: NotRequired[int]
    total_count: NotRequired[int]
    total_page: NotRequired[int]
    list: NotRequired[list[DartDisclosureRecord]]


class DartDocument(TypedDict):
    """``document.xml`` ZIP을 해제한 뒤 파서에 넘기는 내부 값."""

    receipt_number: str
    xml: str
