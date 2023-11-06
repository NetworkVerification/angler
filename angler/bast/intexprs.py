#!/usr/bin/env python3
"""
Integer expressions in the Batfish AST.
"""
from dataclasses import dataclass
from angler.serialize import Serialize, Field
import angler.bast.expression as expr
import angler.util


class IntExprType(angler.util.Variant):
    LITERAL_INT = "LiteralInt"

    def as_class(self) -> type:
        match self:
            case IntExprType.LITERAL_INT:
                return LiteralInt
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class IntExpr(expr.Expression, Serialize, delegate=("class", IntExprType.parse_class)):
    ...


@dataclass
class LiteralInt(IntExpr, Serialize, value=Field("value", int)):
    value: int
