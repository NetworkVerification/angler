#!/usr/bin/env python3
"""
Prefix expressions in the Batfish AST.
"""
from dataclasses import dataclass
from serialize import Serialize
import bast.base as ast
import bast.expression as expr


class PrefixExprType(ast.Variant):
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


class PrefixSetExprType(ast.Variant):
    NAMED_PREFIX_SET = "NamedPrefixSet"
    NAMED_PREFIX6_SET = "NamedPrefix6Set"

    def as_class(self) -> type:
        match self:
            case PrefixSetExprType.NAMED_PREFIX_SET:
                return NamedPrefixSet
            case PrefixSetExprType.NAMED_PREFIX6_SET:
                return NamedPrefix6Set
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
