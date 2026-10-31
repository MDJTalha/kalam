import asyncio

from app.services.file_scanner import scan_file


def test_clamd_scans_clean_file(tmp_path) -> None:
    path = tmp_path / "clean.txt"
    path.write_text("Corporate LMS clean content validation", encoding="utf-8")

    clean, provider = asyncio.run(scan_file(path))

    assert clean is True
    assert provider == "clamd"


def test_content_validation_rejects_mismatched_pdf(tmp_path) -> None:
    from app.services.file_scanner import validate_file_content_type

    path = tmp_path / "not-a-pdf.pdf"
    path.write_text("plain text", encoding="utf-8")

    try:
        validate_file_content_type(path, "application/pdf")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 415
    else:
        raise AssertionError("mismatched PDF content should be rejected")


def test_content_validation_accepts_pdf_signature(tmp_path) -> None:
    from app.services.file_scanner import validate_file_content_type

    path = tmp_path / "valid.pdf"
    path.write_bytes(b"%PDF-1.7\\n")

    validate_file_content_type(path, "application/pdf")
