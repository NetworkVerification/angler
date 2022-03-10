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

    def returns(self) -> bool:
        """Return True if this statement returns, and False otherwise."""
        raise NotImplementedError("Don't call returns() from Statement directly.")


@dataclass
class SkipStatement(
    Statement[NoneType],
    Serialize,
    with_type="$type",
):
    """No-op statement."""

    def returns(self) -> bool:
        return False


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

    def returns(self) -> bool:
        return self.second.returns()


@dataclass
class IfStatement(
    Statement[T],
    Generic[T],
    Serialize,
    with_type="$type",
    comment="comment",
    guard=Field("guard", expr.Expression[bool]),
    true_stmt=Field("trueStatements", Statement[T]),
    false_stmt=Field("falseStatements", Statement[T]),
):
    """If statement allowing branching control flow."""

    comment: str
    guard: expr.Expression[bool]
    true_stmt: Statement[T]
    false_stmt: Statement[T]

    def returns(self) -> bool:
        # NOTE: we can't use type information on what T is here, so this is at best an approximation
        # as of Python 3.10, it does not appear possible to use the type information to determine whether
        # the IfStatement will be correctly constructed at runtime.
        # See https://stackoverflow.com/a/60984681
        return self.true_stmt.returns() and self.false_stmt.returns()


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

    def returns(self) -> bool:
        return False


@dataclass
class ReturnStatement(
    Statement[E],
    Generic[E],
    Serialize,
    with_type="$type",
    return_value=Field("return_value", expr.Expression[E]),
):
    return_value: expr.Expression[E]

    def returns(self) -> bool:
        return True
