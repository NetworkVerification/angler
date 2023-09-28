#!/usr/bin/env python3
"""
Conversion tools to transform Batfish AST terms to Angler AST terms.
Current TODOs:
- No support for protocols other than BGP
- No support for matching on the AS path
- No support for IPv6
- No support for ACLs
- No support for VRFs other than the default
"""
from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import Optional, TypeVar, cast

from bast.base import OwnedIP
import bast.json as json
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
from bast.btypes import Action, Comparator, Protocol
import bast.structure as bstruct
import aast.expression as aex
import aast.statement as asm
import aast.types as aty
import aast.network as net

# the transfer argument
ARG = "env"
ARG_VAR = aex.Var(ARG)


# frozen=True means the class is immutable (and therefore also suitable for hashing)
@dataclass(frozen=True)
class AsnPeer:
    """
    A representation of a peer AS. Used when determining the network topology.
    """

    local_asn: Optional[int]
    local_ip: IPv4Address
    remote_asn: Optional[int]
    remote_ip: IPv4Address


def route_filter_list_var(s: str) -> str:
    return f"route-filter-list-{s}"


def community_set_match_expr_var(s: str) -> str:
    return f"community-set-match-expr-{s}"


def update_arg(update: aex.Expression, ty: aty.EnvironmentType) -> asm.AssignStatement:
    """
    Construct an `aast.statement.AssignStatement` statement for the given
    update to the ARG_VAR at the given field.
    """
    wf = aex.WithField(
        ARG_VAR,
        ty.value,
        update,
        ty_args=(aty.TypeAnnotation.ENVIRONMENT, ty.field_type()),
    )
    return asm.AssignStatement(ARG, wf)


def get_arg(ty: aty.EnvironmentType) -> aex.Expression:
    """Construct a `aast.expression.GetField` expression for accessing the given field of the ARG_VAR."""
    return aex.GetField(
        ARG_VAR, ty.value, ty_args=(aty.TypeAnnotation.ENVIRONMENT, ty.field_type())
    )


def convert_expr(b: bex.Expression, simplify: bool = False) -> aex.Expression:
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
            return aex.CallExprContext()
        case bools.Conjunction(conjuncts):
            if simplify:
                conj = []
                for c in conjuncts:
                    new_c = convert_expr(c)
                    if new_c == aex.LiteralBool(False):
                        return new_c
                    elif new_c == aex.LiteralBool(True):
                        continue
                    conj.append(new_c)
            else:
                conj = [convert_expr(c) for c in conjuncts]
            return aex.Conjunction(conj)
        case bools.ConjunctionChain(subroutines):
            return aex.ConjunctionChain([convert_expr(s) for s in subroutines])
        case bools.FirstMatchChain(subroutines):
            return aex.FirstMatchChain([convert_expr(s) for s in subroutines])
        case bools.Disjunction(disjuncts):
            if simplify:
                disj = []
                for d in disjuncts:
                    new_d = convert_expr(d)
                    if new_d == aex.LiteralBool(False):
                        continue
                    elif new_d == aex.LiteralBool(True):
                        return new_d
                    disj.append(new_d)
            else:
                disj = [convert_expr(d) for d in disjuncts]
            return aex.Disjunction(disj)
        case bools.Not(e):
            inner = convert_expr(e)
            if simplify and isinstance(inner, aex.LiteralBool):
                return aex.LiteralBool(not inner.value)
            return aex.Not(inner)
        case bools.MatchIpv4():
            # NOTE: for now, we assume ipv4
            return aex.LiteralBool(True)
        case bools.MatchIpv6() | bools.MatchPrefix6Set():
            # NOTE: not supported (for now, we assume ipv4)
            return aex.LiteralBool(False)
        case bools.MatchAsPath():
            # NOTE: not supported
            return aex.Havoc()
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
            return aex.SetDifference(convert_expr(to_remove), convert_expr(initial))
        case bools.MatchCommunities(_comms, bcomms.HasCommunity(expr)):
            # check if community is in _comms
            return aex.SetContains(convert_expr(expr), convert_expr(_comms))
        case bools.MatchCommunities(
            _comms, bcomms.CommunitySetMatchExprReference(_name)
        ):
            cvar = aex.Var(community_set_match_expr_var(_name))
            return aex.Subset(cvar, convert_expr(_comms))
        case bcomms.InputCommunities():
            return get_arg(aty.EnvironmentType.COMMS)
        case bcomms.CommunitySetReference(_name):
            return aex.Var(community_set_match_expr_var(_name))
        case bcomms.CommunitySetMatchExprReference(
            _name
        ) | bcomms.CommunityMatchExprReference(_name):
            return aex.Var(community_set_match_expr_var(_name))
        case bcomms.HasCommunity(e):
            # extract the underlying community
            return aex.LiteralSet([convert_expr(e)])
        case bcomms.CommunitySetMatchAll(es):
            # return a set combining all the match expressions
            return aex.SetUnion([convert_expr(e) for e in es])
        case bcomms.CommunityMatchRegex(
            rendering=bcomms.ColonSeparatedRendering(), regex=regex
        ):
            return aex.Regex(regex)
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
            return aex.Var(route_filter_list_var(_name))
        case prefix.ExplicitPrefixSet(prefix_space):
            return aex.PrefixSet(prefix_space)
        case borigin.LiteralOrigin(origin_type):
            return aex.LiteralUInt(origin_type.to_int(), width=2)
        case bools.MatchPrefixSet(_prefix, _prefixes):
            return aex.MatchPrefixSet(convert_expr(_prefix), convert_expr(_prefixes))
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


