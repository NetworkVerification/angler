from dataclasses import dataclass
import functools
from types import NoneType
from typing import Generic, TypeVar
from serialize import Serialize, Field
from aast.base import Variant, ASTNode
import aast.expression as expr

T = TypeVar("T")
E = TypeVar("E")


class StatementType(Variant):
    SEQ = "SeqStatement"
    IF = "IfStatement"
    ASSIGN = "AssignStatement"
    RETURN = "ReturnStatement"

    def as_class(self) -> type:
        match self:
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
class SeqStatement(
    Statement[T],
    Generic[T],
    Serialize,
    with_type="$type",
    first=Field("first", Statement[NoneType]),
    second=Field("second", Statement[T]),
):
    first: Statement[NoneType]
    second: Statement[T]

    @staticmethod
    def into(*stmts: Statement) -> Statement:
        return functools.reduce(SeqStatement, stmts)


@dataclass
class IfStatement(
    Statement[T],
    Generic[T],
    Serialize,
    with_type="$type",
    guard=Field("guard", expr.Expression[bool]),
    true_stmts=Field("trueStatements", Statement[T], []),
    false_stmts=Field("falseStatements", Statement[T], []),
    comment="comment",
):
    """
    An if statement allowing branching control flow.
    The true and false statements can be left empty.
    """

    guard: expr.Expression[bool]
    true_stmts: Statement[T]
    false_stmts: Statement[T]
    comment: str


@dataclass
class AssignStatement(
    Statement[NoneType],
    Generic[E],
    Serialize,
    with_type="$type",
    lhs=Field("lhs", expr.Var),
    rhs=Field("rhs", expr.Expression[E]),
):
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
