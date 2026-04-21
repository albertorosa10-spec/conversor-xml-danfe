from dataclasses import dataclass, field
from typing import List

__NAMESPACE__ = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4"


@dataclass
class NfeDadosMsg:
    class Meta:
        name = "nfeDadosMsg"
        namespace = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4"

    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        }
    )


@dataclass
class NfeResultMsg:
    class Meta:
        name = "nfeResultMsg"
        nillable = True
        namespace = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4"

    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        }
    )
