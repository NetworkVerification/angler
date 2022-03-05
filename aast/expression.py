"""
"""
from ipaddress import IPv4Address, IPv4Network
from dataclasses import dataclass
from typing import Generic, TypeVar
from serialize import Serialize, Field
from aast.base import Variant, ASTNode

T = TypeVar("T")
X = TypeVar("X")


class ExprType(Variant):
    """A type of expression."""

    CALL_EXPR = "CallExpr"
    VAR = "Variable"
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
    delegate=("class", ExprType.parse_class),
):
    """
    The base class for expressions.
    """

    ...


@dataclass
class CallExpr(Expression[T], Serialize, policy="calledPolicyName"):
    """
    Call the given policy.
    """

    policy: str


@dataclass
class Var(Expression[T], Serialize, _name=Field("name", str)):
    _name: str


@dataclass
class LiteralTrue(Expression[bool], Serialize):
    ...


@dataclass
class LiteralFalse(Expression[bool], Serialize):
    ...


@dataclass
class Havoc(Expression[bool], Serialize):
    ...


@dataclass
class Conjunction(
    Expression[bool],
    Serialize,
    conjuncts=Field("conjuncts", list[Expression[bool]]),
):
    conjuncts: list[Expression[bool]]


@dataclass
class ConjunctionChain(
    Expression[bool],
    Serialize,
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
    disjuncts=Field("disjuncts", list[Expression[bool]]),
):
    disjuncts: list[Expression[bool]]


@dataclass
class Not(Expression[bool], Serialize, expr=Field("expr", Expression[bool])):
    expr: Expression[bool]


@dataclass
class LiteralInt(Expression[int], Serialize, value=Field("value", int)):
    value: int


@dataclass
class Add(
    Expression[int],
    Serialize,
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class Sub(
    Expression[int],
    Serialize,
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class Equal(
    Expression[bool],
    Serialize,
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class NotEqual(
    Expression[bool],
    Serialize,
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class LessThan(
    Expression[bool],
    Serialize,
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class LessThanEqual(
    Expression[bool],
    Serialize,
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class GreaterThan(
    Expression[bool],
    Serialize,
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class GreaterThanEqual(
    Expression[bool],
    Serialize,
    operand1=Field("operand1", Expression[int]),
    operand2=Field("operand2", Expression[int]),
):
    operand1: Expression[int]
    operand2: Expression[int]


@dataclass
class EmptySet(Expression[set], Serialize):
    ...


@dataclass
class SetAdd(
    Expression[set],
    Serialize,
    to_add=Field("expr", str),
    _set=Field("set", Expression[set]),
):
    to_add: str
    _set: Expression[set]


@dataclass
class SetUnion(Expression[set], Serialize, sets=Field("sets", list[Expression[set]])):
    sets: list[Expression[set]]


@dataclass
class SetRemove(
    Expression[set],
    Serialize,
    to_remove=Field("expr", str),
    _set=Field("set", Expression[set]),
):
    to_remove: str
    _set: Expression[set]


@dataclass
class SetContains(
    Expression[bool], Serialize, search="search", _set=Field("set", Expression[set])
):
    search: str
    _set: Expression[set]


@dataclass
class CreateRecord(
    Expression[dict[str, Expression[X]]],
    Serialize,
    _fields=Field("fields", dict[str, Expression[X]]),
):
    _fields: dict[str, Expression[X]]


@dataclass
class GetField(
    Expression[X],
    Serialize,
    rec=Field("record", Expression[dict[str, Expression[X]]]),
    field_name=Field("fieldName", str),
):
    rec: Expression[dict[str, Expression[X]]]
    field_name: str


@dataclass
class WithField(
    Expression[dict[str, Expression[X]]],
    Serialize,
    rec=Field("record", Expression[dict[str, Expression[X]]]),
    field_name=Field("fieldName", str),
    field_val=Field("fieldVal", Expression[X]),
):
    rec: Expression[dict[str, Expression[X]]]
    field_name: str
    field_val: Expression[X]


@dataclass
class IpAddress(
    Expression[IPv4Address],
    Serialize,
    ip=Field("ip", IPv4Address),
):
    ip: IPv4Address


@dataclass
class IpPrefix(
    Expression[IPv4Network],
    Serialize,
    ip=Field("ip", IPv4Network),
):
    ip: IPv4Network


@dataclass
class PrefixContains(
    Expression[bool],
    Serialize,
    addr=Field("addr", Expression[IPv4Address]),
    prefix=Field("prefix", Expression[IPv4Network]),
):
    addr: Expression[IPv4Address]
    prefix: Expression[IPv4Network]
