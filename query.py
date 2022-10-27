#!/usr/bin/env python3
# Utilities for expressing queries about routing state.

from dataclasses import dataclass
from enum import Enum
import igraph
from ipaddress import IPv4Address, IPv4Network
from typing import Any, Optional
import aast.program as prog
import aast.types as ty
import aast.expression as e
import aast.predicates as preds
import aast.temporal as temp


@dataclass
class NodeQuery:
    """
    Representation of a safety check and optionally a temporal check at a node.
    """

    safety_check: str
    temporal_check: temp.TemporalOp


@dataclass
class Query:
    """
    Representation of a query concerning the network.
    """

    predicates: dict[str, prog.Predicate]
    symbolics: dict[str, prog.Predicate]
    ghost: Optional[dict[str, ty.TypeAnnotation]]
    nodes: dict[str, NodeQuery]


class QueryType(Enum):
    SP = "reachable"
    FAT = "valleyfree"
    HIJACK = "hijack"
    BTE = "bte"

    def from_nodes(self, nodes: dict[str, Any]) -> Query:
        match self:
            case QueryType.SP:
                return reachable(nodes)
            case QueryType.FAT:
                return vf_reachable(nodes)
            case QueryType.HIJACK:
                return hijack_safe(nodes)
            case QueryType.BTE:
                return block_to_external(nodes)
            case _:
                raise NotImplementedError("Query not yet implemented")


def vf_reachable(nodes: dict[str, Any]) -> Query:
    """
    Return a query that checks that every node is reachable.
    """
    predicates = {
        f"isValidTags-{node}": preds.isValidTags(x.comms) for node, x in nodes.items()
    }
    predicates["isValid"] = preds.isValid()
    predicates["isNull"] = preds.isNull()
    symbolics = {}
    ghost = None
    node_queries = {
        node: NodeQuery("isValid", temp.Until(x.dist, "isNull", f"isValidTags-{node}"))
        for node, x in nodes.items()
    }
    return Query(predicates, symbolics, ghost, node_queries)


def reachable(nodes: dict[str, Any]) -> Query:
    """
    Return a query that checks that every node is reachable.
    The data associated with each node key is used to determine the
    time at which the node becomes reachable.
    """
    predicates = {"isValid": preds.isValid()}
    symbolics = {}
    ghost = None
    node_queries = {
        node: NodeQuery("isValid", temp.Finally(dist, "isValid"))
        for node, dist in nodes.items()
    }
    return Query(predicates, symbolics, ghost, node_queries)


def hijack_safe(nodes: dict[str, Any]) -> Query:
    predicates = {"hasInternalRoute": preds.hasInternalRoute()}
    # add a hijack route variable which is marked as an external route
    symbolics = {"hijack": preds.hasExternalRoute()}
    ghost = {"external": ty.TypeAnnotation.BOOL}
    # TODO: fix the annotations
    node_queries = {
        node: NodeQuery("hasInternalRoute", temp.Finally(x, "hasInternalRoute"))
        for node, x in nodes.items()
    }
    return Query(predicates, symbolics, ghost, node_queries)


def block_to_external(nodes: dict[str, Any]) -> Query:
    """
    Generate a query checking that nodes marked external never have a route
    with origin type "internal" originated inside the network.
    Each node has a boolean origin type associated with it.
    """
    BTE_TAG = "11537:888"
    predicates = {
        # "hasInternalRoute": preds.implies(preds.isValid(), preds.hasInternalRoute()),
        "internal": prog.Predicate.default(),
        "external": preds.all_predicates(preds.tags_absent([BTE_TAG])),
        "external-start": preds.tags_absent([BTE_TAG]),
    }
    # TODO: one internal node has an internal route
    node_queries = {
        node: NodeQuery(
            "external" if external else "internal",
            temp.Globally("external" if external else "internal"),
        )
        for node, external in nodes.items()
    }
    return Query(predicates, {}, {}, node_queries)


def get_node_distances(g: igraph.Graph, destinations: list[str]) -> dict[str, int]:
    """
    Return the shortest distance to any destination node for each node in the graph,
    i.e. computes the minimum shortest path over multiple destinations.
    """
    # compute shortest paths: produces a matrix with a row for each source
    distances: list[list[int]] = g.shortest_paths(source=destinations, mode="all")
    # we want the minimum distance to any source for each node
    best_distances = [
        min([distances[src][v.index] for src in range(len(distances))]) for v in g.vs
    ]
    return {g.vs[i]["name"]: d for i, d in enumerate(best_distances)}


def add_query(
    p: prog.Program, q: QueryType, dest: Optional[IPv4Address], with_time: bool
) -> None:
    """
    Add query information to a given program.
    """
    print("Adding verification elements...")
    # set up verification tooling
    g = igraph.Graph(
        n=len(p.nodes),
        edges=[
            (src, target)
            for (src, props) in p.nodes.items()
            for target in props.policies.keys()
        ],
        directed=True,
    )
    external_nodes = set()
    destinations = []
    for n, props in p.nodes.items():
        if isinstance(props.initial, e.Var):
            # identify the external nodes as ones with a symbolic variable as their initial value
            external_nodes.add(n)
        elif dest and any([dest in prefix for prefix in props.prefixes]):
            destinations.append(n)
            # set the prefix
            update_prefix = e.WithField(
                props.initial,
                ty.EnvironmentType.PREFIX.value,
                e.IpPrefix(IPv4Network(dest)),
            )
            props.initial = e.WithField(
                update_prefix,
                ty.EnvironmentType.RESULT.value,
                e.WithField(
                    e.default_value(ty.TypeAnnotation.RESULT),
                    ty.ResultType.VALUE.value,
                    e.LiteralBool(True),
                ),
            )
    # determine what information we need for the node queries
    match q:
        case QueryType.SP if dest:
            node_info = get_node_distances(g, destinations)
            p.converge_time = max(node_info.values())
            # add all query predicates
            query = q.from_nodes(node_info)
            p.predicates = query.predicates
            # assign safety checks to nodes
            for node, node_query in query.nodes.items():
                p.nodes[node].stable = node_query.safety_check
                if with_time:
                    p.nodes[node].temporal = node_query.temporal_check
        case QueryType.FAT if dest:
            # TODO: get the comms
            dist_node_info = get_node_distances(g, destinations)
            p.converge_time = max(dist_node_info.values())
        case QueryType.BTE:
            # update the external routes
            for node in external_nodes:
                p.symbolics[f"external-route-{node}"] = "external-start"
            node_info = {node: node in external_nodes for node in p.nodes.keys()}
            p.converge_time = 5
            query = q.from_nodes(node_info)
            p.predicates = query.predicates
            # assign safety checks to nodes
            for node, node_query in query.nodes.items():
                p.nodes[node].stable = node_query.safety_check
                if with_time:
                    p.nodes[node].temporal = node_query.temporal_check
        case _:
            raise NotImplementedError("Query not yet implemented")
