#!/usr/bin/env python3
"""
Route origin in the Batfish AST.
"""
from dataclasses import dataclass
from angler.serialize import Serialize, Field
import angler.bast.expression as expr
import angler.bast.btypes as types
import angler.util


class OriginExprType(angler.util.Variant):
    LITERAL_ORIGIN = "LiteralOrigin"

    def as_class(self):
        match self:
            case OriginExprType.LITERAL_ORIGIN:
                return LiteralOrigin
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class OriginExpr(
    expr.Expression, Serialize, delegate=("class", OriginExprType.parse_class)
):
    ...


@dataclass
class LiteralOrigin(
    OriginExpr, Serialize, origin_type=Field("originType", types.OriginType)
):
    origin_type: types.OriginType
