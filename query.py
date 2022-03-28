#!/usr/bin/env python3
# Utilities for expressing queries about routing state.

from dataclasses import dataclass
from enum import Enum
from ipaddress import IPv4Address
from typing import Callable, Optional
import aast.program as prog
import aast.types as ty
import aast.properties as prop
import aast.temporal as temp


@dataclass
class Query:
    """
    Representation of a query concerning the network.
    """

    dest: Optional[prog.Dest]
    predicates: dict[str, prog.Predicate]
    symbolics: dict[str, prog.Predicate]
    ghost: Optional[dict[str, ty.TypeAnnotation]]
    # either a map from nodes to predicate names or a predicate name used by all nodes
    safety_checks: dict[str, str] | str
    with_time: Optional[Callable[[int], temp.TemporalOp]]


class QueryType(Enum):
    SP = "reachable"
    FAT = "valleyfree"
    HIJACK = "hijack"

    def to_query(self, address: IPv4Address, with_time: bool) -> Query:
        match self:
            case QueryType.SP:
                return reachable(address, with_time)
            case QueryType.FAT:
                return vf_reachable(address, with_time)
            case _:
                raise NotImplementedError("Query not yet implemented")


def vf_reachable(address: IPv4Address, with_time: bool) -> Query:
    dest = prog.Dest(address)
    # FIXME: need to specify the tags when calling isValidTags
    predicates = {
        "isValidTags": prop.isValidTags(),
        "isNull": prop.isNull(),
    }
    symbolics = {}
    ghost = None
    temporal_op = None
    if with_time:
        temporal_op = lambda x: temp.Until(x, "isNull", "isValidTags")
    return Query(dest, predicates, symbolics, ghost, "isValidTags", temporal_op)


def reachable(address: IPv4Address, with_time: bool) -> Query:
    dest = prog.Dest(address)
    predicates = {"isValid": prop.isValid()}
    symbolics = {}
    ghost = None
    temporal_op = None
    if with_time:
        temporal_op = lambda x: temp.Finally(x, "isValid")
    return Query(dest, predicates, symbolics, ghost, "isValid", temporal_op)


def hijack_safe(address: IPv4Address, with_time: bool) -> Query:
    dest = prog.Dest(address)
    predicates = {"hasInternalRoute": prop.hasInternalRoute()}
    # add a hijack route variable which is marked as an external route
    symbolics = {"hijack": prop.hasExternalRoute()}
    ghost = {"external": ty.TypeAnnotation.BOOL}
    temporal_op = None
    if with_time:
        temporal_op = lambda x: temp.Finally(x, "hasInternalRoute")
    return Query(dest, predicates, symbolics, ghost, "hasInternalRoute", temporal_op)
