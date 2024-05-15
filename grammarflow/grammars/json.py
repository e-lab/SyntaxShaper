from grammarflow.tools.pydantic import ModelParser
from grammarflow.grammars.error import ParsingError

from typing import List, Dict
from pydantic import BaseModel


class JSON:
    """
    Handles JSON format generation from pydantic and parsing of XML strings.
    """

    @staticmethod
    def format(model: BaseModel):
        """
        Single model JSON format generation.
        """

        grammar = ""

        fields, is_nested_model = ModelParser.extract_fields_with_descriptions([
                                                                               model])

        if is_nested_model:
            format_ = JSON.generate_prompt_from_fields(
                {model.__name__: fields[model.__name__]})
            del fields[model.__name__]
        else:
            format_ = JSON.generate_prompt_from_fields(fields)

        grammar += f"```\n{format_}\n```\n"

        if is_nested_model:
            grammar += "Use the data types given below to fill in the above model\n```\n"
            for nested_model_name, nested_schema in fields.items():
                grammar += f"{JSON.generate_prompt_from_fields(
                    {nested_model_name: nested_schema})}\n"
            grammar += "```"

        return grammar

    @staticmethod
    def make_format(grammars: List[dict], return_sequence: str) -> str:
        """
        Multiple model JSON format generation. Specific for use in .prompt.builder.PromptBuilder.
        """

        grammar, model_names, model_descrip, name = "", [], None, None
        for task in grammars:
            model = task.get("model")

            if isinstance(model, list):
                if not task.get("query"):
                    name = "_".join([m.__name__ for m in model])
            else:
                if task.get("description"):
                    model_descrip = task.get("description")
                if hasattr(model, "__name__"):
                    name = model.__name__
                model = [model]

            if task.get("query"):
                name = "For query: " + repr(task.get("query"))

            if name:
                model_names.append(f'"{name}"')

            fields, is_nested_model = ModelParser.extract_fields_with_descriptions(
                model)

            if is_nested_model:
                format_ = JSON.generate_prompt_from_fields(
                    {name: fields[name]})
                del fields[name]
            else:
                if len(fields) > 1:
                    format_ = JSON.generate_prompt_from_fields(
                        fields, nested=True)
                else:
                    format_ = JSON.generate_prompt_from_fields(fields)

            if model_descrip:
                grammar += f"{model_descrip}:\n"

            grammar += f"```\n{format_}\n```\n"

            if is_nested_model:
                grammar += "Use the data types given below to fill in the above model\n```\n"
                for nested_model_name, nested_schema in fields.items():
                    grammar += f"{JSON.generate_prompt_from_fields(
                        {nested_model_name: nested_schema})}\n"
                grammar += "```"

        return grammar, model_names

    @staticmethod
    def generate_prompt_from_fields(
            fields_info: dict,
            nested: bool = False,
            ignore: bool = False) -> str:
        """
        Takes in formatted schema from .tools.pydantic.ModelParser and generates a representation for the prompt.
        """

        if not ignore:
            prompt_lines = ["{"]
        else:
            prompt_lines = []

        for model_name, fields in fields_info.items():
            model_prompt = JSON._generate_single_model_prompt(
                fields, model_name, nested=True)
            prompt_lines.append(f"{model_prompt},")

        prompt_lines[-1] = prompt_lines[-1].rstrip(",")

        if not ignore:
            prompt_lines.append("}")

        return "\n".join(prompt_lines)

    @staticmethod
    def _generate_single_model_prompt(
            fields: dict,
            model_name: str,
            nested: bool = False) -> str:
        '''
        Helper function to generate prompt for a single model.
        '''

        prompt_lines = [f'"{model_name}": ' + "{" if nested else "{"]

        for var_name, details in fields.items():
            line = f'"{var_name}": '
            if "value" in details:
                line += f'{details["value"]}'
            else:
                line += f'# Type: {details["type"]}'
                if details.get("description"):
                    line += f' | {details["description"]}'
                if not details.get("required"):
                    pass  # Expected to be required
                else:
                    line += " | Optional"
                if str(details.get("default")) not in [
                        "PydanticUndefined", "None"]:
                    line += f' | Default: "{details["default"]}"'
            line += ","
            prompt_lines.append(line)

        prompt_lines[-1] = prompt_lines[-1].rstrip(",")
        prompt_lines.append("    }" if nested else "}")

        return "\n".join(prompt_lines)

    @staticmethod
    def parse_json(json_string) -> Dict:
        """
        JSON character-level parsing.
        """

        def parse_value(json_string, i):
            if json_string[i] == "{":
                return parse_object(json_string, i + 1)
            elif json_string[i] == "[":
                return parse_array(json_string, i + 1)
            elif json_string[i] in "0123456789-.eE":
                return parse_number(json_string, i)
            elif json_string[i] == '"':
                return parse_string(json_string, i + 1)
            elif json_string[i: i + 4].lower() == "true":
                return True, i + 4
            elif json_string[i: i + 5].lower() == "false":
                return False, i + 5
            elif json_string[i: i + 4].lower() in ["null", 'none']:
                return None, i + 4
            else:
                raise ValueError(f"Invalid character at {i}: {json_string[i]}")

        def parse_string(json_string, i):
            start = i
            while json_string[i] != '"':
                i += 1
            if json_string[start:i]:
                return json_string[start:i], i + 1
            return None, i + 1

        def parse_number(json_string, i):
            start = i
            while json_string[i] in "0123456789.-eE":
                i += 1
            return eval(json_string[start:i]), i

        def parse_array(json_string, i):
            array = []
            while json_string[i] != "]":
                i = skip_whitespace(json_string, i)
                value, i = parse_value(json_string, i)
                array.append(value)
                i = skip_whitespace(json_string, i)
                if json_string[i] == ",":
                    i = skip_whitespace(json_string, i + 1)
            return array, i + 1

        def parse_object(json_string, i):
            obj = {}
            while json_string[i] != "}":
                i = skip_whitespace(json_string, i)
                key, i = parse_string(json_string, i + 1)
                key = key.replace("-", "_")
                i = skip_whitespace(json_string, i)
                if json_string[i] != ":":
                    raise ValueError(
                        f'Expected ":" at {i}, got {
                            json_string[i]}')
                i = skip_whitespace(json_string, i + 1)
                value, i = parse_value(json_string, i)
                obj[key] = value
                i = skip_whitespace(json_string, i)
                if json_string[i] == ",":
                    i = skip_whitespace(json_string, i + 1)
            return obj, i + 1

        def skip_whitespace(json_string, i):
            while json_string[i] in " \t\n\r":
                i += 1
            return i

        def prune_starting(json_string):
            index = json_string.find('{')
            if index == 0 or index == -1:
                return json_string
            else:
                return json_string[index:]

        try:
            json_string = prune_starting(json_string)
            return parse_value(json_string, skip_whitespace(json_string, 0))[0]
        except BaseException as exc:
            raise ParsingError(
                'ERROR: Unable to parse response into JSON format!') from exc

    @staticmethod
    def parse(text):
        return JSON.parse_json(text)
