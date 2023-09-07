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
    # numeric type for an unbounded integer
    BIG_INT = "TBigInt"
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
    """
    Base class for using enums to declare fields for record types.
    Implements a fields() class method that generates a dictionary
    from field names to field types
    (requires that the Enum elements have string values).
    """

    @classmethod
    def fields(cls) -> dict[str, TypeAnnotation]:
        return {mem.value: mem.field_type() for mem in cls.__members__.values()}

    def field_type(self) -> TypeAnnotation:
        raise NotImplementedError(f"field_type() not implemented for {self}")


class ResultType(TypeEnum):
    """
    `TypeEnum` representing the result of evaluating a policy or boolean.
    See https://github.com/batfish/batfish/blob/37dc6cfd2c62a667e5288b747c49def21428079b/projects/batfish-common-protocol/src/main/java/org/batfish/datamodel/routing_policy/Result.java#L10
    """

    # Boolean value of the result
    VALUE = "Value"
    # Represents reaching a terminal accept/reject, stopping evaluation of callers.
    EXIT = "Exit"
    # Represents a fall-through case where no policy matched, or no statement led to an exit or return
    FALLTHROUGH = "Fallthrough"
    # Represents terminating the current policy/statement evaluation, returning back to the caller.
    RETURN = "Returned"

    def field_type(self) -> TypeAnnotation:
        match self:
            case ResultType.VALUE:
                return TypeAnnotation.BOOL
            case ResultType.EXIT:
                return TypeAnnotation.BOOL
            case ResultType.FALLTHROUGH:
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

    RESULT = "Result"
    PREFIX = "Prefix"
    LP = "Lp"
    METRIC = "Metric"
    COMMS = "Communities"
    ORIGIN = "OriginType"
    TAG = "Tag"
    WEIGHT = "Weight"
    LOCAL_DEFAULT_ACTION = "LocalDefaultAction"
    AS_PATH_LENGTH = "AsPathLength"

    def field_type(self) -> TypeAnnotation:
        match self:
            case EnvironmentType.RESULT:
                return TypeAnnotation.RESULT
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
            case EnvironmentType.AS_PATH_LENGTH:
                return TypeAnnotation.BIG_INT
            case _:
                raise NotImplementedError(f"{self} field type not implemented.")
