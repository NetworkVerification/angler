#!/usr/bin/env python3
"""
Angler expressions.
"""
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
from dataclasses import InitVar, dataclass, field
from typing import Generic, TypeVar
from serialize import Serialize, Field
from aast.types import (
    TypeAnnotation,
    RouteType,
    ResultType,
    EnvironmentType,
    TYPE_FIELD,
)
from util import Variant, ASTNode

T = TypeVar("T")
X = TypeVar("X")
A = TypeVar("A")
B = TypeVar("B")


class ExprType(Variant):
    """A type of expression."""

    CALL_EXPR = "Call"
    VAR = "Var"
    STR = "String"
    REGEX = "Regex"
    # Boolean expressions
    BOOL = "Bool"
    CALL_EXPR_CONTEXT = "CallExprContext"
    HAVOC = "Havoc"
    CONJUNCTION = "Conjunction"
    DISJUNCTION = "Disjunction"
    NOT = "Not"
    # Juniper chains
    CONJUNCTION_CHAIN = "ConjunctionChain"
    FIRST_MATCH_CHAIN = "FirstMatchChain"
    # Record expressions
    GET_FIELD = "GetField"
    WITH_FIELD = "WithField"
    CREATE = "CreateRecord"
    # Pair expressions
    PAIR = "Pair"
    FIRST = "First"
    SECOND = "Second"
    # Set expressions
    LITERAL_SET = "LiteralSet"
    SET_ADD = "SetAdd"
    SET_UNION = "SetUnion"
    SET_REMOVE = "SetRemove"
    SET_DIFFERENCE = "SetDifference"
    SET_CONTAINS = "SetContains"
    SUBSET = "Subset"
    # Arithmetic expressions
    INT = "Int"
    UINT = "UInt"
    BIG_INT = "BigInt"
    ADD = "Add"
    SUB = "Sub"
    EQ = "Equal"
    NEQ = "NotEqual"
    LT = "LessThan"
    LE = "LessThanOrEqual"
    GT = "GreaterThan"
    GE = "GreaterThanOrEqual"
    # IP expressions
    IP_ADDRESS = "IpAddress"  # string e.g. 10.0.1.0
    IP_PREFIX = "IpPrefix"  # tuple (ipaddress, prefix width)
    PREFIX_CONTAINS = "PrefixContains"
    PREFIX_SET = "PrefixSet"
    MATCH_SET = "MatchSet"
    MATCH = "Match"

    def as_class(self) -> type:
        """Return the class associated with this ExprType."""
        match self:
            case ExprType.CALL_EXPR:
                return CallExpr
            case ExprType.VAR:
                return Var
            case ExprType.STR:
                return LiteralString
            case ExprType.REGEX:
                return Regex
            # booleans
            case ExprType.BOOL:
                return LiteralBool
            case ExprType.CALL_EXPR_CONTEXT:
                return CallExprContext
            case ExprType.HAVOC:
                return Havoc
            case ExprType.CONJUNCTION:
                return Conjunction
            case ExprType.DISJUNCTION:
                return Disjunction
            case ExprType.NOT:
                return Not
            # Juniper policy chains
            case ExprType.CONJUNCTION_CHAIN:
                return ConjunctionChain
            case ExprType.FIRST_MATCH_CHAIN:
                return FirstMatchChain
            # integers
            case ExprType.INT:
                return LiteralInt
            case ExprType.UINT:
                return LiteralUInt
            case ExprType.BIG_INT:
                return LiteralBigInt
            case ExprType.ADD:
                return Add
            case ExprType.SUB:
                return Sub
            case ExprType.EQ:
                return Equal
            case ExprType.NEQ:
                return NotEqual
            case ExprType.LT:
                return LessThan
            case ExprType.LE:
                return LessThanEqual
            case ExprType.GT:
                return GreaterThan
            case ExprType.GE:
                return GreaterThanEqual
            # sets
            case ExprType.LITERAL_SET:
                return LiteralSet
            case ExprType.SET_ADD:
                return SetAdd
            case ExprType.SET_DIFFERENCE:
                return SetDifference
            case ExprType.SET_REMOVE:
                return SetRemove
            case ExprType.SET_UNION:
                return SetUnion
            case ExprType.SET_CONTAINS:
                return SetContains
            case ExprType.SUBSET:
                return Subset
            # records
            case ExprType.CREATE:
                return CreateRecord
            case ExprType.GET_FIELD:
                return GetField
            case ExprType.WITH_FIELD:
                return WithField
            # pair
            case ExprType.PAIR:
                return Pair
            case ExprType.FIRST:
                return First
            case ExprType.SECOND:
                return Second
            # ip addresses
            case ExprType.IP_ADDRESS:
                return IpAddress
            case ExprType.IP_PREFIX:
                return IpPrefix
            case ExprType.PREFIX_CONTAINS:
                return PrefixContains
            case ExprType.PREFIX_SET:
                return PrefixSet
            case ExprType.MATCH_SET:
                return MatchSet
            case ExprType.MATCH:
                return Match
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class Expression(
    ASTNode,
    Generic[T],
    Serialize,
    delegate=(TYPE_FIELD, ExprType.parse_class),
    ty=Field(TYPE_FIELD, str, "Expression"),
):
    """
    The base class for expressions.
    """

    ty: str = field(default="Expression", init=False)

    def subst(self, _environment: dict[str, "Expression"]) -> "Expression":
        """
        Substitute all variable references to elements in the given environment
        in the expression.
        """
        return self


