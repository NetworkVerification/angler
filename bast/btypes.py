#!/usr/bin/env python3
"""
Other Batfish AST types.
"""
from dataclasses import dataclass
from serialize import Serialize
from ipaddress import IPv4Address
import bast.base as ast


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
    iface=("Interface", Interface),
    ips=("IPs", list[IPv4Address]),
    remote_iface=("Remote_Interface", Interface),
    remote_ips=("Remote_IPs", list[IPv4Address]),
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


@dataclass
class ExplicitAs(ast.ASTNode, Serialize, asnum=("as", int)):
    asnum: int


class Metric(dict):
    ...
