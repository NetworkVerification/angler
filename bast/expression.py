#!/usr/bin/env python3
"""
General expressions in the Batfish AST.
"""
from dataclasses import dataclass
import bast.base as ast
from serialize import Serialize


class ExprType(ast.Variant):
    """A type of expression."""

    def as_class(self) -> type:
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
