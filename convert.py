#!/usr/bin/env python3
"""
Conversion tools to transform Batfish AST terms to Angler AST terms.
"""
from ipaddress import IPv4Address, IPv4Network
from typing import Optional, TypeVar
import igraph
from bast.base import OwnedIP
import bast.json as json
import bast.topology as topology
import bast.expression as bexpr
import bast.statement as bstmt
import bast.boolexprs as bools
import bast.communities as bcomms
import bast.longexprs as longs
import bast.intexprs as ints
import bast.prefix as prefix
import bast.acl as bacl
import bast.vrf as bvrf
import bast.origin as borigin
from bast.btypes import Comparator, Protocol, Action
import bast.structure as bstruct
import aast.expression as aexpr
import aast.statement as astmt
import aast.types as atys
import aast.program as prog
import aast.temporal as temp
from query import Query

# the transfer argument
ARG = "env"
ARG_VAR = aexpr.Var(ARG)


def default_value(ty: atys.TypeAnnotation) -> aexpr.Expression:
    """
    Return the default value for the given type.
    Note that not all types have default values.
    """
    match ty:
        case atys.TypeAnnotation.BOOL:
            return aexpr.LiteralBool(False)
        case atys.TypeAnnotation.INT2:
            return aexpr.LiteralInt(0, width=2)
        case atys.TypeAnnotation.INT32:
            return aexpr.LiteralInt(0, width=32)
        case atys.TypeAnnotation.UINT2:
            return aexpr.LiteralUInt(0, width=2)
        case atys.TypeAnnotation.UINT32:
            return aexpr.LiteralUInt(0, width=32)
        case atys.TypeAnnotation.SET:
            return aexpr.LiteralSet([])
        case atys.TypeAnnotation.STRING:
            return aexpr.LiteralString("")
        case atys.TypeAnnotation.IP_ADDRESS:
            return aexpr.IpAddress(IPv4Address(0))
        case atys.TypeAnnotation.IP_PREFIX:
            return aexpr.IpPrefix(IPv4Network(0))
        case atys.TypeAnnotation.ROUTE:
            return aexpr.CreateRecord(
                {
                    field_name: default_value(field_ty)
                    for field_name, field_ty in atys.EnvironmentType.fields().items()
                },
                atys.TypeAnnotation.ROUTE,
            )
        case atys.TypeAnnotation.RESULT:
            return aexpr.CreateRecord(
                {
                    field_name: default_value(field_ty)
                    for field_name, field_ty in atys.ResultType.fields().items()
                },
                atys.TypeAnnotation.RESULT,
            )
        case atys.TypeAnnotation.ENVIRONMENT:
            return aexpr.CreateRecord(
                {
                    field_name: default_value(field_ty)
                    for field_name, field_ty in atys.EnvironmentType.fields().items()
                },
                atys.TypeAnnotation.ENVIRONMENT,
            )
        case _:
            raise ValueError(f"Cannot produce a default value for type {ty}")


