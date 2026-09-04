from io import BytesIO
from zipfile import ZipFile

import httpx

from app.clients.dart import DartClient
from app.core.config import DisclosureConfig


def test_document_zip_prefers_receipt_number_xml_over_first_attachment() -> None:
    receipt_number = "20260318001394"
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr(f"{receipt_number}_00760.xml", "<AUDIT>첨부문서</AUDIT>")
        archive.writestr(f"{receipt_number}.xml", "<DOCUMENT>사업보고서 본문</DOCUMENT>")

    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, content=payload.getvalue())
    )
    client = DartClient(
        DisclosureConfig(dart_api_key="x" * 40), transport=transport
    )
    try:
        document = client.get_document(receipt_number)
    finally:
        client.close()

    assert document["xml"] == "<DOCUMENT>사업보고서 본문</DOCUMENT>"
