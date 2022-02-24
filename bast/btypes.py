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
    ISIS_EL1 = "isisEL1"
    ISIS_EL2 = "isisEL2"
    ISIS_L1 = "isisL1"
    ISIS_L2 = "isisL2"


class Comparator(Enum):
    EQ = "EQ"
    GE = "GE"
    GT = "GT"
    LE = "LE"
    LT = "LT"


class Metric(dict):
    ...
