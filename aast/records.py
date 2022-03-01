#!/usr/bin/env python3
"""
AST representation of records.
"""
from dataclasses import dataclass
from serialize import Serialize, Field
import expression as expr
import base as ast


class RecExprType(ast.Variant):
    CREATE = "CreateRecord"

    def as_class(self) -> type:
        match self:
            case RecExprType.CREATE:
                return CreateRecord
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class RecExpr(expr.Expression, Serialize, delegate=("class", RecExprType.parse_class)):
    ...


@dataclass
class CreateRecord(
    RecExpr, Serialize, _fields=Field("fields", dict[str, expr.Expression])
):
    _fields: dict[str, expr.Expression]


# TODO: figure out where to put this and WithField in the types
@dataclass
class GetField(
    expr.Expression,
    Serialize,
    rec=Field("record", RecExpr),
    field_name=Field("fieldName", str),
):
    rec: RecExpr
    field_name: str


@dataclass
class WithField(
    expr.Expression,
    Serialize,
    rec=Field("record", RecExpr),
    field_name=Field("fieldName", str),
    field_val=Field("fieldVal", expr.Expression),
):
    rec: RecExpr
    field_name: str
    field_val: expr.Expression
