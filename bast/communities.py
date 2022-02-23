#!/usr/bin/env python3
"""
BGP communities in the Batfish AST.
"""
from dataclasses import dataclass
from serialize import Serialize
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
    expr.Expression, Serialize, exprs=("exprs", list[expr.Expression])
):
    exprs: list[expr.Expression]


@dataclass
class CommunitySetMatchExpr(expr.Expression, Serialize, expr=("expr", expr.Expression)):
    expr: expr.Expression


@dataclass
class CommunitySetDifference(
    expr.Expression,
    Serialize,
    initial=("initial", expr.Expression),
    remove=("removalCriterion", expr.Expression),
):
    initial: expr.Expression
    remove: expr.Expression


@dataclass
class LiteralCommunitySet(
    expr.Expression, Serialize, comm_set=("communitySet", list[str])
):
    # TODO: parse the community set
    comm_set: list[str]


@dataclass
class InputCommunities(expr.Var):
    ...


@dataclass
class CommunitySetReference(expr.Var, Serialize, _name="name"):
    _name: str


@dataclass
class CommunitySetMatchExprReference(expr.Var, Serialize, _name="name"):
    _name: str


@dataclass
class CommunityMatchExprReference(expr.Var, Serialize, _name="name"):
    _name: str
