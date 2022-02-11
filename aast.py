#!/usr/bin/env python3
"""
Functionality for parsing Batfish's JSON representation back into an AST.
All classes here are essentially just organized data: the code is written
(perhaps not very Pythonically) to allow us to decode an entire JSON file
directly into a nested hierarchy of Python dataclasses.
Once those are arranged, we can then write code to access the dataclasses
and return the relevant components.
The main benefit of using these dataclasses rather than simply parsing the
JSON directly is that the static classes expect certain data: if the JSON
output is malformed or our implementation no longer aligns with Batfish,
we want to fail to decode the file and return an error immediately.

:author: Tim Alberdingk Thijm <tthijm@cs.princeton.edu>
"""
from enum import Enum
from typing import Any, Union
from ipaddress import IPv4Address, IPv4Interface
from dataclasses import dataclass
from serialize import Serialize


class Action(Enum):
    """An action to perform on routes."""

    PERMIT = "PERMIT"
    DENY = "DENY"


@dataclass
class ASTNode:
    ...


@dataclass
class Expression(ASTNode):
    ...


@dataclass
class Statement(ASTNode, Serialize()):
    ...


@dataclass
class Node(Serialize(nodeid="id", name="name")):
    """A node in the network."""

    nodeid: str
    name: str


@dataclass
class Interface(Serialize(host="hostname", iface="interface")):
    host: str
    iface: str


@dataclass
class Edge(
    Serialize(
        iface=("Interface", Interface),
        ips=("IPs", list[IPv4Address]),
        remote_iface=("Remote_Interface", Interface),
        remote_ips=("Remote_IPs", list[IPv4Address]),
    )
):
    """
    A representation of a directed edge between two interfaces.
    The first (non-remote) interface is the source.
    The second remote interface is the target.
    """

    iface: Interface
    ips: list[IPv4Address]
    remote_iface: Interface
    remote_ips: list[IPv4Address]


@dataclass
class RouteFilter(
    Serialize(
        action=("action", Action),
        ip_wildcard=("ipWildcard", IPv4Interface),
        length_range="lengthRange",
    )
):
    action: Action
    ip_wildcard: IPv4Interface
    # TODO: parse string into a range
    length_range: str


@dataclass
class RoutingPolicy(Serialize(name="name", statements=("statements", list[Statement]))):
    name: str
    statements: list[Statement]


@dataclass
class BgpProcess(Serialize(neighbors=("neighbors", dict[IPv4Address, dict]))):
    neighbors: dict[IPv4Address, dict]


@dataclass
class Vrf(
    Serialize(
        name="name", process=("bgpProcess", BgpProcess), resolution="resolutionPolicy"
    )
):
    name: str
    process: BgpProcess
    resolution: str


Structure_Def = Union[Vrf, RouteFilter, RoutingPolicy]


class StructureType(Enum):
    COMMS_MATCH = "Community_Set_Match_Expr"
    IP_ACCESS_LIST = "IP_Access_List"
    ROUTE_FILTER_LIST = "Route_Filter_List"
    ROUTING_POLICY = "Routing_Policy"
    VRF = "VRF"

    def enum_class(self) -> type:
        if self is StructureType.COMMS_MATCH:
            raise NotImplementedError()
        elif self is StructureType.IP_ACCESS_LIST:
            raise NotImplementedError()
        elif self is StructureType.ROUTE_FILTER_LIST:
            return list[RouteFilter]
        elif self is StructureType.ROUTING_POLICY:
            return RoutingPolicy
        elif self is StructureType.VRF:
            return Vrf
        else:
            raise ValueError(f"received invalid StructureType '{self}'")


@dataclass
class Structure(
    Serialize(
        node=("Node", Node),
        ty=("Structure_Type", StructureType),
        name=("Structure_Name", str),
        definition=("Structure_Definition", dict),
    )
):
    """
    A named structure in Batfish.
    The definition portion holds a different object depending on the structure type.
    TODO: Unfortunately, the deserialization procedure can't yet use one field to
    determine which structure definition we happen to be looking at.
    Because of this, definition needs to be parsed in a second pass.
    """

    node: Node
    ty: StructureType
    name: str
    # TODO: technically, this will be an object with a Structure_Def value,
    # but it's non-obvious how the serializer should figure out which choice of type
    # to use here, and it may not make sense to try them all.
    definition: dict


@dataclass
class AclLine(
    Serialize(
        # cls may not be necessary?
        cls="class",
        action=("action", Action),
        match_cond="matchCondition",
        name="name",
        # these two are probably also skippable
        trace_elem="traceElement",
        vendor_id="vendorStructureId",
    )
):
    cls: str
    action: Action
    match_cond: Any
    name: str
    trace_elem: dict
    vendor_id: dict


@dataclass
class Acl(
    Serialize(
        name="name",
        srcname="sourceName",
        srctype="sourceType",
        lines=("lines", list[AclLine]),
    )
):
    name: str
    srcname: str
    srctype: str
    lines: list[AclLine]


@dataclass
class BatfishJson(
    Serialize(
        topology=("topology", list[Edge]),
        policy="policy",
        declarations=("declarations", list[Structure]),
    )
):
    topology: list[Edge]
    policy: dict
    declarations: list[Structure]


class ExprType(Enum):
    MATCHIPV4 = "matchIpv4"
    CONJUNCTION = "conjuncts"
    DISJUNCTION = "disjuncts"
    NOT = "not"
    MATCHPROTOCOL = "matchProtocol"
    MATCHPREFIXSET = "matchPrefixSet"
    CALLEXPR = "callExpr"
    WITHENVIRONMENTEXPR = "withEnvironmentExpr"
    MATCHCOMMUNITYSET = "matchCommunitySet"
    ASEXPR = "asExpr"
    COMMUNITYSETEXPR = "communitySetExpr"
    LONGEXPR = "longExpr"


class StaticStatementType(Enum):
    TRUE = "ReturnTrue"
    FALSE = "ReturnFalse"
    LOCAL_DEF = "ReturnLocalDefaultAction"


class BooleanExpr(Expression):
    ...


class Conjunction(BooleanExpr):
    def __init__(self, *exprs: list[BooleanExpr]):
        self.children = exprs


class Not(BooleanExpr):
    def __init__(self, expr: BooleanExpr):
        self.children = [expr]


@dataclass
class TraceableStatement(
    Statement,
    Serialize(inner=("innerStatements", list[Statement]), trace_elem="traceElement"),
):
    inner: list[Statement]
    trace_elem: dict


@dataclass
class IfStatement(
    Statement,
    Serialize(
        guard="guard",
        true_stmts=("trueStatements", list[Statement]),
        false_stmts=("falseStatements", list[Statement]),
        comment="comment",
    ),
):
    guard: dict
    true_stmts: list[Statement]
    false_stmts: list[Statement]
    comment: str


@dataclass
class SetLocalPreference(Statement, Serialize(lp="localPreference")):
    lp: dict


class StaticStatement(Statement, Serialize(ty=("type", StaticStatementType))):
    ty: StaticStatementType


class ASTNodeVisitor:
    @staticmethod
    def visit(node: ASTNode):
        pass
