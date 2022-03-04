"""
Boolean expressions
"""
from dataclasses import dataclass
from aast.sets import SetExpr
from serialize import Serialize, Field
from aast.base import Variant
import aast.expression as expr


class BoolExprType(Variant):
    TRUE = "True"
    FALSE = "False"
    HAVOC = "Havoc"
    CALLCONTEXT = "CallExprContext"
    CONJUNCTION = "Conjunction"
    CONJUNCTION_CHAIN = "ConjunctionChain"
    DISJUNCTION = "Disjunction"
    NOT = "Not"
    MATCH = "Match"
    EQ = "Equal"
    NEQ = "NotEqual"
    LT = "LessThan"
    LE = "LessThanOrEqual"
    GT = "GreaterThan"
    GE = "GreaterThanOrEqual"
    CONTAINS = "SetContains"

    def as_class(self) -> type:
        match self:
            case BoolExprType.TRUE:
                return LiteralTrue
            case BoolExprType.FALSE:
                return LiteralFalse
            case BoolExprType.HAVOC:
                return Havoc
            case BoolExprType.CONJUNCTION:
                return Conjunction
            case BoolExprType.CONJUNCTION_CHAIN:
                return ConjunctionChain
            case BoolExprType.DISJUNCTION:
                return Disjunction
            case BoolExprType.NOT:
                return Not
            case BoolExprType.EQ:
                return Equal
            case BoolExprType.NEQ:
                return NotEqual
            case BoolExprType.LT:
                return LessThan
            case BoolExprType.LE:
                return LessThanEqual
            case BoolExprType.GT:
                return GreaterThan
            case BoolExprType.GE:
                return GreaterThanEqual
            case BoolExprType.MATCH:
                return Match
            case BoolExprType.CONTAINS:
                return SetContains
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


class BoolExpr(
    expr.Expression[bool], Serialize, delegate=("class", BoolExprType.parse_class)
):
    ...


@dataclass
class LiteralTrue(expr.Expression[bool], Serialize):
    ...


@dataclass
class LiteralFalse(expr.Expression[bool], Serialize):
    ...


@dataclass
class Havoc(expr.Expression[bool], Serialize):
    ...


@dataclass
class Conjunction(
    expr.Expression[bool],
    Serialize,
    conjuncts=Field("conjuncts", list[expr.Expression[bool]]),
):
    conjuncts: list[expr.Expression[bool]]


@dataclass
class ConjunctionChain(
    expr.Expression[bool],
    Serialize,
    subroutines=Field("subroutines", list[expr.Expression]),
):
    subroutines: list[expr.Expression]


@dataclass
class Disjunction(
    expr.Expression[bool],
    Serialize,
    disjuncts=Field("disjuncts", list[expr.Expression[bool]]),
):
    disjuncts: list[expr.Expression[bool]]


@dataclass
class Not(expr.Expression[bool], Serialize, expr=Field("expr", expr.Expression[bool])):
    expr: expr.Expression[bool]


@dataclass
class Equal(
    expr.Expression[bool],
    Serialize,
    operand1=Field("operand1", expr.Expression[int]),
    operand2=Field("operand2", expr.Expression[int]),
):
    operand1: expr.Expression[int]
    operand2: expr.Expression[int]


@dataclass
class NotEqual(
    expr.Expression[bool],
    Serialize,
    operand1=Field("operand1", expr.Expression[int]),
    operand2=Field("operand2", expr.Expression[int]),
):
    operand1: expr.Expression[int]
    operand2: expr.Expression[int]


@dataclass
class LessThan(
    expr.Expression[bool],
    Serialize,
    operand1=Field("operand1", expr.Expression[int]),
    operand2=Field("operand2", expr.Expression[int]),
):
    operand1: expr.Expression[int]
    operand2: expr.Expression[int]


@dataclass
class LessThanEqual(
    expr.Expression[bool],
    Serialize,
    operand1=Field("operand1", expr.Expression[int]),
    operand2=Field("operand2", expr.Expression[int]),
):
    operand1: expr.Expression[int]
    operand2: expr.Expression[int]


@dataclass
class GreaterThan(
    expr.Expression[bool],
    Serialize,
    operand1=Field("operand1", expr.Expression[int]),
    operand2=Field("operand2", expr.Expression[int]),
):
    operand1: expr.Expression[int]
    operand2: expr.Expression[int]


@dataclass
class GreaterThanEqual(
    expr.Expression[bool],
    Serialize,
    operand1=Field("operand1", expr.Expression[int]),
    operand2=Field("operand2", expr.Expression[int]),
):
    operand1: expr.Expression[int]
    operand2: expr.Expression[int]


@dataclass
class Match(
    expr.Expression[bool],
    Serialize,
    match_var=Field("match_var", expr.Var),
    match_list=Field("match_list", expr.Expression[bool]),
):
    match_var: expr.Var
    match_list: expr.Expression[bool]


@dataclass
class SetContains(
    expr.Expression[bool], Serialize, search="search", _set=Field("set", SetExpr)
):
    search: str
    _set: expr.Expression[set]
