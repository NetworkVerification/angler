"""
"""
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
from dataclasses import InitVar, dataclass, field
from typing import Generic, TypeVar, Any
from serialize import Serialize, Field
from aast.base import Variant, ASTNode
from aast.types import TypeAnnotation

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
    MATCH_SET = "MatchSet"
    MATCH = "Match"

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
    delegate=("$type", ExprType.parse_class),
    ty=Field("$type", str, "Expression"),
):
    """
    The base class for expressions.
    """

    ty: str = field(default="Expression", init=False)


def from_class(e: Expression) -> ExprType:
    match e:
        case CallExpr():
            return ExprType.CALL_EXPR
        case Var():
            return ExprType.VAR
        case LiteralString():
            return ExprType.STR
        # booleans
        case LiteralTrue():
            return ExprType.TRUE
        case LiteralFalse():
            return ExprType.FALSE
        case Havoc():
            return ExprType.HAVOC
        case Conjunction():
            return ExprType.CONJUNCTION
        case Disjunction():
            return ExprType.DISJUNCTION
        case Not():
            return ExprType.NOT
        # integers
        case LiteralInt():
            return ExprType.INT
        case Add():
            return ExprType.ADD
        case Sub():
            return ExprType.SUB
        case Equal():
            return ExprType.EQ
        case NotEqual():
            return ExprType.NEQ
        case LessThan():
            return ExprType.LT
        case LessThanEqual():
            return ExprType.LE
        case GreaterThan():
            return ExprType.GT
        case GreaterThanEqual():
            return ExprType.GE
        # sets
        case EmptySet():
            return ExprType.EMPTY_SET
        case SetAdd():
            return ExprType.SET_ADD
        case SetRemove():
            return ExprType.SET_REMOVE
        case SetUnion():
            return ExprType.SET_UNION
        case SetContains():
            return ExprType.SET_CONTAINS
        # records
        case CreateRecord():
            return ExprType.CREATE
        case GetField():
            return ExprType.GET_FIELD
        case WithField():
            return ExprType.WITH_FIELD
        # pair
        case Pair():
            return ExprType.PAIR
        case First():
            return ExprType.FIRST
        case Second():
            return ExprType.SECOND
        # ip addresses
        case IpAddress():
            return ExprType.IP_ADDRESS
        case IpPrefix():
            return ExprType.IP_PREFIX
        case PrefixContains():
            return ExprType.PREFIX_CONTAINS
        case _:
            raise ValueError(f"No ExprType associated with {e.__class__}.")


# The type alias for route expressions
ROUTE = Expression[tuple[bool, dict[str, Any]]]


@dataclass
class CallExpr(
    Expression[T], Serialize, policy="CalledPolicyName", ty=Field("$type", str, "Call")
):
    """
    Call the given policy.
    """

    policy: str
    ty: str = field(default="Call", init=False)


@dataclass
class Var(
    Expression[T], Serialize, _name=Field("Name", str), ty=Field("$type", str, "Var")
):
    _name: str
    ty: str = field(default="Var", init=False)
    ty_arg: InitVar[TypeAnnotation] = field(
        default=TypeAnnotation.UNKNOWN, kw_only=True
    )

    def __post_init__(self, ty_arg: TypeAnnotation):
        self.ty = f"{self.ty}({ty_arg.value})"


@dataclass
class LiteralTrue(Expression[bool], Serialize, ty=Field("$type", str, "True")):
    ty: str = field(default="True", init=False)


@dataclass
class LiteralFalse(Expression[bool], Serialize, ty=Field("$type", str, "False")):
    ty: str = field(default="False", init=False)


@dataclass
class Havoc(Expression[bool], Serialize, ty=Field("$type", str, "Havoc")):
    ty: str = field(default="Havoc", init=False)


@dataclass
class Conjunction(
    Expression[bool],
    Serialize,
    conjuncts=Field("Conjuncts", list[Expression[bool]]),
    ty=Field("$type", str, "And"),
):
    conjuncts: list[Expression[bool]]
    ty: str = field(default="And", init=False)


@dataclass
class ConjunctionChain(
    Expression[bool],
    Serialize,
    subroutines=Field("Subroutines", list[Expression]),
):
    """
    DEPRECATED?
    """

    subroutines: list[Expression]


@dataclass
class Disjunction(
    Expression[bool],
    Serialize,
    disjuncts=Field("Disjuncts", list[Expression[bool]]),
    ty=Field("$type", str, "Or"),
):
    disjuncts: list[Expression[bool]]
    ty: str = field(default="Or", init=False)


@dataclass
class Not(
    Expression[bool],
    Serialize,
    expr=Field("Expr", Expression[bool]),
    ty=Field("$type", str, "Not"),
):
    expr: Expression[bool]
    ty: str = field(default="Not", init=False)


