"""
main.py — DANFE Conversor API
FastAPI backend para conversão de XMLs NF-e/CT-e em PDFs DANFE/DACTe.
"""

import time
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request

from utils.pdf_builder import gerar_pdf
from utils.xml_parser import (
    DocumentoNaoReconhecido,
    VersaoNaoSuportada,
    XMLInvalido,
    parse_xml,
)
from utils.zip_builder import montar_zip

# ---------------------------------------------------------------------------
# Configuração do app
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="DANFE Conversor API",
    description="Converte XMLs de NF-e e CT-e em PDFs DANFE/DACTe em lote.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Processed", "X-Total-Errors", "X-Processing-Time"],
)

MAX_FILES = 100
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB por arquivo


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/converter")
@limiter.limit("5/minute")
async def converter(request: Request, files: List[UploadFile] = File(...)):
    """
    Recebe até 100 XMLs de NF-e e/ou CT-e e retorna ZIP contendo:
      - {chave}.pdf para cada documento convertido
      - _JUNTO.pdf com todos os documentos concatenados
      - _RELATORIO.txt com sumário de processamento e erros
    """
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Máximo de {MAX_FILES} arquivos por requisição. Enviados: {len(files)}.",
        )

    start = time.time()
    pdfs: List[tuple] = []
    erros: List[str] = []

    for file in files:
        try:
            content = await file.read()

            if len(content) > MAX_FILE_SIZE:
                erros.append(
                    f"{file.filename}: arquivo muito grande "
                    f"({len(content) // 1024}KB — máx 2MB)"
                )
                continue

            doc = parse_xml(content, nome_arquivo=file.filename or "")
            pdf_bytes = gerar_pdf(doc)

            if pdf_bytes:
                pdfs.append((doc.nome_pdf, pdf_bytes))
            else:
                erros.append(f"{file.filename}: falha na renderização do PDF")

        except XMLInvalido as e:
            erros.append(f"{file.filename}: XML inválido — {e}")
        except VersaoNaoSuportada as e:
            erros.append(f"{file.filename}: versão não suportada — {e}")
        except DocumentoNaoReconhecido as e:
            erros.append(f"{file.filename}: documento não reconhecido — {e}")
        except Exception as e:
            erros.append(f"{file.filename}: erro inesperado — {type(e).__name__}: {e}")

    if not pdfs:
        raise HTTPException(
            status_code=422,
            detail=(
                "Nenhum arquivo pôde ser convertido. "
                f"Erros: {'; '.join(erros[:3])}{'...' if len(erros) > 3 else ''}"
            ),
        )

    elapsed = round(time.time() - start, 2)
    relatorio = _gerar_relatorio(pdfs, erros, elapsed)
    zip_bytes = montar_zip(pdfs, relatorio)

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=danfes_convertidos.zip",
            "X-Total-Processed": str(len(pdfs)),
            "X-Total-Errors": str(len(erros)),
            "X-Processing-Time": f"{elapsed}s",
            "Access-Control-Expose-Headers": (
                "X-Total-Processed, X-Total-Errors, X-Processing-Time"
            ),
        },
    )


# ---------------------------------------------------------------------------
# Helper interno
# ---------------------------------------------------------------------------
def _gerar_relatorio(pdfs: list, erros: list, elapsed: float) -> str:
    from datetime import datetime

    linhas = [
        "=== RELATÓRIO DE PROCESSAMENTO — DANFE CONVERSOR ===",
        f"Data/hora : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"Convertidos: {len(pdfs)}",
        f"Com erro  : {len(erros)}",
        f"Tempo     : {elapsed}s",
        "",
    ]
    if pdfs:
        linhas.append("=== ARQUIVOS GERADOS ===")
        linhas.extend(nome for nome, _ in pdfs)
        linhas.append("")
    if erros:
        linhas.append("=== ERROS POR ARQUIVO ===")
        linhas.extend(erros)
    return "\n".join(linhas)