def create_result(
    _value: aex.Expression | bool | None = None,
    _exit: aex.Expression | bool | None = None,
    _fallthrough: aex.Expression | bool | None = None,
    _return: aex.Expression | bool | None = None,
) -> aex.Expression:
    """
    Convert the given Batfish result into an Angler CreateRecord expression to return a new Result.
    """

    def bool_to_expr(
        rt: aty.ResultType, v: aex.Expression | bool | None
    ) -> aex.Expression:
        match v:
            case None:
                return aex.default_value(rt.field_type())
            case bool():
                return aex.LiteralBool(v)
            case aex.Expression():
                return v
            case _:
                raise Exception("unreachable")

    return aex.CreateRecord(
        {
            aty.ResultType.VALUE.value: bool_to_expr(aty.ResultType.VALUE, _value),
            aty.ResultType.EXIT.value: bool_to_expr(aty.ResultType.EXIT, _exit),
            aty.ResultType.FALLTHROUGH.value: bool_to_expr(
                aty.ResultType.FALLTHROUGH, _fallthrough
            ),
            aty.ResultType.RETURN.value: bool_to_expr(aty.ResultType.RETURN, _return),
        },
        aty.TypeAnnotation.RESULT,
    )


def update_arg_result(
    _value: aex.Expression | bool | None = None,
    _exit: aex.Expression | bool | None = None,
    _fallthrough: aex.Expression | bool | None = None,
    _return: aex.Expression | bool | None = None,
) -> asm.Statement:
    """
    Return a new Angler statement updating the arg's result for the specified fields.
    Unlike create_result, the previous values of the result field are preserved.
    """

    def update_field(
        e: aex.Expression, rt: aty.ResultType, v: aex.Expression | bool | None
    ) -> aex.Expression:
        match v:
            case None:
                return e
            case bool():
                return aex.WithField(
                    e,
                    rt.value,
                    aex.LiteralBool(v),
                    ty_args=(aty.TypeAnnotation.RESULT, rt.field_type()),
                )
            case aex.Expression():
                return aex.WithField(
                    e, rt.value, v, ty_args=(aty.TypeAnnotation.RESULT, rt.field_type())
                )
            case _:
                raise Exception("unreachable")

    result: aex.Expression = get_arg(aty.EnvironmentType.RESULT)
    result = update_field(result, aty.ResultType.VALUE, _value)
    result = update_field(result, aty.ResultType.EXIT, _exit)
    result = update_field(result, aty.ResultType.FALLTHROUGH, _fallthrough)
    result = update_field(result, aty.ResultType.RETURN, _return)
    return update_arg(update=result, ty=aty.EnvironmentType.RESULT)


