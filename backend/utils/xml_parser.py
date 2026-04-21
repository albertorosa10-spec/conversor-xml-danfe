"""
xml_parser.py
Detecção e extração de metadados de documentos fiscais brasileiros.

Suporta:
  - NF-e  versão 4.00 (nfeProc ou NFe isolada)
  - CT-e  versão 3.00 (cteProc ou CTe isolado)

Regras de detecção (em ordem de prioridade):
  1. Namespace do elemento raiz
  2. Tag <infNFe> ou <infCte> em qualquer profundidade
  3. Exceção DocumentoNaoReconhecido se nenhum padrão bater
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional
from lxml import etree


# ---------------------------------------------------------------------------
# Namespaces oficiais SEFAZ
# ---------------------------------------------------------------------------
NFE_NS = "http://www.portalfiscal.inf.br/nfe"
CTE_NS = "http://www.portalfiscal.inf.br/cte"

VERSAO_MINIMA_NFE = "4.00"
VERSAO_MINIMA_CTE = "3.00"


# ---------------------------------------------------------------------------
# Erros customizados
# ---------------------------------------------------------------------------
class DocumentoNaoReconhecido(ValueError):
    """XML não é NF-e nem CT-e ou está em formato não suportado."""


class VersaoNaoSuportada(ValueError):
    """Versão do documento abaixo do mínimo exigido."""


class XMLInvalido(ValueError):
    """Arquivo XML malformado ou corrompido."""


# ---------------------------------------------------------------------------
# Dataclass de saída
# ---------------------------------------------------------------------------
@dataclass
class DocumentoFiscal:
    tipo: Literal["NF-e", "CT-e"]
    chave: Optional[str]            # 44 dígitos
    numero: Optional[str]           # nNF ou nCT
    serie: Optional[str]
    emitente_nome: Optional[str]
    emitente_cnpj: Optional[str]
    emitente_uf: Optional[str]
    destinatario_nome: Optional[str]
    destinatario_cnpj: Optional[str]  # pode ser CPF em NF-e
    destinatario_uf: Optional[str]
    valor_total: Optional[str]        # string formatada "1.234,56"
    data_emissao: Optional[str]       # "AAAA-MM-DD"
    tem_protocolo: bool               # False → renderizar com marca d'água
    versao: Optional[str]             # "4.00" / "3.00"
    xml_bytes: bytes = field(repr=False)

    @property
    def nome_pdf(self) -> str:
        """Nome canônico do PDF gerado — prioridade: chave > nNF+CNPJ > fallback."""
        if self.chave and len(self.chave) == 44:
            return f"{self.chave}.pdf"
        if self.numero and self.emitente_cnpj:
            cnpj_limpo = "".join(filter(str.isdigit, self.emitente_cnpj))
            return f"{self.numero}_{cnpj_limpo}.pdf"
        return "documento_sem_chave.pdf"


# ---------------------------------------------------------------------------
# Função pública principal
# ---------------------------------------------------------------------------
def parse_xml(xml_bytes: bytes, nome_arquivo: str = "") -> DocumentoFiscal:
    """
    Recebe os bytes brutos de um arquivo XML e retorna DocumentoFiscal.

    Lança:
        XMLInvalido              — se o XML estiver malformado
        DocumentoNaoReconhecido  — se não for NF-e nem CT-e
        VersaoNaoSuportada       — se a versão for anterior ao mínimo
    """
    if not xml_bytes or not xml_bytes.strip():
        raise XMLInvalido(f"Arquivo vazio: {nome_arquivo}")

    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        raise XMLInvalido(f"XML malformado ({nome_arquivo}): {exc}") from exc

    tipo = _detectar_tipo(root)

    if tipo == "NF-e":
        return _parse_nfe(root, xml_bytes)
    else:
        return _parse_cte(root, xml_bytes)


# ---------------------------------------------------------------------------
# Detecção de tipo
# ---------------------------------------------------------------------------
def _detectar_tipo(root: etree._Element) -> Literal["NF-e", "CT-e"]:
    """Inspeciona namespace e tags para identificar NF-e ou CT-e."""
    # 1. Namespace do root ou de qualquer ancestral mapeado
    todos_ns = set(root.nsmap.values())
    if NFE_NS in todos_ns:
        return "NF-e"
    if CTE_NS in todos_ns:
        return "CT-e"

    # 2. Fallback: busca tag característica em qualquer profundidade
    if root.find(f".//{{{NFE_NS}}}infNFe") is not None:
        return "NF-e"
    if root.find(f".//{{{CTE_NS}}}infCte") is not None:
        return "CT-e"

    # 3. Fallback adicional: tag local sem namespace (XMLs gerados por ERP legado)
    tags_locais = {el.tag.split("}")[-1] for el in root.iter()}
    if "infNFe" in tags_locais:
        return "NF-e"
    if "infCte" in tags_locais:
        return "CT-e"

    raise DocumentoNaoReconhecido(
        "XML não reconhecido como NF-e ou CT-e. "
        "Verifique se o arquivo é um documento fiscal válido."
    )


# ---------------------------------------------------------------------------
# Parser NF-e
# ---------------------------------------------------------------------------
def _parse_nfe(root: etree._Element, xml_bytes: bytes) -> DocumentoFiscal:
    ns = NFE_NS
    p = f"{{{ns}}}"

    inf = root.find(f".//{p}infNFe")
    if inf is None:
        raise DocumentoNaoReconhecido("Tag <infNFe> não encontrada no XML.")

    versao = inf.get("versao")
    _validar_versao(versao, VERSAO_MINIMA_NFE, "NF-e")

    chave_raw = inf.get("Id", "")
    chave = chave_raw.replace("NFe", "").strip() or None

    ide = inf.find(f"{p}ide")
    emit = inf.find(f"{p}emit")
    dest = inf.find(f"{p}dest")
    total = inf.find(f"{p}total/{p}ICMSTot")

    prot = root.find(f".//{p}protNFe")
    tem_protocolo = prot is not None

    return DocumentoFiscal(
        tipo="NF-e",
        chave=chave,
        numero=_txt(ide, f"{p}nNF"),
        serie=_txt(ide, f"{p}serie"),
        emitente_nome=_txt(emit, f"{p}xNome") or _txt(emit, f"{p}xFant"),
        emitente_cnpj=_txt(emit, f"{p}CNPJ"),
        emitente_uf=_txt(emit, f"{p}enderEmit/{p}UF"),
        destinatario_nome=_txt(dest, f"{p}xNome"),
        destinatario_cnpj=_txt(dest, f"{p}CNPJ") or _txt(dest, f"{p}CPF"),
        destinatario_uf=_txt(dest, f"{p}enderDest/{p}UF"),
        valor_total=_formatar_valor(_txt(total, f"{p}vNF")),
        data_emissao=_txt(ide, f"{p}dhEmi", default="")[:10] or None,
        tem_protocolo=tem_protocolo,
        versao=versao,
        xml_bytes=xml_bytes,
    )


# ---------------------------------------------------------------------------
# Parser CT-e
# ---------------------------------------------------------------------------
def _parse_cte(root: etree._Element, xml_bytes: bytes) -> DocumentoFiscal:
    ns = CTE_NS
    p = f"{{{ns}}}"

    inf = root.find(f".//{p}infCte")
    if inf is None:
        raise DocumentoNaoReconhecido("Tag <infCte> não encontrada no XML.")

    versao = inf.get("versao")
    _validar_versao(versao, VERSAO_MINIMA_CTE, "CT-e")

    chave_raw = inf.get("Id", "")
    chave = chave_raw.replace("CTe", "").strip() or None

    ide = inf.find(f"{p}ide")
    emit = inf.find(f"{p}emit")
    dest = inf.find(f"{p}dest")
    vPrest = inf.find(f"{p}vPrest")

    prot = root.find(f".//{p}protCTe")
    tem_protocolo = prot is not None

    return DocumentoFiscal(
        tipo="CT-e",
        chave=chave,
        numero=_txt(ide, f"{p}nCT"),
        serie=_txt(ide, f"{p}serie"),
        emitente_nome=_txt(emit, f"{p}xNome") or _txt(emit, f"{p}xFant"),
        emitente_cnpj=_txt(emit, f"{p}CNPJ"),
        emitente_uf=_txt(ide, f"{p}UFIni"),
        destinatario_nome=_txt(dest, f"{p}xNome"),
        destinatario_cnpj=_txt(dest, f"{p}CNPJ") or _txt(dest, f"{p}CPF"),
        destinatario_uf=_txt(ide, f"{p}UFFim"),
        valor_total=_formatar_valor(_txt(vPrest, f"{p}vTPrest")),
        data_emissao=_txt(ide, f"{p}dhEmi", default="")[:10] or None,
        tem_protocolo=tem_protocolo,
        versao=versao,
        xml_bytes=xml_bytes,
    )


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------
def _txt(element: Optional[etree._Element], path: str, default: str = "") -> Optional[str]:
    """Extrai texto de um subelemento com segurança. Retorna None se ausente."""
    if element is None:
        return None
    node = element.find(path)
    if node is None or node.text is None:
        return default or None
    return node.text.strip()


def _formatar_valor(raw: Optional[str]) -> Optional[str]:
    """Converte "1234.56" → "1.234,56" para exibição."""
    if not raw:
        return None
    try:
        valor = float(raw)
        inteiro, decimal = f"{valor:,.2f}".split(".")
        inteiro = inteiro.replace(",", ".")
        return f"{inteiro},{decimal}"
    except (ValueError, TypeError):
        return raw


def _validar_versao(versao: Optional[str], minima: str, tipo: str) -> None:
    """Lança VersaoNaoSuportada se versão for anterior ao mínimo."""
    if versao is None:
        return
    try:
        v_atual = tuple(int(x) for x in versao.split("."))
        v_min = tuple(int(x) for x in minima.split("."))
    except ValueError:
        return  # formato inesperado → ignora validação

    if v_atual < v_min:
        raise VersaoNaoSuportada(
            f"{tipo} versão {versao} não é suportada. "
            f"Versão mínima: {minima}."
        )
