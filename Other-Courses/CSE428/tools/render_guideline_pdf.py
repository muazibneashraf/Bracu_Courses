from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    pdf_path = repo_root / "CSE428 Spring 26 Project Guidelines (1).pdf"
    out_dir = repo_root / "guideline_pages"
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        pix = page.get_pixmap(dpi=200)
        out_path = out_dir / f"page_{page_index + 1}.png"
        pix.save(out_path)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
