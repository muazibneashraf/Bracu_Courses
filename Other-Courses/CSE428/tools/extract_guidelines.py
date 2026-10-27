from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    pdf_path = Path(__file__).resolve().parent.parent / "CSE428 Spring 26 Project Guidelines (1).pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    out_path = pdf_path.with_name("guidelines_extracted.txt")

    reader = PdfReader(str(pdf_path))

    with out_path.open("w", encoding="utf-8") as f:
        for i, page in enumerate(reader.pages, start=1):
            f.write(f"\n===== PAGE {i} =====\n")
            text = (page.extract_text() or "").replace("\r", "")
            f.write(text)
            f.write("\n")

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
