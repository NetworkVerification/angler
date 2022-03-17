#!/usr/bin/env python3
"""Types for annotation Angler AST terms."""
from enum import Enum

# The field to use when annotating terms with types
# "$type" is the default expected by Newtonsoft
TYPE_FIELD = "$type"


class TypeAnnotation(Enum):
    """
    Possible type annotations.
    """

    UNKNOWN = "_"
    UNIT = "TUnit"
    BOOL = "TBool"
    INT32 = "TInt32"
    INT2 = "TInt2"
    STRING = "TString"
    IP_ADDRESS = "TIpAddress"
    PREFIX_SET = "TPrefixSet"
    SET = "TSet"
    PAIR = "TPair"
    ROUTE = "TRoute"


def annotate(cls: type, tys: list[TypeAnnotation]) -> str:
    """
    Return a type annotation for the given class cls,
    filled in with the given type annotations.
    """
    name = cls.__name__
    match tys:
        case []:
            return name
        case l:
            args = ";".join([a.value for a in l])
            return f"{name}({args})"
