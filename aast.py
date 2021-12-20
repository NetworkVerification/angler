#!/usr/bin/env python3
from enum import Enum
from serialize import Serialize
from ipaddress import IPv4Address, IPv4Interface


class Node(Serialize(nodeid="id", name="name")):
    def __init__(self, nodeid, name):
        super().__init__()
        self.nodeid = nodeid
        self.name = name


class Interface(Serialize(host="hostname", iface="interface")):
    def __init__(self, host: str, iface: str):
        super().__init__()
        self.host = host
        self.iface = iface


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

    def __init__(
        self,
        iface: Interface,
        ips: list[IPv4Address],
        remote_iface: Interface,
        remote_ips: list[IPv4Address],
    ):
        super().__init__()
        self.iface = iface
        self.ips = ips
        self.remote_iface = remote_iface
        self.remote_ips = remote_ips


class Structure(
    Serialize(
        node=("Node", Node),
        ty=("Structure_Type", str),
        name=("Structure_Name", str),
        definition=("Structure_Definition", dict),
    )
):
    def __init__(self, node: Node, ty: str, name: str, definition):
        # val is an AST that also needs to be parsed
        self.node = node
        self.ty = ty
        self.name = name
        self.definition = definition


class Action(Enum):
    PERMIT = "PERMIT"
    DENY = "DENY"


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
    def __init__(self, cls, action, match_cond, name, trace_elem, vendor_id):
        self.cls = cls
        self.action = action
        self.match_cond = match_cond
        self.name = name
        self.trace_elem = trace_elem
        self.vendor_id = vendor_id


class Acl(
    Serialize(
        name="name",
        srcname="sourceName",
        srctype="sourceType",
        lines=("lines", list[AclLine]),
    )
):
    def __init__(self, name: str, srcname: str, srctype: str, lines: list[AclLine]):
        self.name = name
        self.srcname = srcname
        self.srctype = srctype
        self.lines = lines


class BgpProcess(Serialize(neighbors=("neighbors", dict[IPv4Address, dict]))):
    def __init__(self, neighbors: dict[IPv4Address, dict]):
        self.neighbors = neighbors


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


class ASTNodeVisitor:
    @staticmethod
    def visit(node: ASTNode):
        pass
