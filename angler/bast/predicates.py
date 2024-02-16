#!/usr/bin/env python3

"""
Boolean predicates in the Batfish AST.
"""
from dataclasses import dataclass
from angler.serialize import Serialize, Field
import angler.bast.expression as expr
import angler.bast.btypes as types
import angler.bast.intexprs as ints
import angler.util


class PredicateExprType(angler.util.Variant):
    INT_COMPARISON = "IntComparison"

    def as_class(self) -> type:
        match self:
            case PredicateExprType.INT_COMPARISON:
                return IntComparison
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class BooleanPredicateExpr(
    expr.Expression, Serialize, delegate=("class", PredicateExprType.parse_class)
):
    ...


@dataclass
class IntComparison(
    BooleanPredicateExpr,
    Serialize,
    comparator=Field("comparator", types.Comparator),
    expr=Field("expr", ints.IntExpr),
):
    """A predicate for testing a given integer-based comparison."""

    comparator: types.Comparator
    expr: ints.IntExpr
