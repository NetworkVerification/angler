#!/usr/bin/env python3
"""
Base utilities for parsing the Batfish AST.
"""
from enum import Enum
from typing import Callable, Optional
from ipaddress import IPv4Address, IPv4Interface
from dataclasses import dataclass, fields, is_dataclass
from serialize import Serialize, Field
from collections.abc import Iterable
import bast.btypes as types


def parse_bf_clsname(qualified: str) -> str:
    """
    Given a string representing a class in batfish's namespace,
    return the class name.
    """
    _, last = qualified.rsplit(sep=".", maxsplit=1)
    # if a $ is found, name will contain the string following it
    # if $ is not found, name will contain the original string
    try:
        return last[last.rindex("$") + 1 :]
    except ValueError:
        return last


class Variant(Enum):
    """
    A wrapper around the standard Python enum which we use for specifying varieties of
    terms, e.g. the different types of boolean expression.
    Each element of a Variant has an associated type accessed using `as_class`.
    """

    def as_class(self) -> type:
        """
        Return a type associated with each element of the enum.
        """
        raise NotImplementedError(
            f"Variant {self.__class__} must implement 'as_class'."
        )

    @classmethod
    def parse_class(cls, s: str) -> type:
        """
        Return the type associated with a given string parsed into this variant.
        """
        return cls(parse_bf_clsname(s)).as_class()


@dataclass
class ASTNode(Serialize):
    def visit(self, f: Callable) -> None:
        # recursively descend through the fields of the ASTNodes
        if is_dataclass(self):
            f(self)
            for field in fields(self):
                field_node = getattr(self, field.name)
                if isinstance(field_node, dict):
                    for field_elem in [
                        e for e in field_node.values() if isinstance(e, ASTNode)
                    ]:
                        field_elem.visit(f)
                elif isinstance(field_node, Iterable):
                    for field_elem in [e for e in field_node if isinstance(e, ASTNode)]:
                        field_elem.visit(f)
                elif isinstance(field_node, ASTNode):
                    field_node.visit(f)


@dataclass
class RouteFilter(
    ASTNode,
    Serialize,
    action=Field("action", types.Action),
    ip_wildcard=Field("ipWildcard", IPv4Interface),
    length_range="lengthRange",
):
    action: types.Action
    ip_wildcard: IPv4Interface
    # TODO: parse string into a range
    length_range: str


@dataclass
class BgpActivePeerConfig(
    ASTNode,
    Serialize,
    default_metric=Field("defaultMetric", int),
    local_as=Field("localAs", int),
    local_ip=Field("localIp", IPv4Address),
):
    default_metric: int
    local_as: int
    local_ip: IPv4Address


@dataclass
class BgpProcess(
    ASTNode, Serialize, neighbors=Field("neighbors", dict[IPv4Address, dict])
):
    neighbors: dict[IPv4Address, dict]


@dataclass
class OspfProcess(
    ASTNode,
    Serialize,
    admin_costs="adminCosts",
    areas="areas",
    # TODO: other fields?
):
    admin_costs: dict
    areas: dict


@dataclass
class Vrf(
    ASTNode,
    Serialize,
    vrfname="name",
    bgp=Field("bgpProcess", BgpProcess, None),
    ospf=Field("ospfProcesses", dict[str, OspfProcess], None),
    resolution="resolutionPolicy",
):
    vrfname: str
    resolution: str
    bgp: Optional[BgpProcess] = None
    ospf: Optional[dict] = None


@dataclass
class AclLine(
    ASTNode,
    Serialize,
    action=Field("action", types.Action),
    match_cond="matchCondition",
    _name="name",
    # these two are probably also skippable
    trace_elem="traceElement",
    vendor_id="vendorStructureId",
):
    action: types.Action
    match_cond: dict
    _name: str
    trace_elem: dict
    vendor_id: dict


@dataclass
class Acl(
    ASTNode,
    Serialize,
    _name="name",
    srcname="sourceName",
    srctype="sourceType",
    lines=Field("lines", list[AclLine]),
):
    _name: str
    srcname: str
    srctype: str
    lines: list[AclLine]
