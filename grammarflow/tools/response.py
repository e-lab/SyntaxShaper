import json


class Response:
    def __init__(self, data=None):
        if isinstance(data, (dict, list)):
            self._data = data
        else:
            self._data = {}

    def __getattr__(self, name):
        if isinstance(self._data, dict) and name in self._data:
            if isinstance(self._data[name], (dict, list)):
                return Response(self._data[name])
            return self._data[name]
        return None

    def __setattr__(self, name, value):
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def __getitem__(self, key):
        if (isinstance(self._data, list) and isinstance(key, int)) or (
            isinstance(self._data, dict) and key in self._data
        ):
            return self._data[key]
        return None

    def __setitem__(self, key, value):
        if isinstance(self._data, dict) or isinstance(self._data, list):
            self._data[key] = value
        else:
            raise TypeError("Assignment not supported for uninitialized Response objects")

    def __repr__(self):
        return repr(self._data)

    def schema(self, path="", depth=0):
        schema_dict = {}
        if isinstance(self._data, dict):
            for k, v in self._data.items():
                print("    " * depth + str(k))
                if isinstance(v, dict) or isinstance(v, list):
                    schema_dict[k] = Response(v).schema(path, depth + 1)
                else:
                    schema_dict[k] = type(v).__name__
        elif isinstance(self._data, list):
            if self._data:
                print("    " * depth + "[]")
                item_schema = Response(self._data[0]).schema(path, depth + 1)
                schema_dict = item_schema
        else:
            schema_dict = type(self._data).__name__

        return schema_dict

    def __str__(self):
        return json.dumps(self._data, indent=4)
