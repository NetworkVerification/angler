#!/usr/bin/env python3
"""
Conversion tools to transform Batfish AST terms to Angler AST terms.
"""
from ipaddress import IPv4Address, IPv4Network
from typing import TypeVar
import bast.json as json
import bast.expression as bexpr
import bast.statement as bstmt
import bast.boolexprs as bools
import bast.communities as bcomms
import bast.longexprs as longs
import bast.prefix as prefix
import bast.acl as bacl
import bast.vrf as bvrf
from bast.btypes import Comparator, Protocol, Action
import bast.structure as bstruct
import aast.expression as aexpr
import aast.statement as astmt
import aast.types as atys
import aast.program as prog

ARG = aexpr.Var("pair", ty_arg=atys.TypeAnnotation.PAIR)
# the route record passed through the transfer
ROUTE = aexpr.Var("route", ty_arg=atys.TypeAnnotation.ROUTE)

FIELDS = {
    "prefix": atys.TypeAnnotation.IP_ADDRESS,
    "lp": atys.TypeAnnotation.INT32,
    "metric": atys.TypeAnnotation.INT32,
    "communities": atys.TypeAnnotation.SET,
    "tag": atys.TypeAnnotation.INT32,
}


def accept() -> astmt.ReturnStatement:
    """Default accept return."""
    pair = aexpr.Pair(
        aexpr.LiteralTrue(),
        ROUTE,
        ty_args=(atys.TypeAnnotation.BOOL, atys.TypeAnnotation.ROUTE),
    )
    return astmt.ReturnStatement(pair, ty_arg=atys.TypeAnnotation.PAIR)


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
            cvar = aexpr.Var(_name, ty_arg=atys.TypeAnnotation.STRING)
            return aexpr.SetContains(cvar, convert_expr(_comms))
        case bcomms.InputCommunities():
            return aexpr.GetField(
                ROUTE,
                "communities",
                ty_args=(atys.TypeAnnotation.ROUTE, atys.TypeAnnotation.SET),
            )
        case bcomms.CommunitySetReference(_name):
            return aexpr.Var(_name, ty_arg=atys.TypeAnnotation.SET)
        case bcomms.CommunitySetMatchExprReference(
            _name
        ) | bcomms.CommunityMatchExprReference(_name):
            return aexpr.Var(_name)
        case longs.LiteralLong(value):
            return aexpr.LiteralInt(value)
        case longs.IncrementLocalPref(addend):
            x = aexpr.LiteralInt(addend)
            return aexpr.Add(
                aexpr.GetField(
                    ROUTE,
                    "lp",
                    ty_args=(atys.TypeAnnotation.ROUTE, atys.TypeAnnotation.INT32),
                ),
                x,
            )
        case longs.DecrementLocalPref(subtrahend):
            x = aexpr.LiteralInt(subtrahend)
            return aexpr.Sub(
                aexpr.GetField(
                    ROUTE,
                    "lp",
                    ty_args=(atys.TypeAnnotation.ROUTE, atys.TypeAnnotation.INT32),
                ),
                aexpr.LiteralInt(subtrahend),
            )
        case prefix.DestinationNetwork():
            return aexpr.GetField(
                ROUTE,
                "prefix",
                ty_args=(atys.TypeAnnotation.ROUTE, atys.TypeAnnotation.IP_ADDRESS),
            )
        case prefix.NamedPrefixSet(_name):
            return aexpr.Var(_name, ty_arg=atys.TypeAnnotation.PREFIX_SET)
        case bools.MatchPrefixSet(_prefix, _prefixes):
            return aexpr.PrefixContains(convert_expr(_prefix), convert_expr(_prefixes))
        case bools.MatchTag(cmp, tag):
            route_tag = aexpr.GetField(
                ROUTE,
                "tag",
                ty_args=(atys.TypeAnnotation.ROUTE, atys.TypeAnnotation.INT32),
            )
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
            comment=comment, guard=guard, true_stmts=t_stmts, false_stmts=f_stmts
        ):
            # convert the arms of the if
            true_stmt = convert_stmts(t_stmts)
            false_stmt = convert_stmts(f_stmts)
            # check that the types coincide: if either true_stmt or false_stmt ends in a return,
            # the other must as well
            if true_stmt.returns() and false_stmt.returns():
                ty_arg = atys.TypeAnnotation.PAIR
            if true_stmt.returns() and not false_stmt.returns():
                false_stmt = astmt.SeqStatement(false_stmt, accept())
                ty_arg = atys.TypeAnnotation.PAIR
            elif not true_stmt.returns() and false_stmt.returns():
                true_stmt = astmt.SeqStatement(true_stmt, accept())
                ty_arg = atys.TypeAnnotation.PAIR
            else:
                ty_arg = atys.TypeAnnotation.UNIT
            return astmt.IfStatement(
                comment=comment,
                guard=convert_expr(guard),
                true_stmt=true_stmt,
                false_stmt=false_stmt,
                ty_arg=ty_arg,
            )

        case bstmt.SetCommunities(comm_set=comms):
            wf = aexpr.WithField(
                ROUTE,
                "communities",
                convert_expr(comms),
                ty_args=(atys.TypeAnnotation.ROUTE, atys.TypeAnnotation.SET),
            )
            return astmt.AssignStatement(ROUTE, wf, ty_arg=atys.TypeAnnotation.ROUTE)

        case bstmt.SetLocalPreference(lp=lp):
            wf = aexpr.WithField(
                ROUTE,
                "lp",
                convert_expr(lp),
                ty_args=(atys.TypeAnnotation.ROUTE, atys.TypeAnnotation.SET),
            )
            return astmt.AssignStatement(ROUTE, wf, ty_arg=atys.TypeAnnotation.ROUTE)

        case bstmt.SetMetric(metric=metric):
            wf = aexpr.WithField(
                ROUTE,
                "metric",
                convert_expr(metric),
                ty_args=(atys.TypeAnnotation.ROUTE, atys.TypeAnnotation.INT32),
            )
            return astmt.AssignStatement(ROUTE, wf, ty_arg=atys.TypeAnnotation.ROUTE)

        case bstmt.SetNextHop():
            # TODO: for now, ignore nexthop
            # return astmt.AssignStatement(
            #     ROUTE, aexpr.WithField(ROUTE, "nexthop", convert_expr(nexthop_expr))
            # )
            return astmt.SkipStatement()
        case bstmt.StaticStatement(ty=ty):
            match ty:
                case bstmt.StaticStatementType.TRUE | bstmt.StaticStatementType.EXIT_ACCEPT:
                    # TODO: should EXIT_ACCEPT skip any successive policies?
                    fst = aexpr.LiteralTrue()
                case bstmt.StaticStatementType.FALSE | bstmt.StaticStatementType.EXIT_REJECT:
                    fst = aexpr.LiteralFalse()
                case bstmt.StaticStatementType.LOCAL_DEF | bstmt.StaticStatementType.RETURN | bstmt.StaticStatementType.FALL_THROUGH:
                    fst = aexpr.GetField(
                        ROUTE,
                        "LocalDefaultAction",
                        ty_args=(atys.TypeAnnotation.ROUTE, atys.TypeAnnotation.BOOL),
                    )
                case _:
                    raise NotImplementedError(
                        f"No convert case for static statement {ty} found."
                    )
            # return a bool * route pair
            pair = aexpr.Pair(
                fst,
                ROUTE,
                ty_args=(atys.TypeAnnotation.BOOL, atys.TypeAnnotation.ROUTE),
            )
            return astmt.ReturnStatement(pair, ty_arg=atys.TypeAnnotation.PAIR)
        case bstmt.PrependAsPath():
            return astmt.SkipStatement()
        case bstmt.TraceableStatement(inner=inner):
            return convert_stmts(inner)
        case _:
            raise NotImplementedError(f"No convert_stmt case for statement {b} found.")


