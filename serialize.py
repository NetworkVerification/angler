#!/usr/bin/env python3


from typing import (
    Any,
    Protocol,
    cast,
    get_args,
    get_origin,
    runtime_checkable,
)


@runtime_checkable
class Serializable(Protocol):
    """A protocol for checking that a type implements to_dict and from_dict."""

    def to_dict(self) -> dict:
        ...

    @classmethod
    def from_dict(cls, d: dict) -> "Serializable":
        ...


def Serialize(**fields: str | tuple[str, type]):
    """
    Return an anonymous class that implements two dictionary
    transformations `to_dict` and `from_dict`.
    Each given field kwarg is accessed
    and encoded in the dictionary as the given field name value, but
    referred to in the class by its field key.
    Fields in the class which are not listed are skipped in both
    directions.
    The field values may be either strings or tuples of strings and types/classes.
    In the former case, the field is simply assigned to the class as given
    by the dictionary/added to the dictionary as its current type.
    In the latter case, the field is recursively transformed:
    if the field's class is also a subclass of Serialize, it performs another
    encoding/decoding;
    if not, we attempt to call the given type/class on the field.
    :param fields: a sequence of key-value pairs, where the keys are
    fields and the values are a string specifying the desired field name,
    or a tuple containing a field name string and a type.

    >>> class A(Serialize(foo="f",bar="b")):
    ...     def __init__(self, foo, bar, quux=10):
    ...         super().__init__()
    ...         self.foo = foo
    ...         self.bar = bar
    ...         self.quux = quux
    ...     def __eq__(self, other):
    ...         return self.foo == other.foo and self.bar == other.bar
    >>> d = {"f": 1, "b": "hello", "c": 3}
    >>> a = A.from_dict(d)
    >>> a.foo
    1
    >>> a.bar
    'hello'
    >>> a.to_dict()
    {'f': 1, 'b': 'hello'}
    >>> class B(Serialize(baz=("baz", list[A]), spam=("spam", str))):
    ...     def __init__(self, baz: list[A], spam):
    ...         super().__init__()
    ...         self.baz = baz
    ...         self.spam = spam
    >>> b = B.from_dict({'baz': [d], 'spam': 4})
    >>> b.to_dict()
    {'baz': [{'f': 1, 'b': 'hello'}], 'spam': '4'}
    >>> b.baz[0] == a
    True
    """

    class Inner:
        _fields = fields

        def __init__(self, **_):
            # Match an arbitrary number of arguments so that dataclasses
            # that are subclasses of Inner don't get broken.
            ...

        def to_dict(self) -> dict:
            """
            Convert this class into a dictionary.
            """
            d = {}
            for field in fields:
                # will raise an AttributeError if the field is not present
                v = getattr(self, field)
                # NOTE: we don't use the field type when encoding to a dictionary
                if isinstance(fields[field], tuple):
                    fieldname, _ = fields[field]
                else:
                    fieldname = fields[field]
                # if the internal field also has a to_dict implementation, recursively convert it
                if isinstance(v, list):
                    d[fieldname] = [
                        e.to_dict() if isinstance(e, Serializable) else e for e in v
                    ]
                else:
                    d[fieldname] = v.to_dict() if isinstance(v, Serializable) else v
            return d

        @staticmethod
        def _from_dict_aux(v, fieldty, recurse):
            # exit immediately if the field type is any
            if fieldty is Any:
                return v
            # if the fieldty is not None and has a from_dict method, call that
            if recurse and isinstance(fieldty, Serializable):
                if isinstance(v, dict):
                    return fieldty.from_dict(v)
                else:
                    return v
            # if it is not None but callable, call it on v if v needs to be transformed
            elif callable(fieldty) and not isinstance(v, fieldty):
                return fieldty(v)
            else:  # otherwise, just return v
                return v

        @classmethod
        def from_dict(cls, d: dict, recurse=True):
            """
            Construct this class from a dictionary d.
            Any fields not listed in the instantiating fields argument will be skipped.
            If recurse is True (default behavior), any values in the dictionary whose
            type is marked as also implementing from_dict will be recursively transformed.
            """
            kwargs = {}
            for field in fields:
                fieldty = Any
                if isinstance(fields[field], tuple):
                    # NOTE: have to explicitly cast to assuage the type checker
                    fieldname, fieldty = cast(tuple[str, type], fields[field])
                else:
                    fieldname = fields[field]
                v = d[fieldname]
                type_args = get_args(fieldty)
                if get_origin(fieldty) is tuple or isinstance(fieldty, tuple):
                    if not isinstance(v, tuple):
                        raise TypeError(
                            f"given value '{v}' does not match type '{fieldty}'"
                        )
                    # for tuples, zip the arguments
                    if not type_args:
                        type_args = [Any] * len(v)
                    typed_vals = zip(v, type_args)
                    # now process them in sequence
                    kwargs[field] = tuple(
                        [
                            Inner._from_dict_aux(e, ty_arg, recurse)
                            for (e, ty_arg) in typed_vals
                        ]
                    )
                elif get_origin(fieldty) is list or isinstance(fieldty, list):
                    if not isinstance(v, list):
                        raise TypeError(
                            f"given value '{v}' does not match type '{fieldty}'"
                        )
                    # for lists, unwrap the first type argument (if given), otherwise use Any
                    kwargs[field] = [
                        Inner._from_dict_aux(
                            e, type_args[0] if type_args else Any, recurse
                        )
                        for e in v
                    ]
                elif get_origin(fieldty) is dict or isinstance(fieldty, dict):
                    if not isinstance(v, dict):
                        raise TypeError(
                            f"given value '{v}' does not match type '{fieldty}'"
                        )
                    # convert the keys and values of the given dictionary
                    kwargs[field] = {
                        Inner._from_dict_aux(
                            k, type_args[0] if type_args else Any, recurse
                        ): Inner._from_dict_aux(
                            val, type_args[1] if type_args else Any, recurse
                        )
                        for (k, val) in v.items()
                    }
                else:
                    kwargs[field] = Inner._from_dict_aux(v, fieldty, recurse)
            # if "class" in d:
            #     print(f"Inside a {d['class']}")
            instance = cls(**kwargs)
            return instance

    return Inner


