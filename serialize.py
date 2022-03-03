#!/usr/bin/env python3

from collections.abc import Callable
from typing import (
    Any,
    Optional,
    Protocol,
    Type,
    get_args,
    get_origin,
    runtime_checkable,
)


class Field:
    """A field to serialize/deserialize from JSON."""

    json_name: str
    ty: type
    default: Any

    def __init__(self, name: str, ty: type = Any, default: Any = None):
        self.json_name = name
        self.ty = ty
        self.default = default


@runtime_checkable
class Serializable(Protocol):
    """A protocol for checking that a type implements to_dict and from_dict."""

    fields: dict[str, Field]

    def to_dict(self) -> dict:
        ...

    @classmethod
    def from_dict(cls, d: dict) -> "Serializable":
        ...


class Serialize(Serializable):
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

    >>> class A(Serialize, foo=Field("f"), bar=Field("b")):
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
    >>> class B(Serialize, baz=Field("baz", list[A]), spam=Field("spam", str)):
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

    delegate: Optional[tuple[str, Callable[[str], Type]]]
    fields: dict[str, Field] = {}

    def __init__(self, delegate=None, **fields: str | Field):
        self.delegate = delegate
        self.fields = {
            k: (Field(f) if isinstance(f, str) else f) for k, f in fields.items()
        } or {}

    def __init_subclass__(
        cls,
        /,
        delegate: Optional[tuple[str, Callable[[str], Type]]] = None,
        **fields: str | Field,
    ) -> None:
        """
        Construct a subclass using the keyword arguments.
        Note that this consumes all keyword arguments, which means it does not behave
        well with other classes implementing __init_subclass__!
        :param fields: a sequence of key-value pairs, where the keys are
        fields and the values are a string specifying the desired field name,
        or a tuple containing a field name string and a type.
        """
        cls.delegate = delegate
        cls.fields = {
            k: (Field(f) if isinstance(f, str) else f) for k, f in fields.items()
        } or {}

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
            fieldname = fields[field].json_name
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
        # exit immediately if the field type is any or v is None
        if not v or fieldty is Any:
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
        # if a delegate is assigned, delegate to it
        if cls.delegate:
            del_field_name, del_func = cls.delegate
            try:
                # look up the delegate field name in d, and then call del_func on its value
                cls = del_func(d[del_field_name])
            except KeyError as e:
                e.args = (
                    f"expected a delegate field '{del_field_name}' for {cls.__name__} in '{d}'",
                )
                raise e
        kwargs = {}
        for field in cls.fields:
            fieldty = cls.fields[field].ty
            fieldname = cls.fields[field].json_name
            v = d.get(fieldname, cls.fields[field].default)
            # exit early if v is None
            if v is None:
                kwargs[field] = v
                continue
            type_args = get_args(fieldty)
            if get_origin(fieldty) is tuple or isinstance(fieldty, tuple):
                if not isinstance(v, tuple):
                    raise TypeError(
                        f"given value '{v}' for field '{field}' does not match type '{fieldty}'"
                    )
                # for tuples, zip the arguments
                if not type_args:
                    type_args = [Any] * len(v)
                typed_vals = zip(v, type_args)
                # now process them in sequence
                kwargs[field] = tuple(
                    [
                        Serialize._from_dict_aux(e, ty_arg, recurse)
                        for (e, ty_arg) in typed_vals
                    ]
                )
            elif get_origin(fieldty) is list or isinstance(fieldty, list):
                if not isinstance(v, list):
                    raise TypeError(
                        f"given value '{v}' for field '{field}' does not match type '{fieldty}'"
                    )
                # for lists, unwrap the first type argument (if given), otherwise use Any
                kwargs[field] = [
                    Serialize._from_dict_aux(
                        e, type_args[0] if type_args else Any, recurse
                    )
                    for e in v
                ]
            elif get_origin(fieldty) is dict or isinstance(fieldty, dict):
                if not isinstance(v, dict):
                    raise TypeError(
                        f"given value '{v}' for field '{field}' does not match type '{fieldty}'"
                    )
                # convert the keys and values of the given dictionary
                kwargs[field] = {
                    Serialize._from_dict_aux(
                        k, type_args[0] if type_args else Any, recurse
                    ): Serialize._from_dict_aux(
                        val, type_args[1] if type_args else Any, recurse
                    )
                    for (k, val) in v.items()
                }
            else:
                kwargs[field] = Serialize._from_dict_aux(v, fieldty, recurse)
        instance = cls(**kwargs)
        return instance
