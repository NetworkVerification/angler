#!/usr/bin/env python3
"""
Long expressions in the Batfish AST.
"""
from dataclasses import dataclass
from serialize import Serialize, Field
import bast.base as ast
import bast.expression as expr


class LongExprType(ast.Variant):
    LITERAL_LONG = "LiteralLong"
    DECREMENT_LOCAL_PREF = "DecrementLocalPreference"
    INCREMENT_LOCAL_PREF = "IncrementLocalPreference"

    def as_class(self) -> type:
        match self:
            case LongExprType.LITERAL_LONG:
                return LiteralLong
            case LongExprType.DECREMENT_LOCAL_PREF:
                return DecrementLocalPref
            case LongExprType.INCREMENT_LOCAL_PREF:
                return IncrementLocalPref
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class LongExpr(
    expr.Expression, Serialize, delegate=("class", LongExprType.parse_class)
):
    ...


@dataclass
class LiteralLong(LongExpr, Serialize, value=Field("value", int)):
    value: int


@dataclass
class IncrementLocalPref(LongExpr, Serialize, addend=Field("addend", int)):
    addend: int


@dataclass
class DecrementLocalPref(LongExpr, Serialize, subtrahend=Field("subtrahend", int)):
    subtrahend: int
