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
from typing import Any, Callable, Optional, Union
from ipaddress import IPv4Address, IPv4Interface
from dataclasses import dataclass
from serialize import Serializable, Serialize
from collections.abc import Iterable


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


class Action(Enum):
    """An action to perform on routes."""

    PERMIT = "PERMIT"
    DENY = "DENY"


class ExprType(Enum):
    """A type of expression."""

    # MATCHIPV4 = "matchIpv4"
    # CONJUNCTION = "conjuncts"
    # DISJUNCTION = "disjuncts"
    # NOT = "not"
    # MATCHPROTOCOL = "matchProtocol"
    MATCHPREFIXSET = "MatchPrefixSet"
    MATCHCOMMUNITIES = "MatchCommunities"
    # CALLEXPR = "callExpr"
    # WITHENVIRONMENTEXPR = "withEnvironmentExpr"
    # ASEXPR = "asExpr"
    # COMMUNITYSETEXPR = "communitySetExpr"
    COMMUNITYSETUNION = "CommunitySetUnion"
    COMMUNITYSETDIFFERENCE = "CommunitySetDifference"
    # TODO(tim): what's the difference between the following two?
    COMMUNITYSMEREFERENCE = "CommunitySetMatchExprReference"
    COMMUNITYMATCHEXPRREFERENCE = "CommunityMatchExprReference"
    COMMUNITYIS = "CommunityIs"
    LITERALLONG = "LiteralLong"
    LITERALASLIST = "LiteralAsList"
    LITERALCOMMUNITYSET = "LiteralCommunitySet"
    DESTINATION = "DestinationNetwork"  # variable
    INPUTCOMMUNITIES = "InputCommunities"  # variable
    NAMEDPREFIXSET = "NamedPrefixSet"

    def enum_class(self) -> type:
        match self:
            # case ExprType.CONJUNCTION:
            #     return Conjunction
            # case ExprType.DISJUNCTION:
            #     return Disjunction
            # case ExprType.NOT:
            #     return Not
            case ExprType.MATCHCOMMUNITIES:
                return MatchCommunities
            case ExprType.INPUTCOMMUNITIES:
                return InputCommunities
            case ExprType.COMMUNITYSETUNION:
                return CommunitySetUnion
            case ExprType.COMMUNITYSETDIFFERENCE:
                return CommunitySetDifference
            case ExprType.COMMUNITYSMEREFERENCE:
                return CommunitySetMatchExprReference
            case ExprType.COMMUNITYMATCHEXPRREFERENCE:
                return CommunityMatchExprReference
            case ExprType.COMMUNITYIS:
                return CommunityIs
            case ExprType.MATCHPREFIXSET:
                return MatchPrefixSet
            case ExprType.NAMEDPREFIXSET:
                return NamedPrefixSet
            case ExprType.DESTINATION:
                return DestinationNetwork
            case ExprType.LITERALCOMMUNITYSET:
                return LiteralCommunitySet
            case ExprType.LITERALLONG:
                return LiteralLong
            case ExprType.LITERALASLIST:
                return LiteralAsList
            case _:
                raise NotImplementedError(f"{self} conversion not yet implemented.")


class StatementType(Enum):
    IF = "If"
    PREPEND_AS = "PrependAsPath"
    SET_COMMS = "SetCommunities"
    SET_LP = "SetLocalPreference"
    SET_METRIC = "SetMetric"
    STATIC = "StaticStatement"
    TRACEABLE = "TraceableStatement"

    def enum_class(self) -> type:
        match self:
            case StatementType.IF:
                return IfStatement
            case StatementType.PREPEND_AS:
                return PrependAsPath
            case StatementType.SET_COMMS:
                return SetCommunities
            case StatementType.SET_LP:
                return SetLocalPreference
            case StatementType.SET_METRIC:
                return SetMetric
            case StatementType.STATIC:
                return StaticStatement
            case StatementType.TRACEABLE:
                return TraceableStatement
            case _:
                raise NotImplementedError(f"{self} conversion not yet implemented.")


@dataclass
class ASTNode(Serialize):
    def visit(self, f: Callable) -> None:
        f(self)
        for field in self.fields:
            if isinstance(field, Iterable):
                for ff in field:
                    if isinstance(ff, ASTNode):
                        ff.visit(f)
            else:
                field.visit(f)


