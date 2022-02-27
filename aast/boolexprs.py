'''
Boolean expressions
'''
from dataclasses import dataclass
from enum import Enum
from base import Variant
from serialize import Serialize, Field
import expression as expr


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
    #CONTAINS = "Contains" # set containment?

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
            case BoolExprType.MATCH:
                return Match
            # case BoolExprType.CONTAINS:
            #     return Contains
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")

class BoolExpr(
    expr.Expression,
    Serialize,
    delegate = ("class", BoolExprType.parse_class)
):
    ...

@dataclass
class LiteralTrue(BoolExpr, Serialize):
    ...

@dataclass
class LiteralFalse(BoolExpr, Serialize):
    ...

@dataclass
class Havoc(BoolExpr, Serialize):
    ...

@dataclass
class Conjunction(
    BoolExpr, Serialize, conjuncts=Field("conjuncts", list[BoolExpr])
):
    conjuncts: list[BoolExpr]


@dataclass
class ConjunctionChain(
    BoolExpr, Serialize, subroutines=Field("subroutines", list[expr.Expression])
):
    subroutines: list[expr.Expression]


@dataclass
class Disjunction(
    BoolExpr, Serialize, disjuncts=Field("disjuncts", list[BoolExpr])
):
    disjuncts: list[BoolExpr]


@dataclass
class Not(BoolExpr, Serialize, expr=Field("expr", BoolExpr)):
    expr: BoolExpr
    

@dataclass
class Match(
    BoolExpr, 
    Serialize, 
    match_var = Field("match_var", expr.Var),
    match_list = Field("match_list", BoolExpr)
):
    match_var: expr.Var
    match_list: BoolExpr


