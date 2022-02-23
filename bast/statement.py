#!/usr/bin/env python3
"""
Statements in the Batfish AST.
"""
from enum import Enum
from dataclasses import dataclass
from serialize import Serialize, Field
import bast.base as ast
import bast.btypes as types
import bast.expression as expr
import bast.boolexprs as bools
import bast.communities as comms


class StatementType(ast.Variant):
    IF = "If"
    PREPEND_AS = "PrependAsPath"
    SET_COMMS = "SetCommunities"
    SET_LP = "SetLocalPreference"
    SET_METRIC = "SetMetric"
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
            case StatementType.STATIC:
                return StaticStatement
            case StatementType.TRACEABLE:
                return TraceableStatement
            case _:
                raise NotImplementedError(f"{self} conversion not yet implemented.")


class StaticStatementType(Enum):
    TRUE = "ReturnTrue"
    FALSE = "ReturnFalse"
    LOCAL_DEF = "ReturnLocalDefaultAction"
    EXIT_ACCEPT = "ExitAccept"
    EXIT_REJECT = "ExitReject"
    RETURN = "Return"


@dataclass
class Statement(
    ast.ASTNode,
    Serialize,
    delegate=("class", StatementType.parse_class),
):
    """
    The base class for statements.
    """

    ...


@dataclass
class StaticStatement(Statement, Serialize, ty=Field("type", StaticStatementType)):
    ty: StaticStatementType


@dataclass
class TraceableStatement(
    Statement,
    Serialize,
    inner=Field("innerStatements", list[Statement]),
    trace_elem=Field("traceElement"),
):
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
    Statement, Serialize, lp=Field("localPreference", expr.Expression)
):
    lp: expr.Expression


@dataclass
class SetCommunities(
    Statement, Serialize, comm_set=Field("communitySetExpr", comms.CommunityExpr)
):
    comm_set: comms.CommunityExpr


@dataclass
class PrependAsPath(Statement, Serialize, expr=Field("expr", expr.Expression)):
    # convert dict to appropriate expr (LiteralAsList?)
    expr: expr.Expression


@dataclass
class SetMetric(Statement, Serialize, metric=Field("metric", types.Metric)):
    metric: types.Metric
