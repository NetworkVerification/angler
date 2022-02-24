#!/usr/bin/env python3
"""
Next hop in the Batfish AST.
"""
from dataclasses import dataclass
from ipaddress import IPv4Address
from serialize import Serialize, Field
import bast.base as ast
import bast.expression as expr


class NextHopExprType(ast.Variant):
    SELF_NEXT_HOP = "SelfNextHop"
    DISCARD_NEXT_HOP = "DiscardNextHop"
    IP_NEXT_HOP = "IpNextHop"

    def as_class(self):
        match self:
            case NextHopExprType.SELF_NEXT_HOP:
                return SelfNextHop
            case NextHopExprType.DISCARD_NEXT_HOP:
                return DiscardNextHop
            case NextHopExprType.IP_NEXT_HOP:
                return IpNextHop
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class NextHopExpr(
    expr.Expression, Serialize, delegate=("class", NextHopExprType.parse_class)
):
    ...


@dataclass
class IpNextHop(NextHopExpr, Serialize, ips=Field("ips", list[IPv4Address])):
    ips: list[IPv4Address]


@dataclass
class SelfNextHop(NextHopExpr, Serialize):
    ...


@dataclass
class DiscardNextHop(NextHopExpr, Serialize):
    ...
