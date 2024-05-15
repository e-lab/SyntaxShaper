import json
from typing import Dict, List, Union


class Response:
    """
    Dataclass to store the parsed response.
    Does not enforce type checking, but provides a schema method to extract the schema of the response.
    """

    def __init__(self, data=None):
        if isinstance(data, (dict, list)):
            if isinstance(data, list):
                if len(data) == 1:
                    data = data[0]
            self._data = data
        else:
            self._data = {}

    def __getattr__(self, key: str):
        if isinstance(self._data, dict) and key in self._data:
            if isinstance(self._data[key], (dict, list)):
                return Response(self._data[key])
            return self._data[key]
        return None

    def __setattr__(self, key: str, value: Union[Dict, List, str]):
        if key == "_data":
            super().__setattr__(key, value)
        else:
            if isinstance(value, str):
                value = value.replace('\\n', '\n')
            self._data[key] = value

    def __getitem__(self, key: str):
        if (isinstance(self._data, list) and isinstance(key, int)) or (
            isinstance(self._data, dict) and key in self._data
        ):
            return self._data[key]
        return None

    def __setitem__(self, key: str, value: Union[Dict, List]):
        if isinstance(self._data, dict) or isinstance(self._data, list):
            self._data[key] = value
        else:
            raise TypeError(
                "Assignment not supported for uninitialized Response objects.")

    def __repr__(self):
        return repr(self._data)

    def schema(self, path: str = "", depth: int = 0) -> Dict:  # pylint: disable=missing-function-docstring
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

    def __str__(self) -> str:
        try:
            return json.dumps(self._data, indent=4)
        except BaseException:
            return str(self._data)
