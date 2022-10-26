#!/usr/bin/env python3
# Features for adding checks of various properties to Angler AST files.
from ipaddress import IPv4Address
import aast.expression as e
import aast.types as t
import aast.program as prog

# the predicate argument
# we reuse the same one everywhere
# so that we can nest predicates inside one another
# easily by swapping in their bodies
ARG = "env"


def all_predicates(*ps: prog.Predicate) -> prog.Predicate:
    """
    Returns a predicate that is true if all given predicates
    are true.
    """
    if ps == []:
        body = e.LiteralBool(True)
    else:
        body = e.Conjunction([p.body for p in ps])
    return prog.Predicate(arg=ARG, body=body)


def implies(antecedent: prog.Predicate, consequent: prog.Predicate) -> prog.Predicate:
    """
    Return a predicate that is true if the antecedent is false,
    or if the antecedent and consequent are true.
    (i.e. if the antecedent implies the consequent)
    """
    body = e.Disjunction([e.Not(antecedent.body), consequent.body])
    return prog.Predicate(arg=ARG, body=body)


def isValid() -> prog.Predicate:
    """
    Return a predicate testing if the given route is valid,
    i.e. is not a null route.
    """
    arg = e.Var(ARG, ty_arg=t.TypeAnnotation.ENVIRONMENT)
    get_result = e.GetField(
        arg,
        t.EnvironmentType.RESULT.value,
        ty_args=(
            t.TypeAnnotation.ENVIRONMENT,
            t.EnvironmentType.RESULT.field_type(),
        ),
    )
    body = e.GetField(
        get_result,
        t.ResultType.VALUE.value,
        ty_args=(
            t.TypeAnnotation.RESULT,
            t.ResultType.VALUE.field_type(),
        ),
    )
    return prog.Predicate(arg=arg._name, body=body)


def isNull() -> prog.Predicate:
    """
    Return a predicate testing if the given route is a null route.
    This is the negation of isValid().
    """
    p = isValid()
    p.body = e.Not(p.body)
    return p


def layerToComm(node: str, pod: int) -> str:
    """Return the community tag associated with node n's layer."""
    if node.startswith("aggregation"):
        return "1:" + str(pod)
    elif node.startswith("edge"):
        return "2:" + str(pod)
    else:
        return "3:0"


def layerToComm2(node: str, pod: int) -> str:
    """Return the community tag associated with node n's layer."""
    if node.startswith("aggregation"):
        return "4:" + str(pod)
    elif node.startswith("edge"):
        return "5:" + str(pod)
    else:
        return "6:0"


def isValidTags(comms: list[str]) -> prog.Predicate:
    """
    Return a predicate testing if the given route is valid and has
    none of the given community tags.
    """
    return all_predicates(isValid(), tags_absent(comms))


def hasInternalRoute() -> prog.Predicate:
    arg = e.Var(ARG, ty_arg=t.TypeAnnotation.ENVIRONMENT)
    get_origin = e.GetField(
        arg,
        t.EnvironmentType.ORIGIN.value,
        ty_args=(t.TypeAnnotation.ENVIRONMENT, t.EnvironmentType.ORIGIN.field_type()),
    )
    # 2 is the int for internal
    is_internal = e.Equal(get_origin, e.LiteralUInt(2, width=2), width=2)
    return prog.Predicate(arg=arg._name, body=is_internal)


def hasExternalRoute() -> prog.Predicate:
    arg = e.Var(ARG, ty_arg=t.TypeAnnotation.ENVIRONMENT)
    get_origin = e.GetField(
        arg,
        t.EnvironmentType.ORIGIN.value,
        ty_args=(t.TypeAnnotation.ENVIRONMENT, t.EnvironmentType.ORIGIN.field_type()),
    )
    is_not_internal = e.NotEqual(get_origin, e.LiteralUInt(2, width=2), width=2)
    return prog.Predicate(arg=arg._name, body=is_not_internal)


def hasTags(tags: list[str]) -> prog.Predicate:
    """
    Return a predicate that is true if all the given tags are present.
    """
    arg = e.Var(ARG, ty_arg=t.TypeAnnotation.ENVIRONMENT)
    get_comms = e.GetField(
        arg,
        t.EnvironmentType.COMMS.value,
        ty_args=(t.TypeAnnotation.ENVIRONMENT, t.EnvironmentType.COMMS.field_type()),
    )
    # add all the conjuncts specifying that comms contains the given community tag
    conjuncts: list[e.Expression[bool]] = [
        e.SetContains(e.LiteralString(tag), get_comms) for tag in tags
    ]
    return prog.Predicate(arg=arg._name, body=e.Conjunction(conjuncts))


def tags_absent(tags: list[str]) -> prog.Predicate:
    """
    Return a predicate that is true if all the given tags are absent.
    """
    arg = e.Var(ARG, ty_arg=t.TypeAnnotation.ENVIRONMENT)
    get_comms = e.GetField(
        arg,
        t.EnvironmentType.COMMS.value,
        ty_args=(t.TypeAnnotation.ENVIRONMENT, t.EnvironmentType.COMMS.field_type()),
    )
    # add all the conjuncts specifying that comms does not contain the given community tag
    conjuncts: list[e.Expression[bool]] = [
        e.Not(e.SetContains(e.LiteralString(tag), get_comms)) for tag in tags
    ]
    return prog.Predicate(arg=arg._name, body=e.Conjunction(conjuncts))


def route_to_dest(prefix: IPv4Address) -> prog.Predicate:
    """
    Return true if the route has a prefix containing the IP address.
    """
    arg = e.Var(ARG, ty_arg=t.TypeAnnotation.ENVIRONMENT)
    get_prefix = e.GetField(
        arg,
        t.EnvironmentType.PREFIX.value,
        ty_args=(t.TypeAnnotation.ENVIRONMENT, t.EnvironmentType.PREFIX.field_type()),
    )
    body = e.PrefixContains(e.IpAddress(prefix), get_prefix)
    return prog.Predicate(arg=arg._name, body=body)
