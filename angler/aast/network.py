#!/usr/bin/env python3
"""
The top-level representation of a network in Angler.
"""

from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Network
from typing import Optional
import angler.aast.statement as stmt
import angler.aast.types as ty

from angler.serialize import Field, Serialize


@dataclass
class Func(Serialize, arg="arg", body=Field("body", list[stmt.Statement])):
    """
    A function from T to T taking a single argument "arg" of type T
    and executing the statements of its body.
    """

    arg: str
    body: list[stmt.Statement]


@dataclass(order=True)
class Policies(Serialize, asn=Field("Asn", int), imp="Import", exp="Export"):
    """
    Representation of a node in the network with a particular defined import and export policy.
    May optionally specify an AS number if on an inter-network connection.
    """

    asn: Optional[int]
    imp: Optional[str]
    exp: Optional[str]


@dataclass(frozen=True, order=True)
class ExternalPeer(
    Serialize,
    ip=Field("Ip", IPv4Address),
    asnum=Field("ASNumber", int, None),
    peering=Field("Peering", list[str], []),
):
    """
    Representation of an external peer connection.
    """

    ip: IPv4Address
    asnum: Optional[int] = None
    peering: list[str] = field(default_factory=list)


@dataclass
class Properties(
    Serialize,
    asnum=Field("ASNumber", int, None),
    prefixes=Field("Prefixes", set[IPv4Network]),
    policies=Field("Policies", dict[str, Policies]),
    declarations=Field("Declarations", dict[str, Func]),
):
    """
    Representation of the properties of a particular router in the network,
    including its AS number, its prefixes, the policies it applies for its
    peer sessions, and function declarations.
    """

    asnum: Optional[int] = None
    prefixes: set[IPv4Network] = field(default_factory=set)
    policies: dict[str, Policies] = field(default_factory=dict)
    declarations: dict[str, Func] = field(default_factory=dict)

    def add_prefix_from_ip(self, ip: IPv4Address):
        """
        Add a /24 prefix to the properties based on the given address.
        """
        # strict=False causes this to mask the last 8 bits
        net = IPv4Network((ip, 24), strict=False)
        self.prefixes.add(net)


@dataclass
class Network(
    Serialize,
    route=Field("Route", dict[str, ty.TypeAnnotation]),
    nodes=Field("Nodes", dict[str, Properties]),
    externals=Field("Externals", list[ExternalPeer]),
):
    """
    A representation of a network in Angler's AST.
    """

    route: dict[str, ty.TypeAnnotation]
    nodes: dict[str, Properties]
    # External peers and the nodes they connect to
    externals: list[ExternalPeer]