def convert_stmt(b: bsm.Statement, simplify: bool = False) -> list[asm.Statement]:
    """
    Convert a Batfish AST statement into an Angler AST statement.
    If simplify is true, boolean expressions are simplified.
    """
    match b:
        case bsm.IfStatement(
            comment=comment, guard=guard, true_stmts=t_stmts, false_stmts=f_stmts
        ):
            new_guard = convert_expr(guard, simplify=simplify)
            # simplify if the guard statically resolves to true or false
            if new_guard == aex.LiteralBool(True):
                return convert_stmts(t_stmts, simplify=simplify)
            elif new_guard == aex.LiteralBool(False):
                return convert_stmts(f_stmts, simplify=simplify)
            # convert the arms of the if
            true_stmt = convert_stmts(t_stmts, simplify=simplify)
            false_stmt = convert_stmts(f_stmts, simplify=simplify)
            # check if both arms are the same; if so, we can simplify the resulting
            # expression
            if true_stmt == false_stmt:
                return true_stmt
            else:
                return [
                    asm.IfStatement(
                        comment=comment,
                        guard=new_guard,
                        true_stmt=true_stmt,
                        false_stmt=false_stmt,
                    )
                ]

        case bsm.SetCommunities(comm_set=comms):
            return [
                update_arg(
                    convert_expr(comms, simplify=simplify), aty.EnvironmentType.COMMS
                )
            ]

        case bsm.SetLocalPreference(lp=lp):
            return [
                update_arg(convert_expr(lp, simplify=simplify), aty.EnvironmentType.LP)
            ]

        case bsm.SetMetric(metric=metric):
            return [
                update_arg(
                    convert_expr(metric, simplify=simplify), aty.EnvironmentType.METRIC
                )
            ]

        case bsm.SetNextHop(expr=_):
            # FIXME: ignored for now, fix later
            return []
            # return [update_arg(convert_expr(expr), aty.EnvironmentType.NEXTHOP)]

        case bsm.SetOrigin(origin_type):
            return [
                update_arg(
                    convert_expr(origin_type, simplify=simplify),
                    aty.EnvironmentType.ORIGIN,
                )
            ]

        case bsm.SetWeight(expr):
            return [
                update_arg(
                    convert_expr(expr, simplify=simplify), aty.EnvironmentType.WEIGHT
                )
            ]

        case bsm.SetDefaultPolicy(name):
            # NOTE: we treat SetDefaultPolicy specially as it represents a modification to the
            # environment, but not the actual route.
            return [asm.SetDefaultPolicy(name)]

        case bsm.StaticStatement(ty=ty):
            # cases based on
            # https://github.com/batfish/batfish/blob/master/projects/batfish-common-protocol/src/main/java/org/batfish/datamodel/routing_policy/statement/Statements.java
            # NOTE(tim): these statements generate a fresh result type,
            # meaning all result fields are reset to their default values and then
            # assigned according to the type of statement
            match ty:
                case bsm.StaticStatementType.EXIT_ACCEPT:
                    update = create_result(_value=True, _exit=True)
                case bsm.StaticStatementType.EXIT_REJECT:
                    update = create_result(_value=False, _exit=True)
                case bsm.StaticStatementType.RETURN_TRUE:
                    update = create_result(_value=True, _return=True)
                case bsm.StaticStatementType.RETURN_FALSE:
                    update = create_result(_value=False, _return=True)
                case bsm.StaticStatementType.FALL_THROUGH:
                    update = create_result(_fallthrough=True, _return=True)
                case bsm.StaticStatementType.RETURN:
                    update = create_result(_return=True)
                case bsm.StaticStatementType.LOCAL_DEF:
                    value_expr = get_arg(aty.EnvironmentType.LOCAL_DEFAULT_ACTION)
                    update = create_result(_value=value_expr)
                case bsm.StaticStatementType.SET_ACCEPT | bsm.StaticStatementType.SET_LOCAL_ACCEPT:
                    # TODO: distinguish local default action and default action?
                    # NOTE(tim): return directly since this statement updates the default action
                    # instead of the result
                    return [
                        update_arg(
                            aex.LiteralBool(True),
                            aty.EnvironmentType.LOCAL_DEFAULT_ACTION,
                        )
                    ]
                case bsm.StaticStatementType.SET_REJECT | bsm.StaticStatementType.SET_LOCAL_REJECT:
                    # TODO: distinguish local default action and default action?
                    # NOTE(tim): return directly since this statement updates the default action
                    # instead of the result
                    return [
                        update_arg(
                            aex.LiteralBool(False),
                            aty.EnvironmentType.LOCAL_DEFAULT_ACTION,
                        )
                    ]
                case _:
                    raise NotImplementedError(
                        f"No convert case for static statement {ty} found."
                    )
            return [update_arg(update, aty.EnvironmentType.RESULT)]
        case bsm.PrependAsPath():
            # NOTE: ignored
            return []
        case bsm.TraceableStatement(inner=inner):
            return convert_stmts(inner, simplify=simplify)
        case _:
            raise NotImplementedError(f"No convert_stmt case for statement {b} found.")


