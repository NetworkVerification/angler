'''
Boolean expressions
'''
from dataclasses import dataclass
from serialize import Serialize, Field
from aast.arithexprs import ArithExpr
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
class Equal(BoolExpr, Serialize, 
    operand1=Field("operand1", ArithExpr), 
    operand2=Field("operand2", ArithExpr)
):
    operand1: ArithExpr
    operand2: ArithExpr

@dataclass 
class NotEqual(BoolExpr, Serialize, 
    operand1=Field("operand1", ArithExpr), 
    operand2=Field("operand2", ArithExpr)
):
    operand1: ArithExpr
    operand2: ArithExpr

@dataclass 
class LessThan(BoolExpr, Serialize, 
    operand1=Field("operand1", ArithExpr), 
    operand2=Field("operand2", ArithExpr)
):
    operand1: ArithExpr
    operand2: ArithExpr

@dataclass 
class LessThanEqual(BoolExpr, Serialize, 
    operand1=Field("operand1", ArithExpr), 
    operand2=Field("operand2", ArithExpr)
):
    operand1: ArithExpr
    operand2: ArithExpr

@dataclass 
class GreaterThan(BoolExpr, Serialize, 
    operand1=Field("operand1", ArithExpr), 
    operand2=Field("operand2", ArithExpr)
):
    operand1: ArithExpr
    operand2: ArithExpr

@dataclass 
class GreaterThanEqual(BoolExpr, Serialize, 
    operand1=Field("operand1", ArithExpr), 
    operand2=Field("operand2", ArithExpr)
):
    operand1: ArithExpr
    operand2: ArithExpr

@dataclass 
class Equal(BoolExpr, Serialize, 
    operand1=Field("operand1", ArithExpr), 
    operand2=Field("operand2", ArithExpr)
):
    operand1: ArithExpr
    operand2: ArithExpr


@dataclass
class Match(
    BoolExpr, 
    Serialize, 
    match_var = Field("match_var", expr.Var),
    match_list = Field("match_list", BoolExpr)
):
    match_var: expr.Var
    match_list: BoolExpr
