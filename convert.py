#!/usr/bin/env python3
"""
Conversion tools to transform Batfish AST terms to Angler AST terms.
"""
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network
from typing import Optional, TypeVar

import igraph
from bast.base import OwnedIP
import bast.json as json
import bast.topology as topology
import bast.expression as bex
import bast.statement as bsm
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
import aast.expression as aex
import aast.statement as asm
import aast.types as aty
import aast.program as prog
from query import QueryType

# the transfer argument
ARG = "env"
ARG_VAR = aex.Var(ARG)


# frozen=True means the class is immutable (and therefore also suitable for hashing)
@dataclass(frozen=True)
class AsnPeer:
    local_asn: Optional[int]
    local_ip: IPv4Address
    remote_asn: Optional[int]
    remote_ip: IPv4Address


def default_value(ty: aty.TypeAnnotation) -> aex.Expression:
    """
    Return the default value for the given type.
    Note that not all types have default values.
    """
    match ty:
        case aty.TypeAnnotation.BOOL:
            return aex.LiteralBool(False)
        case aty.TypeAnnotation.INT2:
            return aex.LiteralInt(0, width=2)
        case aty.TypeAnnotation.INT32:
            return aex.LiteralInt(0, width=32)
        case aty.TypeAnnotation.UINT2:
            return aex.LiteralUInt(0, width=2)
        case aty.TypeAnnotation.UINT32:
            return aex.LiteralUInt(0, width=32)
        case aty.TypeAnnotation.BIG_INT:
            return aex.LiteralBigInt(0)
        case aty.TypeAnnotation.SET:
            return aex.LiteralSet([])
        case aty.TypeAnnotation.STRING:
            return aex.LiteralString("")
        case aty.TypeAnnotation.IP_ADDRESS:
            return aex.IpAddress(IPv4Address(0))
        case aty.TypeAnnotation.IP_PREFIX:
            return aex.IpPrefix(IPv4Network(0))
        case aty.TypeAnnotation.ROUTE:
            return aex.CreateRecord(
                {
                    field_name: default_value(field_ty)
                    for field_name, field_ty in aty.EnvironmentType.fields().items()
                },
                aty.TypeAnnotation.ROUTE,
            )
        case aty.TypeAnnotation.RESULT:
            return aex.CreateRecord(
                {
                    field_name: default_value(field_ty)
                    for field_name, field_ty in aty.ResultType.fields().items()
                },
                aty.TypeAnnotation.RESULT,
            )
        case aty.TypeAnnotation.ENVIRONMENT:
            return aex.CreateRecord(
                {
                    field_name: default_value(field_ty)
                    for field_name, field_ty in aty.EnvironmentType.fields().items()
                },
                aty.TypeAnnotation.ENVIRONMENT,
            )
        case _:
            raise ValueError(f"Cannot produce a default value for type {ty}")


def update_arg(update: aex.Expression, ty: aty.EnvironmentType) -> asm.AssignStatement:
    """Construct an Assign statement for the given update to the ARG_VAR at the given field."""
    wf = aex.WithField(
        ARG_VAR,
        ty.value,
        update,
        ty_args=(aty.TypeAnnotation.ENVIRONMENT, ty.field_type()),
    )
    return asm.AssignStatement(ARG, wf)


def get_arg(ty: aty.EnvironmentType) -> aex.Expression:
    """Construct a GetField expression for accessing the given field of the ARG_VAR."""
    return aex.GetField(
        ARG_VAR, ty.value, ty_args=(aty.TypeAnnotation.ENVIRONMENT, ty.field_type())
    )


