from pydantic import BaseModel
from typing import List, Optional
from constrain.tools.pydantic import ModelParser

class XML: 
    @staticmethod
    def make_format(tasks: List[dict], return_sequence: str) -> str:
        grammar, instruct = "", []
        for task in tasks:
            model = task.get('model')
            if isinstance(model, list):
                name = "_".join([m.__name__ for m in model])
            else:
                name = model.__name__
                model = [model]
            instruct.append(name)

            variables = ModelParser.extract_variables_with_descriptions(model)
            forma = XML.generate_prompt_from_variables(variables, nested=True)
            grammar += f"{name}:\n```\n{forma}\n```\n\n"

        return grammar, instruct

    @staticmethod
    def generate_prompt_from_variables(variables_info: dict, nested: bool = False) -> str:
        prompt_lines = []
        for model_name, fields in variables_info.items():
            if nested:
                prompt_lines.append(f"<{model_name}>")
            for var_name, details in fields.items():
                line = f'<{var_name}>'
                line += f' #{details["type"]}# </{var_name}>'
                if details.get('description'):
                    line += f' | {details["description"]}'
                if str(details.get("default")) not in ['PydanticUndefined', 'None']:
                    line += f', Default: "{details["default"]}"'
                prompt_lines.append(line)
            if nested:
                prompt_lines.append(f"</{model_name}>")

        return "\n".join(prompt_lines)

    @staticmethod
    def _generate_single_model_prompt(fields: dict, model_name: str, nested: bool = False) -> dict:
        model_data = {}
        for var_name, details in fields.items():
            model_data[var_name] = {
                'description': details['description'],
                'type': details['type'],
                'default': details['default'] if str(details.get("default")) != 'PydanticUndefined' else None
            }
        return model_data

    def parse(xml_string):

        def parse_tags(tags, storage):
            stack = []
            result = {}
            for tag in tags:
                if stack and stack[-1] == tag:
                    stack.pop()
                    if stack:
                        parent = result
                        for item in stack:
                            parent = parent[item][-1]
                        parent[tag] = storage[tag].pop(0)
                    else:
                        result[tag] = storage[tag].pop(0)
                else:
                    stack.append(tag)
                    if stack:
                        parent = result
                        for item in stack[:-1]:
                            parent = parent[item][-1]
                        parent[tag] = [storage[tag][0]]
            return result

        def parse_tag(xml_string, i):
            start = i
            while xml_string[i] != '>':
                i += 1
            tag = xml_string[start:i]
            if ' ' in tag:
                tag, attr = tag.split(' ', 1)
                attr = dict(item.split('=') for item in attr.split())
            else:
                attr = {}
            
            add_val_attr(tag, '', attr)

            return tag, i + 1

        def add_val_attr(tag, value, attr):
            temp = {} 
            if value and value.strip() not in ['\n', '', ' ']: 
                temp.update({'value': value})
            if attr:
                temp.update({'attributes': {key: value.replace('\"', '') for key, value in attr.items()}})

            if tag in storage:
                if temp: 
                    storage[tag] = [val for val in storage[tag] if val ] 
                    storage[tag].append(temp)
            else:
                storage[tag] = [temp] 

        def parse_value(xml_string, i):
            start = i
            while xml_string[i] != '<':
                i += 1
            value = xml_string[start:i].strip()
            if value == '':
                return None, i
            else:
                return value, i

        def sanity_check(tag):
            if ' ' in tag:
                tag, attr = tag.split(' ', 1)
                attr = dict(item.split('=') for item in attr.split())
            else:
                attr = {}
            return tag, attr

        def skip_whitespace(xml_string, i):
            while i < len(xml_string) and xml_string[i] in ' \t\n\r':
                i += 1
            return i

        i = 0
        storage = {}
        tags = [] 
        while i < len(xml_string):
            i = skip_whitespace(xml_string, i)
            if i >= len(xml_string) : break 
            if xml_string[i] == '<':
                if xml_string[i+1] == '/':  
                    tag, i = parse_tag(xml_string, i + 2)
                else:  
                    tag, i = parse_tag(xml_string, i + 1)
                    tag, attr = sanity_check(tag)
                    value, i = parse_value(xml_string, i)
                    add_val_attr(tag, value, attr)
                tags += [tag]
            else:
                break
        
        return parse_tags(tags, storage)