import pytest
from utils.xml_parser import (
    parse_xml, DocumentoNaoReconhecido, VersaoNaoSuportada, XMLInvalido
)

NFE_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe versao="4.00" Id="NFe12345678901234567890123456789012345678901234">
      <ide>
        <nNF>12345</nNF>
        <serie>1</serie>
        <dhEmi>2023-10-01T10:00:00-03:00</dhEmi>
      </ide>
      <emit>
        <xNome>Empresa Teste LTDA</xNome>
        <CNPJ>12345678000199</CNPJ>
        <enderEmit><UF>SP</UF></enderEmit>
      </emit>
      <dest>
        <xNome>Cliente Teste</xNome>
        <CPF>12345678901</CPF>
        <enderDest><UF>RJ</UF></enderDest>
      </dest>
      <total>
        <ICMSTot><vNF>1500.50</vNF></ICMSTot>
      </total>
    </infNFe>
  </NFe>
  <protNFe>
    <infProt><nProt>123456789</nProt></infProt>
  </protNFe>
</nfeProc>
'''

CTE_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<cteProc versao="3.00" xmlns="http://www.portalfiscal.inf.br/cte">
  <CTe>
    <infCte versao="3.00" Id="CTe98765432109876543210987654321098765432101234">
      <ide>
        <nCT>54321</nCT>
        <serie>2</serie>
        <dhEmi>2023-10-02T10:00:00-03:00</dhEmi>
        <UFIni>MG</UFIni>
        <UFFim>SP</UFFim>
      </ide>
      <emit>
        <xNome>Transp Teste</xNome>
        <CNPJ>98765432000199</CNPJ>
      </emit>
      <dest>
        <xNome>Destinatario CTe</xNome>
        <CNPJ>11122233344455</CNPJ>
      </dest>
      <vPrest><vTPrest>350.75</vTPrest></vPrest>
    </infCte>
  </CTe>
  <protCTe>
    <infProt><nProt>987654321</nProt></infProt>
  </protCTe>
</cteProc>
'''

# --- NF-e Tests (13) ---
def test_nfe_tipo():
    doc = parse_xml(NFE_XML)
    assert doc.tipo == "NF-e"

def test_nfe_chave():
    doc = parse_xml(NFE_XML)
    assert doc.chave == "12345678901234567890123456789012345678901234"

def test_nfe_numero():
    doc = parse_xml(NFE_XML)
    assert doc.numero == "12345"

def test_nfe_serie():
    doc = parse_xml(NFE_XML)
    assert doc.serie == "1"

def test_nfe_emitente_nome():
    doc = parse_xml(NFE_XML)
    assert doc.emitente_nome == "Empresa Teste LTDA"

def test_nfe_emitente_cnpj():
    doc = parse_xml(NFE_XML)
    assert doc.emitente_cnpj == "12345678000199"

def test_nfe_emitente_uf():
    doc = parse_xml(NFE_XML)
    assert doc.emitente_uf == "SP"

def test_nfe_destinatario_nome():
    doc = parse_xml(NFE_XML)
    assert doc.destinatario_nome == "Cliente Teste"

def test_nfe_destinatario_cnpj_cpf():
    doc = parse_xml(NFE_XML)
    assert doc.destinatario_cnpj == "12345678901"

def test_nfe_destinatario_uf():
    doc = parse_xml(NFE_XML)
    assert doc.destinatario_uf == "RJ"

def test_nfe_valor_total():
    doc = parse_xml(NFE_XML)
    assert doc.valor_total == "1.500,50"

def test_nfe_data_emissao():
    doc = parse_xml(NFE_XML)
    assert doc.data_emissao == "2023-10-01"

def test_nfe_tem_protocolo():
    doc = parse_xml(NFE_XML)
    assert doc.tem_protocolo is True


# --- CT-e Tests (13) ---
def test_cte_tipo():
    doc = parse_xml(CTE_XML)
    assert doc.tipo == "CT-e"

def test_cte_chave():
    doc = parse_xml(CTE_XML)
    assert doc.chave == "98765432109876543210987654321098765432101234"

def test_cte_numero():
    doc = parse_xml(CTE_XML)
    assert doc.numero == "54321"

