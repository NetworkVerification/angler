#!/usr/bin/env python3
"""
AST representation of sets.
For now, we encode all sets as having strings as arguments:
in the future, we may relax this restriction.
"""
from dataclasses import dataclass
from serialize import Serialize, Field
import expression as expr
import base as ast


class SetExprType(ast.Variant):
    EMPTY = "EmptySet"
    UNION = "SetUnion"
    ADD = "SetAdd"
    REMOVE = "SetRemove"

    def as_class(self) -> type:
        match self:
            case SetExprType.EMPTY:
                return EmptySet
            case SetExprType.ADD:
                return SetAdd
            case SetExprType.REMOVE:
                return SetRemove
            case SetExprType.UNION:
                return SetUnion
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class SetExpr(expr.Expression, Serialize, delegate=("class", SetExprType.parse_class)):
    ...


@dataclass
class EmptySet(SetExpr, Serialize):
    ...


@dataclass
class SetAdd(
    SetExpr,
    Serialize,
    to_add=Field("expr", str),
    _set=Field("set", SetExpr),
):
    to_add: str
    _set: SetExpr


@dataclass
class SetUnion(SetExpr, Serialize, sets=Field("sets", list[SetExpr])):
    sets: list[SetExpr]


@dataclass
class SetRemove(
    SetExpr,
    Serialize,
    to_remove=Field("expr", str),
    _set=Field("set", SetExpr),
):
    to_remove: str
    _set: SetExpr
