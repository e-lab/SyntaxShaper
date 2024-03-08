from pydantic import BaseModel
from typing import List, Optional
from constrain.tools.pydantic import ModelParser


class TOML:
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

            variables = ModelParser.extract_variables_with_descriptions(model)
            forma = TOML.generate_prompt_from_variables(variables, nested=True)
            grammar += f"{name}:\n```\n{forma}\n```\n"

        return grammar, instruct

    @staticmethod
    def generate_prompt_from_variables(variables_info: dict, nested: bool = False) -> str:
        prompt_lines = []
        for model_name, fields in variables_info.items():
            if nested:
                prompt_lines.append(f"[{model_name}]")
            for var_name, details in fields.items():
                line = f'{var_name} = '
                if 'value' in details:
                    line += f'"{details["value"]}"'
                else:
                    line += f'# Type: {details["type"]}'
                    if details.get('description'):
                        line += f' | "{details["description"]}"'

                    if str(details.get("default")) not in ['PydanticUndefined', 'None']:
                        line += f', Default: "{details["default"]}"'
                prompt_lines.append(line)
        return "\n".join(prompt_lines)

    @staticmethod
    def parse_toml(toml_string):
        def parse_section(toml_string, i):
            start = i
            while toml_string[i] != ']':
                i += 1
            key = toml_string[start:i]
            i = skip_whitespace(toml_string, i + 1)
            section = {key: {}}
            while i < len(toml_string) and toml_string[i] not in '[':
                subkey, i = parse_key(toml_string, i)
                i = skip_whitespace(toml_string, i)
                if toml_string[i] == '=':
                    i = skip_whitespace(toml_string, i + 1)
                    value, i = parse_value(toml_string, i)
                    section[key.replace('\n', '').replace(' ', '')][subkey.replace(
                        '\n', '').replace(' ', '')] = value
                i = skip_whitespace(toml_string, i)
            return section, i

        def parse_key(toml_string, i):
            start = i
            while toml_string[i] not in '=':
                i += 1
            return toml_string[start:i], i

        def parse_value(toml_string, i):
            if toml_string[i] == '"':
                return parse_string(toml_string, i + 1)
            elif toml_string[i] == '[':
                return parse_array(toml_string, i)
            else:
                return parse_number(toml_string, i)

        def parse_string(toml_string, i):
            start = i
            while toml_string[i] != '"':
                i += 1
            # i += 1
            return toml_string[start:i], i + 1

        def parse_number(toml_string, i):
            start = i
            while toml_string[i] in '0123456789.-':
                i += 1

            val = toml_string[start:i]
            try:
                if '.' in val:
                    return float(val), i
                return int(val), i
            except ValueError:
                return '', i

        def parse_array(toml_string, i):
            array = []
            i = skip_whitespace(toml_string, i + 1)
            while toml_string[i].strip().replace('\n', '') != ']':
                # print('in array', toml_string[:i])
                # print('after array', toml_string[i].strip().replace('\n', ''))
                value, i = parse_value(toml_string, i)
                # print('value', value)
                array.append(value)
                j = skip_whitespace(toml_string, i + 1)
                if toml_string[i] == ']':
                    break
                i = j
                # print('right after array', toml_string[:i])

            array = [x for x in array if x]
            return array, i + 1

        def skip_whitespace(toml_string, i):
            while i < len(toml_string) and toml_string[i] in [
                    ' ', '\n', '\t', '\r']:
                i += 1
            return i

        i = 0
        storage = {}
        while i < len(toml_string):
            i = skip_whitespace(toml_string, i)
            if i < len(toml_string) and toml_string[i] == '[':
                section, i = parse_section(toml_string, i + 1)
                key = list(section.keys())[0]
                if key in storage:
                    storage[key].append(section[key])
                else:
                    storage[key] = [section[key]]
            else:
                break
        return storage

    @staticmethod
    def parse(text):
        return TOML.parse_toml(text)
