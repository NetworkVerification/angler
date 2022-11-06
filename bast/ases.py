#!/usr/bin/env python3
"""
AS expressions in the Batfish AST.
"""
from dataclasses import dataclass
from serialize import Serialize, Field
import util
import bast.expression as expr
import bast.intexprs as ints


class AsExprType(util.Variant):
    EXPLICIT_AS = "ExplicitAs"
    LAST_AS = "LastAs"

    def as_class(self) -> type:
        match self:
            case AsExprType.LAST_AS:
                return LastAs
            case AsExprType.EXPLICIT_AS:
                return ExplicitAs
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class AsPathListExprType(util.Variant):
    LITERAL_AS_LIST = "LiteralAsList"
    MULTIPLIED_AS = "MultipliedAs"

    def as_class(self) -> type:
        match self:
            case AsPathListExprType.LITERAL_AS_LIST:
                return LiteralAsList
            case AsPathListExprType.MULTIPLIED_AS:
                return MultipliedAs
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


class AsPathExprType(util.Variant):
    INPUT_AS_PATH = "InputAsPath"

    def as_class(self) -> type:
        match self:
            case AsPathExprType.INPUT_AS_PATH:
                return InputAsPath
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
class AsPathExpr(
    expr.Expression, Serialize, delegate=("class", AsPathExprType.parse_class)
):
    ...


@dataclass
class AsPathSetExpr(
    expr.Expression, Serialize, delegate=("class", AsPathSetExprType.parse_class)
):
    ...


@dataclass
class LastAs(AsExpr, Serialize):
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


@dataclass
class MultipliedAs(
    AsPathListExpr,
    Serialize,
    expr=Field("expr", AsExpr),
    n=Field("number", ints.IntExpr),
):
    expr: AsExpr
    n: ints.IntExpr


@dataclass
class InputAsPath(AsPathExpr, Serialize):
    ...


@dataclass
class AsPathMatchExpr(expr.Expression, Serialize):
    ...
