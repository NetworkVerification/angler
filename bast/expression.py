#!/usr/bin/env python3
"""
General expressions in the Batfish AST.
"""
from dataclasses import dataclass
from serialize import Serialize
import util


class ExprType(util.Variant):
    """A type of expression."""

    def as_class(self) -> type:
        raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class Expression(
    util.ASTNode,
    Serialize,
    delegate=("class", ExprType.parse_class),
):
    """
    The base class for expressions.
    """

    ...
