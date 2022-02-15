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

    class Inner(Serializable):
        _fields = fields

        def __init__(self, **kwargs):
            # Match an arbitrary number of arguments so that dataclasses
            # that are subclasses of Inner don't get broken.
            super().__init__(**kwargs)

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


class SerializeMixin(Serializable):
    """
    A mixin class that implements two dictionary
    methods `to_dict` and `from_dict`.
    When subclassed, the mixin allows the user to specify field kwargs
    to use for encoding the dictionary.
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

    >>> class A(SerializeMixin, foo="f",bar="b"):
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
    >>> class B(SerializeMixin, baz=("baz", list[A]), spam=("spam", str)):
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

    fields: dict[str, str | tuple[str, type]]

    def __init__(self, **fields):
        self.fields = fields

    def __init_subclass__(cls, /, **fields: str | tuple[str, type]) -> None:
        """
        Construct a subclass using the keyword arguments.
        Note that this consumes all keyword arguments, which means it does not behave
        well with other classes implementing __init_subclass__!
        :param fields: a sequence of key-value pairs, where the keys are
        fields and the values are a string specifying the desired field name,
        or a tuple containing a field name string and a type.
        """
        cls.fields = fields

    def to_dict(self) -> dict:
        """
        Convert this class into a dictionary.
        """
        d = {}
        fields = self.__class__.fields
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
    def _from_dict_aux(v: Any, fieldty: type, recurse: bool):
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
    def from_dict(cls, d: dict, recurse: bool = True):
        """
        Construct this class from a dictionary d.
        Any fields not listed in the instantiating fields argument will be skipped.
        If recurse is True (default behavior), any values in the dictionary whose
        type is marked as also implementing from_dict will be recursively transformed.
        Raise a KeyError if the dictionary is missing an expected field.
        """
        kwargs = {}
        for field in cls.fields:
            fieldty = Any
            if isinstance(cls.fields[field], tuple):
                # NOTE: have to explicitly cast to assuage the type checker
                fieldname, fieldty = cast(tuple[str, type], cls.fields[field])
            else:
                fieldname = cls.fields[field]
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
                        SerializeMixin._from_dict_aux(e, ty_arg, recurse)
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
                    SerializeMixin._from_dict_aux(
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
                    SerializeMixin._from_dict_aux(
                        k, type_args[0] if type_args else Any, recurse
                    ): SerializeMixin._from_dict_aux(
                        val, type_args[1] if type_args else Any, recurse
                    )
                    for (k, val) in v.items()
                }
            else:
                kwargs[field] = SerializeMixin._from_dict_aux(v, fieldty, recurse)
        instance = cls(**kwargs)
        return instance
