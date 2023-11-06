#!/usr/bin/env python3
"""
Expressions for filtering routes and using access lists in Batfish.
"""
from ipaddress import IPv4Network, IPv6Network
from dataclasses import dataclass, field
from angler.serialize import Serialize, Field
import angler.bast.btypes as types
import angler.util


@dataclass
class RouteFilterLine(
    angler.util.ASTNode,
    Serialize,
    action=Field("action", types.Action),
    ip_wildcard=Field("ipWildcard", IPv4Network),
    length_range=Field("lengthRange", str),
):
    # the action to perform (permit or deny)
    action: types.Action
    ip_wildcard: IPv4Network
    # the permitted prefix length range
    length_range: str


@dataclass
class Route6FilterLine(
    angler.util.ASTNode,
    Serialize,
    action=Field("action", types.Action),
    ip_wildcard=Field("ipWildcard", IPv6Network),
    length_range=Field("lengthRange", str),
):
    action: types.Action
    ip_wildcard: IPv6Network
    length_range: str


@dataclass
class RouteFilterList(
    angler.util.ASTNode,
    Serialize,
    _name="name",
    lines=Field("lines", list[RouteFilterLine], []),
):
    _name: str
    lines: list[RouteFilterLine] = field(default_factory=list)


@dataclass
class Route6FilterList(
    angler.util.ASTNode,
    Serialize,
    _name="name",
    lines=Field("lines", list[Route6FilterLine], []),
):
    _name: str
    lines: list[Route6FilterLine] = field(default_factory=list)


@dataclass
class AclLine(
    angler.util.ASTNode,
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
    angler.util.ASTNode,
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
