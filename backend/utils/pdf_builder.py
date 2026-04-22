"""
pdf_builder.py
RenderizaÃ§Ã£o de PDFs DANFE (NF-e) e DACTe (CT-e).

EstratÃ©gia:
  1. Tentativa primÃ¡ria: erpbrasil.edoc.pdf (renderizaÃ§Ã£o fiel ao padrÃ£o SEFAZ)
  2. Fallback: reportlab (PDF simples com dados extraÃ­dos quando o erpbrasil falha)

O fallback cobre XMLs parciais (sem autorizaÃ§Ã£o SEFAZ) e renderiza
com marca d'Ã¡gua "SEM AUTORIZAÃ‡ÃƒO" quando tem_protocolo=False.
"""

import io
from typing import Optional

from utils.xml_parser import DocumentoFiscal


def gerar_pdf(doc: DocumentoFiscal) -> Optional[bytes]:
    """
    Tenta renderizar o PDF via erpbrasil. Em falha, usa reportlab.
    Retorna bytes do PDF ou None se ambas as tentativas falharem.
    Nunca lanÃ§a exceÃ§Ã£o.
    """
    # Tentativa 1: erpbrasil (renderizador primÃ¡rio â€” fiel ao layout SEFAZ)
    pdf = _tentar_erpbrasil(doc)
    if pdf:
        return pdf

    # Tentativa 2: reportlab (fallback â€” dados textuais simples)
    return _gerar_pdf_fallback(doc)


def _tentar_erpbrasil(doc: DocumentoFiscal) -> Optional[bytes]:
    try:
        from erpbrasil.edoc.pdf import ImprimirXml
        return ImprimirXml.imprimir(doc.xml_bytes)
    except Exception as e:
        import traceback, logging
        logging.error(f"[ERPBRASIL] ERRO: {type(e).__name__}: {e}")
        logging.error(traceback.format_exc())
        return None


def _gerar_pdf_fallback(doc: DocumentoFiscal) -> Optional[bytes]:
    """
    PDF simples via reportlab. Usado quando o erpbrasil nÃ£o consegue renderizar
    (XML sem protocolo, estrutura parcial, etc.).
    Inclui marca d'Ã¡gua "SEM AUTORIZAÃ‡ÃƒO" quando tem_protocolo=False.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        largura, altura = A4

        # CabeÃ§alho
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, altura - 2 * cm, f"DANFE â€” {doc.tipo}")
        c.setFont("Helvetica", 9)
        c.drawString(2 * cm, altura - 2.6 * cm, "(Gerado por fallback â€” layout simplificado)")

        # Linha separadora
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.line(2 * cm, altura - 3 * cm, largura - 2 * cm, altura - 3 * cm)

        # Dados extraÃ­dos
        c.setFont("Helvetica", 10)
        y = altura - 3.8 * cm
        linha_altura = 0.65 * cm

        campos = [
            ("Chave de acesso", doc.chave or "NÃ£o disponÃ­vel"),
            ("NÃºmero", doc.numero or "N/D"),
            ("SÃ©rie", doc.serie or "N/D"),
            ("Data de emissÃ£o", doc.data_emissao or "N/D"),
            ("Emitente", doc.emitente_nome or "N/D"),
            ("CNPJ Emitente", doc.emitente_cnpj or "N/D"),
            ("UF Emitente", doc.emitente_uf or "N/D"),
            ("DestinatÃ¡rio", doc.destinatario_nome or "N/D"),
            ("CNPJ/CPF Dest.", doc.destinatario_cnpj or "N/D"),
            ("UF DestinatÃ¡rio", doc.destinatario_uf or "N/D"),
            ("Valor total", f"R$ {doc.valor_total}" if doc.valor_total else "N/D"),
        ]

        for label, valor in campos:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(2 * cm, y, f"{label}:")
            c.setFont("Helvetica", 9)
            c.drawString(7 * cm, y, str(valor))
            y -= linha_altura

        # Marca d'Ã¡gua para documentos sem autorizaÃ§Ã£o SEFAZ
        if not doc.tem_protocolo:
            c.saveState()
            c.setFont("Helvetica-Bold", 36)
            c.setFillColorRGB(0.85, 0.1, 0.1)
            c.setFillAlpha(0.25)
            c.translate(largura / 2, altura / 2)
            c.rotate(45)
            c.drawCentredString(0, 0, "SEM AUTORIZAÃ‡ÃƒO SEFAZ")
            c.restoreState()

        c.save()
        return buf.getvalue()

    except Exception:
        return None

