#!/usr/bin/env python3
"""
AS expressions in the Batfish AST.
"""
from dataclasses import dataclass
from serialize import Serialize, Field
import util
import bast.expression as expr


class AsExprType(util.Variant):
    EXPLICIT_AS = "ExplicitAs"

    def as_class(self) -> type:
        match self:
            case AsExprType.EXPLICIT_AS:
                return ExplicitAs
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class AsPathListExprType(util.Variant):
    LITERAL_AS_LIST = "LiteralAsList"

    def as_class(self) -> type:
        match self:
            case AsPathListExprType.LITERAL_AS_LIST:
                return LiteralAsList
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class AsPathSetExprType(util.Variant):
    EXPLICIT_AS_PATH_SET = "ExplicitAsPathSet"

    def as_class(self) -> type:
        match self:
            case AsPathSetExprType.EXPLICIT_AS_PATH_SET:
                return ExplicitAsPathSet
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class AsExpr(expr.Expression, Serialize, delegate=("class", AsExprType.parse_class)):
    ...


@dataclass
class AsPathListExpr(
    expr.Expression, Serialize, delegate=("class", AsPathListExprType.parse_class)
):
    ...


@dataclass
class AsPathSetExpr(
    expr.Expression, Serialize, delegate=("class", AsPathSetExprType.parse_class)
):
    ...


@dataclass
class ExplicitAs(AsExpr, Serialize, asnum=Field("as", int)):
    asnum: int


@dataclass
class RegexAsPathSetElem(expr.Expression, Serialize, regex="regex"):
    regex: str


@dataclass
class ExplicitAsPathSet(
    AsPathSetExpr, Serialize, elems=Field("elems", list[RegexAsPathSetElem])
):
    """
    DEPRECATED by Batfish.
    """

    elems: list[RegexAsPathSetElem]


@dataclass
class LiteralAsList(AsPathListExpr, Serialize, ases=Field("list", list[AsExpr])):
    ases: list[AsExpr]
