#!/usr/bin/env python3
"""
Other Batfish AST types.
"""
from enum import Enum


class Action(Enum):
    """An action to perform on routes."""

    PERMIT = "PERMIT"
    DENY = "DENY"


class Protocol(Enum):
    BGP = "bgp"
    IBGP = "ibgp"
    OSPF = "ospf"
    STATIC = "static"
    CONN = "connected"
    AGG = "aggregate"
    LOCAL = "local"
    ISIS_EL1 = "isisEL1"
    ISIS_EL2 = "isisEL2"
    ISIS_L1 = "isisL1"
    ISIS_L2 = "isisL2"


class OriginType(Enum):
    INCOMPLETE = "incomplete"  # corresponds to 0
    EGP = "egp"  # corresponds to 1
    IGP = "igp"  # corresponds to 2

    def to_int(self) -> int:
        match self:
            case OriginType.INCOMPLETE:
                return 0
            case OriginType.EGP:
                return 1
            case OriginType.IGP:
                return 2
            case _:
                raise ValueError(f"No integer representation for origin type {self}")


class Comparator(Enum):
    EQ = "EQ"
    GE = "GE"
    GT = "GT"
    LE = "LE"
    LT = "LT"


class Metric(dict):
    ...
