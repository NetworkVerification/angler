#!/usr/bin/env python3
"""
BGP communities in the Batfish AST.
A community is a 32-bit field composed of two parts:
a 16-bit AS number (the community's originator) and a 16-bit unique number
assigned by the AS.
QUESTION(tim): how would communities be used if we have 32-bit AS numbers?

Batfish distinguishes at least three classes representing communities.
- CommunitySetExpr: represents a literal set of BGP communities;
- CommunityMatchExpr: represents a matching condition (predicate) over a single BGP community;
- CommunitySetMatchExpr: represents a matching condition (predicate)  over a community set.
"""
from dataclasses import dataclass
from angler.serialize import Serialize, Field
import angler.bast.expression as expr
import angler.util


class CommunitySetExprType(angler.util.Variant):
    INPUT_COMMUNITIES = "InputCommunities"  # variable
    LITERAL_COMMUNITIES = "LiteralCommunitySet"
    COMMUNITY_UNION = "CommunitySetUnion"
    COMMUNITY_DIFFERENCE = "CommunitySetDifference"
    COMMUNITIES_REF = "CommunitySetReference"

    def as_class(self) -> type:
        match self:
            case CommunitySetExprType.INPUT_COMMUNITIES:
                return InputCommunities
            case CommunitySetExprType.LITERAL_COMMUNITIES:
                return LiteralCommunitySet
            case CommunitySetExprType.COMMUNITY_UNION:
                return CommunitySetUnion
            case CommunitySetExprType.COMMUNITY_DIFFERENCE:
                return CommunitySetDifference
            case CommunitySetExprType.COMMUNITIES_REF:
                return CommunitySetReference
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class CommunityMatchExprType(angler.util.Variant):
    COMMUNITY_MATCH_REF = "CommunityMatchExprReference"
    COMMUNITY_IS = "CommunityIs"
    COMMUNITY_MATCH_REGEX = "CommunityMatchRegex"
    ALL_STANDARD = "AllStandardCommunities"

    def as_class(self) -> type:
        match self:
            case CommunityMatchExprType.COMMUNITY_MATCH_REF:
                return CommunityMatchExprReference
            case CommunityMatchExprType.COMMUNITY_IS:
                return CommunityIs
            case CommunityMatchExprType.COMMUNITY_MATCH_REGEX:
                return CommunityMatchRegex
            case CommunityMatchExprType.ALL_STANDARD:
                return AllStandardCommunities
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class CommunitySetMatchExprType(angler.util.Variant):
    COMMUNITIES_MATCH_REF = "CommunitySetMatchExprReference"
    COMMUNITY_SET_MATCH_ALL = "CommunitySetMatchAll"
    HAS_COMMUNITY = "HasCommunity"

    def as_class(self) -> type:
        match self:
            case CommunitySetMatchExprType.COMMUNITIES_MATCH_REF:
                return CommunitySetMatchExprReference
            case CommunitySetMatchExprType.COMMUNITY_SET_MATCH_ALL:
                return CommunitySetMatchAll
            case CommunitySetMatchExprType.HAS_COMMUNITY:
                return HasCommunity
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class RenderingType(angler.util.Variant):
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
    angler.util.ASTNode,
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


@dataclass
class CommunitySetExpr(
    expr.Expression, Serialize, delegate=("class", CommunitySetExprType.parse_class)
):
    """An expression representing a community set."""

    ...


@dataclass
class CommunityMatchExpr(
    expr.Expression,
    Serialize,
    delegate=("class", CommunityMatchExprType.parse_class),
):
    """An expression representing a match condition on a specific community."""

    ...


@dataclass
class CommunitySetMatchExpr(
    expr.Expression,
    Serialize,
    delegate=("class", CommunitySetMatchExprType.parse_class),
):
    """An expression representing a match condition on a community set."""

    ...


@dataclass
class HasCommunity(
    CommunitySetMatchExpr, Serialize, expr=Field("expr", CommunityMatchExpr)
):
    """Match a community set iff it has a community that is matched by expr."""

    expr: CommunityMatchExpr


@dataclass
class CommunitySetMatchAll(
    CommunitySetMatchExpr, Serialize, exprs=Field("exprs", list[CommunitySetMatchExpr])
):
    """
    A list of community set match expressions.
    Semantically, this is a logical AND of all the given match expressions:
    see https://www.juniper.net/documentation/us/en/software/junos/bgp/topics/topic-map/routing-policies-communities.html
    """

    exprs: list[CommunitySetMatchExpr]


@dataclass
class CommunitySetUnion(
    CommunitySetExpr, Serialize, exprs=Field("exprs", list[CommunitySetExpr])
):
    exprs: list[CommunitySetExpr]


@dataclass
class CommunitySetDifference(
    CommunitySetExpr,
    Serialize,
    initial=Field("initial", CommunitySetExpr),
    remove=Field("removalCriterion", CommunityMatchExpr),
):
    initial: CommunitySetExpr
    remove: CommunityMatchExpr


@dataclass
class InputCommunities(CommunitySetExpr, Serialize):
    ...


@dataclass
class LiteralCommunitySet(
    CommunitySetExpr, Serialize, comms=Field("communitySet", list[str])
):
    # TODO: parse the community set
    comms: list[str]


@dataclass
class CommunityIs(CommunityMatchExpr, Serialize, community="community"):
    # TODO parse the community set: it appears to be two integers separated by a colon
    community: str


@dataclass
class CommunityMatchRegex(
    CommunityMatchExpr,
    Serialize,
    rendering=Field("communityRendering", CommunityRendering),
    regex="regex",
):
    rendering: CommunityRendering
    # TODO parse
    regex: str


@dataclass
class AllStandardCommunities(CommunityMatchExpr, Serialize):
    ...


@dataclass
class CommunitySetReference(CommunitySetExpr, Serialize, _name="name"):
    _name: str


@dataclass
class CommunityMatchExprReference(CommunityMatchExpr, Serialize, _name="name"):
    _name: str


@dataclass
class CommunitySetMatchExprReference(CommunitySetMatchExpr, Serialize, _name="name"):
    _name: str
