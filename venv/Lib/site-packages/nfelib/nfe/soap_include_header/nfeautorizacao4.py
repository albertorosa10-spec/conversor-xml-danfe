from dataclasses import dataclass, field
from typing import Dict, List, Optional

__NAMESPACE__ = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"


@dataclass
class NfeDadosMsg:
    class Meta:
        name = "nfeDadosMsg"
        namespace = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"

    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        }
    )


@dataclass
class NfeDadosMsgZip:
    class Meta:
        name = "nfeDadosMsgZip"
        namespace = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"

    value: str = field(
        default="",
        metadata={
            "required": True,
        }
    )


@dataclass
class NfeMonitoria:
    class Meta:
        name = "nfeMonitoria"
        namespace = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"

    nomeServidor: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    dhServidor: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    any_attributes: Dict[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##any",
        }
    )


@dataclass
class NfeResultMsg:
    class Meta:
        name = "nfeResultMsg"
        nillable = True
        namespace = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"

    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        }
    )
