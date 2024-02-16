#!/usr/bin/env python3
"""
Statements in the Batfish AST.
"""
from enum import Enum
from dataclasses import dataclass
from angler.serialize import Serialize, Field
import angler.bast.boolexprs as bools
import angler.bast.communities as comms
import angler.bast.nexthop as hop
import angler.bast.ases as ases
import angler.bast.longexprs as longs
import angler.bast.intexprs as ints
import angler.bast.origin as origin
import angler.util


class StatementType(angler.util.Variant):
    IF = "If"
    PREPEND_AS = "PrependAsPath"
    SET_COMMS = "SetCommunities"
    SET_LP = "SetLocalPreference"
    SET_METRIC = "SetMetric"
    SET_NEXT_HOP = "SetNextHop"
    SET_DEFAULT_POLICY = "SetDefaultPolicy"
    SET_ORIGIN = "SetOrigin"
    SET_WEIGHT = "SetWeight"
    STATIC = "StaticStatement"
    TRACEABLE = "TraceableStatement"

    def as_class(self) -> type:
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
            case StatementType.SET_NEXT_HOP:
                return SetNextHop
            case StatementType.SET_ORIGIN:
                return SetOrigin
            case StatementType.SET_WEIGHT:
                return SetWeight
            case StatementType.SET_DEFAULT_POLICY:
                return SetDefaultPolicy
            case StatementType.STATIC:
                return StaticStatement
            case StatementType.TRACEABLE:
                return TraceableStatement
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class StaticStatementType(Enum):
    RETURN_TRUE = "ReturnTrue"
    RETURN_FALSE = "ReturnFalse"
    LOCAL_DEF = "ReturnLocalDefaultAction"
    SET_ACCEPT = "SetDefaultActionAccept"
    SET_REJECT = "SetDefaultActionReject"
    SET_LOCAL_ACCEPT = "SetLocalDefaultActionAccept"
    SET_LOCAL_REJECT = "SetLocalDefaultActionReject"
    EXIT_ACCEPT = "ExitAccept"
    EXIT_REJECT = "ExitReject"
    RETURN = "Return"
    FALL_THROUGH = "FallThrough"


@dataclass
class Statement(
    angler.util.ASTNode,
    Serialize,
    delegate=("class", StatementType.parse_class),
):
    """
    The base class for statements.
    """


@dataclass
class StaticStatement(Statement, Serialize, ty=Field("type", StaticStatementType)):
    ty: StaticStatementType


@dataclass
class TraceableStatement(
    Statement,
    Serialize,
    inner=Field("innerStatements", list[Statement], []),
    trace_elem=Field("traceElement"),
):
    """
    A statement that as a side effect reports some information?
    TODO: can we check if there are legitimate situations in which having no inner statements is sensible?
    """

    inner: list[Statement]
    trace_elem: dict


@dataclass
class IfStatement(
    Statement,
    Serialize,
    guard=Field("guard", bools.BooleanExpr),
    true_stmts=Field("trueStatements", list[Statement], []),
    false_stmts=Field("falseStatements", list[Statement], []),
    comment="comment",
):
    """
    An if statement allowing branching control flow.
    The true and false statements can be left empty.
    """

    comment: str
    guard: bools.BooleanExpr
    true_stmts: list[Statement]
    false_stmts: list[Statement]


@dataclass
class SetLocalPreference(
    Statement, Serialize, lp=Field("localPreference", longs.LongExpr)
):
    lp: longs.LongExpr


@dataclass
class SetCommunities(
    Statement, Serialize, comm_set=Field("communitySetExpr", comms.CommunitySetExpr)
):
    comm_set: comms.CommunitySetExpr


@dataclass
class PrependAsPath(Statement, Serialize, expr=Field("expr", ases.AsPathListExpr)):
    expr: ases.AsPathListExpr


@dataclass
class SetMetric(Statement, Serialize, metric=Field("metric", longs.LongExpr)):
    metric: longs.LongExpr


@dataclass
class SetNextHop(Statement, Serialize, expr=Field("expr", hop.NextHopExpr)):
    expr: hop.NextHopExpr


@dataclass
class SetOrigin(Statement, Serialize, expr=Field("originType", origin.OriginExpr)):
    expr: origin.OriginExpr


@dataclass
class SetWeight(Statement, Serialize, expr=Field("weight", ints.IntExpr)):
    expr: ints.IntExpr


@dataclass
class SetDefaultPolicy(Statement, Serialize, policy=Field("defaultPolicy", str)):
    policy: str
