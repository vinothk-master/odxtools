# SPDX-License-Identifier: MIT
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree

from .admindata import AdminData
from .audience import Audience
from .basicstructure import BasicStructure
from .dataobjectproperty import DataObjectProperty
from .dtcdop import DtcDop
from .element import IdentifiableElement
from .exceptions import odxassert, odxraise, odxrequire
from .functionalclass import FunctionalClass
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef, resolve_snref
from .odxtypes import AtomicOdxType, odxstr_to_bool
from .preconditionstateref import PreConditionStateRef
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .statetransitionref import StateTransitionRef
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .table import Table


@dataclass
class TableRow(IdentifiableElement):
    """This class represents a TABLE-ROW."""
    key_raw: str
    table_ref: OdxLinkRef

    # The spec mandates that either a structure or a non-complex DOP
    # must be referenced here, i.e., exactly one of the four
    # attributes below is not None
    dop_ref: Optional[OdxLinkRef]
    dop_snref: Optional[str]
    structure_ref: Optional[OdxLinkRef]
    structure_snref: Optional[str]

    sdgs: List[SpecialDataGroup]
    audience: Optional[Audience]
    functional_class_refs: List[OdxLinkRef]
    state_transition_refs: List[StateTransitionRef]
    pre_condition_state_refs: List[PreConditionStateRef]
    admin_data: Optional[AdminData]

    is_executable_raw: Optional[bool]
    semantic: Optional[str]
    is_mandatory_raw: Optional[bool]
    is_final_raw: Optional[bool]

    @property
    def functional_classes(self) -> NamedItemList[FunctionalClass]:
        return self._functional_classes

    @property
    def is_executable(self) -> bool:
        return self.is_executable_raw in (None, True)

    @property
    def is_mandatory(self) -> bool:
        return self.is_mandatory_raw is True

    @property
    def is_final(self) -> bool:
        return self.is_final_raw is True

    def __post_init__(self) -> None:
        self._structure: Optional[BasicStructure] = None
        self._dop: Optional[DataObjectProperty] = None

        n = sum([0 if x is None else 1 for x in (self.structure_ref, self.structure_snref)])
        odxassert(
            n <= 1,
            f"Table row {self.short_name}: The structure can either be defined using ODXLINK or SNREF but not both."
        )
        n = sum([0 if x is None else 1 for x in (self.dop_ref, self.dop_snref)])
        odxassert(
            n <= 1,
            f"Table row {self.short_name}: The dop can either be defined using ODXLINK or SNREF but not both."
        )

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> Any:
        raise RuntimeError(
            "Calling TableRow.from_et() is not allowed. Use TableRow.tablerow_from_et().")

    @staticmethod
    def tablerow_from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment], *,
                         table_ref: OdxLinkRef) -> "TableRow":
        """Reads a TABLE-ROW."""
        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))
        semantic = et_element.get("SEMANTIC")
        key_raw = odxrequire(et_element.findtext("KEY"))
        structure_ref = OdxLinkRef.from_et(et_element.find("STRUCTURE-REF"), doc_frags)
        structure_snref: Optional[str] = None
        if (structure_snref_elem := et_element.find("STRUCTURE-SNREF")) is not None:
            structure_snref = structure_snref_elem.attrib["SHORT-NAME"]
        dop_ref = OdxLinkRef.from_et(et_element.find("DATA-OBJECT-PROP-REF"), doc_frags)
        dop_snref: Optional[str] = None
        if (dop_snref_elem := et_element.find("DATA-OBJECT-PROP-SNREF")) is not None:
            dop_snref = dop_snref_elem.attrib["SHORT-NAME"]
        sdgs = [
            SpecialDataGroup.from_et(sdge, doc_frags) for sdge in et_element.iterfind("SDGS/SDG")
        ]

        audience = None
        if (audience_elem := et_element.find("AUDIENCE")) is not None:
            audience = Audience.from_et(audience_elem, doc_frags)

        functional_class_refs = [
            odxrequire(OdxLinkRef.from_et(el, doc_frags))
            for el in et_element.iterfind("FUNCT-CLASS-REFS/FUNCT-CLASS-REF")
        ]

        state_transition_refs = [
            StateTransitionRef.from_et(el, doc_frags)
            for el in et_element.iterfind("STATE-TRANSITION-REFS/STATE-TRANSITION-REF")
        ]

        pre_condition_state_refs = [
            PreConditionStateRef.from_et(el, doc_frags)
            for el in et_element.iterfind("PRE-CONDITION-STATE-REFS/PRE-CONDITION-STATE-REF")
        ]

        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)

        is_executable_raw = odxstr_to_bool(et_element.attrib.get("IS-EXECUTABLE"))
        semantic = et_element.attrib.get("SEMANTIC")
        is_mandatory_raw = odxstr_to_bool(et_element.attrib.get("IS-MANDATORY"))
        is_final_raw = odxstr_to_bool(et_element.attrib.get("IS-FINAL"))

        return TableRow(
            table_ref=table_ref,
            key_raw=key_raw,
            structure_ref=structure_ref,
            structure_snref=structure_snref,
            dop_ref=dop_ref,
            dop_snref=dop_snref,
            sdgs=sdgs,
            audience=audience,
            functional_class_refs=functional_class_refs,
            state_transition_refs=state_transition_refs,
            pre_condition_state_refs=pre_condition_state_refs,
            admin_data=admin_data,
            is_executable_raw=is_executable_raw,
            semantic=semantic,
            is_mandatory_raw=is_mandatory_raw,
            is_final_raw=is_final_raw,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for st_ref in self.state_transition_refs:
            result.update(st_ref._build_odxlinks())

        for pc_ref in self.pre_condition_state_refs:
            result.update(pc_ref._build_odxlinks())

        for sdg in self.sdgs:
            result.update(sdg._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        if self.structure_ref is not None:
            self._structure = odxlinks.resolve(self.structure_ref, BasicStructure)
        if self.dop_ref is not None:
            self._dop = odxlinks.resolve(self.dop_ref)
            if not isinstance(self._dop, (DataObjectProperty, DtcDop)):
                odxraise("The DOP-REF of TABLE-ROWs must reference a simple DOP!")

        if TYPE_CHECKING:
            self._table = odxlinks.resolve(self.table_ref, Table)
        else:
            self._table = odxlinks.resolve(self.table_ref)

        for st_ref in self.state_transition_refs:
            st_ref._resolve_odxlinks(odxlinks)

        for pc_ref in self.pre_condition_state_refs:
            pc_ref._resolve_odxlinks(odxlinks)

        for sdg in self.sdgs:
            sdg._resolve_odxlinks(odxlinks)

        self._functional_classes = NamedItemList(
            [odxlinks.resolve(fc_ref, FunctionalClass) for fc_ref in self.functional_class_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # convert the raw key into the proper internal
        # representation. note that we cannot do this earlier because
        # the table's ODXLINKs must be resolved and the order of
        # ODXLINK resolution between tables and table-rows is
        # undefined.
        key_dop = self.table.key_dop
        self._key: AtomicOdxType
        if key_dop is None:
            # if the table does not define a DOP for the keys: though
            # luck, expose the raw key string. This is probably a gap
            # in the ODX specification because table-rows must exhibit
            # a "KEY" sub-tag, while the KEY-DOP-REF is optional for
            # tables (and non-existant for table rows...)
            self._key = self.key_raw
        else:
            self._key = key_dop.physical_type.base_data_type.from_string(self.key_raw)

        ddd_spec = odxrequire(context.diag_layer).diag_data_dictionary_spec

        if self.structure_snref is not None:
            self._structure = resolve_snref(self.structure_snref, ddd_spec.structures,
                                            BasicStructure)
        if self.dop_snref is not None:
            self._dop = resolve_snref(self.dop_snref, ddd_spec.data_object_props,
                                      DataObjectProperty)

        for st_ref in self.state_transition_refs:
            st_ref._resolve_snrefs(context)

        for pc_ref in self.pre_condition_state_refs:
            pc_ref._resolve_snrefs(context)

        for sdg in self.sdgs:
            sdg._resolve_snrefs(context)

    @property
    def table(self) -> "Table":
        return self._table

    # the value of the key expressed in the type represented by the
    # referenced DOP
    @property
    def key(self) -> Optional[AtomicOdxType]:
        return self._key

    @property
    def structure(self) -> Optional[BasicStructure]:
        """The structure associated with this table row."""
        return self._structure

    @property
    def dop(self) -> Optional[DataObjectProperty]:
        """The data object property object resolved by dop_ref."""
        return self._dop

    def __reduce__(self) -> Tuple[Any, ...]:
        """This ensures that the object can be correctly reconstructed during unpickling."""
        state = self.__dict__.copy()
        return self.__class__, tuple([getattr(self, x.name) for x in fields(self)]), state
