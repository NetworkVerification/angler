#!/usr/bin/env python3


from typing import Optional, cast


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
    fields and the values are the desired field names, optionally also
    including a type or class.

    >>> class A(Serialize(foo="f",bar="b")):
    ...     def __init__(self, foo, bar, quux=10):
    ...         super().__init__()
    ...         self.foo = foo
    ...         self.bar = bar
    ...         self.quux = quux
    >>> a = A.from_dict({"f": 1, "b": 2, "c": 3})
    >>> a.foo
    1
    >>> a.bar
    2
    >>> a.to_dict()
    {'f': 1, 'b': 2}
    """

    class Inner:
        def __init__(self):
            self._jsonFields = fields

        def to_dict(self) -> dict:
            """
            Convert this class into a dictionary.
            """
            d = {}
            for field in fields:
                v = getattr(self, field)
                # TODO: use the field type?
                if isinstance(fields[field], tuple):
                    fieldname, _ = fields[field]
                else:
                    fieldname = fields[field]
                # if the internal field also has a to_dict implementation, recursively convert it
                if isinstance(v, list):
                    d[fieldname] = [
                        e.to_dict() if hasattr(e.__class__, "to_dict") else e for e in v
                    ]
                else:
                    d[fieldname] = v.to_dict() if hasattr(v.__class__, "to_dict") else v
            return d

        @classmethod
        def from_dict(cls, d: dict):
            """
            Construct this class from a dictionary d.
            Any fields not listed in the instantiating fields argument will be skipped.
            """
            kwargs = {}
            for field in fields:
                fieldty: Optional[type] = None
                if isinstance(fields[field], tuple):
                    # NOTE: have to explicitly cast to assuage the type checker
                    fieldname, fieldty = cast(tuple[str, type], fields[field])
                else:
                    fieldname = fields[field]
                v = d[fieldname]
                # if the fieldty is not None and has a from_dict method, call that
                # if it is just not None but callable, call it on v
                # otherwise, just return v
                kwargs[field] = (
                    v.from_dict()
                    if fieldty and hasattr(fieldty, "from_dict")
                    else fieldty(v)
                    if fieldty and callable(fieldty)
                    else v
                )
            instance = cls(**kwargs)
            return instance

    return Inner
