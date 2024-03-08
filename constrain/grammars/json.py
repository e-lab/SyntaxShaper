from pydantic import BaseModel
from typing import List, Optional
from constrain.tools.pydantic import ModelParser


class JSON:
    @staticmethod
    def make_format(tasks: List[dict], return_sequence: str) -> str:
        grammar, instruct = "", []
        for task in tasks:
            model = task.get('model')

            if isinstance(model, list):
                if not task.get('query'): 
                    name = "_".join([m.__name__ for m in model])
            else: 
                if hasattr(model, '__name__'):
                    name = model.__name__
                model = [model]
            
            if task.get('query'):
                name = "For query: " + repr(task.get('query'))

            if name:
                instruct.append(name)

            variables, nested_models = ModelParser.extract_variables_with_descriptions(model)

            if nested_models:
                forma = JSON.generate_prompt_from_variables({name: variables[name]})
                del variables[name]
            else: 
                if len(variables) > 1:
                        forma = JSON.generate_prompt_from_variables(
                            variables, nested=True)
                else:
                    forma = JSON.generate_prompt_from_variables(variables)

            grammar += f"{name}:\n```\n{forma}\n```\n"

            if nested_models:
                grammar += "Use the data types given below to fill in the above model\n```\n"
                # print(variables)
                for variable in variables:
                    # print('variable is', variable)
                    grammar += f"{JSON.generate_prompt_from_variables({variable: variables[variable]}, ignore=True)}\n"
                grammar += "```"

        return grammar, instruct

    @staticmethod
    def generate_prompt_from_variables(variables_info: dict, nested: bool = False, ignore=False) -> str:
        if not ignore: prompt_lines = ["{"] 
        else : prompt_lines = []
        for model_name, fields in variables_info.items():
            model_prompt = JSON._generate_single_model_prompt(
                fields, model_name, nested=True)
            prompt_lines.append(f'{model_prompt},')
        # Ensure proper JSON formatting
        prompt_lines[-1] = prompt_lines[-1].rstrip(',')
        if not ignore: prompt_lines.append("}")
        return "\n".join(prompt_lines)

    @staticmethod
    def _generate_single_model_prompt(fields: dict, model_name: str, nested: bool = False) -> str:
        prompt_lines = [f'"{model_name}": ' + "{" if nested else "{"]
        for var_name, details in fields.items():
            # print(var_name, details)
            line = f'"{var_name}": '
            if 'value' in details:
                line += f'{details["value"]}'
            else:
                line += f'# Type: {details["type"]}'
                if details.get('description'):
                    line += f' | {details["description"]}'
                if not details.get("required"):
                    pass # Expected to be required
                else: 
                    line += " | Optional"
                if str(details.get("default")) not in ['PydanticUndefined', 'None']:
                    line += f' | Default: "{details["default"]}"'
            line += ","
            prompt_lines.append(line)
        prompt_lines[-1] = prompt_lines[-1].rstrip(',')
        prompt_lines.append("    }" if nested else "}")
        return "\n".join(prompt_lines)

    @staticmethod
    def parse_json(json_string):
        def parse_value(json_string, i):
            if json_string[i] == '{':
                return parse_object(json_string, i + 1)
            elif json_string[i] == '[':
                return parse_array(json_string, i + 1)
            elif json_string[i] in '0123456789-':
                return parse_number(json_string, i)
            elif json_string[i] == '"':
                return parse_string(json_string, i + 1)
            elif json_string[i:i+4] == 'true':
                return True, i + 4
            elif json_string[i:i+5] == 'false':
                return False, i + 5
            elif json_string[i:i+4] == 'null':
                return None, i + 4
            else:
                raise ValueError(f'Invalid character at {i}: {json_string[i]}')

        def parse_string(json_string, i):
            # print('in string')
            # print(json_string, i)
            start = i
            if json_string[i] == '"':
                start = i + 1
                i += 1
            while json_string[i] != '"':
                i += 1
            # print(i)
            return json_string[start:i], i + 1

        def parse_number(json_string, i):
            start = i
            while json_string[i] in '0123456789.-eE':
                i += 1
            return int(json_string[start:i]), i

        def parse_array(json_string, i):
            array = []
            while json_string[i] != ']':
                value, i = parse_value(json_string, i)
                array.append(value)
                i = skip_whitespace(json_string, i)
                if json_string[i] == ',':
                    i = skip_whitespace(json_string, i + 1)
            return array, i + 1

        def parse_object(json_string, i):
            # print('in object')
            # print(json_string)
            obj = {}
            while json_string[i] != '}':
                key, i = parse_string(json_string, i)
                i = skip_whitespace(json_string, i)
                if json_string[i] != ':':
                    raise ValueError(
                        f'Expected ":" at {i}, got {json_string[i]}')
                i = skip_whitespace(json_string, i + 1)
                value, i = parse_value(json_string, i)
                obj[key] = value
                i = skip_whitespace(json_string, i)
                if json_string[i] == ',':
                    i = skip_whitespace(json_string, i + 1)
            return obj, i + 1

        def skip_whitespace(json_string, i):
            while json_string[i] in ' \t\n\r':
                i += 1
            return i

        return parse_value(json_string, skip_whitespace(json_string, 0))[0]

    @staticmethod
    def parse(text):
        return JSON.parse_json(text)
