#!/usr/bin/env python3
from enum import Enum
from typing import List


class ExprType(Enum):
    MATCHIPV4 = "matchIpv4"
    CONJUNCTION = "conjuncts"
    DISJUNCTION = "disjuncts"
    NOT = "not"
    MATCHPROTOCOL = "matchProtocol"
    MATCHPREFIXSET = "matchPrefixSet"
    CALLEXPR = "callExpr"
    WITHENVIRONMENTEXPR = "withEnvironmentExpr"
    MATCHCOMMUNITYSET = "matchCommunitySet"
    ASEXPR = "asExpr"
    COMMUNITYSETEXPR = "communitySetExpr"
    LONGEXPR = "longExpr"


class ASTNode:
    """
    A node of the AST.
    """

    def __init__(self, text, *children):
        """
        Construct a node, given source content, and a list of children.
        """
        self.text = text
        self.children = list(children)


class Expression(ASTNode):
    ...


class Statement(ASTNode):
    ...


class BooleanExpr(Expression):
    ...


class Conjunction(BooleanExpr):
    def __init__(self, *exprs: List[BooleanExpr]):
        self.children = exprs


class Not(BooleanExpr):
    def __init__(self, expr: BooleanExpr):
        self.children = [expr]


class ASTNodeVisitor:
    @staticmethod
    def visit(node: ASTNode):
        pass