def test_cte_serie():
    doc = parse_xml(CTE_XML)
    assert doc.serie == "2"

def test_cte_emitente_nome():
    doc = parse_xml(CTE_XML)
    assert doc.emitente_nome == "Transp Teste"

def test_cte_emitente_cnpj():
    doc = parse_xml(CTE_XML)
    assert doc.emitente_cnpj == "98765432000199"

def test_cte_emitente_uf():
    doc = parse_xml(CTE_XML)
    assert doc.emitente_uf == "MG"

def test_cte_destinatario_nome():
    doc = parse_xml(CTE_XML)
    assert doc.destinatario_nome == "Destinatario CTe"

def test_cte_destinatario_cnpj():
    doc = parse_xml(CTE_XML)
    assert doc.destinatario_cnpj == "11122233344455"

def test_cte_destinatario_uf():
    doc = parse_xml(CTE_XML)
    assert doc.destinatario_uf == "SP"

def test_cte_valor_total():
    doc = parse_xml(CTE_XML)
    assert doc.valor_total == "350,75"

def test_cte_data_emissao():
    doc = parse_xml(CTE_XML)
    assert doc.data_emissao == "2023-10-02"

def test_cte_tem_protocolo():
    doc = parse_xml(CTE_XML)
    assert doc.tem_protocolo is True


# --- Errors and Edge Cases (13) ---
def test_xml_vazio():
    with pytest.raises(XMLInvalido):
        parse_xml(b"")

def test_xml_malformado():
    with pytest.raises(XMLInvalido):
        parse_xml(b"<nfeProc>broken")

def test_xml_nao_reconhecido():
    with pytest.raises(DocumentoNaoReconhecido):
        parse_xml(b"<root><alguma_tag/></root>")

def test_nfe_sem_infnfe():
    with pytest.raises(DocumentoNaoReconhecido):
        parse_xml(b'<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"></nfeProc>')

def test_cte_sem_infcte():
    with pytest.raises(DocumentoNaoReconhecido):
        parse_xml(b'<cteProc xmlns="http://www.portalfiscal.inf.br/cte"></cteProc>')

def test_nfe_versao_nao_suportada():
    old = NFE_XML.replace(b'versao="4.00"', b'versao="3.10"')
    with pytest.raises(VersaoNaoSuportada):
        parse_xml(old)

def test_cte_versao_nao_suportada():
    old = CTE_XML.replace(b'versao="3.00"', b'versao="2.00"')
    with pytest.raises(VersaoNaoSuportada):
        parse_xml(old)

def test_nfe_sem_protocolo():
    no_prot = NFE_XML.replace(b'<protNFe>', b'<prot>').replace(b'</protNFe>', b'</prot>')
    doc = parse_xml(no_prot)
    assert doc.tem_protocolo is False

def test_cte_sem_protocolo():
    no_prot = CTE_XML.replace(b'<protCTe>', b'<prot>').replace(b'</protCTe>', b'</prot>')
    doc = parse_xml(no_prot)
    assert doc.tem_protocolo is False

def test_nfe_com_cnpj_destinatario():
    cnpj_xml = NFE_XML.replace(b'<CPF>12345678901</CPF>', b'<CNPJ>12345678000199</CNPJ>')
    doc = parse_xml(cnpj_xml)
    assert doc.destinatario_cnpj == "12345678000199"

def test_nome_pdf_com_chave():
    doc = parse_xml(NFE_XML)
    assert doc.nome_pdf == "12345678901234567890123456789012345678901234.pdf"

def test_nome_pdf_fallback_nNF_cnpj():
    no_chave = NFE_XML.replace(b'Id="NFe12345678901234567890123456789012345678901234"', b'')
    doc = parse_xml(no_chave)
    assert doc.nome_pdf == "12345_12345678000199.pdf"

def test_nome_pdf_fallback_sem_nada():
    no_chave_no_ide = NFE_XML.replace(b'Id="NFe12345678901234567890123456789012345678901234"', b'').replace(b'<nNF>12345</nNF>', b'')
    doc = parse_xml(no_chave_no_ide)
    assert doc.nome_pdf == "documento_sem_chave.pdf"

