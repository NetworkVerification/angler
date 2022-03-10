from dataclasses import dataclass
from types import NoneType
from typing import Generic, TypeVar
from serialize import Serialize, Field
from aast.base import Variant, ASTNode
import aast.expression as expr

T = TypeVar("T")
E = TypeVar("E")


class StatementType(Variant):
    SKIP = "SkipStatement"
    SEQ = "SeqStatement"
    IF = "IfStatement"
    ASSIGN = "AssignStatement"
    RETURN = "ReturnStatement"

    def as_class(self) -> type:
        match self:
            case StatementType.SKIP:
                return SkipStatement
            case StatementType.SEQ:
                return SeqStatement
            case StatementType.IF:
                return IfStatement
            case StatementType.ASSIGN:
                return AssignStatement
            case StatementType.RETURN:
                return ReturnStatement
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class Statement(
    ASTNode,
    Generic[T],
    Serialize,
    with_type="$type",
    delegate=("$type", StatementType.parse_class),
):
    """
    The base class for statements.
    """

    ...


@dataclass
class SkipStatement(
    Statement[NoneType],
    Serialize,
    with_type="$type",
):
    """No-op statement."""


@dataclass
class SeqStatement(
    Statement[T],
    Generic[T],
    Serialize,
    with_type="$type",
    first=Field("first", Statement[NoneType]),
    second=Field("second", Statement[T]),
):
    """Two statements in sequence (cf. semi-colon operator in C)."""

    first: Statement[NoneType]
    second: Statement[T]


@dataclass
class IfStatement(
    Statement[T],
    Generic[T],
    Serialize,
    with_type="$type",
    comment="comment",
    guard=Field("guard", expr.Expression[bool]),
    true_stmts=Field("trueStatements", Statement[T]),
    false_stmts=Field("falseStatements", Statement[T]),
):
    """If statement allowing branching control flow."""

    comment: str
    guard: expr.Expression[bool]
    true_stmts: Statement[T]
    false_stmts: Statement[T]


@dataclass
class AssignStatement(
    Statement[NoneType],
    Generic[E],
    Serialize,
    with_type="$type",
    lhs=Field("lhs", expr.Var),
    rhs=Field("rhs", expr.Expression[E]),
):
    """Assignment binding an expression to a variable."""

    lhs: expr.Var
    rhs: expr.Expression[E]


@dataclass
class ReturnStatement(
    Statement[E],
    Generic[E],
    Serialize,
    with_type="$type",
    return_value=Field("return_value", expr.Expression[E]),
):
    return_value: expr.Expression[E]