def convert_expr(b: bex.Expression) -> aex.Expression:
    """
    Convert the given Batfish AST expression into an Angler AST expression.
    """
    match b:
        case bools.CallExpr(policy):
            # NOTE: handling how the call modifies the environment around it
            # is left up to the user of angler's output
            return aex.CallExpr(policy)
        case bools.StaticBooleanExpr(ty=bools.StaticBooleanExprType.TRUE):
            return aex.LiteralBool(True)
        case bools.StaticBooleanExpr(ty=bools.StaticBooleanExprType.FALSE):
            return aex.LiteralBool(False)
        case bools.StaticBooleanExpr(ty=bools.StaticBooleanExprType.CALLCONTEXT):
            # NOTE: not supported
            # TODO(tim): maybe it should be? would be easy enough to add
            return aex.Havoc()
        case bools.Conjunction(conjuncts):
            conj = [convert_expr(c) for c in conjuncts]
            return aex.Conjunction(conj)
        case bools.ConjunctionChain(subroutines):
            return aex.ConjunctionChain([convert_expr(s) for s in subroutines])
        case bools.FirstMatchChain(subroutines):
            return aex.FirstMatchChain([convert_expr(s) for s in subroutines])
        case bools.Disjunction(disjuncts):
            disj = [convert_expr(d) for d in disjuncts]
            return aex.Disjunction(disj)
        case bools.Not(e):
            return aex.Not(convert_expr(e))
        case bools.MatchIpv4():
            # NOTE: for now, we assume ipv4
            return aex.LiteralBool(True)
        case bools.MatchIpv6() | bools.MatchPrefix6Set():
            # NOTE: not supported (for now, we assume ipv4)
            return aex.LiteralBool(False)
        case bools.LegacyMatchAsPath():
            # NOTE: not supported
            return aex.Havoc()
        case bcomms.CommunityIs(community):
            return aex.LiteralString(community)
        case bcomms.LiteralCommunitySet(comms):
            return aex.LiteralSet([aex.LiteralString(comm) for comm in comms])
        case bcomms.CommunitySetUnion(exprs):
            aes = [convert_expr(expr) for expr in exprs]
            return aex.SetUnion(aes)
        case bcomms.CommunitySetDifference(initial, bcomms.AllStandardCommunities()):
            # NOTE: assuming all communities are standard communities
            # remove all communities
            return aex.LiteralSet([])
        case bcomms.CommunitySetDifference(initial, to_remove):
            # remove a single community from the set
            return aex.SetRemove(convert_expr(to_remove), convert_expr(initial))
        case bools.MatchCommunities(_comms, bcomms.HasCommunity(expr)):
            # check if community is in _comms
            return aex.SetContains(convert_expr(expr), convert_expr(_comms))
        case bools.MatchCommunities(
            _comms, bcomms.CommunitySetMatchExprReference(_name)
        ):
            cvar = aex.Var(_name)
            return aex.SetContains(cvar, convert_expr(_comms))
        case bcomms.InputCommunities():
            return get_arg(aty.EnvironmentType.COMMS)
        case bcomms.CommunitySetReference(_name):
            return aex.Var(_name)
        case bcomms.CommunitySetMatchExprReference(
            _name
        ) | bcomms.CommunityMatchExprReference(_name):
            return aex.Var(_name)
        case bcomms.HasCommunity(e):
            # extract the underlying community
            return convert_expr(e)
        case bcomms.CommunityMatchRegex(_):
            # NOTE: for now, we treat regexes as havoc
            return aex.Havoc()
        case ints.LiteralInt(value):
            # TODO: should this be signed or unsigned?
            return aex.LiteralUInt(value)
        case longs.LiteralLong(value):
            # TODO: should this be signed or unsigned?
            return aex.LiteralUInt(value)
        case longs.IncrementLocalPref(addend):
            x = aex.LiteralUInt(addend)
            return aex.Add(get_arg(aty.EnvironmentType.LP), x)
        case longs.DecrementLocalPref(subtrahend):
            x = aex.LiteralUInt(subtrahend)
            return aex.Sub(get_arg(aty.EnvironmentType.LP), x)
        case prefix.DestinationNetwork():
            return get_arg(aty.EnvironmentType.PREFIX)
        case prefix.NamedPrefixSet(_name):
            return aex.Var(_name)
        case prefix.ExplicitPrefixSet(prefix_space):
            return aex.PrefixSet(prefix_space)
        case borigin.LiteralOrigin(origin_type):
            return aex.LiteralUInt(origin_type.to_int(), width=2)
        case bools.MatchPrefixSet(_prefix, _prefixes):
            return aex.PrefixContains(convert_expr(_prefix), convert_expr(_prefixes))
        case bools.MatchTag(cmp, tag):
            route_tag = get_arg(aty.EnvironmentType.TAG)
            match cmp:
                case Comparator.EQ:
                    return aex.Equal(route_tag, convert_expr(tag))
                case Comparator.LE:
                    return aex.LessThanEqual(route_tag, convert_expr(tag))
                case Comparator.LT:
                    return aex.LessThan(route_tag, convert_expr(tag))
                case Comparator.GE:
                    return aex.GreaterThanEqual(route_tag, convert_expr(tag))
                case Comparator.GT:
                    return aex.GreaterThan(route_tag, convert_expr(tag))
        case bools.MatchProtocol(protocols):
            # TODO: for now, return true if Protocol.BGP is in protocols, and false otherwise
            if Protocol.BGP in protocols:
                return aex.LiteralBool(True)
            else:
                return aex.LiteralBool(False)
        case _:
            raise NotImplementedError(f"No convert case for {b} found.")


