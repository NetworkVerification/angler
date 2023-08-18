#!/usr/bin/env python3
"""
The top-level representation of a network in Angler.
"""

from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Network
from typing import Optional
import aast.statement as stmt
import aast.types as ty

from serialize import Field, Serialize


@dataclass
class Func(Serialize, arg="arg", body=Field("body", list[stmt.Statement])):
    """
    A function from T to T taking a single argument "arg" of type T
    and executing the statements of its body.
    """

    arg: str
    body: list[stmt.Statement]


@dataclass
class Policies(Serialize, asn=Field("Asn", int), imp="Import", exp="Export"):
    """
    Representation of a peer with a particular defined import and export policy.
    May optionally specify an AS number if on an inter-network connection.
    """

    asn: Optional[int]
    imp: Optional[str]
    exp: Optional[str]


@dataclass
class Properties(
    Serialize,
    asnum=Field("ASNumber", int, None),
    prefixes=Field("Prefixes", set[IPv4Network]),
    policies=Field("Policies", dict[str, Policies]),
    declarations=Field("Declarations", dict[str, Func]),
):
    asnum: Optional[int] = None
    prefixes: set[IPv4Network] = field(default_factory=set)
    policies: dict[str, Policies] = field(default_factory=dict)
    declarations: dict[str, Func] = field(default_factory=dict)

    def add_prefix_from_ip(self, ip: IPv4Address):
        """
        Add a /24 prefix to the properties based on the given address.
        """
        net = IPv4Network((ip, 24), strict=False)
        self.prefixes.add(net)


@dataclass
class Network(
    Serialize,
    route=Field("Route", dict[str, ty.TypeAnnotation]),
    nodes=Field("Nodes", dict[str, Properties]),
    symbolics=Field("Symbolics", dict[str, str]),
):
    """
    A representation of a network in Angler's AST.
    """

    route: dict[str, ty.TypeAnnotation]
    nodes: dict[str, Properties]
    symbolics: dict[str, Optional[str]] = field(default_factory=dict)
