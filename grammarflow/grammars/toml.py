from grammarflow.tools.pydantic import ModelParser
from grammarflow.grammars.error import ParsingError

from typing import List, Dict
from pydantic import BaseModel


class TOML:
    '''
    Handles TOML format generation from pydantic and parsing of XML strings.
    '''

    @staticmethod
    def format(model: BaseModel):
        '''
        Single model tOML format generation.
        '''

        grammar = ''

        fields, is_nested_model = ModelParser.extract_fields_with_descriptions([
                                                                               model])

        if is_nested_model:
            format_ = TOML.generate_prompt_from_fields(
                {model.__name__: fields[model.__name__]})
            del fields[model.__name__]
        else:
            format_ = TOML.generate_prompt_from_fields(fields)

        grammar += f'```\n{format_}\n```\n'

        if is_nested_model:
            grammar += 'Use the data types given below to fill in the above model\n```\n'
            for nested_model_name, nested_schema in fields.items():
                grammar += f"{TOML.generate_prompt_from_fields(
                    {nested_model_name: nested_schema})}\n"
            grammar += '```\n'

        return grammar

    @staticmethod
    def make_format(grammars: List[dict], return_sequence: str) -> str:
        '''
        Multiple model TOML format generation. Specific for use in .prompt.builder.PromptBuilder.
        '''

        grammar, model_names, model_descrip, name = '', [], None, None
        for task in grammars:
            model = task.get('model')
            if isinstance(model, list):
                if not task.get('query'):
                    name = '_'.join([m.__name__ for m in model])
            else:
                if task.get('description'):
                    model_descrip = task.get('description')
                if hasattr(model, '__name__'):
                    name = model.__name__
                model = [model]

            if task.get('query'):
                name = 'For query: ' + repr(task.get('query'))

            if name:
                model_names.append(f'[{name}]')

            fields, is_nested_model = ModelParser.extract_fields_with_descriptions(
                model)

            if is_nested_model:
                format_ = TOML.generate_prompt_from_fields(
                    {name: fields[name]})
                del fields[name]
            else:
                format_ = TOML.generate_prompt_from_fields(fields)

            if model_descrip:
                grammar += f'{model_descrip}:\n'

            grammar += f'```\n{format_}\n```\n'

            if is_nested_model:
                grammar += 'Use the data types given below to fill in the above model\n```\n'
                for nested_model_name, nested_schema in fields.items():
                    grammar += f"{TOML.generate_prompt_from_fields(
                        {nested_model_name: nested_schema})}\n"
                grammar += '```\n'

        return grammar, model_names

    @staticmethod
    def generate_prompt_from_fields(fields_info: dict) -> str:
        '''
        Takes in formatted schema from .tools.pydantic.ModelParser and generates a representation for the prompt.
        '''

        prompt_lines = []
        for model_name, fields in fields_info.items():
            prompt_lines.append(f'[{model_name}]')
            for var_name, details in fields.items():
                line = f'{var_name} = '
                if 'value' in details:
                    line += f'"{details['value']}"'
                else:
                    if details.get('type') == 'boolean':
                        line += f'# Type: "{details['type']}"'
                    else:
                        line += f'# Type: {details['type']}'
                    if details.get('description'):
                        line += f' | "{details['description']}"'

                    if str(details.get('default')) not in [
                            'PydanticUndefined', 'None']:
                        line += f', Default: "{details['default']}"'
                prompt_lines.append(line)
        return '\n'.join(prompt_lines)

    @staticmethod
    def parse_toml(toml_string: str) -> Dict:
        '''
        TOML character-level parsing.
        '''

        def parse_section(toml_string, i):
            start = i
            while toml_string[i] != ']':
                i += 1
            key = toml_string[start:i].strip().replace('-', '_')
            i = skip_whitespace(toml_string, i + 1)
            section = {key: {}}
            while i < len(toml_string) and toml_string[i] not in '[':
                subkey, i = parse_key(toml_string, i)
                i = skip_whitespace(toml_string, i)
                if toml_string[i] == '=':
                    i = skip_whitespace(toml_string, i + 1)
                    value, i = parse_value(toml_string, i)
                    section[key.replace('\n', '')][subkey.replace(
                        '\n', '').strip()] = value
                i = skip_whitespace(toml_string, i)
            return section, i

        def parse_value(toml_string, i):
            i = skip_whitespace(toml_string, i)
            if toml_string[i] == '"':
                return parse_string(toml_string, i + 1)
            elif toml_string[i] == '[':
                return parse_array(toml_string, i)
            elif toml_string[i] == '{':
                return parse_dict(toml_string, i)
            else:
                return parse_other(toml_string, i)

        def parse_string(toml_string, i):
            start = i
            while toml_string[i] != '"':
                i += 1
            return toml_string[start:i], i + 1

        def parse_other(toml_string, i):
            start = i
            if toml_string[start:start+4].lower() == 'true':
                return True, i + 4
            elif toml_string[start:start+5].lower() == 'false':
                return False, i + 5

            while toml_string[i] in '01234567890.':
                i += 1

            val = toml_string[start:i]
            try:
                return eval(val), i
            except ValueError:
                return val, i

        def parse_array(toml_string, i):
            i = skip_whitespace(toml_string, i + 1)
            array = []
            while toml_string[i] != ']':
                value, i = parse_value(toml_string, i)
                array += [value]
                if toml_string[i] == ',':
                    i += 1
                i = skip_whitespace(toml_string, i)
            return array, i + 1

        def parse_key(toml_string, i):
            start = i
            while toml_string[i] not in '=':
                i += 1
            return toml_string[start:i], i

        def parse_dict(toml_string, i):
            dictionary = {}
            i = skip_whitespace(toml_string, i + 1)  # Move past the "{'
            while toml_string[i] != '}':
                key, i = parse_key(toml_string, i)
                i = skip_whitespace(toml_string, i)
                if toml_string[i] == '=' or toml_string[i] == ':':
                    i += 1  # Skip the '='
                    i = skip_whitespace(toml_string, i)
                    value, i = parse_value(toml_string, i)
                    dictionary[key] = value
                    i = skip_whitespace(toml_string, i)
                    if toml_string[i] == ',':
                        i += 1  # Skip the comma
                        i = skip_whitespace(toml_string, i)
            return dictionary, i + 1

        def skip_whitespace(toml_string, i):
            while i < len(toml_string) and toml_string[i] in [
                    ' ', '\n', '\t', '\r']:
                i += 1
            return i

        def prune_starting(toml_string):
            index = toml_string.find('[')
            if index == 0 or index == -1:
                return toml_string
            else:
                return toml_string[index:]

        i = 0
        storage = {}

        toml_string = prune_starting(toml_string)

        try:
            while i < len(toml_string):
                i = skip_whitespace(toml_string, i)
                if i < len(toml_string) and toml_string[i] == '[':
                    i = skip_whitespace(toml_string, i + 1)
                    section, i = parse_section(toml_string, i)
                    key = list(section.keys())[0]
                    if key in storage:
                        storage[key.replace(' ', '')].append(section[key])
                    else:
                        storage[key.replace(' ', '')] = [section[key]]
                else:
                    break

            return storage
        except BaseException as exc:
            raise ParsingError(
                'ERROR: Unable to parse response into TOML format!') from exc

    @staticmethod
    def parse(text: str):
        return TOML.parse_toml(text)
