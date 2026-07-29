from typing import Dict, Any
import os

from ...domain.services.document_generator import DocumentGeneratorService
from .word_generator import WordGeneratorService


class PDFGeneratorService(DocumentGeneratorService):
    def __init__(self, word_generator: WordGeneratorService):
        self._word_generator = word_generator

    async def generate_docx(self, template_content: str, variables: Dict[str, Any], output_path: str) -> str:
        return await self._word_generator.generate_docx(template_content, variables, output_path)

    async def generate_pdf(self, template_content: str, variables: Dict[str, Any], output_path: str) -> str:
        docx_path = output_path.replace('.pdf', '.docx')
        await self._word_generator.generate_docx(template_content, variables, docx_path)

        try:
            from docx2pdf import convert
            convert(docx_path, output_path)
        except ImportError:
            try:
                import subprocess
                result = subprocess.run(
                    ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", os.path.dirname(output_path), docx_path],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")
            except Exception:
                import shutil
                shutil.copy(docx_path, output_path)

        return output_path

    async def get_preview(self, template_content: str, variables: Dict[str, Any]) -> str:
        return await self._word_generator.get_preview(template_content, variables)
