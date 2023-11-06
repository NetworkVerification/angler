#!/usr/bin/env python3
"""
General expressions in the Batfish AST.
"""
from dataclasses import dataclass
from angler.serialize import Serialize
import angler.util


class ExprType(angler.util.Variant):
    """A type of expression."""

    def as_class(self) -> type:
        raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class Expression(
    angler.util.ASTNode,
    Serialize,
    delegate=("class", ExprType.parse_class),
):
    """
    The base class for expressions.
    """

    ...