class Serialize3:
    def __init__(self, **fields: str | tuple[str, type]):
        self.fields = fields

    def __call__(self, cls):
        """
        Decorate the given class with to_dict and from_dict methods.
        """

        def to_dict(self) -> dict:
            """
            Convert this class into a dictionary.
            """
            d = {}
            for field in self.fields:
                # will raise an AttributeError if the field is not present
                v = getattr(self, field)
                # NOTE: we don't use the field type when encoding to a dictionary
                if isinstance(self.fields[field], tuple):
                    fieldname, _ = self.fields[field]
                else:
                    fieldname = self.fields[field]
                # if the internal field also has a to_dict implementation, recursively convert it
                if isinstance(v, list):
                    d[fieldname] = [
                        e.to_dict() if isinstance(e, Serializable) else e for e in v
                    ]
                else:
                    d[fieldname] = v.to_dict() if isinstance(v, Serializable) else v
            return d

        cls.to_dict = to_dict
        ...


def Serialize2(**fields: str | tuple[str, type]):
    def to_dict(self) -> dict:
        """
        Convert this class into a dictionary.
        """
        d = {}
        for field in fields:
            # will raise an AttributeError if the field is not present
            v = getattr(self, field)
            # NOTE: we don't use the field type when encoding to a dictionary
            if isinstance(fields[field], tuple):
                fieldname, _ = fields[field]
            else:
                fieldname = fields[field]
            # if the internal field also has a to_dict implementation, recursively convert it
            if isinstance(v, list):
                d[fieldname] = [
                    e.to_dict() if isinstance(e, Serializable) else e for e in v
                ]
            else:
                d[fieldname] = v.to_dict() if isinstance(v, Serializable) else v
        return d

    @staticmethod
    def _from_dict_aux(v, fieldty, recurse):
        # exit immediately if the field type is any
        if fieldty is Any:
            return v
        # if the fieldty is not None and has a from_dict method, call that
        if recurse and isinstance(fieldty, Serializable):
            if isinstance(v, dict):
                return fieldty.from_dict(v)
            else:
                return v
        # if it is not None but callable, call it on v if v needs to be transformed
        elif callable(fieldty) and not isinstance(v, fieldty):
            return fieldty(v)
        else:  # otherwise, just return v
            return v

    @classmethod
    def from_dict(cls, d: dict, recurse=True):
        """
        Construct this class from a dictionary d.
        Any fields not listed in the instantiating fields argument will be skipped.
        If recurse is True (default behavior), any values in the dictionary whose
        type is marked as also implementing from_dict will be recursively transformed.
        Raise a KeyError if the dictionary is missing an expected field.
        """
        kwargs = {}
        for field in fields:
            fieldty = Any
            if isinstance(fields[field], tuple):
                # NOTE: have to explicitly cast to assuage the type checker
                fieldname, fieldty = cast(tuple[str, type], fields[field])
            else:
                fieldname = fields[field]
            v = d[fieldname]
            type_args = get_args(fieldty)
            if get_origin(fieldty) is tuple or isinstance(fieldty, tuple):
                if not isinstance(v, tuple):
                    raise TypeError(
                        f"given value '{v}' does not match type '{fieldty}'"
                    )
                # for tuples, zip the arguments
                if not type_args:
                    type_args = [Any] * len(v)
                typed_vals = zip(v, type_args)
                # now process them in sequence
                kwargs[field] = tuple(
                    [_from_dict_aux(e, ty_arg, recurse) for (e, ty_arg) in typed_vals]
                )
            elif get_origin(fieldty) is list or isinstance(fieldty, list):
                if not isinstance(v, list):
                    raise TypeError(
                        f"given value '{v}' does not match type '{fieldty}'"
                    )
                # for lists, unwrap the first type argument (if given), otherwise use Any
                kwargs[field] = [
                    _from_dict_aux(e, type_args[0] if type_args else Any, recurse)
                    for e in v
                ]
            elif get_origin(fieldty) is dict or isinstance(fieldty, dict):
                if not isinstance(v, dict):
                    raise TypeError(
                        f"given value '{v}' does not match type '{fieldty}'"
                    )
                # convert the keys and values of the given dictionary
                kwargs[field] = {
                    _from_dict_aux(
                        k, type_args[0] if type_args else Any, recurse
                    ): _from_dict_aux(val, type_args[1] if type_args else Any, recurse)
                    for (k, val) in v.items()
                }
            else:
                kwargs[field] = _from_dict_aux(v, fieldty, recurse)
        # if "class" in d:
        #     print(f"Inside a {d['class']}")
        instance = cls(**kwargs)
        return instance

    def decorator(cls):
        old_getter = cls.__getattribute__

        def getter(self, key):
            if key == "to_dict":
                return self.to_dict()

        cls.__getattribute__("to_dict", to_dict)
        cls.__getattribute__("from_dict", from_dict)
        return cls

    return decorator
