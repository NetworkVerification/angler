#!/usr/bin/env python3

from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Network
from typing import Optional
import aast.expression as expr
import aast.statement as stmt
import aast.types as ty
import aast.temporal as temp

from serialize import Field, Serialize


@dataclass
class Dest(Serialize, address=Field("address", IPv4Address)):
    address: IPv4Address


@dataclass
class Predicate(Serialize, arg="arg", body=Field("body", expr.Expression[bool])):
    """
    A predicate from T to bool to check on an argument "arg" of type T.
    """

    arg: str
    body: expr.Expression[bool]

    @staticmethod
    def default():
        """Return a predicate that always holds."""
        return Predicate("_", expr.LiteralBool(True))


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
    initial=Field("Initial", expr.Expression),
    declarations=Field("Declarations", dict[str, Func]),
    stable=Field("Stable", str, None),
    temporal=Field("Temporal", temp.TemporalOp, None),
):
    initial: expr.Expression
    asnum: Optional[int] = None
    prefixes: set[IPv4Network] = field(default_factory=set)
    policies: dict[str, Policies] = field(default_factory=dict)
    declarations: dict[str, Func] = field(default_factory=dict)
    # asserts over a route
    stable: Optional[str] = None
    temporal: Optional[temp.TemporalOp] = None

    def add_prefix_from_ip(self, ip: IPv4Address):
        """
        Add a /24 prefix to the properties based on the given address.
        """
        net = IPv4Network((ip, 24), strict=False)
        self.prefixes.add(net)


@dataclass
class Program(
    Serialize,
    route=Field("Route", dict[str, ty.TypeAnnotation]),
    nodes=Field("Nodes", dict[str, Properties]),
    ghost=Field("Ghost", dict[str, ty.TypeAnnotation], None),
    predicates=Field("Predicates", dict[str, Predicate]),
    symbolics=Field("Symbolics", dict[str, str]),
    converge_time=Field("ConvergeTime", int, None),
):
    route: dict[str, ty.TypeAnnotation]
    nodes: dict[str, Properties]
    ghost: Optional[dict[str, ty.TypeAnnotation]] = None
    predicates: dict[str, Predicate] = field(default_factory=dict)
    symbolics: dict[str, Optional[str]] = field(default_factory=dict)
    converge_time: Optional[int] = None
