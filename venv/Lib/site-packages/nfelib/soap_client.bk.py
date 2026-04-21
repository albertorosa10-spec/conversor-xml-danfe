from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import NamedTuple
from typing import Optional
from typing import Type

from enum import EnumMeta

from requests import Response
from requests import Session

import logging

from xsdata.formats.dataclass.transports import Transport, DefaultTransport
from xsdata.formats.dataclass.client import Config, Client

from erpbrasil.assinatura.certificado import ArquivoCertificado


import inspect
from enum import EnumMeta
from nfelib.nfe.bindings import v4_0 as nfe_bindings


_logger = logging.Logger(__name__)


def match_response_class(name):
    """
    the challenge with the Fiscal SOAP format is the return type
    is a wildcard in the WSDL, so here we help xsdata to figure
    out which dataclass to use to parse the resultMsg content
    based on the XML qname of the element.
    """

    def visit_nested_classes(cls, classes):
        classes.add(cls)
        for attr in dir(cls):
            nested = getattr(cls, attr)
            if (
                not inspect.isclass(nested)
                or nested.__name__ == "type"
                or nested.__name__.endswith(".Meta")
            ):
                continue
            visit_nested_classes(nested, classes)

    # TODO make it work with cte, mdfe...
    # TODO memoize?
    for _klass_name, klass in nfe_bindings.__dict__.items():
        if isinstance(klass, type) and type(klass) != EnumMeta:
#            classes = set()
#            visit_nested_classes(klass, classes)
#            for cls in classes:
            cls = klass
            print(klass)
            if True:
                if (
                    hasattr(cls, "Meta")
                    and hasattr(cls.Meta, "name")
                    and cls.Meta.name == name
                    or cls.__name__ == name
                ):
                    return cls


@dataclass
class SoapClient(Client):
    certificate: "Any" = (
        object()
    )

    @classmethod
    def from_service(cls, obj: Type, certificate: Any, **kwargs: str) -> "Client":
        """Instantiate client from a service definition."""
        client = cls(config=Config.from_service(obj, **kwargs))
        client.certificate = certificate
        return client

    def send(self, obj: Any, headers: Optional[Dict] = None, string_content: str = "") -> Any:
        with ArquivoCertificado(self.certificate, "r") as (key, cert):
            self.transport.session.cert = (key, cert)
            self.transport.session.verify = False  # TODO improve (param)

            data = self.prepare_payload(obj)
            if string_content:
                data = data.replace("<NFe>PLACEHOLDER</NFe>", string_content)

            headers = self.prepare_headers(headers or {})
            response = self.transport.post(self.config.location, data=data, headers=headers)
            print("RESP", response)
            res = self.parser.from_bytes(response, self.config.output)

            _logger.debug(res)

            # the challenge with the Fiscal SOAP format is the return type
            # is a wildcard in the WSDL, so here we help xsdata to figure
            # out which dataclass to use to parse the resultMsg content
            # based on the XML qname of the element.
            anyElement = res.body.nfeResultMsg.content[0]  # TODO safe guard
            return_type_name = anyElement.qname.split("}")[
                1
            ]  # it comes with a {namespace} prefix
            return_type = match_response_class(return_type_name)
            anyElement.qname = None
            anyElement.text = None
            # TODO deal with children or attributes (and remove their qname and text) ?

            from xsdata.formats.dataclass.serializers.config import SerializerConfig
            from xsdata.formats.dataclass.parsers import XmlParser
            from xsdata.formats.dataclass.serializers import XmlSerializer

            # TODO remove pretty_print and print
            serializer = XmlSerializer(config=SerializerConfig(pretty_print=True))
            xml = serializer.render(
                obj=anyElement, ns_map={None: "http://www.portalfiscal.inf.br/nfe"}
            )
            print(xml)
            parser = XmlParser()
            return parser.from_string(xml, return_type)

    def prepare_payload(self, obj: Any) -> Any:
        """
        Prepare and serialize payload to be sent.

        :raises ClientValueError: If the config input type doesn't match the given
            input.
        """
        if isinstance(obj, Dict):
            obj = self.dict_converter.convert(obj, self.config.input)

        if False: #TODO not isinstance(obj, self.config.input):
            raise ClientValueError(
                f"Invalid input service type, "
                f"expected `{self.config.input.__name__}` "
                f"got `{type(obj).__name__}`"
            )

        result = self.serializer.render(
            obj=obj,
            ns_map={None: "http://www.portalfiscal.inf.br/nfe"}
        )
#        if self.config.encoding:
#            return result.encode(self.config.encoding)
#        print(result)
        return result
