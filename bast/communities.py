#!/usr/bin/env python3
"""
BGP communities in the Batfish AST.
"""
from dataclasses import dataclass
from serialize import Serialize, Field
import bast.base as ast
import bast.expression as expr


class CommunityExprType(ast.Variant):
    INPUT_COMMUNITIES = "InputCommunities"  # variable
    LITERAL_COMMUNITIES = "LiteralCommunitySet"
    COMMUNITY_UNION = "CommunitySetUnion"
    COMMUNITY_DIFFERENCE = "CommunitySetDifference"
    COMMUNITIES_REF = "CommunitySetReference"
    COMMUNITIES_MATCH_REF = "CommunitySetMatchExprReference"
    COMMUNITY_MATCH_REF = "CommunityMatchExprReference"

    def as_class(self) -> type:
        match self:
            case CommunityExprType.INPUT_COMMUNITIES:
                return InputCommunities
            case CommunityExprType.LITERAL_COMMUNITIES:
                return LiteralCommunitySet
            case CommunityExprType.COMMUNITY_UNION:
                return CommunitySetUnion
            case CommunityExprType.COMMUNITY_DIFFERENCE:
                return CommunitySetDifference
            case CommunityExprType.COMMUNITIES_REF:
                return CommunitySetReference
            case CommunityExprType.COMMUNITIES_MATCH_REF:
                return CommunitySetMatchExprReference
            case CommunityExprType.COMMUNITY_MATCH_REF:
                return CommunityMatchExprReference
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class RenderingType(ast.Variant):
    COLONSEP = "ColonSeparatedRendering"
    INTVAL = "IntegerValueRendering"

    def as_class(self) -> type:
        match self:
            case RenderingType.COLONSEP:
                return ColonSeparatedRendering
            case _:
                raise NotImplementedError(
                    f"Rendering class for {self} not implemented."
                )


@dataclass
class CommunityRendering(
    ast.ASTNode,
    Serialize,
    delegate=(
        "class",
        RenderingType.parse_class,
    ),
):
    ...


@dataclass
class ColonSeparatedRendering(CommunityRendering, Serialize):
    ...


class CommunityExpr(expr.Expression, Serialize):
    ...


@dataclass
class CommunitySetUnion(
    CommunityExpr, Serialize, exprs=Field("exprs", list[CommunityExpr])
):
    exprs: list[CommunityExpr]


@dataclass
class CommunitySetMatchExpr(
    CommunityExpr, Serialize, expr=Field("expr", CommunityExpr)
):
    expr: CommunityExpr


@dataclass
class CommunitySetDifference(
    CommunityExpr,
    Serialize,
    initial=Field("initial", CommunityExpr),
    remove=Field("removalCriterion", CommunityExpr),
):
    initial: CommunityExpr
    remove: CommunityExpr


@dataclass
class LiteralCommunitySet(
    CommunityExpr, Serialize, comms=Field("communitySet", list[str])
):
    # TODO: parse the community set
    comms: list[str]


@dataclass
class InputCommunities(CommunityExpr, Serialize):
    ...


@dataclass
class CommunitySetReference(CommunityExpr, Serialize, _name="name"):
    _name: str


@dataclass
class CommunitySetMatchExprReference(CommunityExpr, Serialize, _name="name"):
    _name: str


@dataclass
class CommunityMatchExprReference(CommunityExpr, Serialize, _name="name"):
    _name: str
