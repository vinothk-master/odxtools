# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass
from typing import Dict, Any

from .parameters import read_parameter_from_odx
from .utils import read_description_from_odx
from .odxlink import OdxLinkId, OdxDocFragment
from .structures import BasicStructure
from .globals import logger

@dataclass
class EnvironmentData(BasicStructure):
    """This class represents Environment Data that describes the circumstances in which the error occurred."""

    def __init__(
        self,
        id,
        short_name,
        parameters,
        long_name=None,
        description=None,
    ):
        super().__init__(
            id, short_name, parameters, long_name=long_name, description=description
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = {}
        odxlinks.update({self.id: self})
        return odxlinks

    def __repr__(self) -> str:
        return (
            f"EnvironmentData('{self.short_name}', "
            + ", ".join([f"id='{self.id}'", f"parameters='{self.parameters}'"])
            + ")"
        )


def read_env_data_from_odx(et_element, doc_frag):
    """Reads Environment Data from Diag Layer."""
    id = OdxLinkId.from_et(et_element, doc_frag)
    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.find("LONG-NAME")
    if long_name is not None:
        long_name = long_name.text
    description = read_description_from_odx(et_element.find("DESC"))
    parameters = [
        read_parameter_from_odx(et_parameter, doc_frag)
        for et_parameter in et_element.iterfind("PARAMS/PARAM")
    ]
    logger.debug("Parsing ENV-DATA " + short_name)

    env_data = EnvironmentData(
        id,
        short_name,
        parameters=parameters,
        long_name=long_name,
        description=description,
    )

    return env_data
