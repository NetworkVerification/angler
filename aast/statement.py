from dataclasses import dataclass, field
from types import NoneType
from typing import Generic, TypeVar
from serialize import Serialize, Field
from aast.base import Variant, ASTNode
from aast.types import TypeAnnotation
import aast.expression as expr

T = TypeVar("T")
E = TypeVar("E")


class StatementType(Variant):
    SKIP = "Skip"
    SEQ = "Seq"
    IF = "If"
    ASSIGN = "Assign"
    RETURN = "Return"

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
    delegate=("$type", StatementType.parse_class),
    ty=Field("$type", str, "Statement"),
):
    """
    The base class for statements.
    """

    ty: str = field(default="Statement", init=False)
    # dummy ty_arg field
    ty_arg: TypeAnnotation = field(default=TypeAnnotation.UNKNOWN, init=False)

    def returns(self) -> bool:
        """Return True if this statement returns, and False otherwise."""
        raise NotImplementedError("Don't call returns() from Statement directly.")


@dataclass
class SkipStatement(Statement[NoneType], Serialize, ty=Field("$type", str, "Skip")):
    """No-op statement."""

    ty: str = field(default="Skip", init=False)

    def returns(self) -> bool:
        return False


@dataclass
class SeqStatement(
    Statement[T],
    Generic[T],
    Serialize,
    first=Field("first", Statement[NoneType]),
    second=Field("second", Statement[T]),
    ty=Field("$type", str, "Seq"),
):
    """Two statements in sequence (cf. semi-colon operator in C)."""

    first: Statement[NoneType]
    second: Statement[T]
    ty: str = field(default="Seq", init=False)
    ty_arg: TypeAnnotation = field(default=TypeAnnotation.UNKNOWN, kw_only=True)

    def __post_init__(self):
        self.ty = f"{self.ty}({self.ty_arg.value})"

    def returns(self) -> bool:
        return self.second.returns()


@dataclass
class IfStatement(
    Statement[T],
    Generic[T],
    Serialize,
    comment="comment",
    guard=Field("guard", expr.Expression[bool]),
    true_stmt=Field("trueStatements", Statement[T]),
    false_stmt=Field("falseStatements", Statement[T]),
    ty=Field("$type", str, "If"),
):
    """If statement allowing branching control flow."""

    comment: str
    guard: expr.Expression[bool]
    true_stmt: Statement[T]
    false_stmt: Statement[T]
    ty: str = field(default="If", init=False)
    ty_arg: TypeAnnotation = field(default=TypeAnnotation.UNKNOWN, kw_only=True)

    def __post_init__(self):
        self.ty = f"{self.ty}({self.ty_arg.value})"

    def returns(self) -> bool:
        # NOTE: we can't use type information on what T is here, so this is at best an approximation:
        # as of Python 3.10, it does not appear possible to use the type information to determine whether
        # the IfStatement will be correctly constructed at runtime.
        # See https://stackoverflow.com/a/60984681
        return self.true_stmt.returns() and self.false_stmt.returns()


@dataclass
class AssignStatement(
    Statement[NoneType],
    Generic[E],
    Serialize,
    lhs=Field("lhs", expr.Var),
    rhs=Field("rhs", expr.Expression[E]),
    ty=Field("$type", str, "Assign"),
):
    """Assignment binding an expression to a variable."""

    lhs: expr.Var
    rhs: expr.Expression[E]
    ty: str = field(default="Assign", init=False)
    ty_arg: TypeAnnotation = field(default=TypeAnnotation.UNKNOWN, kw_only=True)

    def __post_init__(self):
        self.ty = f"{self.ty}({self.ty_arg.value})"

    def returns(self) -> bool:
        return False


@dataclass
class ReturnStatement(
    Statement[E],
    Generic[E],
    Serialize,
    return_value=Field("return_value", expr.Expression[E]),
    ty=Field("$type", str, "Return"),
):
    return_value: expr.Expression[E]
    ty: str = field(default="Return", init=False)
    ty_arg: TypeAnnotation = field(default=TypeAnnotation.UNKNOWN, kw_only=True)

    def __post_init__(self):
        self.ty = f"{self.ty}({self.ty_arg.value})"

    def returns(self) -> bool:
        return True
