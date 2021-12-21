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
from typing import Any
from serialize import Serialize
from ipaddress import IPv4Address, IPv4Interface
from dataclasses import dataclass


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


class StructureType(Enum):
    IP_ACCESS_LIST = "IP_Access_List"
    ROUTING_POLICY = "Routing_Policy"
    ROUTE_FILTER_LIST = "Route_Filter_List"
    VRF = "VRF"
    COMMS_MATCH = "Community_Set_Match_Expr"


@dataclass
class Structure(
    Serialize(
        node=("Node", Node),
        ty=("Structure_Type", StructureType),
        name=("Structure_Name", str),
        definition=("Structure_Definition", dict),
    )
):
    node: Node
    ty: StructureType
    name: str
    definition: dict


class Action(Enum):
    PERMIT = "PERMIT"
    DENY = "DENY"


@dataclass
class AclLine(
    Serialize(
        # cls may not be necessary?
        cls="class",
        action=("action", Action),
        match_cond="matchCondition",
        name="name",
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
class BgpProcess(Serialize(neighbors=("neighbors", dict[IPv4Address, dict]))):
    neighbors: dict[IPv4Address, dict]


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


class ASTNode:
    ...


class Expression(ASTNode):
    ...


class Statement(ASTNode):
    ...


class BooleanExpr(Expression):
    ...


class Conjunction(BooleanExpr):
    def __init__(self, *exprs: list[BooleanExpr]):
        self.children = exprs


class Not(BooleanExpr):
    def __init__(self, expr: BooleanExpr):
        self.children = [expr]


@dataclass
class RouteFilter:
    action: Action
    ip_wildcard: IPv4Interface
    # TODO: parse string into a range
    length_range: str


@dataclass
class IfStatement(Statement):
    guard: dict
    trueStatements: list[Statement]
    falseStatements: list[Statement]
    comment: str


@dataclass
class RoutingPolicy(Serialize(name="name", statements=("statements", list[Statement]))):
    name: str
    statements: list[Statement]


class ASTNodeVisitor:
    @staticmethod
    def visit(node: ASTNode):
        pass
