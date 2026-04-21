from dataclasses import dataclass, field
from typing import List, Optional

__NAMESPACE__ = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"


@dataclass
class NfeDistDfeInteresse:
    class Meta:
        name = "nfeDistDFeInteresse"
        namespace = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"

    nfeDadosMsg: Optional["NfeDistDfeInteresse.NfeDadosMsg"] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )

    @dataclass
    class NfeDadosMsg:
        content: List[object] = field(
            default_factory=list,
            metadata={
                "type": "Wildcard",
                "namespace": "##any",
                "mixed": True,
            }
        )


@dataclass
class NfeDistDfeInteresseResponse:
    class Meta:
        name = "nfeDistDFeInteresseResponse"
        namespace = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"

    nfeDistDFeInteresseResult: Optional["NfeDistDfeInteresseResponse.NfeDistDfeInteresseResult"] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )

    @dataclass
    class NfeDistDfeInteresseResult:
        content: List[object] = field(
            default_factory=list,
            metadata={
                "type": "Wildcard",
                "namespace": "##any",
                "mixed": True,
            }
        )