def update_result(
    _value: aex.Expression | bool | None = None,
    _exit: aex.Expression | bool | None = None,
    _fallthrough: aex.Expression | bool | None = None,
    _return: aex.Expression | bool | None = None,
) -> aex.Expression:
    """
    Convert the given Batfish result into an Angler WithField expression to update the environment.
    """
    arg_expr = ARG_VAR
    if _value is not None:
        value_update = (
            _value if isinstance(_value, aex.Expression) else aex.LiteralBool(_value)
        )
        arg_expr = aex.WithField(
            arg_expr, aty.EnvironmentType.RESULT_VALUE.value, value_update
        )
    if _exit is not None:
        exit_update = (
            _exit if isinstance(_exit, aex.Expression) else aex.LiteralBool(_exit)
        )
        arg_expr = aex.WithField(
            arg_expr, aty.EnvironmentType.RESULT_EXIT.value, exit_update
        )
    if _fallthrough is not None:
        fallthrough_update = (
            _fallthrough
            if isinstance(_fallthrough, aex.Expression)
            else aex.LiteralBool(_fallthrough)
        )
        arg_expr = aex.WithField(
            arg_expr,
            aty.EnvironmentType.RESULT_FALLTHRU.value,
            fallthrough_update,
        )
    if _return is not None:
        return_update = (
            _return if isinstance(_return, aex.Expression) else aex.LiteralBool(_return)
        )
        arg_expr = aex.WithField(
            arg_expr, aty.EnvironmentType.RESULT_RETURN.value, return_update
        )
    return arg_expr


