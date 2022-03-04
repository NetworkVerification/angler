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
    expr.Expression[int], Serialize, delegate=("class", ArithExprType.parse_class)
):
    ...


@dataclass
class LiteralInt(expr.Expression[int], Serialize, value=Field("value", int)):
    value: int


@dataclass
class Add(
    expr.Expression[int],
    Serialize,
    operand1=Field("operand1", expr.Expression[int]),
    operand2=Field("operand2", expr.Expression[int]),
):
    operand1: expr.Expression[int]
    operand2: expr.Expression[int]


@dataclass
class Sub(
    expr.Expression[int],
    Serialize,
    operand1=Field("operand1", expr.Expression[int]),
    operand2=Field("operand2", expr.Expression[int]),
):
    operand1: expr.Expression[int]
    operand2: expr.Expression[int]
