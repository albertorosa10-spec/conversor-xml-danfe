---
name: danfe-conversor
description: >
  Use esta skill para qualquer tarefa relacionada ao projeto DANFE Conversor Online:
  arquitetura, endpoints FastAPI, componentes React, lógica de conversão XML→PDF,
  tratamento de erros de NF-e/CT-e, deploy, ou decisões de stack. Inclui regras de
  negócio, estrutura de pastas, cronograma e dependências definidas no BRIEFING.
---

# DANFE Conversor — Skill do Agente

## Visão do Projeto

Plataforma web para converter XMLs de NF-e e CT-e em PDFs no padrão DANFE/DACTe.
Processa lotes de até 100 arquivos, retorna ZIP com PDFs individuais + `_JUNTO.pdf`.
**Stack:** FastAPI (Python 3.11) + React/TypeScript/Vite + Tailwind CSS.
**Deploy alvo:** Railway (backend) + Vercel (frontend).

---

## Stack e Dependências

### Backend (Python)
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9
lxml==5.2.2
erpbrasil.edoc.pdf==1.4.0
pypdf==4.2.0
reportlab==4.2.0
nfelib==2.0.0
slowapi==0.1.9          # rate limiting
```

### Frontend
```
react + typescript + vite
tailwindcss
```

---

## Estrutura de Pastas

```
danfe-conversor/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── conversor.py         # Orquestrador de conversão
│   ├── schemas.py           # Pydantic models
│   └── utils/
│       ├── xml_parser.py    # Parse + detecção NF-e/CT-e
│       ├── pdf_builder.py   # erpbrasil wrapper + fallback
│       └── zip_builder.py   # Montagem ZIP + _JUNTO.pdf
└── frontend/
    └── src/
        ├── components/
        │   ├── UploadZone.tsx
        │   ├── ResultTable.tsx
        │   ├── ProgressBar.tsx
        │   └── ErrorLog.tsx
        └── api/converter.ts
```

---

## Endpoint Principal

### `POST /converter`
- **Input:** `multipart/form-data`, campo `files[]`, até 100 arquivos `.xml`
- **Limites:** 2MB/arquivo, 50MB total, 5 req/min por IP
- **Output:** `application/zip` com:
  - `{chave_44digitos}.pdf` por documento convertido
  - `_JUNTO.pdf` (todos os PDFs concatenados)
  - `_RELATORIO.txt` (sumário: total processado, erros, tempo)
- **Headers de resposta:**
  - `X-Total-Processed`, `X-Total-Errors`, `X-Processing-Time`

---

## Regras de Negócio Críticas

### Detecção de tipo de documento
```python
# NF-e: namespace contém "nfe.fazenda.gov.br", versão 4.00
# CT-e: namespace contém "cte.fazenda.gov.br", versão 3.00
# Fallback: busca por tag <infNFe> ou <infCte>
```

### Nomeação dos PDFs no ZIP
```
1º: chave de acesso (44 dígitos) → {chave}.pdf
2º: nNF + CNPJ emitente          → {nnf}_{cnpj}.pdf
3º: nome original sem extensão   → {nome_original}.pdf
```

### Tratamento de erros por arquivo (nunca interrompe o lote)
| Situação | Comportamento |
|---|---|
| XML malformado | Skip + entrada no relatório de erros |
| NF-e sem `protNFe` (sem autorização) | Renderiza com marca d'água "SEM AUTORIZAÇÃO" |
| Versão < 4.00 (NF-e) ou < 3.00 (CT-e) | Skip + aviso de versão não suportada |
| Arquivo > 2MB | Skip + aviso de tamanho |
| Tipo MIME inválido | Rejeitar antes do processamento (400) |

### Segurança (OBRIGATÓRIO)
- **Zero persistência em disco**: usar exclusivamente `io.BytesIO`
- **Validar MIME**: aceitar somente `text/xml` e `application/xml`
- **Rate limiting**: `slowapi` — 5 req/min por IP

---

## Template de Código — Backend

### `utils/xml_parser.py`
```python
from lxml import etree
from typing import Literal, Optional
from dataclasses import dataclass

