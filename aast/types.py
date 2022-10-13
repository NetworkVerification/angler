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
    IP_PREFIX = "TIpPrefix"
    PREFIX_SET = "TPrefixSet"
    SET = "TSet"
    RESULT = "TResult"
    ROUTE = "TRoute"
    RESULT_ROUTE = "TPair(TResult;TRoute)"


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


class ResultType(Enum):
    VALUE = "Value"
    EXIT = "Exit"
    FALLTHRU = "FallThrough"
    RETURN = "Return"

    @staticmethod
    def fields() -> dict[str, TypeAnnotation]:
        return {
            ResultType.VALUE.value: ResultType.VALUE.field_type(),
            ResultType.EXIT.value: ResultType.EXIT.field_type(),
            ResultType.FALLTHRU.value: ResultType.FALLTHRU.field_type(),
            ResultType.RETURN.value: ResultType.RETURN.field_type(),
        }

    def field_type(self) -> TypeAnnotation:
        match self:
            case ResultType.VALUE:
                return TypeAnnotation.BOOL
            case ResultType.EXIT:
                return TypeAnnotation.BOOL
            case ResultType.FALLTHRU:
                return TypeAnnotation.BOOL
            case ResultType.RETURN:
                return TypeAnnotation.BOOL
            case _:
                raise NotImplementedError(f"{self} field type not implemented.")


class RouteType(Enum):
    PREFIX = "Prefix"
    LP = "Lp"
    METRIC = "Metric"
    COMMS = "Communities"
    NEXT_HOP = "NextHop"
    ORIGIN = "Origin"
    TAG = "Tag"
    WEIGHT = "Weight"
    LOCAL_DEFAULT_ACTION = "LocalDefaultAction"

    @staticmethod
    def fields() -> dict[str, TypeAnnotation]:
        return {
            RouteType.PREFIX.value: RouteType.PREFIX.field_type(),
            RouteType.LP.value: RouteType.LP.field_type(),
            RouteType.METRIC.value: RouteType.METRIC.field_type(),
            RouteType.COMMS.value: RouteType.COMMS.field_type(),
            RouteType.ORIGIN.value: RouteType.ORIGIN.field_type(),
            RouteType.TAG.value: RouteType.TAG.field_type(),
            RouteType.WEIGHT.value: RouteType.WEIGHT.field_type(),
            RouteType.LOCAL_DEFAULT_ACTION.value: RouteType.LOCAL_DEFAULT_ACTION.field_type(),
        }

    def field_type(self) -> TypeAnnotation:
        match self:
            case RouteType.PREFIX:
                return TypeAnnotation.IP_PREFIX
            case RouteType.LP:
                return TypeAnnotation.INT32
            case RouteType.METRIC:
                return TypeAnnotation.INT32
            case RouteType.COMMS:
                return TypeAnnotation.SET
            case RouteType.ORIGIN:
                return TypeAnnotation.INT2
            case RouteType.TAG:
                return TypeAnnotation.INT32
            case RouteType.WEIGHT:
                return TypeAnnotation.INT32
            case RouteType.LOCAL_DEFAULT_ACTION:
                return TypeAnnotation.BOOL
            case _:
                raise NotImplementedError(f"{self} field type not implemented.")
