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
import bast.btypes as types
import bast.ases as ases
import bast.prefix as prefix
import bast.longexprs as longs
import aast.boolexprs as abools


class StaticBooleanExprType(Enum):
    CALLCONTEXT = "CallExprContext"
    FALSE = "False"
    TRUE = "True"


class BooleanExprType(ast.Variant):
    STATIC = "StaticBooleanExpr"
    CONJUNCTION = "Conjunction"
    CONJUNCTION_CHAIN = "ConjunctionChain"
    DISJUNCTION = "Disjunction"
    NOT = "Not"
    MATCH_PROTOCOL = "MatchProtocol"
    MATCH_IPV6 = "MatchIpv6"
    MATCH_IPV4 = "MatchIpv4"
    MATCH_PREFIXES = "MatchPrefixSet"
    MATCH_PREFIXES6 = "MatchPrefix6Set"
    LEGACY_MATCH_AS_PATH = "LegacyMatchAsPath"
    MATCH_TAG = "MatchTag"
    MATCH_COMMUNITIES = "MatchCommunities"
    COMMUNITY_MATCH_REGEX = "CommunityMatchRegex"
    COMMUNITY_IS = "CommunityIs"

    def as_class(self) -> type:
        match self:
            case BooleanExprType.STATIC:
                return StaticBooleanExpr
            case BooleanExprType.CONJUNCTION:
                return Conjunction
            case BooleanExprType.CONJUNCTION_CHAIN:
                return ConjunctionChain
            case BooleanExprType.DISJUNCTION:
                return Disjunction
            case BooleanExprType.NOT:
                return Not
            case BooleanExprType.LEGACY_MATCH_AS_PATH:
                return LegacyMatchAsPath
            case BooleanExprType.MATCH_TAG:
                return MatchTag
            case BooleanExprType.MATCH_COMMUNITIES:
                return MatchCommunities
            case BooleanExprType.COMMUNITY_IS:
                return CommunityIs
            case BooleanExprType.COMMUNITY_MATCH_REGEX:
                return CommunityMatchRegex
            case BooleanExprType.MATCH_PREFIXES:
                return MatchPrefixSet
            case BooleanExprType.MATCH_PREFIXES6:
                return MatchPrefix6Set
            case BooleanExprType.MATCH_PROTOCOL:
                return MatchProtocol
            case BooleanExprType.MATCH_IPV4:
                return MatchIpv4
            case BooleanExprType.MATCH_IPV6:
                return MatchIpv6
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class BooleanExpr(
    expr.Expression,
    Serialize,
    delegate=("class", BooleanExprType.parse_class),
):
    def to_aast(self) -> abools.BoolExpr:
        raise NotImplementedError()


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

    def to_aast(self) -> abools.Conjunction:
        return abools.Conjunction([e.to_aast() for e in self.conjuncts])


@dataclass
class ConjunctionChain(
    BooleanExpr, Serialize, subroutines=Field("subroutines", list[expr.Expression])
):
    subroutines: list[expr.Expression]


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
    _comms=Field("communitySetExpr", comms.CommunityExpr),
    _comms_match=Field("communitySetMatchExpr", comms.CommunityExpr),
):
    # the set of communities to match
    _comms: comms.CommunityExpr
    # the set to match against
    _comms_match: comms.CommunityExpr


@dataclass
class LegacyMatchAsPath(
    BooleanExpr,
    Serialize,
    expr=Field("expr", ases.AsPathSetExpr),
):
    expr: ases.AsPathSetExpr


@dataclass
class MatchPrefixSet(
    BooleanExpr,
    Serialize,
    _prefix=Field("prefix", prefix.PrefixExpr),
    _prefixes=Field("prefixSet", prefix.PrefixExpr),
):
    _prefix: prefix.PrefixExpr
    _prefixes: prefix.PrefixExpr


@dataclass
class MatchPrefix6Set(
    BooleanExpr,
    Serialize,
    _prefix=Field("prefix", prefix.PrefixExpr),
    _prefixes=Field("prefixSet", prefix.PrefixExpr),
):
    _prefix: prefix.PrefixExpr
    _prefixes: prefix.PrefixExpr


@dataclass
class MatchIpv6(
    BooleanExpr,
    Serialize,
):
    ...


@dataclass
class MatchIpv4(
    BooleanExpr,
    Serialize,
):
    ...


@dataclass
class MatchProtocol(
    BooleanExpr, Serialize, protocols=Field("protocols", list[types.Protocol])
):
    protocols: list[types.Protocol]


@dataclass
class MatchTag(
    BooleanExpr,
    Serialize,
    cmp=Field("cmp", types.Comparator),
    tag=Field("tag", longs.LongExpr),
):
    cmp: types.Comparator
    tag: longs.LongExpr