def convert_expr(b: bexpr.Expression) -> aexpr.Expression:
    """
    Convert the given Batfish AST expression into an Angler AST expression.
    """
    match b:
        case bools.CallExpr(policy):
            return aexpr.CallExpr(policy)
        case bools.StaticBooleanExpr(ty=bools.StaticBooleanExprType.TRUE):
            return aexpr.LiteralBool(True)
        case bools.StaticBooleanExpr(ty=bools.StaticBooleanExprType.FALSE):
            return aexpr.LiteralBool(False)
        case bools.StaticBooleanExpr(ty=bools.StaticBooleanExprType.CALLCONTEXT):
            # NOTE: not supported
            return aexpr.Havoc()
        case bools.Conjunction(conjuncts):
            conj = [convert_expr(c) for c in conjuncts]
            return aexpr.Conjunction(conj)
        case bools.ConjunctionChain(subroutines) if len(subroutines) == 1:
            # NOTE: for now, we're just handling cases where there is only one subroutine
            return convert_expr(subroutines[0])
        case bools.FirstMatchChain(subroutines):
            # FIXME: handle this properly
            for _ in subroutines:
                # evaluate the subroutine
                ...
            return aexpr.GetField(
                ARG_VAR,
                atys.EnvironmentType.LOCAL_DEFAULT_ACTION.value,
                ty_args=(
                    atys.TypeAnnotation.ENVIRONMENT,
                    atys.EnvironmentType.LOCAL_DEFAULT_ACTION.field_type(),
                ),
            )
        case bools.Disjunction(disjuncts):
            disj = [convert_expr(d) for d in disjuncts]
            return aexpr.Disjunction(disj)
        case bools.Not(e):
            return aexpr.Not(convert_expr(e))
        case bools.MatchIpv4():
            # NOTE: for now, we assume ipv4
            return aexpr.LiteralBool(True)
        case bools.MatchIpv6() | bools.MatchPrefix6Set():
            # NOTE: not supported (for now, we assume ipv4)
            return aexpr.LiteralBool(False)
        case bools.LegacyMatchAsPath():
            # NOTE: not supported
            return aexpr.Havoc()
        case bcomms.CommunityIs(community):
            return aexpr.LiteralString(community)
        case bcomms.LiteralCommunitySet(comms):
            return aexpr.LiteralSet([aexpr.LiteralString(comm) for comm in comms])
        case bcomms.CommunitySetUnion(exprs):
            aes = [convert_expr(expr) for expr in exprs]
            return aexpr.SetUnion(aes)
        case bcomms.CommunitySetDifference(initial, bcomms.AllStandardCommunities()):
            # NOTE: assuming all communities are standard communities
            # remove all communities
            return aexpr.LiteralSet([])
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
            return aexpr.GetField(
                ARG_VAR,
                atys.EnvironmentType.COMMS.value,
                ty_args=(
                    atys.TypeAnnotation.ENVIRONMENT,
                    atys.EnvironmentType.COMMS.field_type(),
                ),
            )
        case bcomms.CommunitySetReference(_name):
            return aexpr.Var(_name)
        case bcomms.CommunitySetMatchExprReference(
            _name
        ) | bcomms.CommunityMatchExprReference(_name):
            return aexpr.Var(_name)
        case bcomms.HasCommunity(e):
            # extract the underlying community
            return convert_expr(e)
        case bcomms.CommunityMatchRegex(_):
            # NOTE: for now, we treat regexes as havoc
            return aexpr.Havoc()
        case ints.LiteralInt(value):
            # TODO: should this be signed or unsigned?
            return aexpr.LiteralUInt(value)
        case longs.LiteralLong(value):
            # TODO: should this be signed or unsigned?
            return aexpr.LiteralUInt(value)
        case longs.IncrementLocalPref(addend):
            x = aexpr.LiteralUInt(addend)
            return aexpr.Add(
                aexpr.GetField(
                    ARG_VAR,
                    atys.EnvironmentType.LP.value,
                    ty_args=(
                        atys.TypeAnnotation.ENVIRONMENT,
                        atys.EnvironmentType.LP.field_type(),
                    ),
                ),
                x,
            )
        case longs.DecrementLocalPref(subtrahend):
            x = aexpr.LiteralUInt(subtrahend)
            return aexpr.Sub(
                aexpr.GetField(
                    ARG_VAR,
                    atys.EnvironmentType.LP.value,
                    ty_args=(
                        atys.TypeAnnotation.ENVIRONMENT,
                        atys.EnvironmentType.LP.field_type(),
                    ),
                ),
                x,
            )
        case prefix.DestinationNetwork():
            return aexpr.GetField(
                ARG_VAR,
                atys.EnvironmentType.PREFIX.value,
                ty_args=(
                    atys.TypeAnnotation.ENVIRONMENT,
                    atys.EnvironmentType.PREFIX.field_type(),
                ),
            )
        case prefix.NamedPrefixSet(_name):
            return aexpr.Var(_name)
        case prefix.ExplicitPrefixSet(prefix_space):
            return aexpr.PrefixSet(prefix_space)
        case borigin.LiteralOrigin(origin_type):
            return aexpr.LiteralUInt(origin_type.to_int(), width=2)
        case bools.MatchPrefixSet(_prefix, _prefixes):
            return aexpr.PrefixContains(convert_expr(_prefix), convert_expr(_prefixes))
        case bools.MatchTag(cmp, tag):
            route_tag = aexpr.GetField(
                ARG_VAR,
                atys.EnvironmentType.TAG.value,
                ty_args=(
                    atys.TypeAnnotation.ENVIRONMENT,
                    atys.EnvironmentType.TAG.field_type(),
                ),
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
                return aexpr.LiteralBool(True)
            else:
                return aexpr.LiteralBool(False)
        case _:
            raise NotImplementedError(f"No convert case for {b} found.")


def update_result(
    _value: aexpr.Expression | bool | None = None,
    _exit: aexpr.Expression | bool | None = None,
    _fallthrough: aexpr.Expression | bool | None = None,
    _return: aexpr.Expression | bool | None = None,
) -> aexpr.Expression:
    """
    Convert the given Batfish result into an Angler WithField expression to update the environment.
    """
    arg_expr = ARG_VAR
    if _value is not None:
        value_update = (
            _value
            if isinstance(_value, aexpr.Expression)
            else aexpr.LiteralBool(_value)
        )
        arg_expr = aexpr.WithField(
            arg_expr, atys.EnvironmentType.RESULT_VALUE.value, value_update
        )
    if _exit is not None:
        exit_update = (
            _exit if isinstance(_exit, aexpr.Expression) else aexpr.LiteralBool(_exit)
        )
        arg_expr = aexpr.WithField(
            arg_expr, atys.EnvironmentType.RESULT_EXIT.value, exit_update
        )
    if _fallthrough is not None:
        fallthrough_update = (
            _fallthrough
            if isinstance(_fallthrough, aexpr.Expression)
            else aexpr.LiteralBool(_fallthrough)
        )
        arg_expr = aexpr.WithField(
            arg_expr,
            atys.EnvironmentType.RESULT_FALLTHRU.value,
            fallthrough_update,
        )
    if _return is not None:
        return_update = (
            _return
            if isinstance(_return, aexpr.Expression)
            else aexpr.LiteralBool(_return)
        )
        arg_expr = aexpr.WithField(
            arg_expr, atys.EnvironmentType.RESULT_RETURN.value, return_update
        )
    return arg_expr


def convert_stmt(b: bstmt.Statement) -> list[astmt.Statement]:
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
            # check if both arms are the same; if so, we can simplify the resulting
            # expression
            if true_stmt == false_stmt:
                return true_stmt
            else:
                return [
                    astmt.IfStatement(
                        comment=comment,
                        guard=convert_expr(guard),
                        true_stmt=true_stmt,
                        false_stmt=false_stmt,
                    )
                ]

        case bstmt.SetCommunities(comm_set=comms):
            wf = aexpr.WithField(
                ARG_VAR, atys.EnvironmentType.COMMS.value, convert_expr(comms)
            )
            return [astmt.AssignStatement(ARG, wf)]

        case bstmt.SetLocalPreference(lp=lp):
            wf = aexpr.WithField(
                ARG_VAR, atys.EnvironmentType.LP.value, convert_expr(lp)
            )
            return [astmt.AssignStatement(ARG, wf)]

        case bstmt.SetMetric(metric=metric):
            wf = aexpr.WithField(
                ARG_VAR, atys.EnvironmentType.METRIC.value, convert_expr(metric)
            )
            return [astmt.AssignStatement(ARG, wf)]

        case bstmt.SetNextHop(expr=_):
            # FIXME: ignored for now, fix later
            return []  # [
            #     astmt.AssignStatement(
            #         ARG,
            #         aexpr.WithField(ARG_VAR, atys.EnvironmentType.NEXTHOP.value, convert_expr(nexthop_expr)),
            #     )
            # ]

        case bstmt.SetOrigin(origin_type):
            wf = aexpr.WithField(
                ARG_VAR, atys.EnvironmentType.ORIGIN.value, convert_expr(origin_type)
            )
            return [astmt.AssignStatement(ARG, wf)]

        case bstmt.SetWeight(expr):
            wf = aexpr.WithField(
                ARG_VAR, atys.EnvironmentType.WEIGHT.value, convert_expr(expr)
            )
            return [astmt.AssignStatement(ARG, wf)]

        case bstmt.SetDefaultPolicy(name):
            wf = aexpr.WithField(
                ARG_VAR,
                atys.EnvironmentType.DEFAULT_POLICY.value,
                aexpr.LiteralString(name),
            )
            return [astmt.AssignStatement(ARG, wf)]

        case bstmt.StaticStatement(ty=ty):
            # cases based on
            # https://github.com/batfish/batfish/blob/master/projects/batfish-common-protocol/src/main/java/org/batfish/datamodel/routing_policy/statement/Statements.java
            match ty:
                case bstmt.StaticStatementType.EXIT_ACCEPT:
                    update = update_result(_value=True, _exit=True)
                case bstmt.StaticStatementType.EXIT_REJECT:
                    update = update_result(_value=False, _exit=True)
                case bstmt.StaticStatementType.RETURN_TRUE:
                    update = update_result(_value=True, _return=True)
                case bstmt.StaticStatementType.RETURN_FALSE:
                    update = update_result(_value=False, _return=True)
                case bstmt.StaticStatementType.FALL_THROUGH:
                    update = update_result(_fallthrough=True, _return=True)
                case bstmt.StaticStatementType.RETURN:
                    update = update_result(_return=True)
                case bstmt.StaticStatementType.LOCAL_DEF:
                    value_expr = aexpr.GetField(
                        ARG_VAR,
                        atys.EnvironmentType.LOCAL_DEFAULT_ACTION.value,
                        ty_args=(
                            atys.TypeAnnotation.ENVIRONMENT,
                            atys.EnvironmentType.LOCAL_DEFAULT_ACTION.field_type(),
                        ),
                    )
                    update = update_result(_value=value_expr)
                case bstmt.StaticStatementType.SET_ACCEPT | bstmt.StaticStatementType.SET_LOCAL_ACCEPT:
                    # TODO: distinguish local default action and default action?
                    update = aexpr.WithField(
                        ARG_VAR,
                        atys.EnvironmentType.LOCAL_DEFAULT_ACTION.value,
                        aexpr.LiteralBool(True),
                    )
                case bstmt.StaticStatementType.SET_REJECT | bstmt.StaticStatementType.SET_LOCAL_REJECT:
                    # TODO: distinguish local default action and default action?
                    update = aexpr.WithField(
                        ARG_VAR,
                        atys.EnvironmentType.LOCAL_DEFAULT_ACTION.value,
                        aexpr.LiteralBool(False),
                    )
                case _:
                    raise NotImplementedError(
                        f"No convert case for static statement {ty} found."
                    )
            return [astmt.AssignStatement(ARG, update)]
        case bstmt.PrependAsPath():
            # return astmt.SkipStatement()
            return []
        case bstmt.TraceableStatement(inner=inner):
            return convert_stmts(inner)
        case _:
            raise NotImplementedError(f"No convert_stmt case for statement {b} found.")


def convert_stmts(stmts: list[bstmt.Statement]) -> list[astmt.Statement]:
    """Convert a list of Batfish statements into an Angler statement."""
    match stmts:
        case []:
            return []
        case [hd, *tl]:
            return convert_stmt(hd) + convert_stmts(tl)
        case _:
            raise Exception("unreachable")


TResult = TypeVar("TResult")
TRoute = TypeVar("TRoute")


def get_ip_node_mapping(ips: list[OwnedIP]) -> dict[IPv4Address, str]:
    """
    Return the mapping from IP addresses to nodes
    according to the given IP information.
    """
    # TODO: should we also include the mask & interface here?
    return {ip.ip: ip.node.nodename for ip in ips if ip.active}


def convert_batfish(
    bf: json.BatfishJson, query: Optional[Query] = None
) -> prog.Program:
    """
    Convert the Batfish JSON object to an Angler program.
    """
    # generate a graph of the topology
    g = topology.edges_to_graph(bf.topology)
    ips = get_ip_node_mapping(bf.ips)
    nodes: dict[str, prog.Properties] = {}
    # add import and export policies from the BGP peer configs
    for peer_conf in bf.bgp:
        print(f"BGP peer configuration for {peer_conf.desc}")
        pol = prog.Policies(imp=peer_conf.import_policy, exp=peer_conf.export_policy)
        # look up the node in g
        name = peer_conf.node.nodename
        node: igraph.Vertex = g.vs.find(name)
        if name not in nodes:
            # add the node if it has not been seen before
            nodes[name] = prog.Properties(peer_conf.local_as)
        elif nodes[name].asnum != peer_conf.local_as:
            # throw an error if the node's AS number is different from the others
            raise ConvertException(f"Found multiple AS numbers for node {name}")
        if peer_conf.local_as == peer_conf.remote_as:
            # The peer config is for an internal connection
            # look up the neighbor of node whose edge has the associated remote IP
            incident_edge_ids = g.incident(node)
            # search for an edge which is incident to this node with the same ip as
            # the peer_conf's remote ip
            # TODO: check the ips dict?
            possible_edges: list[igraph.Edge] = g.es.select(incident_edge_ids).select(
                lambda e: peer_conf.remote_ip.value in e["ips"][1]
            )
            # throw an error if the neighbor can't be found
            if len(possible_edges) == 0:
                print(
                    f"Could not find a neighbor with remote IP {peer_conf.remote_ip.value}"
                )
                if len(peer_conf.export_policy) + len(peer_conf.import_policy) > 0:
                    print(
                        f"The following policies may be lost: "
                        + ", ".join(peer_conf.export_policy + peer_conf.import_policy)
                    )
                continue
            # otherwise, we found a possible edge
            nbr = g.vs[possible_edges[0].target]["name"]
        else:
            # The peer config is for an external connection
            nbr = ips.get(peer_conf.remote_ip.value, str(peer_conf.remote_ip.value))
            if nbr not in g.vs:
                g.add_vertex(name=nbr)
            g.add_edge(
                name, nbr, ips=([peer_conf.local_ip], [peer_conf.remote_ip.value])
            )
            # add external neighbor
            if nbr not in nodes:
                nodes[nbr] = prog.Properties(peer_conf.remote_as)
            nodes[nbr].policies[name] = prog.Policies([], [])
            # TODO: identify the node as symbolic
        nodes[name].policies[nbr] = pol
    # add constants, declarations and prefixes for each of the nodes
    for s in bf.declarations:
        n, k, v = convert_structure(s)
        match v:
            case prog.Func():
                nodes[n].declarations[k] = v
            case aexpr.Expression():
                nodes[n].consts[k] = v
            case IPv4Address():
                # add a /24 prefix based on the given address
                # strict=False causes this to mask the last 8 bits
                ip_net = IPv4Network((v, 24), strict=False)
                nodes[n].prefixes.add(ip_net)
            case None:
                pass
    # inline constants
    # TODO: inline function calls
    print("Inlining constants for...")
    for node, properties in nodes.items():
        print(node)
        for func in properties.declarations.values():
            for stmt in func.body:
                # NOTE: stmt substitution returns None, but expr substitution
                # returns an expression
                stmt.subst(properties.consts)
        # delete the constants
        properties.consts = {}
    print("Adding initial routes...")
    destinations = []
    default_env = default_value(atys.TypeAnnotation.ENVIRONMENT)
    for n, p in nodes.items():
        if (
            query
            and query.dest
            and any([query.dest.address in prefix for prefix in p.prefixes])
        ):
            destinations.append(n)
            # set the prefix
            update_prefix = aexpr.WithField(
                default_env,
                atys.EnvironmentType.PREFIX.value,
                aexpr.IpPrefix(IPv4Network(query.dest.address)),
            )
            # set the value as True
            p.initial = aexpr.WithField(
                update_prefix,
                atys.EnvironmentType.RESULT_VALUE.value,
                aexpr.LiteralBool(True),
            )
        else:
            p.initial = default_env
    print("Adding verification elements...")
    # set up verification tooling
    predicates = {}
    ghost = None
    symbolics = {}
    converge_time = None
    if query:
        # add all query predicates
        predicates = query.predicates
        if isinstance(query.safety_checks, dict):
            for node, pred_name in query.safety_checks.items():
                nodes[node].stable = pred_name
        else:
            for node in nodes.keys():
                nodes[node].stable = query.safety_checks

        # determine the destination for routing
        if query.dest and query.with_time:
            # compute shortest paths: produces a matrix with a row for each source
            distances: list[list[int]] = g.shortest_paths(
                source=destinations, mode="all"
            )
            # we want the minimum distance to any source for each node
            best_distances = [
                min([distances[src][v.index] for src in range(len(distances))])
                for v in g.vs
            ]
            converge_time = max(best_distances)
            for i, d in enumerate(best_distances):
                name = g.vs[i]["name"]
                pred = nodes[name].stable
                if pred is not None:
                    if d == 0:
                        t = temp.Globally(pred)
                    else:
                        t = query.with_time(d)
                    nodes[name].temporal = t

    print("Conversion complete!")
    return prog.Program(
        route=atys.EnvironmentType.fields(),
        nodes=nodes,
        ghost=ghost,
        predicates=predicates,
        symbolics=symbolics,
        converge_time=converge_time,
    )


def convert_structure(
    b: bstruct.Structure,
) -> tuple[str, str, prog.Func | aexpr.Expression | IPv4Address | None]:
    node_name = b.node.nodename
    struct_name: str = b.struct_name
    value = None
    match b.definition.value:
        case bstruct.RoutingPolicy(policyname=name, statements=stmts):
            print(f"Routing policy {b.struct_name}")
            body = convert_stmts(stmts)
            struct_name = name
            value = prog.Func(ARG, body)
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
            # if the disjuncts are empty, simply use False
            value = aexpr.MatchSet(
                permit=aexpr.Disjunction(permit_disjuncts)
                if len(permit_disjuncts) > 0
                else aexpr.LiteralBool(False),
                deny=aexpr.Disjunction(deny_disjuncts)
                if len(deny_disjuncts) > 0
                else aexpr.LiteralBool(False),
            )

            # TODO: What is the default action if no rule matches?

        case bcomms.CommunitySetMatchAll(es):
            # convert the internal CommunityMatchExprs
            # into a literal set to match against
            print(f"CommunitySetMatchAll {b.struct_name}")
            value = aexpr.LiteralSet([convert_expr(e) for e in es])
        case bcomms.HasCommunity(e):
            # convert the internal CommunityMatchExpr
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


class ConvertException(Exception):
    ...
