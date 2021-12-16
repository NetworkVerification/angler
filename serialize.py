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
        def toDict(self) -> dict:
            d = {}
            for (field, fieldname) in self.__class__._jsonFields.items():
                v = self.__getattribute__(field)
                if isinstance(v, list):
                    d[fieldname] = [
                        e.toDict() if hasattr(e.__class__, "_jsonFields") else e
                        for e in v
                    ]
                else:
                    d[fieldname] = (
                        v.toDict() if hasattr(v.__class__, "_jsonFields") else v
                    )
            return d

        cls.toDict = toDict

        # construct a function from dict to class
        @classmethod
        def fromDict(cls, d):
            return cls(**d)

        cls.fromDict = fromDict

        return cls
