from dataclasses import dataclass
from aast.base import Variant
from serialize import Serialize, Field
import aast.expression as expr


class ArithExprType(Variant):
    LITERAL_INT = "LiteralInt"
    ADD = "Add"
    SUBTRACT = "Subtract"

    def as_class(self) -> type:
        match self:
            case ArithExprType.LITERAL_INT:
                return LiteralInt
            case ArithExprType.ADD:
                return Add
            case ArithExprType.SUBTRACT:
                return Sub
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class ArithExpr(
    expr.Expression, Serialize, delegate=("class", ArithExprType.parse_class)
):
    ...


@dataclass
class LiteralInt(ArithExpr, Serialize, value=Field("value", int)):
    value: int


@dataclass
class Add(
    ArithExpr,
    Serialize,
    operand1=Field("operand1", ArithExpr),
    operand2=Field("operand2", ArithExpr),
):
    operand1: ArithExpr
    operand2: ArithExpr


@dataclass
class Sub(
    ArithExpr,
    Serialize,
    operand1=Field("operand1", ArithExpr),
    operand2=Field("operand2", ArithExpr),
):
    operand1: ArithExpr
    operand2: ArithExpr
