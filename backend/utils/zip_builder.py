"""
zip_builder.py
Monta o arquivo ZIP final com PDFs individuais, _JUNTO.pdf e _RELATORIO.txt.
Todo processamento ocorre em memória (io.BytesIO) — zero escrita em disco.
"""

import io
import zipfile
from typing import List, Tuple

from pypdf import PdfReader, PdfWriter


def montar_zip(pdfs: List[Tuple[str, bytes]], relatorio: str) -> bytes:
    """
    Parâmetros:
        pdfs      — lista de (nome_arquivo.pdf, bytes_do_pdf)
        relatorio — conteúdo do _RELATORIO.txt como string

    Retorna bytes do ZIP contendo:
        - cada PDF individual nomeado pelo primeiro elemento da tupla
        - _JUNTO.pdf com todos os documentos concatenados na ordem recebida
        - _RELATORIO.txt com o sumário de processamento
    """
    zip_buffer = io.BytesIO()
    junto_writer = PdfWriter()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:

        for nome, pdf_bytes in pdfs:
            # Adiciona PDF individual
            zf.writestr(nome, pdf_bytes)

            # Acumula páginas para o _JUNTO.pdf
            try:
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    junto_writer.add_page(page)
            except Exception:
                # PDF corrompido ou vazio não deve travar a concatenação
                pass

        # Gera _JUNTO.pdf
        if len(junto_writer.pages) > 0:
            junto_buffer = io.BytesIO()
            junto_writer.write(junto_buffer)
            zf.writestr("_JUNTO.pdf", junto_buffer.getvalue())

        # Relatório de processamento (OBRIGATÓRIO)
        zf.writestr(
            "_RELATORIO.txt",
            relatorio.encode("utf-8") if isinstance(relatorio, str) else relatorio,
        )

    return zip_buffer.getvalue()