def default_value(ty: TypeAnnotation) -> Expression:
    """
    Return the default value for the given type.
    Note that not all types have default values.
    """
    match ty:
        case TypeAnnotation.BOOL:
            return LiteralBool(False)
        case TypeAnnotation.INT2:
            return LiteralInt(0, width=2)
        case TypeAnnotation.INT32:
            return LiteralInt(0, width=32)
        case TypeAnnotation.UINT2:
            return LiteralUInt(0, width=2)
        case TypeAnnotation.UINT32:
            return LiteralUInt(0, width=32)
        case TypeAnnotation.BIG_INT:
            return LiteralBigInt(0)
        case TypeAnnotation.SET:
            return LiteralSet([])
        case TypeAnnotation.STRING:
            return LiteralString("")
        case TypeAnnotation.IP_ADDRESS:
            return IpAddress(IPv4Address(0))
        case TypeAnnotation.IP_PREFIX:
            return IpPrefix(IPv4Network(0))
        case TypeAnnotation.ROUTE:
            return CreateRecord(
                {
                    field_name: default_value(field_ty)
                    for field_name, field_ty in RouteType.fields().items()
                },
                TypeAnnotation.ROUTE,
            )
        case TypeAnnotation.RESULT:
            return CreateRecord(
                {
                    field_name: default_value(field_ty)
                    for field_name, field_ty in ResultType.fields().items()
                },
                TypeAnnotation.RESULT,
            )
        case TypeAnnotation.ENVIRONMENT:
            return CreateRecord(
                {
                    field_name: default_value(field_ty)
                    for field_name, field_ty in EnvironmentType.fields().items()
                },
                TypeAnnotation.ENVIRONMENT,
            )
        case _:
            raise ValueError(f"Cannot produce a default value for type {ty}")


@dataclass
class CallExpr(
    Expression[T],
    Serialize,
    policy="Name",
    ty=Field(TYPE_FIELD, str, "Call"),
):
    """
    Call the given policy with the given argument.
    """

    policy: str
    ty: str = field(default="Call", init=False)


@dataclass
class CallExprContext(
    Expression[bool], Serialize, ty=Field(TYPE_FIELD, str, "CallExprContext")
):
    """
    A boolean sentinel value identifying if the current context was reached via a CallExpr.
    """

    ty: str = field(default="CallExprContext", init=False)