def convert_stmt(b: bsm.Statement) -> list[asm.Statement]:
    """
    Convert a Batfish AST statement into an Angler AST statement.
    """
    match b:
        case bsm.IfStatement(
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
                    asm.IfStatement(
                        comment=comment,
                        guard=convert_expr(guard),
                        true_stmt=true_stmt,
                        false_stmt=false_stmt,
                    )
                ]

        case bsm.SetCommunities(comm_set=comms):
            return [update_arg(convert_expr(comms), aty.EnvironmentType.COMMS)]

        case bsm.SetLocalPreference(lp=lp):
            return [update_arg(convert_expr(lp), aty.EnvironmentType.LP)]

        case bsm.SetMetric(metric=metric):
            return [update_arg(convert_expr(metric), aty.EnvironmentType.METRIC)]

        case bsm.SetNextHop(expr=_):
            # FIXME: ignored for now, fix later
            return []
            # return [update_arg(convert_expr(expr), aty.EnvironmentType.NEXTHOP)]

        case bsm.SetOrigin(origin_type):
            return [update_arg(convert_expr(origin_type), aty.EnvironmentType.ORIGIN)]

        case bsm.SetWeight(expr):
            return [update_arg(convert_expr(expr), aty.EnvironmentType.WEIGHT)]

        case bsm.SetDefaultPolicy(name):
            # NOTE: we treat SetDefaultPolicy specially as it represents a modification to the
            # environment, but not the actual route.
            return [asm.SetDefaultPolicy(name)]

        case bsm.StaticStatement(ty=ty):
            # cases based on
            # https://github.com/batfish/batfish/blob/master/projects/batfish-common-protocol/src/main/java/org/batfish/datamodel/routing_policy/statement/Statements.java
            match ty:
                case bsm.StaticStatementType.EXIT_ACCEPT:
                    update = update_result(_value=True, _exit=True)
                case bsm.StaticStatementType.EXIT_REJECT:
                    update = update_result(_value=False, _exit=True)
                case bsm.StaticStatementType.RETURN_TRUE:
                    update = update_result(_value=True, _return=True)
                case bsm.StaticStatementType.RETURN_FALSE:
                    update = update_result(_value=False, _return=True)
                case bsm.StaticStatementType.FALL_THROUGH:
                    update = update_result(_fallthrough=True, _return=True)
                case bsm.StaticStatementType.RETURN:
                    update = update_result(_return=True)
                case bsm.StaticStatementType.LOCAL_DEF:
                    value_expr = get_arg(aty.EnvironmentType.LOCAL_DEFAULT_ACTION)
                    update = update_result(_value=value_expr)
                case bsm.StaticStatementType.SET_ACCEPT | bsm.StaticStatementType.SET_LOCAL_ACCEPT:
                    # TODO: distinguish local default action and default action?
                    update = aex.WithField(
                        ARG_VAR,
                        aty.EnvironmentType.LOCAL_DEFAULT_ACTION.value,
                        aex.LiteralBool(True),
                    )
                case bsm.StaticStatementType.SET_REJECT | bsm.StaticStatementType.SET_LOCAL_REJECT:
                    # TODO: distinguish local default action and default action?
                    update = aex.WithField(
                        ARG_VAR,
                        aty.EnvironmentType.LOCAL_DEFAULT_ACTION.value,
                        aex.LiteralBool(False),
                    )
                case _:
                    raise NotImplementedError(
                        f"No convert case for static statement {ty} found."
                    )
            return [asm.AssignStatement(ARG, update)]
        case bsm.PrependAsPath():
            # NOTE: ignored
            return []
        case bsm.TraceableStatement(inner=inner):
            return convert_stmts(inner)
        case _:
            raise NotImplementedError(f"No convert_stmt case for statement {b} found.")


def convert_stmts(stmts: list[bsm.Statement]) -> list[asm.Statement]:
    """Convert a list of Batfish statements into an Angler statement."""
    match stmts:
        case []:
            return []
        case [hd, *tl]:
            return convert_stmt(hd) + convert_stmts(tl)
        case _:
            raise Exception("unreachable")


def unreachable() -> aex.Expression[bool]:
    """Return an expression that is true if the route has returned or exited."""
    return aex.Disjunction(
        [
            get_arg(aty.EnvironmentType.RESULT_RETURN),
            get_arg(aty.EnvironmentType.RESULT_EXIT),
        ]
    )


