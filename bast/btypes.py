#!/usr/bin/env python3
"""
Other Batfish AST types.
"""
from enum import Enum
from dataclasses import dataclass
from serialize import Serialize, Field
from ipaddress import IPv4Address
import bast.base as ast


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


@dataclass
class Node(ast.ASTNode, Serialize, nodeid="id", nodename="name"):
    """A node in the network."""

    nodeid: str
    nodename: str


@dataclass
class Interface(ast.ASTNode, Serialize, host="hostname", iface="interface"):
    host: str
    iface: str


@dataclass
class Edge(
    ast.ASTNode,
    Serialize,
    iface=Field("Interface", Interface),
    ips=Field("IPs", list[IPv4Address]),
    remote_iface=Field("Remote_Interface", Interface),
    remote_ips=Field("Remote_IPs", list[IPv4Address]),
):
    """
    A representation of a directed edge between two interfaces.
    The first (non-remote) interface is the source.
    The second remote interface is the target.
    """

    iface: Interface
    ips: list[IPv4Address]
    remote_iface: Interface
    remote_ips: list[IPv4Address]


class Metric(dict):
    ...
