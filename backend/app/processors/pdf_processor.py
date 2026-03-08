"""
PDF Processor - Extract pages and text from PDF
"""
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from pathlib import Path
from typing import List, Dict


class PDFProcessor:
    def __init__(self):
        self.dpi = 150  # Resolution for page images

    def process(self, pdf_path: str, output_dir: str) -> Dict:
        """
        Process PDF and extract pages as images + text

        Returns:
            Dict with pages data: {
                "num_pages": int,
                "pages": [
                    {
                        "page_num": int,
                        "image_path": str,
                        "text": str
                    },
                    ...
                ]
            }
        """
        output_path = Path(output_dir)
        pages_dir = output_path / "pages"
        pages_dir.mkdir(exist_ok=True)

        # Open PDF
        doc = fitz.open(pdf_path)
        num_pages = len(doc)

        pages_data = []

        # Process each page
        for page_num in range(num_pages):
            page = doc[page_num]

            # Extract text
            text = page.get_text()

            # Save page as image using pdf2image
            image_path = pages_dir / f"page_{page_num + 1}.png"

            # Convert single page
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=page_num + 1,
                last_page=page_num + 1
            )

            if images:
                images[0].save(image_path, 'PNG')

            pages_data.append({
                "page_num": page_num + 1,
                "image_path": str(image_path),
                "text": text.strip()
            })

            print(f"Processed page {page_num + 1}/{num_pages}")

        doc.close()

        return {
            "num_pages": num_pages,
            "pages": pages_data
        }
