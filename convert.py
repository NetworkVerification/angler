#!/usr/bin/env python3
"""
Conversion tools to transform Batfish AST terms to Angler AST terms.
"""
import bast.expression as bexpr
import bast.boolexprs as bbools
import bast.communities as bcomms
import bast.longexprs as blongs
import aast.expression as aexpr


def convert_expr(b: bexpr.Expression) -> aexpr.Expression:
    """
    Convert the given Batfish AST expression into an Angler AST expression.
    """
    match b:
        case bexpr.CallExpr(policy):
            return aexpr.CallExpr(policy)
        case bbools.StaticBooleanExpr(ty=bbools.StaticBooleanExprType.TRUE):
            return aexpr.LiteralTrue()
        case bbools.StaticBooleanExpr(ty=bbools.StaticBooleanExprType.FALSE):
            return aexpr.LiteralFalse()
        case bbools.StaticBooleanExpr(ty=bbools.StaticBooleanExprType.CALLCONTEXT):
            # NOTE: not supported
            return aexpr.Havoc()
        case bbools.Conjunction(conjuncts):
            conj = [convert_expr(c) for c in conjuncts]
            return aexpr.Conjunction(conj)
        case bbools.Disjunction(disjuncts):
            disj = [convert_expr(d) for d in disjuncts]
            return aexpr.Disjunction(disj)
        case bbools.Not(e):
            return aexpr.Not(convert_expr(e))
        case bbools.MatchIpv4():
            # NOTE: for now, we assume ipv4
            return aexpr.LiteralTrue()
        case bbools.MatchIpv6 | bbools.MatchPrefix6Set:
            # NOTE: not supported (for now, we assume ipv4)
            return aexpr.LiteralFalse()
        case bbools.LegacyMatchAsPath:
            # NOTE: not supported
            return aexpr.Havoc()
        case bcomms.LiteralCommunitySet(comms):
            # add each community to the set one-by-one
            e = aexpr.EmptySet()
            for comm in comms:
                e = aexpr.SetAdd(comm, e)
            return e
        case bcomms.CommunitySetUnion(exprs):
            aes = [convert_expr(expr) for expr in exprs]
            return aexpr.SetUnion(aes)
        case bcomms.CommunitySetDifference(initial, bcomms.CommunityIs(community)):
            # remove a single community from the set
            return aexpr.SetRemove(community, convert_expr(initial))
        case bbools.MatchCommunities(
            _comms, bcomms.HasCommunity(bcomms.CommunityIs(community))
        ):
            # check if community is in _comms
            return aexpr.SetContains(community, convert_expr(_comms))
        case bcomms.InputCommunities:
            arg = aexpr.Var("route")
            return aexpr.GetField(arg, "communities")
        case bcomms.CommunitySetReference(_name) | bcomms.CommunityMatchExprReference(
            _name
        ) | bcomms.CommunitySetMatchExprReference(_name):
            return aexpr.Var(_name)
        case blongs.LiteralLong(value):
            return aexpr.LiteralInt(value)
        case blongs.IncrementLocalPref(addend):
            arg = aexpr.Var("route")
            return aexpr.Add(aexpr.GetField(arg, "lp"), aexpr.LiteralInt(addend))
        case blongs.DecrementLocalPref(subtrahend):
            arg = aexpr.Var("route")
            return aexpr.Sub(aexpr.GetField(arg, "lp"), aexpr.LiteralInt(subtrahend))
        case _:
            raise NotImplementedError(f"No convert case for {b} found.")
