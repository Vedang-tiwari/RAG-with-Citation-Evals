import os
from typing import List, Tuple

class DocumentParser:
    @staticmethod
    def parse_pdf(file_path: str) -> List[Tuple[int, str]]:
        """
        Parses a PDF file page by page using PyMuPDF (fitz).
        Returns a list of (page_number, text).
        """
        import fitz  # PyMuPDF
        pages = []
        doc = fitz.open(file_path)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            text = page.get_text("text")
            if text and text.strip():
                pages.append((page_idx + 1, text.strip()))
        doc.close()
        return pages

    @staticmethod
    def parse_docx(file_path: str) -> List[Tuple[int, str]]:
        """
        Parses a DOCX file using python-docx.
        Returns a list of (page_or_section_number, text).
        """
        import docx
        doc = docx.Document(file_path)
        paragraphs = []
        for p in doc.paragraphs:
            if p.text and p.text.strip():
                paragraphs.append(p.text.strip())
        
        # Also parse tables if present
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                if row_text:
                    paragraphs.append(row_text)

        full_text = "\n\n".join(paragraphs)
        if not full_text:
            return []
        # Return as single logical page / section 1
        return [(1, full_text)]

    @staticmethod
    def parse_txt(file_path: str) -> List[Tuple[int, str]]:
        """
        Parses a plain text file.
        Returns [(1, text)].
        """
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if not text.strip():
            return []
        return [(1, text.strip())]

    @classmethod
    def parse_file(cls, file_path: str, file_type: str) -> List[Tuple[int, str]]:
        ext = file_type.lower().replace(".", "")
        if ext == "pdf":
            return cls.parse_pdf(file_path)
        elif ext in ["docx", "doc"]:
            return cls.parse_docx(file_path)
        elif ext in ["txt", "md", "csv", "json"]:
            return cls.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