def convert_routing_policy(body: list[bsm.Statement]) -> prog.Func:
    """
    Convert a Batfish routing policy into an Angler function.
    We insert cases around each statement to handle possibly returning early depending on
    the values set by the statement fields, as follows:

    Statement return logic:
    When Batfish executes an environment, it executes each statement in sequence
    and checks the result of the statement.
    If Exited is true, we return immediately from execution with this result.
    If Returned is true, we return immediately from execution and set Returned to false.
    If all statements have been executed without a return, we return a Result with
    FallThrough = true and Value per DefaultAction.
    See https://github.com/batfish/batfish/blob/master/projects/batfish-common-protocol/src/main/java/org/batfish/datamodel/routing_policy/RoutingPolicy.java#L120
    """

    def recurse(stmts: list[asm.Statement]) -> list[asm.Statement]:
        # To convert the original body to the early-return body, we need to rewrite each
        # list of statements [s1, s2, s3, ...] into:
        # [s1, (if unreachable then [] else [s2, (if unreachable then [] else [s3, ...])])]
        # where "unreachable" is an expression that checks if exited or returned is true.
        match stmts:
            case []:
                return []
            case [hd]:
                # NOTE(tim):
                # this is an additional case to reduce nesting; without it, we can end up producing
                # empty "if unreachable then [] else []" statements
                if isinstance(hd, asm.IfStatement):
                    hd.true_stmt = recurse(hd.true_stmt)
                    hd.false_stmt = recurse(hd.false_stmt)
                return [hd]
            case [hd, *tl]:
                if isinstance(hd, asm.IfStatement):
                    hd.true_stmt = recurse(hd.true_stmt)
                    hd.false_stmt = recurse(hd.false_stmt)
                return [
                    hd,
                    asm.IfStatement("early_return", unreachable(), [], recurse(tl)),
                ]
            case _:
                raise Exception("unreachable")

    # convert the body and then add the early-return tests
    new_body = recurse(convert_stmts(body))
    check_returned = asm.IfStatement(
        "reset_return",
        # TODO(tim): should this be unreachable() or just checking if the result returned?
        # it seems like in either case, returned should be set to false
        # get_arg(aty.EnvironmentType.RESULT_RETURN),
        unreachable(),
        [
            # reset return to false
            update_arg(aex.LiteralBool(False), aty.EnvironmentType.RESULT_RETURN)
        ],
        [
            # set fallthrough to true and the value to the local default
            asm.AssignStatement(
                ARG,
                update_result(
                    _fallthrough=True,
                    _value=get_arg(aty.EnvironmentType.LOCAL_DEFAULT_ACTION),
                ),
            ),
        ],
    )
    # add the end statement to new_body
    new_body.append(check_returned)
    return prog.Func(ARG, new_body)


TResult = TypeVar("TResult")
TRoute = TypeVar("TRoute")


def get_ip_node_mapping(ips: list[OwnedIP]) -> dict[IPv4Address, str]:
    """
    Return the mapping from IP addresses to nodes
    according to the given IP information.
    """
    # TODO: should we also include the mask & interface here?
    return {ip.ip: ip.node.nodename for ip in ips if ip.active}


def get_node_distances(g: igraph.Graph, destinations: list[str]) -> dict[str, int]:
    # compute shortest paths: produces a matrix with a row for each source
    distances: list[list[int]] = g.shortest_paths(source=destinations, mode="all")
    # we want the minimum distance to any source for each node
    best_distances = [
        min([distances[src][v.index] for src in range(len(distances))]) for v in g.vs
    ]
    return {g.vs[i]["name"]: d for i, d in enumerate(best_distances)}


