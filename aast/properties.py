#!/usr/bin/env python3
# Features for adding checks of various properties to Angler AST files.
import aast.expression as e
import aast.types as t
import aast.program as prog


def isValid() -> prog.Predicate:
    """
    Return a predicate testing if the given route is valid,
    i.e. is not a null route.
    """
    arg = e.Var("route", ty_arg=t.TypeAnnotation.ENVIRONMENT)
    body = e.GetField(
        arg,
        t.EnvironmentType.RESULT_VALUE.value,
        ty_args=(
            t.TypeAnnotation.ENVIRONMENT,
            t.EnvironmentType.RESULT_VALUE.field_type(),
        ),
    )
    return prog.Predicate(arg=arg._name, body=body)


def isNull() -> prog.Predicate:
    """
    Return a predicate testing if the given route is a null route.
    """
    arg = e.Var("route", ty_arg=t.TypeAnnotation.ENVIRONMENT)
    body = e.Not(
        e.GetField(
            arg,
            t.EnvironmentType.RESULT_VALUE.value,
            ty_args=(
                t.TypeAnnotation.ENVIRONMENT,
                t.EnvironmentType.RESULT_VALUE.field_type(),
            ),
        )
    )
    return prog.Predicate(arg=arg._name, body=body)


def isValidTags(*comms: str) -> prog.Predicate:
    """
    Return a predicate testing if the given route is valid and has appropriate tags.
    """
    arg = e.Var("route", ty_arg=t.TypeAnnotation.ENVIRONMENT)
    is_valid = isValid().body
    conjuncts: list[e.Expression[bool]] = [is_valid]
    get_comms = e.GetField(
        arg,
        t.EnvironmentType.COMMS.value,
        ty_args=(t.TypeAnnotation.ENVIRONMENT, t.EnvironmentType.COMMS.field_type()),
    )
    # add all the conjuncts specifying that comms does not contain the given community tag
    for comm in comms:
        conjuncts.append(e.Not(e.SetContains(e.LiteralString(comm), get_comms)))
    return prog.Predicate(arg=arg._name, body=e.Conjunction(conjuncts))


def hasInternalRoute() -> prog.Predicate:
    raise NotImplementedError()


def hasExternalRoute() -> prog.Predicate:
    raise NotImplementedError()