NFE_NS = "http://www.portalfiscal.inf.br/nfe"
CTE_NS = "http://www.portalfiscal.inf.br/cte"

@dataclass
class DocumentoFiscal:
    tipo: Literal["NF-e", "CT-e"]
    chave: Optional[str]
    numero: Optional[str]
    emitente_nome: Optional[str]
    emitente_cnpj: Optional[str]
    destinatario_nome: Optional[str]
    destinatario_cnpj: Optional[str]
    valor_total: Optional[str]
    tem_protocolo: bool
    xml_bytes: bytes

def parse_xml(xml_bytes: bytes) -> DocumentoFiscal:
    root = etree.fromstring(xml_bytes)
    ns = root.nsmap.get(None, "")
    
    if NFE_NS in ns or root.find(f".//{{{NFE_NS}}}infNFe") is not None:
        return _parse_nfe(root, xml_bytes)
    elif CTE_NS in ns or root.find(f".//{{{CTE_NS}}}infCte") is not None:
        return _parse_cte(root, xml_bytes)
    else:
        raise ValueError("Documento não reconhecido como NF-e ou CT-e")
```

### `utils/pdf_builder.py`
```python
import io
from erpbrasil.edoc.pdf import danfe as danfe_lib
from .xml_parser import DocumentoFiscal

def gerar_pdf(doc: DocumentoFiscal) -> bytes:
    """Retorna bytes do PDF. Nunca lança exceção — retorna None em falha."""
    try:
        if doc.tipo == "NF-e":
            pdf = danfe_lib.danfe(doc.xml_bytes)
        else:
            from erpbrasil.edoc.pdf import dacte
            pdf = dacte.dacte(doc.xml_bytes)
        return pdf.output()
    except Exception as e:
        # Fallback: tentar com reportlab básico
        return _gerar_pdf_fallback(doc, str(e))

