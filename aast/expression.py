from dataclasses import dataclass
from base import Variant, ASTNode
from serialize import Serialize, Field

class ExprType(Variant):
    """A type of expression."""

    VAR = "Variable"
    CONTAINER = "Container" # set or list
    # add, subtract
    SETUNION = "SetUnion"
    SETDIFFERENCE = "SetDifference"
    SETCONTAINMENT = "SetContainment"
    PREPEND = "Prepend" # add to front of list
    # value types (literals)
    INT = "Int"
    LIST = "List"
    SET = "Set"
    IPADDRESS = "IPaddress" # string e.g. 10.0.1.0
    IPPREFIX = "IPprefix" # tuple (ipaddress, prefix width)
    COMMUNITY = "Community" # tuple (AS number, tag) TODO: confirm
    CALL_EXPR = "CallExpr"

    def as_class(self) -> type:
        match self:
            case ExprType.CALL_EXPR:
                return CallExpr
            case ExprType.VAR:
                return Var
            # case ExprType.LITERAL:
            #     return Literal
            # case ExprType.CONTAINER:
            #     return Container
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
class Var(Expression, Serialize, name=Field("name", str)):
        name: str