@dataclass
class Expression(
    ASTNode,
    Serialize,
    delegate=("class", lambda s: ExprType(parse_bf_clsname(s)).enum_class()),
):
    """
    The base class for expressions.
    """

    ...


@dataclass
class Statement(
    ASTNode,
    Serialize,
    delegate=(
        "class",
        lambda s: StatementType(parse_bf_clsname(s)).enum_class(),
    ),
):
    """
    The base class for statements.
    """

    ...


@dataclass
class Var(Expression, Serialize):
    """A class representing a Batfish variable."""


@dataclass
class DestinationNetwork(Var):
    ...


@dataclass
class InputCommunities(Var):
    ...


@dataclass
class NamedPrefixSet(Var, Serialize, _name="name"):
    _name: str


@dataclass
class CommunitySetMatchExprReference(Var, Serialize, _name="name"):
    _name: str


@dataclass
class CommunityMatchExprReference(Var, Serialize, _name="name"):
    _name: str


@dataclass
class Node(ASTNode, Serialize, nodeid="id", nodename="name"):
    """A node in the network."""

    nodeid: str
    nodename: str


@dataclass
class Interface(ASTNode, Serialize, host="hostname", iface="interface"):
    host: str
    iface: str


@dataclass
class Edge(
    ASTNode,
    Serialize,
    iface=("Interface", Interface),
    ips=("IPs", list[IPv4Address]),
    remote_iface=("Remote_Interface", Interface),
    remote_ips=("Remote_IPs", list[IPv4Address]),
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


class StaticStatementType(Enum):
    TRUE = "ReturnTrue"
    FALSE = "ReturnFalse"
    LOCAL_DEF = "ReturnLocalDefaultAction"


class BooleanExpr(Expression):
    ...


class Conjunction(BooleanExpr):
    def __init__(self, *exprs: list[BooleanExpr]):
        self.children = exprs


class Disjunction(BooleanExpr):
    def __init__(self, *exprs: list[BooleanExpr]):
        self.children = exprs


class Not(BooleanExpr):
    def __init__(self, expr: BooleanExpr):
        self.children = [expr]


@dataclass
class TraceableStatement(
    Statement,
    Serialize,
    inner=("innerStatements", list[Statement]),
    trace_elem="traceElement",
):
    inner: list[Statement]
    trace_elem: dict


@dataclass
class IfStatement(
    Statement,
    Serialize,
    guard=("guard", Expression),
    true_stmts=("trueStatements", list[Statement]),
    false_stmts=("falseStatements", list[Statement]),
    comment="comment",
):
    guard: Expression
    true_stmts: list[Statement]
    false_stmts: list[Statement]
    comment: str


@dataclass
class LiteralLong(Expression, Serialize, value=("value", int)):
    value: int


@dataclass
class SetLocalPreference(Statement, Serialize, lp=("localPreference", Expression)):
    lp: Expression


@dataclass
class CommunitySetMatchExpr(Expression, Serialize, expr=("expr", Expression)):
    expr: Expression


@dataclass
class CommunityIs(Expression, Serialize, community="community"):
    # TODO parse the community set: it appears to be two integers separated by a colon
    community: str


@dataclass
class MatchCommunities(
    Expression,
    Serialize,
    comm_set=("communitySetExpr", Expression),
    comm_match=("communitySetMatchExpr", Expression),
):
    # the set of communities to match
    comm_set: Expression
    # the set to match against
    comm_match: Expression


@dataclass
class SetCommunities(Statement, Serialize, comm_set=("communitySetExpr", Expression)):
    comm_set: Expression


@dataclass
class CommunitySetUnion(Expression, Serialize, exprs=("exprs", list[Expression])):
    exprs: list[Expression]


@dataclass
class CommunitySetDifference(
    Expression,
    Serialize,
    initial=("initial", Expression),
    remove=("removalCriterion", Expression),
):
    initial: Expression
    remove: Expression


@dataclass
class LiteralCommunitySet(Expression, Serialize, comm_set=("communitySet", list[str])):
    # TODO: parse the community set
    comm_set: list[str]


@dataclass
class MatchPrefixSet(
    Expression,
    Serialize,
    prefix=("prefix", Expression),
    prefix_set=("prefixSet", Expression),
):
    prefix: Expression
    prefix_set: Expression


@dataclass
class PrependAsPath(Statement, Serialize, expr=("expr", Expression)):
    # convert dict to appropriate expr (LiteralAsList?)
    expr: Expression


@dataclass
class ExplicitAs(ASTNode, Serialize, asnum=("as", int)):
    asnum: int


@dataclass
class LiteralAsList(Expression, Serialize, ases=("list", list[ExplicitAs])):
    ases: list[ExplicitAs]


@dataclass
class StaticStatement(Statement, Serialize, ty=("type", StaticStatementType)):
    ty: StaticStatementType


class Metric(dict):
    ...


@dataclass
class SetMetric(Statement, Serialize, metric=("metric", Metric)):
    metric: Metric


@dataclass
class RouteFilter(
    ASTNode,
    Serialize,
    action=("action", Action),
    ip_wildcard=("ipWildcard", IPv4Interface),
    length_range="lengthRange",
):
    action: Action
    ip_wildcard: IPv4Interface
    # TODO: parse string into a range
    length_range: str


@dataclass
class RoutingPolicy(
    ASTNode, Serialize, policyname="name", statements=("statements", list[Statement])
):
    policyname: str
    statements: list[Statement]


@dataclass
class BgpActivePeerConfig(
    ASTNode,
    Serialize,
    default_metric=("defaultMetric", int),
    local_as=("localAs", int),
    local_ip=("localIp", IPv4Address),
):
    default_metric: int
    local_as: int
    local_ip: IPv4Address


@dataclass
class BgpProcess(ASTNode, Serialize, neighbors=("neighbors", dict[IPv4Address, dict])):
    neighbors: dict[IPv4Address, dict]


@dataclass
class Vrf(
    ASTNode,
    Serialize,
    vrfname="name",
    bgp=("bgpProcess", BgpProcess),
    ospf=("ospfProcesses", dict),
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
    action=("action", Action),
    match_cond="matchCondition",
    _name="name",
    # these two are probably also skippable
    trace_elem="traceElement",
    vendor_id="vendorStructureId",
):
    action: Action
    match_cond: Any
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
    lines=("lines", list[AclLine]),
):
    _name: str
    srcname: str
    srctype: str
    lines: list[AclLine]


