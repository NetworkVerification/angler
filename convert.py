#!/usr/bin/env python3
"""
Conversion tools to transform Batfish AST terms to Angler AST terms.
"""
import bast.expression as bexpr
import bast.boolexprs as bools
import bast.communities as bcomms
import bast.longexprs as longs
import bast.prefix as prefix
from bast.btypes import Comparator
import aast.expression as aexpr

# the argument to the transfer
ARG = aexpr.Var("route")


def convert_expr(b: bexpr.Expression) -> aexpr.Expression:
    """
    Convert the given Batfish AST expression into an Angler AST expression.
    """
    match b:
        case bexpr.CallExpr(policy):
            return aexpr.CallExpr(policy)
        case bools.StaticBooleanExpr(ty=bools.StaticBooleanExprType.TRUE):
            return aexpr.LiteralTrue()
        case bools.StaticBooleanExpr(ty=bools.StaticBooleanExprType.FALSE):
            return aexpr.LiteralFalse()
        case bools.StaticBooleanExpr(ty=bools.StaticBooleanExprType.CALLCONTEXT):
            # NOTE: not supported
            return aexpr.Havoc()
        case bools.Conjunction(conjuncts):
            conj = [convert_expr(c) for c in conjuncts]
            return aexpr.Conjunction(conj)
        case bools.Disjunction(disjuncts):
            disj = [convert_expr(d) for d in disjuncts]
            return aexpr.Disjunction(disj)
        case bools.Not(e):
            return aexpr.Not(convert_expr(e))
        case bools.MatchIpv4():
            # NOTE: for now, we assume ipv4
            return aexpr.LiteralTrue()
        case bools.MatchIpv6 | bools.MatchPrefix6Set:
            # NOTE: not supported (for now, we assume ipv4)
            return aexpr.LiteralFalse()
        case bools.LegacyMatchAsPath:
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
        case bools.MatchCommunities(
            _comms, bcomms.HasCommunity(bcomms.CommunityIs(community))
        ):
            # check if community is in _comms
            return aexpr.SetContains(community, convert_expr(_comms))
        case bcomms.InputCommunities:
            return aexpr.GetField(ARG, "communities")
        case bcomms.CommunitySetReference(_name) | bcomms.CommunityMatchExprReference(
            _name
        ) | bcomms.CommunitySetMatchExprReference(_name):
            return aexpr.Var(_name)
        case longs.LiteralLong(value):
            return aexpr.LiteralInt(value)
        case longs.IncrementLocalPref(addend):
            return aexpr.Add(aexpr.GetField(ARG, "lp"), aexpr.LiteralInt(addend))
        case longs.DecrementLocalPref(subtrahend):
            return aexpr.Sub(aexpr.GetField(ARG, "lp"), aexpr.LiteralInt(subtrahend))
        case prefix.DestinationNetwork:
            return aexpr.GetField(ARG, "prefix")
        case prefix.NamedPrefixSet(_name):
            return aexpr.Var(_name)
        case bools.MatchPrefixSet(_prefix, _prefixes):
            return aexpr.PrefixContains(convert_expr(_prefix), convert_expr(_prefixes))
        case bools.MatchTag(cmp, tag):
            route_tag = aexpr.GetField(ARG, "tag")
            match cmp:
                case Comparator.EQ:
                    return aexpr.Equal(route_tag, convert_expr(tag))
                case Comparator.LE:
                    return aexpr.LessThanEqual(route_tag, convert_expr(tag))
                case Comparator.LT:
                    return aexpr.LessThan(route_tag, convert_expr(tag))
                case Comparator.GE:
                    return aexpr.GreaterThanEqual(route_tag, convert_expr(tag))
                case Comparator.GT:
                    return aexpr.GreaterThan(route_tag, convert_expr(tag))
        case _:
            raise NotImplementedError(f"No convert case for {b} found.")