def convert_stmts(
    stmts: list[bsm.Statement], simplify: bool = False
) -> list[asm.Statement]:
    """Convert a list of Batfish statements into an Angler statement."""
    match stmts:
        case []:
            return []
        case [hd, *tl]:
            return convert_stmt(hd, simplify=simplify) + convert_stmts(
                tl, simplify=simplify
            )
        case _:
            raise Exception("unreachable")


def unreachable() -> aex.Expression[bool]:
    """Return an expression that is true if the route has returned or exited."""
    result = get_arg(aty.EnvironmentType.RESULT)
    return aex.Disjunction(
        [
            aex.GetField(
                result,
                aty.ResultType.RETURN.value,
                ty_args=(aty.TypeAnnotation.RESULT, aty.TypeAnnotation.BOOL),
            ),
            aex.GetField(
                result,
                aty.ResultType.EXIT.value,
                ty_args=(aty.TypeAnnotation.RESULT, aty.TypeAnnotation.BOOL),
            ),
        ]
    )


def convert_routing_policy(
    body: list[bsm.Statement], simplify: bool = False
) -> net.Func:
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
                return cast(list[asm.Statement], [hd])
            case [hd, *tl]:
                if isinstance(hd, asm.IfStatement):
                    hd.true_stmt = recurse(hd.true_stmt)
                    hd.false_stmt = recurse(hd.false_stmt)
                return cast(
                    list[asm.Statement],
                    [
                        hd,
                        asm.IfStatement("early_return", unreachable(), [], recurse(tl)),
                    ],
                )
            case _:
                raise Exception("unreachable")

    # convert the body and then add the early-return tests
    new_body = recurse(convert_stmts(body, simplify=simplify))
    check_returned = asm.IfStatement(
        "reset_return",
        # TODO(tim): should this be unreachable() or just checking if the result returned?
        # it seems like in either case, returned should be set to false
        # get_arg(aty.EnvironmentType.RESULT_RETURN),
        unreachable(),
        [
            update_arg_result(
                _return=False,
            )
        ],
        [
            # set fallthrough to true and the value to the local default
            update_arg_result(
                _fallthrough=True,
                _value=get_arg(aty.EnvironmentType.LOCAL_DEFAULT_ACTION),
            ),
        ],
    )
    # add the end statement to new_body
    new_body.append(check_returned)
    return net.Func(ARG, new_body)


TResult = TypeVar("TResult")
TRoute = TypeVar("TRoute")


def get_ip_node_mapping(ips: list[OwnedIP]) -> dict[IPv4Address, str]:
    """
    Return the mapping from IP addresses to nodes
    according to the given IP information.
    """
    # TODO: should we also include the mask & interface here?
    return {ip.ip: ip.node.nodename for ip in ips if ip.active}


