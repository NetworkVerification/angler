#!/usr/bin/env python3
"""
Angler statements.
"""
from dataclasses import dataclass, field
from types import NoneType
from typing import Generic, TypeVar
from angler.serialize import Serialize, Field
from angler.aast.types import TypeAnnotation, TYPE_FIELD
import angler.aast.expression as expr
from angler.util import Variant, ASTNode

T = TypeVar("T")
E = TypeVar("E")


class StatementType(Variant):
    SKIP = "Skip"
    SEQ = "Seq"
    IF = "If"
    ASSIGN = "Assign"
    RETURN = "Return"
    SET_DEFAULT_POLICY = "SetDefaultPolicy"

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
            case StatementType.SET_DEFAULT_POLICY:
                return SetDefaultPolicy
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class Statement(
    ASTNode,
    Generic[T],
    Serialize,
    delegate=(TYPE_FIELD, StatementType.parse_class),
    ty=Field(TYPE_FIELD, str, "Statement"),
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

    def subst(self, _environment: dict[str, expr.Expression]):
        """
        Substitute all variable references to elements in the given environment
        in the statement.
        """
        ...


@dataclass
class SkipStatement(Statement[NoneType], Serialize, ty=Field(TYPE_FIELD, str, "Skip")):
    """No-op statement."""

    ty: str = field(default="Skip", init=False)

    def returns(self) -> bool:
        return False


@dataclass
class SeqStatement(
    Statement[T],
    Generic[T],
    Serialize,
    first=Field("S1", Statement[NoneType]),
    second=Field("S2", Statement[T]),
    ty=Field(TYPE_FIELD, str, "Seq"),
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

    def subst(self, environment: dict[str, expr.Expression]):
        self.first.subst(environment)
        self.second.subst(environment)


@dataclass
class IfStatement(
    Statement[T],
    Generic[T],
    Serialize,
    comment="Comment",
    guard=Field("Guard", expr.Expression[bool]),
    true_stmt=Field("ThenCase", list[Statement]),
    false_stmt=Field("ElseCase", list[Statement]),
    ty=Field(TYPE_FIELD, str, "If"),
):
    """If statement allowing branching control flow."""

    comment: str
    guard: expr.Expression[bool]
    true_stmt: list[Statement]
    false_stmt: list[Statement]
    ty: str = field(default="If", init=False)
    ty_arg: TypeAnnotation = field(default=TypeAnnotation.UNKNOWN, kw_only=True)

    def __post_init__(self):
        self.ty = f"{self.ty}({self.ty_arg.value})"

    def returns(self) -> bool:
        # NOTE: we can't use type information on what T is here, so this is at best an approximation:
        # as of Python 3.10, it does not appear possible to use the type information to determine whether
        # the IfStatement will be correctly constructed at runtime.
        # See https://stackoverflow.com/a/60984681
        return any(s.returns() for s in self.true_stmt) and any(
            s.returns() for s in self.false_stmt
        )

    def subst(self, environment: dict[str, expr.Expression]):
        # NOTE: subst returns an expression when used for expressions, but None when used
        # for statements
        self.guard = self.guard.subst(environment)
        for s in self.true_stmt:
            s.subst(environment)
        for s in self.false_stmt:
            s.subst(environment)


@dataclass
class AssignStatement(
    Statement[NoneType],
    Generic[E],
    Serialize,
    lhs=Field("Var", str),
    rhs=Field("Expr", expr.Expression[E]),
    ty=Field(TYPE_FIELD, str, "Assign"),
):
    """Assignment binding an expression to a variable."""

    lhs: str
    rhs: expr.Expression[E]
    ty: str = field(default="Assign", init=False)
    ty_arg: TypeAnnotation = field(default=TypeAnnotation.UNKNOWN, kw_only=True)

    def __post_init__(self):
        self.ty = f"{self.ty}({self.ty_arg.value})"

    def returns(self) -> bool:
        return False

    def subst(self, environment: dict[str, expr.Expression]):
        self.rhs.subst(environment)


@dataclass
class ReturnStatement(
    Statement[E],
    Generic[E],
    Serialize,
    return_value=Field("Expr", expr.Expression[E]),
    ty=Field(TYPE_FIELD, str, "Return"),
):
    return_value: expr.Expression[E]
    ty: str = field(default="Return", init=False)
    ty_arg: TypeAnnotation = field(default=TypeAnnotation.UNKNOWN, kw_only=True)

    def __post_init__(self):
        self.ty = f"{self.ty}({self.ty_arg.value})"

    def returns(self) -> bool:
        return True

    def subst(self, environment: dict[str, expr.Expression]):
        self.return_value.subst(environment)


@dataclass
class SetDefaultPolicy(
    Statement[NoneType],
    Serialize,
    policy_name="PolicyName",
    ty=Field(TYPE_FIELD, str, "SetDefaultPolicy"),
):
    policy_name: str
    ty: str = field(default="SetDefaultPolicy", init=False)
