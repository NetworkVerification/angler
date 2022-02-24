#!/usr/bin/env python3
"""
Prefix expressions in the Batfish AST.
"""
from dataclasses import dataclass
from serialize import Serialize, Field
import bast.base as ast
import bast.expression as expr


class PrefixExprType(ast.Variant):
    DESTINATION = "DestinationNetwork"  # variable
    DESTINATION6 = "DestinationNetwork6"  # variable
    NAMED_PREFIX_SET = "NamedPrefixSet"
    NAMED_PREFIX6_SET = "NamedPrefix6Set"

    def as_class(self) -> type:
        match self:
            case PrefixExprType.NAMED_PREFIX_SET:
                return NamedPrefixSet
            case PrefixExprType.DESTINATION:
                return DestinationNetwork
            case PrefixExprType.NAMED_PREFIX6_SET:
                return NamedPrefix6Set
            case PrefixExprType.DESTINATION6:
                return DestinationNetwork6
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class PrefixExpr(
    expr.Expression, Serialize, delegate=("class", PrefixExprType.parse_class)
):
    ...


@dataclass
class DestinationNetwork(PrefixExpr, Serialize):
    ...


@dataclass
class NamedPrefixSet(PrefixExpr, Serialize, _name="name"):
    _name: str


@dataclass
class DestinationNetwork6(PrefixExpr, Serialize):
    ...


@dataclass
class NamedPrefix6Set(PrefixExpr, Serialize, _name="name"):
    _name: str
