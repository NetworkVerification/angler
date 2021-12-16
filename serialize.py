#!/usr/bin/env python3


class Serializable:
    """
    A class decorator to implement off-the-shelf JSON serialization and deserialization.
    When serializing, each field of the class is converted to a field of a JSON dict.
    The value of the field depends on its type.
    Deserialization reconstructs the class from the JSON object.
    Based on a StackOverflow example:
    https://stackoverflow.com/a/14906547
    """

    def __init__(self, **args):
        """
        Construct a Jsonable class which serializes the given fields
        using the given field names.
        """
        self.fields = args

    def __call__(self, cls):
        # store that this class has a property where these specific fields are serialized
        cls._jsonFields = self.fields
        # construct a function from class to dict
        def to_dict(self) -> dict:
            d = {}
            for (field, fieldname) in self.__class__._jsonFields.items():
                v = self.__getattribute__(field)
                if isinstance(v, list):
                    d[fieldname] = [
                        e.to_dict() if hasattr(e.__class__, "_jsonFields") else e
                        for e in v
                    ]
                else:
                    d[fieldname] = (
                        v.to_dict() if hasattr(v.__class__, "_jsonFields") else v
                    )
            return d

        cls.to_dict = to_dict

        # construct a function from dict to class
        @classmethod
        def from_dict(cls, d):
            instance = cls(**d)
            return instance

        cls.from_dict = from_dict

        return cls


def Serialize(**fields):
    """
    Return an anonymous class that implements a dictionary
    transformation `to_dict`, where each given field is accessed
    and encoded in the dictionary as the given field name.
    :param fields: a sequence of key-value pairs, where the keys are
    fields and the values are the desired field names.
    """

    class Inner:
        def __init__(self):
            self._jsonFields = fields

        def to_dict(self) -> dict:
            d = {}
            for field in fields:
                v = getattr(self, field)
                if isinstance(v, list):
                    d[fields[field]] = [
                        e.to_dict() if hasattr(e.__class__, "_jsonFields") else e
                        for e in v
                    ]
                else:
                    d[fields[field]] = (
                        v.to_dict() if hasattr(v.__class__, "_jsonFields") else v
                    )
            return d

    return Inner
