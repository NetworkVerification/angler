#!/usr/bin/env python3
"""
Route origin in the Batfish AST.
"""
from dataclasses import dataclass
from serialize import Serialize, Field
import bast.base as ast
import bast.expression as expr
import bast.btypes as types


class OriginExprType(ast.Variant):
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
