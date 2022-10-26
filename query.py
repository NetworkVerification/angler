#!/usr/bin/env python3
# Utilities for expressing queries about routing state.

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
import aast.program as prog
import aast.types as ty
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