StructureValue = Union[Vrf, RouteFilter, RoutingPolicy, Acl]


@dataclass
class StructureDef(ASTNode, Serialize, value=("value", dict)):
    """
    A structure definition of some particular value, based on the
    StructureType of the enclosing Structure.
    TODO: perhaps we can flatten this?
    """

    value: StructureValue


class StructureType(Enum):
    COMMS_MATCH = "Community_Set_Match_Expr"
    IP_ACCESS_LIST = "IP_Access_List"
    ROUTE_FILTER_LIST = "Route_Filter_List"
    ROUTE6_FILTER_LIST = "Route6_Filter_List"
    ROUTING_POLICY = "Routing_Policy"
    VRF = "VRF"

    def enum_class(self) -> type:
        match self:
            case StructureType.COMMS_MATCH:
                return CommunitySetMatchExpr
            case StructureType.IP_ACCESS_LIST:
                return Acl
            case StructureType.ROUTE_FILTER_LIST:
                return list[RouteFilter]
            case StructureType.ROUTE6_FILTER_LIST:
                # TODO
                return dict
            case StructureType.ROUTING_POLICY:
                return RoutingPolicy
            case StructureType.VRF:
                return Vrf
            case _:
                raise ValueError(f"{self} is not a valid {self.__class__}")


@dataclass
class Structure(
    ASTNode,
    Serialize,
    node=("Node", Node),
    ty=("Structure_Type", StructureType),
    struct_name=("Structure_Name", str),
    definition=("Structure_Definition", StructureDef),
):
    """
    A named structure in Batfish.
    """

    node: Node
    ty: StructureType
    struct_name: str
    definition: StructureDef

    def __post_init__(self):
        """
        Using the type of the structure, update the value of the underlying StructureDef
        to the appropriate type.
        """
        cls = self.ty.enum_class()
        if isinstance(cls, Serializable):
            self.definition.value = cls.from_dict(self.definition.value)


@dataclass
class BatfishJson(
    ASTNode,
    Serialize,
    topology=("topology", list[Edge]),
    policy="policy",
    declarations=("declarations", list[Structure]),
):
    topology: list[Edge]
    policy: dict
    declarations: list[Structure]
