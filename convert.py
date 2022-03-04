#!/usr/bin/env python3
"""
Conversion tools to transform Batfish AST terms to Angler AST terms.
"""
from typing import Generic, Optional, TypeVar, cast
import bast.base as bast
import bast.expression as bexpr
import bast.boolexprs as bbools
import bast.communities as bcomms
import aast.base as aast
import aast.expression as aexpr
import aast.boolexprs as abools
import aast.sets as asets

BT = TypeVar("BT", bound=bast.ASTNode)
AT = TypeVar("AT", bound=aast.ASTNode)


class ToAast(Generic[AT, BT]):
    """
    Class decorator to add a to_aast implementation to a given subclass
    of bast.base.ASTNode.
    to_aast converts this bast.base.ASTNode into an equivalent aast.base.ASTNode.
    """

    def __init__(self, ty: Optional[type[AT]] = None, **kwargs):
        self.ty = ty
        self.kwargs = kwargs

    def __call__(self, cls: type[BT]) -> type[BT]:

        _kwargs = self.kwargs
        ty = self.ty

        def to_aast(self: BT) -> AT:
            if ty is None:
                raise NotImplementedError()
            else:
                kwargs = {k: getattr(self, v) for k, v in _kwargs.items()}
                return ty(**kwargs)

        setattr(cls, to_aast.__name__, to_aast)
        return cls


def convert_expr(b: bexpr.Expression) -> aexpr.Expression:
    """
    Convert the given Batfish AST expression into an Angler AST expression.
    """
    match b:
        case bexpr.CallExpr(policy):
            return aexpr.CallExpr(policy)
        case bbools.StaticBooleanExpr(ty=bbools.StaticBooleanExprType.TRUE):
            return abools.LiteralTrue()
        case bbools.StaticBooleanExpr(ty=bbools.StaticBooleanExprType.FALSE):
            return abools.LiteralFalse()
        case bbools.StaticBooleanExpr(ty=bbools.StaticBooleanExprType.CALLCONTEXT):
            # NOTE: not supported
            return abools.Havoc()
        case bbools.Conjunction(conjuncts):
            return abools.Conjunction(
                [cast(abools.BoolExpr, convert(conjunct)) for conjunct in conjuncts]
            )
        case bbools.Disjunction(disjuncts):
            adisj: list[abools.BoolExpr] = [
                cast(abools.BoolExpr, convert(d)) for d in disjuncts
            ]
            return abools.Disjunction(adisj)
        case bbools.Not(e):
            return abools.Not(cast(abools.BoolExpr, convert(e)))
        case bbools.MatchIpv4():
            # NOTE: for now, we assume ipv4
            return abools.LiteralTrue()
        case bbools.MatchIpv6 | bbools.MatchPrefix6Set:
            # NOTE: not supported (for now, we assume ipv4)
            return abools.LiteralFalse()
        case bbools.LegacyMatchAsPath:
            # NOTE: not supported
            return abools.Havoc()
        case bcomms.LiteralCommunitySet(comms):
            # add each community to the set one-by-one
            e = asets.EmptySet()
            for comm in comms:
                e = asets.SetAdd(comm, e)
            return e
        case bcomms.CommunitySetUnion(exprs):
            aes = [cast(asets.SetExpr, convert(expr)) for expr in exprs]
            return asets.SetUnion(aes)
        case bcomms.CommunitySetDifference(initial, bcomms.CommunityIs(community)):
            ainitial = cast(asets.SetExpr, convert(initial))
            return asets.SetRemove(community, ainitial)
        case _:
            raise NotImplementedError(f"No convert case for {b} found.")
