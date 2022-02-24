#!/usr/bin/env python3
"""
General expressions in the Batfish AST.
"""
from dataclasses import dataclass
import bast.base as ast
from serialize import Serialize, Field


class ExprType(ast.Variant):
    """A type of expression."""

    CALL_EXPR = "CallExpr"

    def as_class(self) -> type:
        match self:
            case ExprType.CALL_EXPR:
                return CallExpr
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
class CallExpr(Expression, Serialize, policy="calledPolicyName"):
    """
    Call the given policy.
    """

    policy: str