def convert_batfish(
    bf: json.BatfishJson,
    query: Optional[QueryType],
    dest: Optional[IPv4Address],
    with_time: bool,
) -> prog.Program:
    """
    Convert the Batfish JSON object to an Angler program.
    """
    # generate a graph of the topology
    g = topology.edges_to_graph(bf.topology)
    ips = get_ip_node_mapping(bf.ips)
    nodes: dict[str, prog.Properties] = {}
    constants: dict[str, dict[str, aex.Expression]] = {}
    external_nodes = set()
    # add constants, declarations and prefixes for each of the nodes
    print("Converting found structures...")
    for s in bf.declarations:
        n, k, v = convert_structure(s)
        if n not in nodes:
            nodes[n] = prog.Properties()
        if n not in constants:
            constants[n] = {}
        match v:
            case prog.Func():
                nodes[n].declarations[k] = v
            case aex.Expression():
                constants[n][k] = v
            case (address, peers_to_policies):
                # add a /24 prefix based on the given address
                # strict=False causes this to mask the last 8 bits
                nodes[n].add_prefix_from_ip(address)
                neighbor_policies = {}
                for peering, policy_block in peers_to_policies.items():
                    # add the local ASN to the node
                    if nodes[n].asnum is None:
                        nodes[n].asnum = peering.local_asn
                    elif peering.local_asn != nodes[n].asnum:
                        print(
                            f"WARNING: multiple ASNs {nodes[n].asnum} and {peering.local_asn} for node {n}"
                        )
                    # look up the remote IP's owner
                    node_owner = ips.get(peering.remote_ip)
                    if node_owner is None:
                        # IP belongs to an external neighbor
                        # we first try and use the ASN as the name, then use the IP if there is no ASN
                        external_node = str(peering.remote_asn) or str(
                            peering.remote_ip
                        )
                        neighbor_policies[external_node] = policy_block
                        if external_node not in g.vs:
                            g.add_vertex(name=external_node)
                            # identify the external neighbor as symbolic
                            external_nodes.add(external_node)
                        g.add_edge(
                            n,
                            external_node,
                            ips=([peering.local_ip], [peering.remote_ip]),
                        )
                        # add a reverse connection from the external neighbor to this node
                        if external_node not in nodes:
                            nodes[external_node] = prog.Properties(
                                asnum=peering.remote_asn
                            )
                        nodes[external_node].policies[n] = prog.Policies(
                            peering.remote_asn, None, None
                        )
                    else:
                        neighbor_policies[node_owner] = policy_block
                # bind the policies to the node
                nodes[n].policies = neighbor_policies
            case None:
                pass
    # inline constants
    print("Inlining constants for...")
    for node, properties in nodes.items():
        print(node)
        for func in properties.declarations.values():
            for stmt in func.body:
                # NOTE: stmt substitution returns None, but expr substitution returns an expression
                stmt.subst(constants[node])
    print("Adding initial routes...")
    # keep track of nodes which advertise the destination IP
    destinations: list[str] = []
    symbolics = {}
    default_env = default_value(aty.TypeAnnotation.ENVIRONMENT)
    for n, p in nodes.items():
        if n in external_nodes:
            # external node: starts with an arbitrary route
            symbolic_name = f"external-route-{n}"
            symbolics[symbolic_name] = prog.Predicate.default()
            p.initial = aex.Var(symbolic_name)
        elif query and dest and any([dest in prefix for prefix in p.prefixes]):
            # internal destination node: starts with route to itself
            destinations.append(n)
            # set the prefix
            update_prefix = aex.WithField(
                default_env,
                aty.EnvironmentType.PREFIX.value,
                aex.IpPrefix(IPv4Network(dest)),
            )
            # set the value as True
            p.initial = aex.WithField(
                update_prefix,
                aty.EnvironmentType.RESULT_VALUE.value,
                aex.LiteralBool(True),
            )
        else:
            # internal non-destination node: starts with no route
            p.initial = default_env
    print("Adding verification elements...")
    # set up verification tooling
    predicates = {}
    ghost = None
    converge_time = None
    if query:
        # determine what information we need for the node queries
        match query:
            case QueryType.SP if dest:
                node_info = get_node_distances(g, destinations)
                converge_time = max(node_info.values())
                # add all query predicates
                q = query.from_nodes(node_info)
                predicates = q.predicates
                # assign safety checks to nodes
                for node, node_query in q.nodes.items():
                    nodes[node].stable = node_query.safety_check
                    if with_time:
                        nodes[node].temporal = node_query.temporal_check
            case QueryType.FAT if dest:
                # TODO: get the comms
                dist_node_info = get_node_distances(g, destinations)
                converge_time = max(dist_node_info.values())
            case _:
                raise NotImplementedError("Query not yet implemented")

    print("Conversion complete!")
    return prog.Program(
        route=aty.EnvironmentType.fields(),
        nodes=nodes,
        ghost=ghost,
        predicates=predicates,
        symbolics=symbolics,
        converge_time=converge_time,
    )


