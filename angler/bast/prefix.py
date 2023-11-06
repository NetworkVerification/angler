#!/usr/bin/env python3
"""
Prefix expressions in the Batfish AST.
"""
from dataclasses import dataclass
from ipaddress import IPv4Network
from serialize import Serialize, Field
import bast.expression as expr
import util


class PrefixExprType(util.Variant):
    DESTINATION = "DestinationNetwork"  # variable
    DESTINATION6 = "DestinationNetwork6"  # variable

    def as_class(self) -> type:
        match self:
            case PrefixExprType.DESTINATION:
                return DestinationNetwork
            case PrefixExprType.DESTINATION6:
                return DestinationNetwork6
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class PrefixSetExprType(util.Variant):
    NAMED_PREFIX_SET = "NamedPrefixSet"
    NAMED_PREFIX6_SET = "NamedPrefix6Set"
    EXPLICIT_PREFIX_SET = "ExplicitPrefixSet"

    def as_class(self) -> type:
        match self:
            case PrefixSetExprType.NAMED_PREFIX_SET:
                return NamedPrefixSet
            case PrefixSetExprType.NAMED_PREFIX6_SET:
                return NamedPrefix6Set
            case PrefixSetExprType.EXPLICIT_PREFIX_SET:
                return ExplicitPrefixSet
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class PrefixExpr(
    expr.Expression, Serialize, delegate=("class", PrefixExprType.parse_class)
):
    ...


@dataclass
class PrefixSetExpr(
    expr.Expression, Serialize, delegate=("class", PrefixSetExprType.parse_class)
):
    ...


@dataclass
class DestinationNetwork(PrefixExpr, Serialize):
    ...


@dataclass
class DestinationNetwork6(PrefixExpr, Serialize):
    ...


@dataclass
class NamedPrefixSet(PrefixSetExpr, Serialize, _name="name"):
    _name: str


@dataclass
class NamedPrefix6Set(PrefixSetExpr, Serialize, _name="name"):
    _name: str


@dataclass
class ExplicitPrefixSet(
    PrefixSetExpr, Serialize, prefix_space=Field("prefixSpace", list[IPv4Network])
):
    prefix_space: list[IPv4Network]
