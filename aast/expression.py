from dataclasses import dataclass
from serialize import Serialize, Field
from aast.base import Variant, ASTNode


class ExprType(Variant):
    """A type of expression."""

    CALL_EXPR = "CallExpr"
    VAR = "Variable"
    # IPADDRESS = "IPaddress" # string e.g. 10.0.1.0
    # IPPREFIX = "IPprefix" # tuple (ipaddress, prefix width)
    # COMMUNITY = "Community" # tuple (AS number, tag) TODO: confirm

    def as_class(self) -> type:
        match self:
            case ExprType.CALL_EXPR:
                return CallExpr
            case ExprType.VAR:
                return Var
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
