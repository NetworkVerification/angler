#!/usr/bin/env python3
"""
Statements in the Batfish AST.
"""
from enum import Enum
from dataclasses import dataclass
from serialize import Serialize, Field
import bast.base as ast
import bast.btypes as types
import bast.boolexprs as bools
import bast.communities as comms
import bast.nexthop as hop
import bast.ases as ases
import bast.longexprs as longs
import aast.statement as astmt
import aast.boolexprs as abools


class StatementType(ast.Variant):
    IF = "If"
    PREPEND_AS = "PrependAsPath"
    SET_COMMS = "SetCommunities"
    SET_LP = "SetLocalPreference"
    SET_METRIC = "SetMetric"
    SET_NEXT_HOP = "SetNextHop"
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
            case StatementType.STATIC:
                return StaticStatement
            case StatementType.TRACEABLE:
                return TraceableStatement
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class StaticStatementType(Enum):
    TRUE = "ReturnTrue"
    FALSE = "ReturnFalse"
    LOCAL_DEF = "ReturnLocalDefaultAction"
    EXIT_ACCEPT = "ExitAccept"
    EXIT_REJECT = "ExitReject"
    RETURN = "Return"
    FALL_THROUGH = "FallThrough"


@dataclass
class Statement(
    ast.ASTNode,
    Serialize,
    delegate=("class", StatementType.parse_class),
):
    """
    The base class for statements.
    """

    def to_aast(self) -> astmt.Statement:
        raise NotImplementedError()


@dataclass
class StaticStatement(Statement, Serialize, ty=Field("type", StaticStatementType)):
    ty: StaticStatementType

    def to_aast(self) -> astmt.Statement:
        match self.ty:
            case StaticStatementType.TRUE | StaticStatementType.EXIT_ACCEPT:
                return astmt.ReturnStatement(abools.LiteralTrue())
            case StaticStatementType.FALSE | StaticStatementType.EXIT_REJECT:
                return astmt.ReturnStatement(abools.LiteralFalse())
            case StaticStatementType.LOCAL_DEF:
                return astmt.ReturnStatement(abools.Havoc())
            case _:
                raise NotImplementedError()


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

    def to_aast(self) -> astmt.IfStatement:
        return astmt.IfStatement(
            self.guard.to_aast(),
            [s.to_aast() for s in self.true_stmts],
            [s.to_aast() for s in self.false_stmts],
            self.comment,
        )


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
class SetMetric(Statement, Serialize, metric=Field("metric", types.Metric)):
    metric: types.Metric


@dataclass
class SetNextHop(Statement, Serialize, expr=Field("expr", hop.NextHopExpr)):
    expr: hop.NextHopExpr
