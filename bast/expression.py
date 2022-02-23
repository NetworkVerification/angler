#!/usr/bin/env python3
"""
General expressions in the Batfish AST.
"""
from dataclasses import dataclass
import bast.base as ast
import bast.btypes as types
from serialize import Serialize, Field


class ExprType(ast.Variant):
    """A type of expression."""

    # MATCHIPV4 = "matchIpv4"
    # CALLEXPR = "callExpr"
    # WITHENVIRONMENTEXPR = "withEnvironmentExpr"
    # ASEXPR = "asExpr"
    # COMMUNITYSETEXPR = "communitySetExpr"
    LITERALLONG = "LiteralLong"
    LITERALASLIST = "LiteralAsList"
    DESTINATION = "DestinationNetwork"  # variable
    NAMEDPREFIXSET = "NamedPrefixSet"

    def as_class(self) -> type:
        match self:
            case ExprType.NAMEDPREFIXSET:
                return NamedPrefixSet
            case ExprType.DESTINATION:
                return DestinationNetwork
            case ExprType.LITERALLONG:
                return LiteralLong
            case ExprType.LITERALASLIST:
                return LiteralAsList
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class Expression(
    ast.ASTNode,
    Serialize,
    delegate=("class", ExprType.parse_class),
):
    """
    The base class for expressions.
    """

    ...


@dataclass
class Var(Expression, Serialize):
    """A class representing a Batfish variable."""


@dataclass
class DestinationNetwork(Var):
    ...


@dataclass
class NamedPrefixSet(Var, Serialize, _name="name"):
    _name: str


@dataclass
class LiteralLong(Expression, Serialize, value=Field("value", int)):
    value: int


@dataclass
class LiteralAsList(Expression, Serialize, ases=Field("list", list[types.ExplicitAs])):
    ases: list[types.ExplicitAs]
