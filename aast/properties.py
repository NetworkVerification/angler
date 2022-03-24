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
    arg = e.Var("route", ty_arg=t.TypeAnnotation.PAIR)
    body = e.First(arg, ty_args=(t.TypeAnnotation.BOOL, t.TypeAnnotation.ROUTE))
    return prog.Predicate(arg=arg._name, expr=body)


def isNull() -> prog.Predicate:
    """
    Return a predicate testing if the given route is a null route.
    """
    arg = e.Var("route", ty_arg=t.TypeAnnotation.PAIR)
    body = e.Not(e.First(arg, ty_args=(t.TypeAnnotation.BOOL, t.TypeAnnotation.ROUTE)))
    return prog.Predicate(arg=arg._name, expr=body)


def isValidTags(*comms: str) -> prog.Predicate:
    """
    Return a predicate testing if the given route is valid and has appropriate tags.
    """
    arg = e.Var("route", ty_arg=t.TypeAnnotation.PAIR)
    is_valid = e.First(arg, ty_args=(t.TypeAnnotation.BOOL, t.TypeAnnotation.ROUTE))
    conjuncts: list[e.Expression[bool]] = [is_valid]
    get_comms = e.GetField(
        e.Second(arg, ty_args=(t.TypeAnnotation.BOOL, t.TypeAnnotation.ROUTE)),
        "communities",
        ty_args=(t.TypeAnnotation.ROUTE, t.TypeAnnotation.SET),
    )
    # add all the conjuncts specifying that comms does not contain the given community tag
    for comm in comms:
        conjuncts.append(e.Not(e.SetContains(e.LiteralString(comm), get_comms)))
    return prog.Predicate(arg=arg._name, expr=e.Conjunction(conjuncts))


def hasInternalRoute() -> prog.Predicate:
    raise NotImplementedError()


def hasExternalRoute() -> prog.Predicate:
    raise NotImplementedError()
