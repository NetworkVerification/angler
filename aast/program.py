#!/usr/bin/env python3

from dataclasses import dataclass, field
from ipaddress import IPv4Network
from typing import Optional
import aast.expression as expr
import aast.statement as stmt

from serialize import Serialize


@dataclass
class Assert(Serialize, arg="arg", expr="expr"):
    """
    An assertion to check on an argument "arg".
    """

    arg: str
    expr: expr.Expression[bool]


@dataclass
class Func(Serialize, arg="arg", body="body"):
    """
    A function taking a single argument "arg" and executing the statements of its body.
    """

    arg: str
    body: list[stmt.Statement]


@dataclass
class Policies(Serialize, imp="import", exp="export"):
    imp: list[Func | str] = field(default_factory=list)
    exp: list[Func | str] = field(default_factory=list)


@dataclass
class Properties(
    Serialize, prefixes="prefixes", policies="policies", assertions="assertions"
):
    prefixes: list[IPv4Network] = field(default_factory=list)
    policies: dict[str, Policies] = field(default_factory=dict)
    assertions: list[Assert] = field(default_factory=list)


@dataclass
class Program(
    Serialize,
    route="route",
    nodes="nodes",
    consts="consts",
    declarations="declarations",
    ghost="ghost",
    symbolics="symbolics",
):
    route: dict
    nodes: dict[str, Properties]
    consts: dict[str, expr.Expression] = field(default_factory=dict)
    declarations: dict[str, Func] = field(default_factory=dict)
    ghost: Optional[dict] = None
    symbolics: dict[str, Func] = field(default_factory=dict)