def convert_stmts(stmts: list[bstmt.Statement]) -> astmt.Statement:
    """Convert a list of Batfish statements into an Angler statement."""
    # use a match to simplify the case where we generate a Seq(Skip, s) element when stmts = [s]
    match [convert_stmt(s) for s in stmts]:
        case []:
            return astmt.SkipStatement()
        case [hd, *tl]:
            # filter out extra skips and reduce list to nested SeqStatements
            for s in tl:
                if not isinstance(s, astmt.SkipStatement):
                    # TODO: re-add type annotations
                    hd = astmt.SeqStatement(hd, s)
            return hd
            # return functools.reduce(
            #     astmt.SeqStatement,
            #     [s for s in l if not isinstance(s, astmt.SkipStatement)],
            # )
        case _:
            raise Exception("unreachable")


T = TypeVar("T")


def bind_stmt(body: astmt.Statement[tuple[bool, T]]) -> astmt.Statement[tuple[bool, T]]:
    """
    Return a new statement which maps the old statement onto the second
    element of a (bool, T) pair, which is only executed if the bool is true.
    Its behavior is thus equivalent to Option.bind in a functional language,
    where the pair is returned unchanged if the bool is false.
    """
    guard = aexpr.First(
        ARG, ty_args=(atys.TypeAnnotation.BOOL, atys.TypeAnnotation.ROUTE)
    )
    # assign ROUTE from the second element of the pair
    assign_route = astmt.AssignStatement(
        ROUTE,
        aexpr.Second(
            ARG, ty_args=(atys.TypeAnnotation.BOOL, atys.TypeAnnotation.ROUTE)
        ),
        ty_arg=atys.TypeAnnotation.ROUTE,
    )
    return_pair = astmt.ReturnStatement(ARG, ty_arg=atys.TypeAnnotation.PAIR)
    return astmt.IfStatement(
        "bind",
        guard,
        astmt.SeqStatement(assign_route, body, ty_arg=atys.TypeAnnotation.PAIR),
        return_pair,
        ty_arg=atys.TypeAnnotation.PAIR,
    )


