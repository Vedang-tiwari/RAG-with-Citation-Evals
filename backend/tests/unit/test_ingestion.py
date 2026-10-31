import pytest
from backend.app.ingestion.cleaner import TextCleaner
from backend.app.ingestion.chunker import ConfigurableChunker
from backend.app.ingestion.parser import DocumentParser

def test_text_cleaner():
    raw_text = "This  is   a   test \t with \n\n\n excessive newlines and “smart quotes”."
    cleaned = TextCleaner.clean(raw_text)
    assert '“' not in cleaned
    assert '"smart quotes"' in cleaned
    assert "\n\n\n" not in cleaned
    assert "This is a test with" in cleaned

def test_configurable_chunker():
    chunker = ConfigurableChunker(chunk_size=10, chunk_overlap=3)
    pages = [
        (1, "Word1 Word2 Word3 Word4 Word5 Word6 Word7 Word8 Word9 Word10 Word11 Word12 Word13 Word14 Word15"),
        (2, "Page2Word1 Page2Word2 Page2Word3 Page2Word4 Page2Word5")
    ]
    chunks = chunker.split_text_into_chunks(doc_id="test_doc", pages_content=pages)

    assert len(chunks) >= 2
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["id"] == "test_doc_c0"
    assert "Word1" in chunks[0]["content"]

    # Check page tracking
    page_2_chunks = [c for c in chunks if c["page_number"] == 2]
    assert len(page_2_chunks) > 0
    assert "Page2Word1" in page_2_chunks[0]["content"]

def test_txt_parser():
    test_file = "data/sample_documents/rag_overview.txt"
    pages = DocumentParser.parse_file(test_file, "txt")
    assert len(pages) == 1
    assert pages[0][0] == 1
    assert "Retrieval-Augmented Generation" in pages[0][1]

