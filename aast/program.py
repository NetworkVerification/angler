#!/usr/bin/env python3

from dataclasses import dataclass, field
from ipaddress import IPv4Network
from typing import Optional
import aast.expression as expr
import aast.statement as stmt
import aast.types as ty

from serialize import Serialize


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
        return Predicate("_", expr.LiteralTrue())


@dataclass
class Func(Serialize, arg="arg", body="body"):
    """
    A function from T to T taking a single argument "arg" of type T
    and executing the statements of its body.
    """

    arg: str
    body: stmt.Statement


@dataclass
class Policies(Serialize, imp="import", exp="export"):
    imp: list[str] = field(default_factory=list)
    exp: list[str] = field(default_factory=list)


@dataclass
class Properties(
    Serialize, prefixes="prefixes", policies="policies", assertions="assertions"
):
    prefixes: list[IPv4Network] = field(default_factory=list)
    policies: dict[str, Policies] = field(default_factory=dict)
    # asserts over a route
    assertions: list[str] = field(default_factory=list)
    # assert over a route and a time
    invariant: Optional[str] = None


@dataclass
class Program(
    Serialize,
    route="route",
    nodes="nodes",
    consts="consts",
    declarations="declarations",
    ghost="ghost",
    assertions="assertions",
    symbolics="symbolics",
    invariants="invariants",
):
    route: dict[str, ty.TypeAnnotation]
    nodes: dict[str, Properties]
    consts: dict[str, expr.Expression] = field(default_factory=dict)
    declarations: dict[str, Func] = field(default_factory=dict)
    ghost: Optional[dict] = None
    assertions: dict[str, Predicate] = field(default_factory=dict)
    symbolics: dict[str, Predicate] = field(default_factory=dict)
    invariants: dict[str, Predicate] = field(default_factory=dict)
