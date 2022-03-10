#!/usr/bin/env python3
"""
Conversion tools to transform Batfish AST terms to Angler AST terms.
"""
import functools
import bast.expression as bexpr
import bast.statement as bstmt
import bast.boolexprs as bools
import bast.communities as bcomms
import bast.longexprs as longs
import bast.prefix as prefix
from bast.btypes import Comparator, Protocol
import bast.structure as struct
import bast.json as json
import aast.expression as aexpr
import aast.statement as astmt
import aast.program as prog

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
        case bools.ConjunctionChain(subroutines) if len(subroutines) == 1:
            # NOTE: for now, we're just handling cases where there is only one subroutine
            return convert_expr(subroutines[0])
        case bools.Disjunction(disjuncts):
            disj = [convert_expr(d) for d in disjuncts]
            return aexpr.Disjunction(disj)
        case bools.Not(e):
            return aexpr.Not(convert_expr(e))
        case bools.MatchIpv4():
            # NOTE: for now, we assume ipv4
            return aexpr.LiteralTrue()
        case bools.MatchIpv6() | bools.MatchPrefix6Set():
            # NOTE: not supported (for now, we assume ipv4)
            return aexpr.LiteralFalse()
        case bools.LegacyMatchAsPath():
            # NOTE: not supported
            return aexpr.Havoc()
        case bcomms.CommunityIs(community):
            return aexpr.LiteralString(community)
        case bcomms.LiteralCommunitySet(comms):
            # add each community to the set one-by-one
            e = aexpr.EmptySet()
            for comm in comms:
                e = aexpr.SetAdd(aexpr.LiteralString(comm), e)
            return e
        case bcomms.CommunitySetUnion(exprs):
            aes = [convert_expr(expr) for expr in exprs]
            return aexpr.SetUnion(aes)
        case bcomms.CommunitySetDifference(initial, bcomms.AllStandardCommunities()):
            # NOTE: assuming all communities are standard communities
            # remove all communities
            return aexpr.EmptySet()
        case bcomms.CommunitySetDifference(initial, to_remove):
            # remove a single community from the set
            return aexpr.SetRemove(convert_expr(to_remove), convert_expr(initial))
        case bools.MatchCommunities(_comms, bcomms.HasCommunity(expr)):
            # check if community is in _comms
            return aexpr.SetContains(convert_expr(expr), convert_expr(_comms))
        case bools.MatchCommunities(
            _comms, bcomms.CommunitySetMatchExprReference(_name)
        ):
            cvar = aexpr.Var(_name)
            return aexpr.SetContains(cvar, convert_expr(_comms))
        case bcomms.InputCommunities():
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
        case prefix.DestinationNetwork():
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
        case bools.MatchProtocol(protocols):
            # TODO: for now, return true if Protocol.BGP is in protocols, and false otherwise
            if Protocol.BGP in protocols:
                return aexpr.LiteralTrue()
            else:
                return aexpr.LiteralFalse()
        case _:
            raise NotImplementedError(f"No convert case for {b} found.")


def convert_stmt(b: bstmt.Statement) -> astmt.Statement:
    """
    Convert a Batfish AST statement into an Angler AST statement.
    """
    match b:
        case bstmt.IfStatement(
            comment=comment, guard=guard, t_stmts=t_stmts, f_stmts=f_stmts
        ):
            # convert the arms of the batfish if into seq statements
            return astmt.IfStatement(
                convert_expr(guard),
                convert_stmts(t_stmts),
                convert_stmts(f_stmts),
                comment,
            )

        case bstmt.SetCommunities(comm_set=comm_set):
            return astmt.AssignStatement(
                ARG, aexpr.WithField(ARG, "communities", convert_expr(comm_set))
            )

        case bstmt.SetLocalPreference(lp=lp):
            return astmt.AssignStatement(
                ARG, aexpr.WithField(ARG, "lp", convert_expr(lp))
            )

        case bstmt.SetMetric(metric=metric):
            return astmt.AssignStatement(
                ARG, aexpr.WithField(ARG, "metric", convert_expr(metric))
            )

        case bstmt.SetNextHop():
            # TODO: for now, ignore nexthop
            # return astmt.AssignStatement(
            #     ARG, aexpr.WithField(ARG, "nexthop", convert_expr(nexthop_expr))
            # )
            return astmt.SkipStatement()
        case bstmt.StaticStatement(ty=ty):
            match ty:
                case bstmt.StaticStatementType.TRUE | bstmt.StaticStatementType.EXIT_ACCEPT:
                    fst = aexpr.LiteralTrue()
                case bstmt.StaticStatementType.FALSE | bstmt.StaticStatementType.EXIT_REJECT:
                    fst = aexpr.LiteralFalse()
                case bstmt.StaticStatementType.LOCAL_DEF | bstmt.StaticStatementType.RETURN | bstmt.StaticStatementType.FALL_THROUGH:
                    fst = aexpr.GetField(ARG, "LocalDefaultAction")
                case _:
                    raise NotImplementedError(
                        f"No convert case for static statement {ty} found."
                    )
            # return a bool * route pair
            pair = aexpr.Pair(fst, ARG)
            return astmt.ReturnStatement(pair)
        case bstmt.PrependAsPath():
            return astmt.SkipStatement()
        case bstmt.TraceableStatement(inner=inner):
            return convert_stmts(inner)
        case _:
            raise NotImplementedError(f"No convert case for {b} found.")


def convert_stmts(stmts: list[bstmt.Statement]) -> astmt.Statement:
    """Convert a list of Batfish statements into an Angler statement."""
    # use a match to simplify the case where we generate a Seq(Skip, s) element when stmts = [s]
    match stmts:
        case []:
            return astmt.SkipStatement()
        case [s]:
            return convert_stmt(s)
        case _:
            # convert each statement, then reduce them all to a sequence
            return functools.reduce(astmt.SeqStatement, map(convert_stmt, stmts))


def convert_batfish(bf: json.BatfishJson) -> prog.Program:
    """
    Convert the Batfish JSON object to an Angler program.
    """
    edges = bf.topology
    nodes = {}
    for edge in edges:
        # get the names of the hosts
        src = edge.iface.host
        src_ips = edge.ips
        snk = edge.remote_iface.host
        snk_ips = edge.remote_ips
        if src in nodes:
            pol = nodes[src].policies
            if snk in pol:
                # TODO: add import/export policy
                for peer_conf in bf.bgp:
                    if peer_conf.node.nodename == src:
                        print("foo")
            else:
                pol[snk] = prog.Policies()
        else:
            nodes[src] = prog.Properties()
    decls = {}
    for decl in bf.declarations:
        match decl.definition.value:
            case struct.RoutingPolicy(policyname, statements):
                body = convert_stmts(statements)
                decls[policyname] = prog.Func("route", body)
            case _:
                print(
                    f"Encountered {decl.definition.value.__class__} which has no handler."
                )

    return prog.Program(route={}, nodes=nodes, declarations=decls)
