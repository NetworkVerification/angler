#!/usr/bin/env python3
"""
Boolean expressions in the Batfish AST.
"""
from dataclasses import dataclass
from enum import Enum
from serialize import Serialize, Field
import bast.base as ast
import bast.expression as expr
import bast.communities as comms


class StaticBooleanExprType(Enum):
    CALLCONTEXT = "CallExprContext"


class BooleanExprType(ast.Variant):
    STATIC = "StaticBooleanExpr"
    CONJUNCTION = "Conjunction"
    DISJUNCTION = "Disjunction"
    NOT = "Not"
    MATCHPROTOCOL = "MatchProtocol"
    MATCHPREFIXSET = "MatchPrefixSet"
    MATCHCOMMUNITIES = "MatchCommunities"
    COMMUNITYMATCHREGEX = "CommunityMatchRegex"
    COMMUNITYIS = "CommunityIs"

    def as_class(self) -> type:
        match self:
            case BooleanExprType.STATIC:
                return StaticBooleanExpr
            case BooleanExprType.CONJUNCTION:
                return Conjunction
            case BooleanExprType.DISJUNCTION:
                return Disjunction
            case BooleanExprType.NOT:
                return Not
            case BooleanExprType.MATCHCOMMUNITIES:
                return MatchCommunities
            case BooleanExprType.COMMUNITYIS:
                return CommunityIs
            case BooleanExprType.COMMUNITYMATCHREGEX:
                return CommunityMatchRegex
            case BooleanExprType.MATCHPREFIXSET:
                return MatchPrefixSet
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class BooleanExpr(
    expr.Expression,
    Serialize,
    delegate=("class", BooleanExprType.parse_class),
):
    ...


@dataclass
class StaticBooleanExpr(
    BooleanExpr, Serialize, ty=Field("type", StaticBooleanExprType)
):
    ty: StaticBooleanExprType


@dataclass
class Conjunction(
    BooleanExpr, Serialize, conjuncts=Field("conjuncts", list[BooleanExpr])
):
    conjuncts: list[BooleanExpr]


@dataclass
class Disjunction(
    BooleanExpr, Serialize, disjuncts=Field("disjuncts", list[BooleanExpr])
):
    disjuncts: list[BooleanExpr]


@dataclass
class Not(BooleanExpr, Serialize, expr=Field("expr", BooleanExpr)):
    expr: BooleanExpr


@dataclass
class CommunityIs(BooleanExpr, Serialize, community="community"):
    # TODO parse the community set: it appears to be two integers separated by a colon
    community: str


@dataclass
class CommunityMatchRegex(
    BooleanExpr, Serialize, rendering="communityRendering", regex="regex"
):
    rendering: comms.CommunityRendering
    # TODO parse
    regex: str


@dataclass
class MatchCommunities(
    BooleanExpr,
    Serialize,
    comm_set=Field("communitySetExpr", expr.Expression),
    comm_match=Field("communitySetMatchExpr", expr.Expression),
):
    # the set of communities to match
    comm_set: expr.Expression
    # the set to match against
    comm_match: expr.Expression


@dataclass
class MatchPrefixSet(
    BooleanExpr,
    Serialize,
    prefix=Field("prefix", expr.Expression),
    prefix_set=Field("prefixSet", expr.Expression),
):
    prefix: expr.Expression
    prefix_set: expr.Expression