def convert_structure(
    b: bstruct.Structure,
) -> tuple[
    str,
    str,
    prog.Func
    | aex.Expression
    | tuple[IPv4Address, dict[AsnPeer, prog.Policies]]
    | None,
]:
    """
    Convert a Batfish structure definition into an Angler node component.
    The component generated depends on the structure:
    - Routing policies are converted to `Func` functions.
    - Route filter lists are converted to boolean expressions.
    - Community set match expressions are converted to set expressions.
    - VRFs are converted to policy blocks (dictionaries from neighbor IPs to `Policies`).
    """
    node_name = b.node.nodename
    struct_name: str = b.struct_name
    value = None
    match b.definition.value:
        case bstruct.RoutingPolicy(policyname=name, statements=stmts):
            print(f"Routing policy {b.struct_name}")
            struct_name = name
            value = convert_routing_policy(stmts)
        case bacl.RouteFilterList(_name=name, lines=lines):
            print(f"Route filter list {b.struct_name}")
            permit_disjuncts = []
            deny_disjuncts = []
            prev_conds = []
            for l in lines:
                cond = aex.PrefixMatches(l.ip_wildcard, l.length_range)

                not_prev: list[aex.Expression[bool]] = [aex.Not(c) for c in prev_conds]

                if len(not_prev) > 0:
                    curr_matches = aex.Conjunction(not_prev + [cond])
                else:
                    curr_matches = cond

                if l.action == Action.PERMIT:
                    permit_disjuncts.append(curr_matches)
                else:
                    deny_disjuncts.append(curr_matches)

                prev_conds.append(cond)

            struct_name = name
            # if the disjuncts are empty, simply use False
            value = aex.MatchSet(
                permit=aex.Disjunction(permit_disjuncts)
                if len(permit_disjuncts) > 0
                else aex.LiteralBool(False),
                deny=aex.Disjunction(deny_disjuncts)
                if len(deny_disjuncts) > 0
                else aex.LiteralBool(False),
            )

            # TODO: What is the default action if no rule matches?

        case bcomms.CommunitySetMatchAll(es):
            # convert the internal CommunityMatchExprs
            # into a literal set to match against
            print(f"CommunitySetMatchAll {b.struct_name}")
            value = aex.LiteralSet([convert_expr(e) for e in es])
        case bcomms.HasCommunity(e):
            # convert the internal CommunityMatchExpr
            print(f"HasCommunity {b.struct_name}")
            value = convert_expr(e)
        case bacl.Acl(name=name):
            # TODO
            struct_name = name
        case bvrf.Vrf(vrfname="default", bgp=bgp) if bgp is not None:
            value = (
                # the address of this node
                bgp.router,
                # the export and import policies for each of its neighbors
                {
                    AsnPeer(
                        config.local_as, config.local_ip, config.remote_as, neighbor
                    ): prog.Policies(
                        asn=config.remote_as,
                        imp=config.address_family.import_policy,
                        exp=config.address_family.export_policy,
                    )
                    for neighbor, config in bgp.neighbors.items()
                },
            )
        case bacl.Route6FilterList(_name=name):
            # TODO
            struct_name = name
        case _:
            raise NotImplementedError(f"No convert case for {b} found.")
    return node_name, struct_name, value


class ConvertException(Exception):
    ...