@dataclass
class LiteralInt(
    Expression[int],
    Serialize,
    value=Field("Value", int),
    ty=Field("$type", str, "Int32"),
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
    ty=Field("$type", str, "Plus32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="Plus", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"


@dataclass
class Sub(
    Expression[int],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field("$type", str, "Sub32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="Sub", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"


@dataclass
class Equal(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field("$type", str, "Equals32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="Equals", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"


@dataclass
class NotEqual(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field("$type", str, "NotEqual32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="NotEqual", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"


@dataclass
class LessThan(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field("$type", str, "LessThan32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="LessThan", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"


@dataclass
class LessThanEqual(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field("$type", str, "LessThanEqual32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="LessThanEqual", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"


@dataclass
class GreaterThan(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field("$type", str, "GreaterThan32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="GreaterThan", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"


@dataclass
class GreaterThanEqual(
    Expression[bool],
    Serialize,
    operand1=Field("Operand1", Expression[int]),
    operand2=Field("Operand2", Expression[int]),
    ty=Field("$type", str, "GreaterThanEqual32"),
):
    operand1: Expression[int]
    operand2: Expression[int]
    ty: str = field(default="GreaterThanEqual", init=False)
    width: InitVar[int] = field(default=32, kw_only=True)

    def __post_init__(self, width: int):
        self.ty = f"{self.ty}{width}"


@dataclass
class LiteralString(
    Expression[str], Serialize, value="Value", ty=Field("$type", str, "String")
):
    value: str
    ty: str = field(default="String", init=False)


@dataclass
class EmptySet(Expression[set], Serialize, ty=Field("$type", str, "EmptySet")):
    ty: str = field(default="EmptySet", init=False)


@dataclass
class SetAdd(
    Expression[set],
    Serialize,
    to_add=Field("Expr", Expression[str]),
    _set=Field("Set", Expression[set]),
    ty=Field("$type", str, "SetAdd"),
):
    to_add: Expression[str]
    _set: Expression[set]
    ty: str = field(default="SetAdd", init=False)


@dataclass
class SetUnion(
    Expression[set],
    Serialize,
    sets=Field("Sets", list[Expression[set]]),
    ty=Field("$type", str, "SetUnion"),
):
    sets: list[Expression[set]]
    ty: str = field(default="SetUnion", init=False)


@dataclass
class SetRemove(
    Expression[set],
    Serialize,
    to_remove=Field("Expr", Expression[str]),
    _set=Field("Set", Expression[set]),
    ty=Field("$type", str, "SetRemove"),
):
    to_remove: Expression[str]
    _set: Expression[set]
    ty: str = field(default="SetRemove", init=False)


@dataclass
class SetContains(
    Expression[bool],
    Serialize,
    search=Field("Search", Expression[str]),
    _set=Field("Set", Expression[set]),
    ty=Field("$type", str, "SetContains"),
):
    search: Expression[str]
    _set: Expression[set]
    ty: str = field(default="SetContains", init=False)


@dataclass
class CreateRecord(
    Expression[dict[str, Expression[X]]],
    Serialize,
    _fields=Field("Fields", dict[str, Expression[X]]),
    ty=Field("$type", str, "CreateRecord"),
):
    _fields: dict[str, Expression[X]]
    ty: str = field(default="CreateRecord", init=False)


@dataclass
class GetField(
    Expression[X],
    Serialize,
    rec=Field("Record", Expression[dict[str, Expression[X]]]),
    field_name=Field("FieldName", str),
    ty=Field("$type", str, "GetField"),
):
    rec: Expression[dict[str, Expression[X]]]
    field_name: str
    ty: str = field(default="GetField", init=False)
    ty_args: InitVar[tuple[TypeAnnotation, TypeAnnotation]] = field(
        default=(TypeAnnotation.UNKNOWN, TypeAnnotation.UNKNOWN), kw_only=True
    )

    def __post_init__(self, ty_args: tuple[TypeAnnotation, TypeAnnotation]):
        self.ty = f"{self.ty}({ty_args[0].value};{ty_args[1].value})"


@dataclass
class WithField(
    Expression[dict[str, Expression[X]]],
    Serialize,
    rec=Field("Record", Expression[dict[str, Expression[X]]]),
    field_name=Field("FieldName", str),
    field_val=Field("FieldValue", Expression[X]),
    ty=Field("$type", str, "WithField"),
):
    rec: Expression[dict[str, Expression[X]]]
    field_name: str
    field_val: Expression[X]
    ty: str = field(default="WithField", init=False)
    ty_args: InitVar[tuple[TypeAnnotation, TypeAnnotation]] = field(
        default=(TypeAnnotation.UNKNOWN, TypeAnnotation.UNKNOWN), kw_only=True
    )

    def __post_init__(self, ty_args: tuple[TypeAnnotation, TypeAnnotation]):
        self.ty = f"{self.ty}({ty_args[0].value};{ty_args[1].value})"


@dataclass
class Pair(
    Expression[tuple[A, B]],
    Serialize,
    first=Field("First", Expression[A]),
    second=Field("Second", Expression[B]),
    ty=Field("$type", str, "Pair"),
):
    first: Expression[A]
    second: Expression[B]
    ty: str = field(default="Pair", init=False)
    ty_args: InitVar[tuple[TypeAnnotation, TypeAnnotation]] = field(
        default=(TypeAnnotation.UNKNOWN, TypeAnnotation.UNKNOWN), kw_only=True
    )

    def __post_init__(self, ty_args: tuple[TypeAnnotation, TypeAnnotation]):
        self.ty = f"{self.ty}({ty_args[0].value};{ty_args[1].value})"


@dataclass
class First(
    Expression[A],
    Generic[A, B],
    Serialize,
    pair=Field("Pair", Expression[tuple[A, B]]),
    ty=Field("$type", str, "First"),
):
    pair: Expression[tuple[A, B]]
    ty: str = field(default="First", init=False)
    ty_args: InitVar[tuple[TypeAnnotation, TypeAnnotation]] = field(
        default=(TypeAnnotation.UNKNOWN, TypeAnnotation.UNKNOWN), kw_only=True
    )

    def __post_init__(self, ty_args: tuple[TypeAnnotation, TypeAnnotation]):
        self.ty = f"{self.ty}({ty_args[0].value};{ty_args[1].value})"


@dataclass
class Second(
    Expression[B],
    Generic[A, B],
    Serialize,
    pair=Field("Pair", Expression[tuple[A, B]]),
    ty=Field("$type", str, "Second"),
):
    pair: Expression[tuple[A, B]]
    ty: str = field(default="Second", init=False)
    ty_args: InitVar[tuple[TypeAnnotation, TypeAnnotation]] = field(
        default=(TypeAnnotation.UNKNOWN, TypeAnnotation.UNKNOWN), kw_only=True
    )

    def __post_init__(self, ty_args: tuple[TypeAnnotation, TypeAnnotation]):
        self.ty = f"{self.ty}({ty_args[0].value};{ty_args[1].value})"


@dataclass
class IpAddress(
    Expression[IPv4Address],
    Serialize,
    ip=Field("Ip", IPv4Address),
    ty=Field("$type", str, "IpAddress"),
):
    ip: IPv4Address
    ty: str = field(default="IpAddress", init=False)


@dataclass
class IpPrefix(
    Expression[IPv4Network],
    Serialize,
    ip=Field("Ip", IPv4Network),
    ty=Field("$type", str, "IpAddress"),
):
    ip: IPv4Network
    ty: str = field(default="IpPrefix", init=False)


@dataclass
class PrefixContains(
    Expression[bool],
    Serialize,
    addr=Field("Addr", Expression[IPv4Address]),
    prefix=Field("Prefix", Expression[IPv4Network]),
    ty=Field("$type", str, "PrefixContains"),
):
    addr: Expression[IPv4Address]
    prefix: Expression[IPv4Network]
    ty: str = field(default="PrefixContains", init=False)


@dataclass
class PrefixMatches(
    Expression[bool],
    Serialize,
    ip_wildcard=Field("IpWildcard", IPv4Interface),
    prefix_length_range="PrefixLengthRange",
    ty=Field("$type", str, "PrefixMatches"),
):
    ip_wildcard: IPv4Interface
    prefix_length_range: str
    ty: str = field(default="PrefixMatches", init=False)


@dataclass
class CommunityMatches(
    Expression[bool],
    Serialize,
    community=Field("Community", LiteralString),
    ty=Field("$type", str, "CommunityMatches"),
):
    community: LiteralString
    ty: str = field(default="CommunityMatches", init=False)


@dataclass
class MatchSet(
    Expression[bool],
    Serialize,
    permit=Field("Permit", Expression[bool]),
    deny=Field("Deny", Expression[bool]),
    ty=Field("$type", str, "MatchSet"),
):
    permit: Expression[bool]
    deny: Expression[bool]
    ty: str = field(default="MatchSet", init=False)


@dataclass
class Match(
    Expression[bool],
    Serialize,
    match_key=Field("MatchKey", Expression),
    match_set=Field("MatchSet", MatchSet),
):
    match_key: Expression
    match_set: MatchSet
