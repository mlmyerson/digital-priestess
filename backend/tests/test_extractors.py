from app.ingestion.extractors import extract_text


def test_extract_text_reads_html_as_visible_text(tmp_path) -> None:
    html_path = tmp_path / "symbol.html"
    html_path.write_text("<html><body><h1>Moon</h1><p>Dreams and tides.</p></body></html>", encoding="utf-8")

    extracted = extract_text(html_path)

    assert extracted.extractor == "html"
    assert "Moon" in extracted.text
    assert "Dreams and tides." in extracted.text