#!/usr/bin/env python3

from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Network
from typing import Optional
import aast.expression as expr
import aast.statement as stmt
import aast.types as ty
import aast.temporal as temp

from serialize import Serialize


@dataclass
class Dest(Serialize, address="address"):
    address: IPv4Address


@dataclass
class Predicate(Serialize, arg="arg", expr="expr"):
    """
    A predicate from T to bool to check on an argument "arg" of type T.
    """

    arg: str
    expr: expr.Expression[bool]

    @staticmethod
    def default():
        """Return a predicate that always holds."""
        return Predicate("_", expr.LiteralBool(True))


@dataclass
class Func(Serialize, arg="arg", body="body"):
    """
    A function from T to T taking a single argument "arg" of type T
    and executing the statements of its body.
    """

    arg: str
    body: list[stmt.Statement]


@dataclass
class Policies(Serialize, imp="import", exp="export"):
    imp: list[str] = field(default_factory=list)
    exp: list[str] = field(default_factory=list)


@dataclass
class Properties(
    Serialize,
    asnum="ASNumber",
    prefixes="Prefixes",
    policies="Policies",
    initial="Initial",
    consts="Constants",
    declarations="Declarations",
    stable="Stable",
    temporal="Temporal",
):
    asnum: int
    prefixes: set[IPv4Network] = field(default_factory=set)
    policies: dict[str, Policies] = field(default_factory=dict)
    initial: Optional[expr.Expression] = None
    consts: dict[str, expr.Expression] = field(default_factory=dict)
    declarations: dict[str, Func] = field(default_factory=dict)
    # asserts over a route
    stable: Optional[str] = None
    temporal: Optional[temp.TemporalOp] = None


@dataclass
class Program(
    Serialize,
    route="Route",
    nodes="Nodes",
    ghost="Ghost",
    predicates="Predicates",
    symbolics="Symbolics",
    converge_time="ConvergeTime",
):
    route: dict[str, ty.TypeAnnotation]
    nodes: dict[str, Properties]
    ghost: Optional[dict[str, ty.TypeAnnotation]] = None
    predicates: dict[str, Predicate] = field(default_factory=dict)
    symbolics: dict[str, Predicate] = field(default_factory=dict)
    converge_time: Optional[int] = None
