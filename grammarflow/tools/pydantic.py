from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel


class EmptyModelField(BaseModel):
    default: Optional[str] = None
    required: Optional[bool] = True
    description: Optional[str] = None
    value: Optional[str] = None


class ModelParser:
    @staticmethod
    def screen_field_info(model: BaseModel):
        temp = {}

        for field_name, field_info in model.__fields__.items():
            if not field_info:
                field_info = EmptyModelField()

            temp[field_name] = {}
            temp[field_name]["default"] = field_info.default
            temp[field_name]["required"] = field_info.required
            temp[field_name]["description"] = None

            try:
                temp[field_name]["description"] = field_info.field_info.description
            except:
                try:
                    temp[field_name]["description"] = field_info.description
                except:
                    pass

            try:
                temp[field_name]["value"] = getattr(model, field_name)
            except:
                pass

        return temp

    @staticmethod
    def screen_model_schema(schema: dict):
        temp = {}

        for field_name in schema["properties"]:

            temp[field_name] = {}
            if "anyOf" in schema["properties"][field_name]:
                temp[field_name]["type"] = " OR ".join([x["type"] for x in schema["properties"][field_name]["anyOf"]])
            elif "items" in schema["properties"][field_name]:
                if "$ref" in schema["properties"][field_name]["items"]:
                    nested_model_name = schema["properties"][field_name]["items"]["$ref"].split("/")[-1]
                    temp[field_name]["type"] = "List[" + nested_model_name + "]"
                else:
                    temp[field_name]["type"] = "List[" + schema["properties"][field_name]["items"]["type"] + "]"
            elif "$ref" in schema["properties"][field_name]:
                temp[field_name]["type"] = schema["properties"][field_name]["$ref"].split("/")[-1]
            else:
                temp[field_name]["type"] = schema["properties"][field_name]["type"]

        return temp

    @staticmethod
    def extract_fields_with_descriptions(model_classes: List[Type[BaseModel]]) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Extracts and returns a dictionary containing descriptions of fields
        from a list of Pydantic model classes.
        """

        def update_dict(d1, d2):
            for key, value in d2.items():
                if key in d1:
                    if isinstance(d1[key], dict):
                        update_dict(d1[key], value)
                    else:
                        d1[key] = value
                else:
                    d1[key] = value

        fields = {}
        nested = 0

        for count, model in enumerate(model_classes):
            temp = {}
            schema = model.schema()

            if "definitions" in schema:
                nested = 1
                for nested_model_name, nested_model_schema in schema["definitions"].items():
                    fields[nested_model_name] = ModelParser.screen_model_schema(nested_model_schema)

            update_dict(temp, ModelParser.screen_field_info(model))
            update_dict(temp, ModelParser.screen_model_schema(schema))

            if hasattr(model, "__name__"):
                fields[model.__name__] = temp
            else:
                fields[model.__class__.__name__] = temp

        return fields, nested
