#!/usr/bin/env python3
"""
Expressions for filtering routes and using access lists in Batfish.
"""
from ipaddress import IPv4Interface, IPv6Interface
from dataclasses import dataclass, field
from serialize import Serialize, Field
import bast.btypes as types
import util


@dataclass
class RouteFilterLine(
    util.ASTNode,
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
class Route6FilterLine(
    util.ASTNode,
    Serialize,
    action=Field("action", types.Action),
    ip_wildcard=Field("ipWildcard", IPv6Interface),
    length_range="lengthRange",
):
    action: types.Action
    ip_wildcard: IPv6Interface
    # TODO: parse string into a range
    length_range: str


@dataclass
class RouteFilterList(
    util.ASTNode,
    Serialize,
    _name="name",
    lines=Field("lines", list[RouteFilterLine], []),
):
    _name: str
    lines: list[RouteFilterLine] = field(default_factory=list)


@dataclass
class Route6FilterList(
    util.ASTNode,
    Serialize,
    _name="name",
    lines=Field("lines", list[Route6FilterLine], []),
):
    _name: str
    lines: list[Route6FilterLine] = field(default_factory=list)


@dataclass
class AclLine(
    util.ASTNode,
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
    util.ASTNode,
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
