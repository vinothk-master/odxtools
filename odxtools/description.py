from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxlink import OdxDocFragment


@dataclass
class ExternalDoc:
    description: Optional[str]
    href: str

    @staticmethod
    def from_et(et_element: Optional[ElementTree.Element],
                doc_frags: List[OdxDocFragment]) -> Optional["ExternalDoc"]:
        if et_element is None:
            return None

        description = et_element.text
        href = odxrequire(et_element.get("HREF"))

        return ExternalDoc(description=description, href=href)


@dataclass
class Description:
    text: str
    external_docs: List[ExternalDoc]

    text_identifier: Optional[str]

    @staticmethod
    def from_et(et_element: Optional[ElementTree.Element],
                doc_frags: List[OdxDocFragment]) -> Optional["Description"]:
        if et_element is None:
            return None

        # Extract the contents of the tag as a XHTML string.
        raw_string = et_element.text or ""
        for e in et_element:
            if e.tag == "EXTERNAL-DOCS":
                break
            raw_string += ElementTree.tostring(e, encoding="unicode")

        # remove white spaces at the beginning and at the end of all
        # extracted lines
        stripped_lines = [x.strip() for x in raw_string.split("\n")]

        text = "\n".join(stripped_lines).strip()

        external_docs = \
            [
                odxrequire(ExternalDoc.from_et(ed, doc_frags)) for ed in et_element.iterfind("EXTERNAL-DOCS/EXTERNAL-DOC")
            ]

        text_identifier = et_element.attrib.get("TI")

        return Description(text=text, text_identifier=text_identifier, external_docs=external_docs)

    @staticmethod
    def from_string(text: str) -> "Description":
        return Description(text=text, external_docs=[], text_identifier=None)

    def __str__(self) -> str:
        return self.text
