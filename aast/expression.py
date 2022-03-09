"""
"""
from ipaddress import IPv4Address, IPv4Network
from dataclasses import dataclass
from typing import Generic, TypeVar
from serialize import Serialize, Field
from aast.base import Variant, ASTNode

T = TypeVar("T")
X = TypeVar("X")
A = TypeVar("A")
B = TypeVar("B")


class ExprType(Variant):
    """A type of expression."""

    CALL_EXPR = "CallExpr"
    VAR = "Variable"
    STR = "String"
    # Boolean expressions
    TRUE = "True"
    FALSE = "False"
    HAVOC = "Havoc"
    CONJUNCTION = "Conjunction"
    DISJUNCTION = "Disjunction"
    NOT = "Not"
    # Record expressions
    GET_FIELD = "GetField"
    WITH_FIELD = "WithField"
    CREATE = "CreateRecord"
    # Pair expressions
    PAIR = "Pair"
    FIRST = "First"
    SECOND = "Second"
    # Set expressions
    EMPTY_SET = "EmptySet"
    SET_UNION = "SetUnion"
    SET_ADD = "SetAdd"
    SET_REMOVE = "SetRemove"
    SET_CONTAINS = "SetContains"
    # Arithmetic expressions
    INT = "Int"
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

    def as_class(self) -> type:
        match self:
            case ExprType.CALL_EXPR:
                return CallExpr
            case ExprType.VAR:
                return Var
            case ExprType.STR:
                return LiteralString
            # booleans
            case ExprType.TRUE:
                return LiteralTrue
            case ExprType.FALSE:
                return LiteralFalse
            case ExprType.HAVOC:
                return Havoc
            case ExprType.CONJUNCTION:
                return Conjunction
            case ExprType.DISJUNCTION:
                return Disjunction
            case ExprType.NOT:
                return Not
            # integers
            case ExprType.INT:
                return LiteralInt
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
            case ExprType.EMPTY_SET:
                return EmptySet
            case ExprType.SET_ADD:
                return SetAdd
            case ExprType.SET_REMOVE:
                return SetRemove
            case ExprType.SET_UNION:
                return SetUnion
            case ExprType.SET_CONTAINS:
                return SetContains
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
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class Expression(
    ASTNode,
    Generic[T],
    Serialize,
    with_type="$type",
    delegate=("$type", ExprType.parse_class),
):
    """
    The base class for expressions.
    """

    ...


@dataclass
class CallExpr(Expression[T], Serialize, with_type="$type", policy="calledPolicyName"):
    """
    Call the given policy.
    """

    policy: str


@dataclass
class Var(Expression[T], Serialize, with_type="$type", _name=Field("name", str)):
    _name: str


@dataclass
class LiteralTrue(Expression[bool], Serialize, with_type="$type"):
    ...


@dataclass
class LiteralFalse(Expression[bool], Serialize, with_type="$type"):
    ...


@dataclass
class Havoc(Expression[bool], Serialize, with_type="$type"):
    ...


@dataclass
class Conjunction(
    Expression[bool],
    Serialize,
    with_type="$type",
    conjuncts=Field("conjuncts", list[Expression[bool]]),
):
    conjuncts: list[Expression[bool]]


@dataclass
class ConjunctionChain(
    Expression[bool],
    Serialize,
    with_type="$type",
    subroutines=Field("subroutines", list[Expression]),
):
    """
    DEPRECATED?
    """

    subroutines: list[Expression]


@dataclass
class Disjunction(
    Expression[bool],
    Serialize,
    with_type="$type",
    disjuncts=Field("disjuncts", list[Expression[bool]]),
):
    disjuncts: list[Expression[bool]]


@dataclass
class Not(
    Expression[bool], Serialize, with_type="$type", expr=Field("expr", Expression[bool])
):
    expr: Expression[bool]


@dataclass
class LiteralInt(
    Expression[int], Serialize, with_type="$type", value=Field("value", int)
):
    value: int


