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
    BOOL = "TBool"
    UINT32 = "TUInt32"
    UINT2 = "TUInt2"
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
    ENVIRONMENT = "TEnvironment"


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


class TypeEnum(Enum):
    @classmethod
    def fields(cls) -> dict:
        return {mem.value: mem.field_type() for mem in cls.__members__.values()}

    def field_type(self) -> TypeAnnotation:
        raise NotImplementedError(f"field_type() not implemented for {self}")


class ResultType(TypeEnum):
    VALUE = "Value"
    EXIT = "Exit"
    FALLTHRU = "FallThrough"
    RETURN = "Return"

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


class RouteType(TypeEnum):
    PREFIX = "Prefix"
    LP = "Lp"
    METRIC = "Metric"
    COMMS = "Communities"
    ORIGIN = "Origin"
    TAG = "Tag"
    WEIGHT = "Weight"
    LOCAL_DEFAULT_ACTION = "LocalDefaultAction"

    def field_type(self) -> TypeAnnotation:
        match self:
            case RouteType.PREFIX:
                return TypeAnnotation.IP_PREFIX
            case RouteType.LP:
                return TypeAnnotation.UINT32
            case RouteType.METRIC:
                return TypeAnnotation.UINT32
            case RouteType.COMMS:
                return TypeAnnotation.SET
            case RouteType.ORIGIN:
                return TypeAnnotation.UINT2
            case RouteType.TAG:
                return TypeAnnotation.UINT32
            case RouteType.WEIGHT:
                return TypeAnnotation.UINT32
            case RouteType.LOCAL_DEFAULT_ACTION:
                return TypeAnnotation.BOOL
            case _:
                raise NotImplementedError(f"{self} field type not implemented.")


class EnvironmentType(TypeEnum):
    """
    A type representing the result of transferring a route.
    Combines the data of a Result with a Route.
    """

    RESULT_VALUE = "Value"
    RESULT_EXIT = "Exit"
    RESULT_FALLTHRU = "FallThrough"
    RESULT_RETURN = "Return"
    PREFIX = "Prefix"
    LP = "Lp"
    METRIC = "Metric"
    COMMS = "Communities"
    ORIGIN = "Origin"
    TAG = "Tag"
    WEIGHT = "Weight"
    LOCAL_DEFAULT_ACTION = "LocalDefaultAction"
    DEFAULT_POLICY = "DefaultPolicy"

    def field_type(self) -> TypeAnnotation:
        match self:
            case EnvironmentType.RESULT_VALUE:
                return TypeAnnotation.BOOL
            case EnvironmentType.RESULT_EXIT:
                return TypeAnnotation.BOOL
            case EnvironmentType.RESULT_FALLTHRU:
                return TypeAnnotation.BOOL
            case EnvironmentType.RESULT_RETURN:
                return TypeAnnotation.BOOL
            case EnvironmentType.PREFIX:
                return TypeAnnotation.IP_PREFIX
            case EnvironmentType.LP:
                return TypeAnnotation.UINT32
            case EnvironmentType.METRIC:
                return TypeAnnotation.UINT32
            case EnvironmentType.COMMS:
                return TypeAnnotation.SET
            case EnvironmentType.ORIGIN:
                return TypeAnnotation.UINT2
            case EnvironmentType.TAG:
                return TypeAnnotation.UINT32
            case EnvironmentType.WEIGHT:
                return TypeAnnotation.UINT32
            case EnvironmentType.LOCAL_DEFAULT_ACTION:
                return TypeAnnotation.BOOL
            case EnvironmentType.DEFAULT_POLICY:
                return TypeAnnotation.STRING
            case _:
                raise NotImplementedError(f"{self} field type not implemented.")