@dataclass
class Var(
    Expression[T], Serialize, _name=Field("Name", str), ty=Field(TYPE_FIELD, str, "Var")
):
    """A variable reference."""

    _name: str
    ty: str = field(default="Var", init=False)
    ty_arg: InitVar[TypeAnnotation] = field(
        default=TypeAnnotation.UNKNOWN, kw_only=True
    )

    def __post_init__(self, ty_arg: TypeAnnotation):
        self.ty = f"{self.ty}({ty_arg.value})"

    def subst(self, environment: dict[str, Expression]) -> Expression:
        if self._name in environment:
            return environment[self._name]
        else:
            return self


@dataclass
class LiteralBool(
    Expression[bool],
    Serialize,
    value=Field("Value", bool),
    ty=Field(TYPE_FIELD, str, "Bool"),
):
    """A boolean literal."""

    value: bool
    ty: str = field(default="Bool", init=False)


@dataclass
class Havoc(Expression[bool], Serialize, ty=Field(TYPE_FIELD, str, "Havoc")):
    """A boolean "havoc" value representing nondeterministic choice."""

    ty: str = field(default="Havoc", init=False)


@dataclass
class Conjunction(
    Expression[bool],
    Serialize,
    conjuncts=Field("Exprs", list[Expression[bool]]),
    ty=Field(TYPE_FIELD, str, "And"),
):
    """Boolean conjunction."""

    conjuncts: list[Expression[bool]]
    ty: str = field(default="And", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.conjuncts = [e.subst(environment) for e in self.conjuncts]
        return self


@dataclass
class FirstMatchChain(
    Expression[bool],
    Serialize,
    subroutines=Field("Subroutines", list[Expression]),
    ty=Field(TYPE_FIELD, str, "FirstMatchChain"),
):
    """
    (taken from Batfish's docs)
    Juniper subroutine chain.
    Evaluates a route against a series of routing policies in order.
    Return once the first matching subroutine is reached.
    """

    subroutines: list[Expression]
    ty: str = field(default="FirstMatchChain", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.subroutines = [e.subst(environment) for e in self.subroutines]
        return self


@dataclass
class ConjunctionChain(
    Expression[bool],
    Serialize,
    subroutines=Field("Subroutines", list[Expression]),
    ty=Field(TYPE_FIELD, str, "ConjunctionChain"),
):
    """
    DEPRECATED? (Could we replace this with Conjunction?)
    """

    subroutines: list[Expression]
    ty: str = field(default="ConjunctionChain", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.subroutines = [e.subst(environment) for e in self.subroutines]
        return self


@dataclass
class Disjunction(
    Expression[bool],
    Serialize,
    disjuncts=Field("Exprs", list[Expression[bool]]),
    ty=Field(TYPE_FIELD, str, "Or"),
):
    disjuncts: list[Expression[bool]]
    ty: str = field(default="Or", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.disjuncts = [e.subst(environment) for e in self.disjuncts]
        return self


@dataclass
class Not(
    Expression[bool],
    Serialize,
    expr=Field("Expr", Expression[bool]),
    ty=Field(TYPE_FIELD, str, "Not"),
):
    expr: Expression[bool]
    ty: str = field(default="Not", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.expr = self.expr.subst(environment)
        return self


@dataclass
class LiteralBigInt(
    Expression[int],
    Serialize,
    value=Field("Value", int),
    ty=Field(TYPE_FIELD, str, "BigInt"),
):
    value: int
    ty: str = field(default="BigInt", init=False)


@dataclass
class LiteralUInt(
    Expression[int],
    Serialize,
    value=Field("Value", int),
    ty=Field(TYPE_FIELD, str, "UInt32"),
):
    value: int
    ty: str = field(default="UInt", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"


@dataclass
class LiteralInt(
    Expression[int],
    Serialize,
    value=Field("Value", int),
    ty=Field(TYPE_FIELD, str, "Int32"),
):
    value: int
    ty: str = field(default="Int", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"


@dataclass
class Add(
    Expression[int],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field(TYPE_FIELD, str, "Plus32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="Plus", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class Sub(
    Expression[int],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field(TYPE_FIELD, str, "Sub32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="Sub", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class Equal(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field(TYPE_FIELD, str, "Equals32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="Equals", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class NotEqual(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field(TYPE_FIELD, str, "NotEqual32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="NotEqual", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class LessThan(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field(TYPE_FIELD, str, "LessThan32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="LessThan", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class LessThanEqual(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field(TYPE_FIELD, str, "LessThanEqual32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="LessThanEqual", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class GreaterThan(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field(TYPE_FIELD, str, "GreaterThan32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="GreaterThan", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class GreaterThanEqual(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field(TYPE_FIELD, str, "GreaterThanEqual32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="GreaterThanEqual", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class LiteralString(
    Expression[str], Serialize, value="Value", ty=Field(TYPE_FIELD, str, "String")
):
    value: str
    ty: str = field(default="String", init=False)


@dataclass
class Regex(
    Expression[str], Serialize, regex="Regex", ty=Field(TYPE_FIELD, str, "Regex")
):
    regex: str
    ty: str = field(default="Regex", init=False)


@dataclass
class LiteralSet(
    Expression[set],
    Serialize,
    elements=Field("elements", list[Expression[str]]),
    ty=Field(TYPE_FIELD, str, "LiteralSet"),
):
    elements: list[Expression[str]]
    ty: str = field(default="LiteralSet", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.elements = [e.subst(environment) for e in self.elements]
        return self


@dataclass
class SetAdd(
    Expression[set],
    Serialize,
    operand1=Field("Operand1", Expression[str]),
    operand2=Field("Operand2", Expression[set]),
    ty=Field(TYPE_FIELD, str, "SetAdd"),
):
    # expression to add
    operand1: Expression[str]
    # original set
    operand2: Expression[set]
    ty: str = field(default="SetAdd", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class SetUnion(
    Expression[set],
    Serialize,
    sets=Field("Exprs", list[Expression[set]]),
    ty=Field(TYPE_FIELD, str, "SetUnion"),
):
    sets: list[Expression[set]]
    ty: str = field(default="SetUnion", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.sets = [e.subst(environment) for e in self.sets]
        return self


@dataclass
class SetRemove(
    Expression[set],
    Serialize,
    operand1=Field("Operand1", Expression[str]),
    operand2=Field("Operand2", Expression[set]),
    ty=Field(TYPE_FIELD, str, "SetRemove"),
):
    # expression to remove
    operand1: Expression[str]
    # original set
    operand2: Expression[set]
    ty: str = field(default="SetRemove", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class SetDifference(
    Expression[set],
    Serialize,
    operand1=Field("Operand1", Expression[set]),
    operand2=Field("Operand2", Expression[set]),
    ty=Field(TYPE_FIELD, str, "SetDifference"),
):
    operand1: Expression[set]
    operand2: Expression[set]
    ty: str = field(default="SetDifference", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class SetContains(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[str]),
    operand2=Field("Operand2", Expression[set]),
    ty=Field(TYPE_FIELD, str, "SetContains"),
):
    operand1: Expression[str]
    operand2: Expression[set]
    ty: str = field(default="SetContains", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class Subset(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[set]),
    operand2=Field("Operand2", Expression[set]),
    ty=Field(TYPE_FIELD, str, "Subset"),
):
    operand1: Expression[set]
    operand2: Expression[set]
    ty: str = field(default="Subset", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.operand1 = self.operand1.subst(environment)
        self.operand2 = self.operand2.subst(environment)
        return self


@dataclass
class CreateRecord(
    Expression[dict[str, Expression]],
    Serialize,
    _fields=Field("Fields", dict[str, Expression]),
    record_ty=Field("RecordType", TypeAnnotation),
    ty=Field(TYPE_FIELD, str, "CreateRecord"),
):
    _fields: dict[str, Expression]
    record_ty: TypeAnnotation
    ty: str = field(default="CreateRecord", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self._fields = {
            fname: e.subst(environment) for fname, e in self._fields.items()
        }
        return self


@dataclass
class GetField(
    Expression[X],
    Serialize,
    rec=Field("Record", Expression[dict[str, Expression[X]]]),
    field_name=Field("FieldName", str),
    ty=Field(TYPE_FIELD, str, "GetField"),
    record_ty=Field("RecordType", str),
    field_ty=Field("FieldType", str),
):
    rec: Expression[dict[str, Expression[X]]]
    field_name: str
    ty: str = field(default="GetField", init=False)
    ty_args: InitVar[tuple[TypeAnnotation, TypeAnnotation]] = field(
        default=(TypeAnnotation.UNKNOWN, TypeAnnotation.UNKNOWN), kw_only=True
    )

    def __post_init__(self, ty_args: tuple[TypeAnnotation, TypeAnnotation]):
        self.ty = f"{self.ty}({ty_args[0].value};{ty_args[1].value})"
        self.record_ty = ty_args[0].value
        self.field_ty = ty_args[1].value

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.rec = self.rec.subst(environment)
        return self


@dataclass
class WithField(
    Expression[dict[str, Expression]],
    Serialize,
    rec=Field("Record", Expression[dict[str, Expression]]),
    field_name=Field("FieldName", str),
    field_val=Field("FieldValue", Expression),
    ty=Field(TYPE_FIELD, str, "WithField"),
    record_ty=Field("RecordType", str),
    field_ty=Field("FieldType", str),
):
    rec: Expression[dict[str, Expression]]
    field_name: str
    field_val: Expression
    ty: str = field(default="WithField", init=False)
    ty_args: InitVar[tuple[TypeAnnotation, TypeAnnotation]] = field(
        default=(TypeAnnotation.UNKNOWN, TypeAnnotation.UNKNOWN), kw_only=True
    )

    def __post_init__(self, ty_args: tuple[TypeAnnotation, TypeAnnotation]):
        self.ty = f"{self.ty}({ty_args[0].value};{ty_args[1].value})"
        self.record_ty = ty_args[0].value
        self.field_ty = ty_args[1].value

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.rec = self.rec.subst(environment)
        self.field_val = self.field_val.subst(environment)
        return self


@dataclass
class Pair(
    Expression[tuple[A, B]],
    Serialize,
    first=Field("First", Expression[A]),
    second=Field("Second", Expression[B]),
    ty=Field(TYPE_FIELD, str, "Pair"),
    first_ty=Field("FirstType", str),
    second_ty=Field("SecondType", str),
):
    first: Expression[A]
    second: Expression[B]
    ty: str = field(default="Pair", init=False)
    ty_args: InitVar[tuple[TypeAnnotation, TypeAnnotation]] = field(
        default=(TypeAnnotation.UNKNOWN, TypeAnnotation.UNKNOWN), kw_only=True
    )

    def __post_init__(self, ty_args: tuple[TypeAnnotation, TypeAnnotation]):
        self.ty = f"{self.ty}({ty_args[0].value};{ty_args[1].value})"
        self.first_ty = ty_args[0].value
        self.second_ty = ty_args[1].value

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.first = self.first.subst(environment)
        self.second = self.second.subst(environment)
        return self


@dataclass
class First(
    Expression[A],
    Generic[A, B],
    Serialize,
    pair=Field("Pair", Expression[tuple[A, B]]),
    ty=Field(TYPE_FIELD, str, "First"),
    first_ty=Field("FirstType", str),
    second_ty=Field("SecondType", str),
):
    pair: Expression[tuple[A, B]]
    ty: str = field(default="First", init=False)
    ty_args: InitVar[tuple[TypeAnnotation, TypeAnnotation]] = field(
        default=(TypeAnnotation.UNKNOWN, TypeAnnotation.UNKNOWN), kw_only=True
    )

    def __post_init__(self, ty_args: tuple[TypeAnnotation, TypeAnnotation]):
        self.ty = f"{self.ty}({ty_args[0].value};{ty_args[1].value})"
        self.first_ty = ty_args[0].value
        self.second_ty = ty_args[1].value

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.pair = self.pair.subst(environment)
        return self


@dataclass
class Second(
    Expression[B],
    Generic[A, B],
    Serialize,
    pair=Field("Pair", Expression[tuple[A, B]]),
    ty=Field(TYPE_FIELD, str, "Second"),
    first_ty=Field("FirstType", str),
    second_ty=Field("SecondType", str),
):
    pair: Expression[tuple[A, B]]
    ty: str = field(default="Second", init=False)
    ty_args: InitVar[tuple[TypeAnnotation, TypeAnnotation]] = field(
        default=(TypeAnnotation.UNKNOWN, TypeAnnotation.UNKNOWN), kw_only=True
    )

    def __post_init__(self, ty_args: tuple[TypeAnnotation, TypeAnnotation]):
        self.ty = f"{self.ty}({ty_args[0].value};{ty_args[1].value})"
        self.first_ty = ty_args[0].value
        self.second_ty = ty_args[1].value

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.pair = self.pair.subst(environment)
        return self


@dataclass
class IpAddress(
    Expression[IPv4Address],
    Serialize,
    ip=Field("Ip", IPv4Address),
    ty=Field(TYPE_FIELD, str, "IpAddress"),
):
    ip: IPv4Address
    ty: str = field(default="IpAddress", init=False)


@dataclass
class IpPrefix(
    Expression[IPv4Network],
    Serialize,
    ip=Field("Prefix", IPv4Network),
    ty=Field(TYPE_FIELD, str, "IpPrefix"),
):
    ip: IPv4Network
    ty: str = field(default="IpPrefix", init=False)


@dataclass
class PrefixContains(
    Expression[bool],
    Serialize,
    addr=Field("Addr", Expression[IPv4Address]),
    prefix=Field("Prefix", Expression[IPv4Network]),
    ty=Field(TYPE_FIELD, str, "PrefixContains"),
):
    addr: Expression[IPv4Address]
    prefix: Expression[IPv4Network]
    ty: str = field(default="PrefixContains", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.addr = self.addr.subst(environment)
        self.prefix = self.prefix.subst(environment)
        return self


@dataclass
class PrefixMatches(
    Expression[bool],
    Serialize,
    ip_wildcard=Field("IpWildcard", IPv4Interface),
    prefix_length_range="PrefixLengthRange",
    ty=Field(TYPE_FIELD, str, "PrefixMatches"),
):
    ip_wildcard: IPv4Interface
    prefix_length_range: str
    ty: str = field(default="PrefixMatches", init=False)


@dataclass
class PrefixSet(
    Expression[set[IPv4Interface]],
    Serialize,
    prefix_space=Field("PrefixSpace", list[IPv4Interface]),
    ty=Field(TYPE_FIELD, str, "PrefixSet"),
):
    prefix_space: list[IPv4Interface]
    ty: str = field(default="PrefixSet", init=False)


@dataclass
class CommunityMatches(
    Expression[bool],
    Serialize,
    community=Field("Community", LiteralString),
    ty=Field(TYPE_FIELD, str, "CommunityMatches"),
):
    community: LiteralString
    ty: str = field(default="CommunityMatches", init=False)


@dataclass
class MatchSet(
    Expression[bool],
    Serialize,
    permit=Field("Permit", Expression[bool]),
    deny=Field("Deny", Expression[bool]),
    ty=Field(TYPE_FIELD, str, "MatchSet"),
):
    permit: Expression[bool]
    deny: Expression[bool]
    ty: str = field(default="MatchSet", init=False)

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.permit = self.permit.subst(environment)
        self.deny = self.deny.subst(environment)
        return self


@dataclass
class Match(
    Expression[bool],
    Serialize,
    match_key=Field("MatchKey", Expression),
    match_set=Field("MatchSet", Expression[bool]),
):
    match_key: Expression[bool]
    match_set: Expression[bool]

    def subst(self, environment: dict[str, Expression]) -> Expression:
        self.match_key = self.match_key.subst(environment)
        self.match_set = self.match_set.subst(environment)
        return self
