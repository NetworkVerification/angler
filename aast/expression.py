from dataclasses import dataclass
from serialize import Serialize, Field
from aast.base import Variant, ASTNode


class ExprType(Variant):
    """A type of expression."""

    CALL_EXPR = "CallExpr"
    VAR = "Variable"
    GET_FIELD = "GetField"
    WITH_FIELD = "WithField"
    # IPADDRESS = "IPaddress" # string e.g. 10.0.1.0
    # IPPREFIX = "IPprefix" # tuple (ipaddress, prefix width)
    # COMMUNITY = "Community" # tuple (AS number, tag) TODO: confirm

    def as_class(self) -> type:
        match self:
            case ExprType.CALL_EXPR:
                return CallExpr
            case ExprType.VAR:
                return Var
            case ExprType.GET_FIELD:
                return GetField
            case ExprType.WITH_FIELD:
                return WithField
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class Expression(
    ASTNode,
    Serialize,
    delegate=("class", ExprType.parse_class),
):
    """
    The base class for expressions.
    """

    ...


@dataclass
class CallExpr(Expression, Serialize, policy="calledPolicyName"):
    """
    Call the given policy.
    """

    policy: str


@dataclass
class Var(Expression, Serialize, _name=Field("name", str)):
    _name: str


class RecExprType(Variant):
    CREATE = "CreateRecord"

    def as_class(self) -> type:
        match self:
            case RecExprType.CREATE:
                return CreateRecord
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class RecExpr(Expression, Serialize, delegate=("class", RecExprType.parse_class)):
    ...


@dataclass
class CreateRecord(RecExpr, Serialize, _fields=Field("fields", dict[str, Expression])):
    _fields: dict[str, Expression]


@dataclass
class GetField(
    Expression,
    Serialize,
    rec=Field("record", RecExpr),
    field_name=Field("fieldName", str),
):
    rec: RecExpr
    field_name: str


@dataclass
class WithField(
    Expression,
    Serialize,
    rec=Field("record", RecExpr),
    field_name=Field("fieldName", str),
    field_val=Field("fieldVal", Expression),
):
    rec: RecExpr
    field_name: str
    field_val: Expression