def convert_batfish(bf: json.BatfishJson) -> prog.Program:
    """
    Convert the Batfish JSON object to an Angler program.
    """
    edges = bf.topology
    nodes: dict[str, prog.Properties] = {}
    for edge in edges:
        # get the names of the hosts
        src = edge.iface.host
        # src_ips = edge.ips
        snk = edge.remote_iface.host
        # snk_ips = edge.remote_ips
        if src in nodes:
            pol = nodes[src].policies
            if snk in pol:
                for peer_conf in bf.bgp:
                    if peer_conf.node.nodename == src:
                        pol[snk].imp.extend(peer_conf.import_policy)
                        pol[snk].exp.extend(peer_conf.export_policy)
            else:
                pol[snk] = prog.Policies()
        else:
            nodes[src] = prog.Properties()
    for s in bf.declarations:
        n, k, v = convert_structure(s)
        match v:
            case prog.Func():
                nodes[n].declarations[k] = v
            case aexpr.Expression():
                nodes[n].consts[k] = v
            case IPv4Address():
                nodes[n].prefixes.append(IPv4Network((v, 24)))
            case None:
                pass

    return prog.Program(route=FIELDS, nodes=nodes)


def convert_structure(
    b: bstruct.Structure,
) -> tuple[str, str, prog.Func | aexpr.Expression | IPv4Address | None]:
    node_name = b.node.nodename
    struct_name: str = b.struct_name
    value = None
    match b.definition.value:
        case bstruct.RoutingPolicy(policyname=name, statements=stmts):
            print(f"Routing policy {b.struct_name}")
            # convert the statements and then add a bind check to capture
            # the semantics of potentially dropping the route
            body = bind_stmt(convert_stmts(stmts))
            struct_name = name
            value = prog.Func(ARG._name, body)
        case bacl.RouteFilterList(_name=name, lines=lines):
            print(f"Route filter list {b.struct_name}")
            permit_disjuncts = []
            deny_disjuncts = []
            prev_conds = []
            for l in lines:
                cond = aexpr.PrefixMatches(l.ip_wildcard, l.length_range)

                not_prev: list[aexpr.Expression[bool]] = [
                    aexpr.Not(c) for c in prev_conds
                ]

                if len(not_prev) > 0:
                    curr_matches = aexpr.Conjunction(not_prev + [cond])
                else:
                    curr_matches = cond

                if l.action == Action.PERMIT:
                    permit_disjuncts.append(curr_matches)
                else:
                    deny_disjuncts.append(curr_matches)

                prev_conds.append(cond)

            struct_name = name
            value = aexpr.MatchSet(
                permit=aexpr.Disjunction(permit_disjuncts),
                deny=aexpr.Disjunction(deny_disjuncts),
            )

            # TODO: What is the default action if no rule matches?

        case bcomms.HasCommunity(e):
            print(f"HasCommunity {b.struct_name}")
            value = convert_expr(e)
        case bacl.Acl(name=name):
            # TODO
            struct_name = name
        case bvrf.Vrf(vrfname="default", bgp=bgp) if bgp is not None:
            value = bgp.router
        case bacl.Route6FilterList(_name=name):
            # TODO
            struct_name = name
        case _:
            raise NotImplementedError(f"No convert case for {b} found.")
    return node_name, struct_name, value
