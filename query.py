#!/usr/bin/env python3
# Utilities for expressing queries about routing state.

from dataclasses import dataclass
from enum import Enum
from ipaddress import IPv4Address
from typing import Optional
import aast.program as prog
import aast.types as ty
import aast.properties as prop


@dataclass
class Query:
    """
    Representation of a query concerning the network.
    """

    dest: Optional[prog.Dest]
    # map from nodes to predicates or a single predicate for all nodes
    predicates: dict[str, prog.Predicate] | prog.Predicate
    symbolics: dict[str, prog.Predicate]
    ghost: Optional[dict[str, ty.TypeAnnotation]]
    with_time: bool


class QueryType(Enum):
    SP = "reachable"
    FAT = "valleyfree"
    HIJACK = "hijack"

    def to_query(self, address: IPv4Address, with_time: bool) -> Query:
        match self:
            case QueryType.SP:
                return reachable(address, with_time)
            case _:
                raise NotImplementedError("Query not yet implemented")


def reachable(address: IPv4Address, with_time: bool) -> Query:
    dest = prog.Dest(address)
    predicates = prop.isValid()
    symbolics = {}
    ghost = None
    return Query(dest, predicates, symbolics, ghost, with_time)