def convert_structure(
    b: bstruct.Structure,
    simplify: bool = False,
) -> tuple[
    str,
    str,
    net.Func | aex.Expression | tuple[IPv4Address, dict[AsnPeer, net.Policies]] | None,
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
            struct_name = name
            value = convert_routing_policy(stmts, simplify=simplify)
        case bacl.RouteFilterList(_name=name, lines=_lines):
            struct_name = route_filter_list_var(name)
            # convert the batfish line to an angler line
            # (almost the same, just written out a bit differently)
            lines = []
            for l in _lines:
                action = l.action == Action.PERMIT
                # split the range into two ints
                low, high = l.length_range.split("-")
                wildcard = aex.IPv4Wildcard(l.ip_wildcard)
                lines.append(aex.RouteFilterLine(action, wildcard, int(low), int(high)))
            rfl = aex.RouteFilterList(lines)
            value = aex.RouteFilterListExpr(rfl)
        case bcomms.CommunitySetMatchExpr():
            struct_name = community_set_match_expr_var(struct_name)
            value = convert_expr(b.definition.value)
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
                    ): net.Policies(
                        asn=config.remote_as,
                        imp=config.address_family.import_policy,
                        exp=config.address_family.export_policy,
                    )
                    for neighbor, config in bgp.neighbors.items()
                },
            )
        case bvrf.Vrf(vrfname=name):
            # TODO
            print(f"Skipping VRF with unexpected name {name}...")
        case bacl.Route6FilterList(_name=name):
            # TODO
            struct_name = name
        case _:
            raise NotImplementedError(f"No convert case for {b} found.")
    return node_name, struct_name, value


def convert_batfish(bf: json.BatfishJson, simplify=False) -> net.Network:
    """
    Convert the Batfish JSON object to an Angler `net.Network`.
    If `simplify` is True, simplify boolean expressions found when possible.
    """
    ips = get_ip_node_mapping(bf.ips)
    nodes: dict[str, net.Properties] = {}
    constants: dict[str, dict[str, aex.Expression]] = {}
    externals: dict[tuple[IPv4Address, Optional[int]], set[str]] = {}
    # add constants, declarations and prefixes for each of the nodes
    print("Converting found structures...")
    for s in bf.declarations:
        n, k, v = convert_structure(s, simplify=simplify)
        if n not in nodes:
            nodes[n] = net.Properties()
        if n not in constants:
            constants[n] = {}
        match v:
            case net.Func():
                nodes[n].declarations[k] = v
            case aex.Expression():
                constants[n][k] = v
            case (address, peers_to_policies):
                # add a /24 prefix based on the given address
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
                        neighbor = str(peering.remote_ip)
                        neighbor_policies[neighbor] = policy_block
                        # if we've not previously matched to this node, check if it's external
                        if neighbor not in nodes:
                            # IP belongs to an external neighbor if the ASes differ
                            if (
                                peering.local_asn is None
                                or peering.local_asn != peering.remote_asn
                            ):
                                # node is external, add to externals (if not already present)
                                extpeer = (peering.remote_ip, peering.remote_asn)
                                if extpeer not in externals:
                                    externals[extpeer] = set()
                                # add this node to the peer's connections
                                externals[extpeer].add(n)
                            else:
                                # internal node
                                nodes[neighbor] = net.Properties(
                                    asnum=peering.remote_asn
                                )
                                nodes[neighbor].policies[n] = net.Policies(
                                    peering.remote_asn, None, None
                                )
                    else:
                        neighbor_policies[node_owner] = policy_block
                # bind the policies to the node
                nodes[n].policies = neighbor_policies
            case None:
                pass
    # inline constants
    print("Inlining constants...")
    for node, properties in nodes.items():
        for func in properties.declarations.values():
            for stmt in func.body:
                # NOTE: stmt substitution returns None, but expr substitution returns an expression
                stmt.subst(constants[node])
    print("Conversion complete!")
    # construct external peers so that they can be encoded to JSON
    external_peers = [
        net.ExternalPeer(ip, asn, list(peers))
        for ((ip, asn), peers) in externals.items()
    ]
    return net.Network(
        route=aty.EnvironmentType.fields(),
        nodes=nodes,
        externals=external_peers,
    )


class ConvertException(Exception):
    ...