@dataclass
class Add(
    Expression[int],
    Serialize,
    with_type="$type",
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class Sub(
    Expression[int],
    Serialize,
    with_type="$type",
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class Equal(
    Expression[bool],
    Serialize,
    with_type="$type",
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class NotEqual(
    Expression[bool],
    Serialize,
    with_type="$type",
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class LessThan(
    Expression[bool],
    Serialize,
    with_type="$type",
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class LessThanEqual(
    Expression[bool],
    Serialize,
    with_type="$type",
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class GreaterThan(
    Expression[bool],
    Serialize,
    with_type="$type",
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class GreaterThanEqual(
    Expression[bool],
    Serialize,
    with_type="$type",
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class LiteralString(Expression[str], Serialize, with_type="$type", value="value"):
    value: str


@dataclass
class EmptySet(Expression[set], Serialize, with_type="$type"):
    ...


@dataclass
class SetAdd(
    Expression[set],
    Serialize,
    with_type="$type",
    to_add=Field("expr", Expression[str]),
    _set=Field("set", Expression[set]),
):
    to_add: Expression[str]
    _set: Expression[set]


@dataclass
class SetUnion(
    Expression[set],
    Serialize,
    with_type="$type",
    sets=Field("sets", list[Expression[set]]),
):
    sets: list[Expression[set]]


@dataclass
class SetRemove(
    Expression[set],
    Serialize,
    with_type="$type",
    to_remove=Field("expr", Expression[str]),
    _set=Field("set", Expression[set]),
):
    to_remove: Expression[str]
    _set: Expression[set]


@dataclass
class SetContains(
    Expression[bool],
    Serialize,
    with_type="$type",
    search=Field("search", Expression[str]),
    _set=Field("set", Expression[set]),
):
    search: Expression[str]
    _set: Expression[set]


@dataclass
class CreateRecord(
    Expression[dict[str, Expression[X]]],
    Serialize,
    with_type="$type",
    _fields=Field("fields", dict[str, Expression[X]]),
):
    _fields: dict[str, Expression[X]]


@dataclass
class GetField(
    Expression[X],
    Serialize,
    with_type="$type",
    rec=Field("record", Expression[dict[str, Expression[X]]]),
    field_name=Field("fieldName", str),
):
    rec: Expression[dict[str, Expression[X]]]
    field_name: str


@dataclass
class WithField(
    Expression[dict[str, Expression[X]]],
    Serialize,
    with_type="$type",
    rec=Field("record", Expression[dict[str, Expression[X]]]),
    field_name=Field("fieldName", str),
    field_val=Field("fieldVal", Expression[X]),
):
    rec: Expression[dict[str, Expression[X]]]
    field_name: str
    field_val: Expression[X]


@dataclass
class Pair(
    Expression[tuple[A, B]],
    Serialize,
    with_type="$type",
    first=Field("first", Expression[A]),
    second=Field("second", Expression[B]),
):
    first: Expression[A]
    second: Expression[B]


@dataclass
class First(
    Expression[A],
    Generic[A, B],
    Serialize,
    with_type="$type",
    pair=Field("pair", Expression[tuple[A, B]]),
):
    pair: Expression[tuple[A, B]]


@dataclass
class Second(
    Expression[B],
    Generic[A, B],
    Serialize,
    with_type="$type",
    pair=Field("pair", Expression[tuple[A, B]]),
):
    pair: Expression[tuple[A, B]]


@dataclass
class IpAddress(
    Expression[IPv4Address],
    Serialize,
    with_type="$type",
    ip=Field("ip", IPv4Address),
):
    ip: IPv4Address


@dataclass
class IpPrefix(
    Expression[IPv4Network],
    Serialize,
    with_type="$type",
    ip=Field("ip", IPv4Network),
):
    ip: IPv4Network


@dataclass
class PrefixContains(
    Expression[bool],
    Serialize,
    with_type="$type",
    addr=Field("addr", Expression[IPv4Address]),
    prefix=Field("prefix", Expression[IPv4Network]),
):
    addr: Expression[IPv4Address]
    prefix: Expression[IPv4Network]