def _gerar_pdf_fallback(doc: DocumentoFiscal, erro: str) -> bytes | None:
    """Gera PDF simples com dados disponíveis quando erpbrasil falha."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 800, f"DANFE — {doc.tipo}")
        c.setFont("Helvetica", 10)
        c.drawString(50, 780, f"Chave: {doc.chave or 'N/D'}")
        c.drawString(50, 765, f"Emitente: {doc.emitente_nome or 'N/D'}")
        c.drawString(50, 750, f"Destinatário: {doc.destinatario_nome or 'N/D'}")
        c.drawString(50, 735, f"Número: {doc.numero or 'N/D'}")
        c.drawString(50, 720, f"Valor: R$ {doc.valor_total or 'N/D'}")
        if not doc.tem_protocolo:
            c.setFont("Helvetica-Bold", 20)
            c.setFillColorRGB(0.8, 0, 0)
            c.drawString(100, 400, "SEM AUTORIZAÇÃO SEFAZ")
        c.save()
        return buf.getvalue()
    except Exception:
        return None
```

### `utils/zip_builder.py`
```python
import io
import zipfile
from pypdf import PdfWriter
from typing import list

def montar_zip(pdfs: list[tuple[str, bytes]], relatorio: str) -> bytes:
    """
    pdfs: lista de (nome_arquivo.pdf, bytes_do_pdf)
    Retorna bytes do ZIP final.
    """
    zip_buffer = io.BytesIO()
    junto_writer = PdfWriter()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, pdf_bytes in pdfs:
            zf.writestr(nome, pdf_bytes)
            # Adiciona ao _JUNTO.pdf
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    junto_writer.add_page(page)
            except Exception:
                pass
        
        # Gera _JUNTO.pdf
        junto_buffer = io.BytesIO()
        junto_writer.write(junto_buffer)
        zf.writestr("_JUNTO.pdf", junto_buffer.getvalue())
        
        # Relatório
        zf.writestr("_RELATORIO.txt", relatorio)
    
    return zip_buffer.getvalue()
```

### `main.py` (FastAPI)
```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
import time

from utils.xml_parser import parse_xml
from utils.pdf_builder import gerar_pdf
from utils.zip_builder import montar_zip

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="DANFE Conversor API")
app.state.limiter = limiter

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST"])

MAX_FILES = 100
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

@app.post("/converter")
@limiter.limit("5/minute")
async def converter(files: list[UploadFile] = File(...)):
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Máximo {MAX_FILES} arquivos por requisição")
    
    start = time.time()
    pdfs = []
    erros = []
    
    for file in files:
        try:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                erros.append(f"{file.filename}: arquivo muito grande (máx 2MB)")
                continue
            
            doc = parse_xml(content)
            pdf_bytes = gerar_pdf(doc)
            
            if pdf_bytes:
                nome_pdf = f"{doc.chave or file.filename.replace('.xml', '')}.pdf"
                pdfs.append((nome_pdf, pdf_bytes))
            else:
                erros.append(f"{file.filename}: falha na renderização do PDF")
        
        except ValueError as e:
            erros.append(f"{file.filename}: {str(e)}")
        except Exception as e:
            erros.append(f"{file.filename}: erro inesperado — {str(e)}")
    
    if not pdfs:
        raise HTTPException(422, "Nenhum arquivo pôde ser convertido")
    
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
            "X-Processing-Time": f"{elapsed}s"
        }
    )

def _gerar_relatorio(pdfs, erros, elapsed):
    linhas = [
        "=== RELATÓRIO DE PROCESSAMENTO ===",
        f"Total convertido: {len(pdfs)}",
        f"Total com erro: {len(erros)}",
        f"Tempo: {elapsed}s",
        ""
    ]
    if erros:
        linhas.append("=== ERROS ===")
        linhas.extend(erros)
    return "\n".join(linhas)
```

---

## Frontend — Componentes Chave

### `UploadZone.tsx`
- Drag-and-drop nativo ou clique para abrir seletor
- Aceitar apenas `.xml`
- Mostrar lista de arquivos selecionados com nome e tamanho
- Botão "Processar" dispara `POST /converter`

### `ResultTable.tsx`
Colunas: `Tipo | Chave de Acesso | Emitente | Destinatário | Número | Valor`

### `ErrorLog.tsx`
Exibe lista de erros por arquivo com ícone de aviso, inline abaixo da tabela.

### `api/converter.ts`
```typescript
export async function converterXmls(files: File[]): Promise<{
  zipBlob: Blob;
  totalProcessado: number;
  totalErros: number;
  tempoProcessamento: string;
}> {
  const formData = new FormData();
  files.forEach(f => formData.append("files", f));
  
  const response = await fetch(`${API_BASE}/converter`, {
    method: "POST",
    body: formData,
  });
  
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail);
  }
  
  return {
    zipBlob: await response.blob(),
    totalProcessado: parseInt(response.headers.get("X-Total-Processed") || "0"),
    totalErros: parseInt(response.headers.get("X-Total-Errors") || "0"),
    tempoProcessamento: response.headers.get("X-Processing-Time") || "N/D",
  };
}
```

---

## Deploy

### Railway (Backend)
```
# Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Vercel (Frontend)
```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/" }]
}
```

### Variáveis de ambiente
```
CORS_ORIGINS=https://seu-frontend.vercel.app
MAX_FILES=100
RATE_LIMIT=5/minute
```

---

## Checklist de Qualidade Pré-Deploy

- [ ] Testar com NF-e 4.00 com protocolo SEFAZ
- [ ] Testar com NF-e 4.00 SEM protocolo (marca d'água)
- [ ] Testar com CT-e 3.00
- [ ] Testar lote de 100 XMLs mistos
- [ ] Testar XML malformado (não deve travar o lote)
- [ ] Verificar que nenhum arquivo é gravado em disco
- [ ] Verificar CORS em produção
- [ ] Verificar rate limiting (6ª req deve retornar 429)
- [ ] Verificar que _JUNTO.pdf contém todos os documentos
- [ ] Verificar _RELATORIO.txt com erros discriminados

---

## Referências

- FSist (referência de produto): https://www.fsist.com.br/converter-xml-nfe-para-danfe
- erpbrasil.edoc docs: https://erpbrasil.github.io/erpbrasil.edoc.pdf/
- Portal SEFAZ schema NF-e 4.00: https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=BMPFMBoln3w=
- FastAPI docs: https://fastapi.tiangolo.com
