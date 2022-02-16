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
from serialize import Serializable, Serialize


def parse_bf_clsname(qualified: str) -> str:
    """
    Given a string representing a class in batfish's namespace,
    return the class name.
    """
    _, last = qualified.rsplit(sep=".", maxsplit=1)
    # if a $ is found, name will contain the string following it
    # if $ is not found, name will contain the original string
    _, _, name = last.partition("$")
    return name


class Action(Enum):
    """An action to perform on routes."""

    PERMIT = "PERMIT"
    DENY = "DENY"


class ExprType(Enum):
    """A type of expression."""

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

    def enum_class(self) -> type:
        match self:
            case ExprType.CONJUNCTION:
                return Conjunction
            case ExprType.DISJUNCTION:
                return Disjunction
            case ExprType.NOT:
                return Not
            case ExprType.MATCHCOMMUNITYSET:
                return MatchCommunities
            case _:
                raise NotImplementedError(f"{self} conversion not yet implemented.")


class StatementType(Enum):
    IF = "IfStatement"
    PREPEND_AS = "PrependAsPath"
    SET_LP = "SetLocalPreference"
    SET_METRIC = "SetMetric"
    TRACEABLE = "TraceableStatement"

    def enum_class(self) -> type:
        match self:
            case StatementType.IF:
                return IfStatement
            case StatementType.PREPEND_AS:
                return PrependAsPath
            case StatementType.SET_LP:
                return SetLocalPreference
            case StatementType.SET_METRIC:
                return SetMetric
            case StatementType.TRACEABLE:
                return TraceableStatement
            case _:
                raise NotImplementedError(f"{self} conversion not yet implemented.")


@dataclass
class ASTNode:
    ...


@dataclass
class Expression(
    ASTNode,
    Serialize,
    delegate=("class", lambda s: ExprType(parse_bf_clsname(s)).enum_class()),
):
    """
    The base class for expressions.
    TODO: We need a way to narrow these appropriately during deserialization.
    In most cases, there is a "class" key in the dict which specifies which type
    of expression is given, which will be a subclass of Expression.
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
class Node(Serialize, nodeid="id", nodename="name"):
    """A node in the network."""

    nodeid: str
    nodename: str


@dataclass
class Interface(Serialize, host="hostname", iface="interface"):
    host: str
    iface: str


@dataclass
class Edge(
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
    guard="guard",
    true_stmts=("trueStatements", list[Statement]),
    false_stmts=("falseStatements", list[Statement]),
    comment="comment",
):
    guard: dict
    true_stmts: list[Statement]
    false_stmts: list[Statement]
    comment: str


@dataclass
class SetLocalPreference(Statement, Serialize, lp="localPreference"):
    lp: dict


@dataclass
class CommunitySetMatchExpr(Expression, Serialize, expr="expr"):
    expr: dict


@dataclass
class CommunityIs(Expression, Serialize, community="community"):
    # TODO parse the community set: it appears to be two integers separated by a colon
    community: str


@dataclass
class MatchCommunities(
    Serialize, comm_set="communitySetExpr", comm_match="communitySetMatchExpr"
):
    # the set of communities to match
    comm_set: dict
    # the set to match against
    comm_match: dict


@dataclass
class SetCommunities(Serialize, comm_set="communitySetExpr"):
    comm_set: dict


@dataclass
class CommunitySetUnion(Expression, Serialize, exprs=("exprs", list[dict])):
    exprs: list[dict]


@dataclass
class CommunitySetDifference(
    Expression,
    Serialize,
    initial=("initial", dict),
    remove=("removalCriterion", dict),
):
    initial: dict
    remove: dict


@dataclass
class LiteralCommunitySet(Expression, Serialize, comm_set=("communitySet", list[str])):
    # TODO: parse the community set
    comm_set: list[str]


@dataclass
class PrependAsPath(Statement, Serialize, expr=("expr", dict)):
    # convert dict to appropriate expr (LiteralAsList?)
    expr: dict


@dataclass
class ExplicitAs(Serialize, asnum=("as", int)):
    asnum: int


@dataclass
class LiteralAsList(Serialize, ases=("list", list[ExplicitAs])):
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
    Serialize, policyname="name", statements=("statements", list[dict])
):
    policyname: str
    # FIXME: need to figure out which kind of statement it is
    statements: list[Statement]


@dataclass
class BgpActivePeerConfig(
    Serialize,
    default_metric=("defaultMetric", int),
    local_as=("localAs", int),
    local_ip=("localIp", IPv4Address),
):
    default_metric: int
    local_as: int
    local_ip: IPv4Address


@dataclass
class BgpProcess(Serialize, neighbors=("neighbors", dict[IPv4Address, dict])):
    neighbors: dict[IPv4Address, dict]


@dataclass
class Vrf(
    Serialize,
    vrfname="name",
    process=("bgpProcess", BgpProcess),
    resolution="resolutionPolicy",
):
    vrfname: str
    process: BgpProcess
    resolution: str


@dataclass
class AclLine(
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
class StructureDef(Serialize, value=("value", dict)):
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
                return dict
            case StructureType.ROUTING_POLICY:
                return RoutingPolicy
            case StructureType.VRF:
                return Vrf
            case _:
                raise ValueError(f"{self} is not a valid {self.__class__}")


@dataclass
class Structure(
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
    Serialize,
    topology=("topology", list[Edge]),
    policy="policy",
    declarations=("declarations", list[Structure]),
):
    topology: list[Edge]
    policy: dict
    declarations: list[Structure]
