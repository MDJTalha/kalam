import asyncio

from app.services.file_scanner import scan_file


def test_clamd_scans_clean_file(tmp_path) -> None:
    path = tmp_path / "clean.txt"
    path.write_text("Corporate LMS clean content validation", encoding="utf-8")

    clean, provider = asyncio.run(scan_file(path))

    assert clean is True
    assert provider == "clamd"
