from collections import deque
from typing import List, Optional

import re
from pydantic import BaseModel

from grammarflow.tools.pydantic import ModelParser


class XML:
    @staticmethod
    def format(model: BaseModel):
        grammar = ""
    
        fields, is_nested_model = ModelParser.extract_fields_with_descriptions([model])

        if is_nested_model:
            format_ = XML.generate_prompt_from_fields({name: fields[name]})
            del fields[name]
        else:
            format_ = XML.generate_prompt_from_fields(fields)

        grammar += f"***\n{format_}\n***\n"

        if is_nested_model:
            grammar += "Use the data types given below to fill in the above model\n***\n"
            for nested_model in fields:
                grammar += f"{XML.generate_prompt_from_fields({nested_model: fields[nested_model]})}\n"
            grammar += "***\n"
    
        return grammar 

    @staticmethod
    def make_format(grammars: List[dict], return_sequence: str) -> str:
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
                model_names.append(f'<{name}>')

            fields, is_nested_model = ModelParser.extract_fields_with_descriptions(model)

            if is_nested_model:
                format_ = XML.generate_prompt_from_fields({name: fields[name]})
                del fields[name]
            else:
                format_ = XML.generate_prompt_from_fields(fields)

            if model_descrip:
                grammar += f"{model_descrip}:\n"
            else: 
                grammar += f"{name}:\n"

            grammar += f"***\n{format_}\n***\n"

            if is_nested_model:
                grammar += "Use the data types given below to fill in the above model\n***\n"
                for nested_model in fields:
                    grammar += f"{XML.generate_prompt_from_fields({nested_model: fields[nested_model]})}\n"
                grammar += "***\n"

        return grammar, model_names

    @staticmethod
    def generate_prompt_from_fields(fields_info: dict) -> str:
        prompt_lines = []
        for model_name, fields in fields_info.items():
            prompt_lines.append(f"<{model_name}>")
            for var_name, details in fields.items():
                line = f"<{var_name}>"
                if "value" in details:
                    line += f' {details["value"]} </{var_name}>'
                else:
                    line += f' #{details["type"]}# </{var_name}>'
                    if details.get("description"):
                        line += f' # {details["description"]}'
                    if str(details.get("default")) not in ["PydanticUndefined", "None"]:
                        line += f' # Default: "{details["default"]}"'
                prompt_lines.append(line)
            prompt_lines.append(f"</{model_name}>\n")

        return "\n".join(prompt_lines)

    def parse(xml_string):

        def build_structure(tags):
            result = {}
            stack = []
            objects = {}

            for tag in tags:
                if not stack or stack[-1] != tag:
                    if tag not in objects:
                        objects[tag] = []
                    stack.append(tag)
                    new_obj = {}
                    objects[tag].append(new_obj)
                    if len(stack) > 1:
                        parent_tag = stack[-2]
                        parent_obj = objects[parent_tag][-1]
                        if tag in parent_obj:
                            if not isinstance(parent_obj[tag], list):
                                parent_obj[tag] = [parent_obj[tag]]
                            parent_obj[tag].append(new_obj)
                        else:
                            parent_obj[tag] = new_obj
                else:
                    stack.pop()

            result[tag] = objects[tags[0]]

            for tag, value in result.items():
                if isinstance(value, list):
                    if len(value) == 1:
                        result[tag] = value[0]

            return result

        def populate_structure(structure, storage):
            queue = deque([(structure, None)])

            while queue:
                current, parent_tag = queue.popleft()

                if isinstance(current, dict):
                    for tag, value in current.items():
                        if isinstance(value, dict) and not value:
                            if tag in storage and storage[tag]:
                                current[tag] = storage[tag].pop(0)["value"]
                            continue
                        elif isinstance(value, list):
                            for item in value:
                                queue.append((item, tag))
                        else:
                            queue.append((value, tag))
                elif isinstance(current, list) and parent_tag not in ["grammars", "grammars"]:
                    for item in current:
                        if isinstance(item, dict):
                            queue.append((item, parent_tag))

        def parse_tags(tags, storage):
            structure = build_structure(tags)
            populate_structure(structure, storage)
            return structure

        def find_attr_value_pairs(tag):
            pattern = r'\b(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')'
            
            matches = re.findall(pattern, tag)
            results = []
            for attr, value_double, value_single in matches:
                value = value_double if value_double else value_single
                results.append((attr, value))
            
            return results

        def parse_tag(xml_string, i):
            start = i
            while xml_string[i] != ">":
                i += 1
            tag = xml_string[start:i]

            attr_value_pairs = find_attr_value_pairs(tag)

            if attr_value_pairs: 
                for attr, value in attr_value_pairs:
                    tag = tag.replace('=', '').replace(attr, '').replace(value, '')

            return tag.replace(' ', '').replace('/', '').replace('"', '').replace("-", "_"), i + 1, attr_value_pairs

        def add_val(tag, value):
            value = evaluate(value)
            temp = {}
            if not (value == None):
                if isinstance(value, str) and value.strip() in ["\n", "", " "]:
                    pass
                else:
                    temp.update({"value": value})

            if tag in storage:
                if temp:
                    storage[tag] = [val for val in storage[tag] if val]
                    storage[tag].append(temp)
            else:
                storage[tag] = [temp]

        def parse_value(xml_string, i):
            i = skip_whitespace(xml_string, i)
            start = i
            temp_xml = xml_string.replace(" < ", "lsr")  # In case, '<' is used in the value
            if temp_xml[i] == '"':
                i += 1
                start = i
                while temp_xml[i] != '"':
                    i += 1
            else: 
                while temp_xml[i] != "<":
                    i += 1

            value = temp_xml[start:i].strip()

            if value == "":
                return None, i
            else:
                return value.replace("lsr", " < "), i

        def evaluate(value):
            try:
                if value.lower().replace('"', '') == "true":
                    return True
                elif value.lower().replace('"', '') == "false":
                    return False
                elif value.lower().replace('"', '') in ["null", "none"]:
                    return None
                else: 
                    return eval(value)
            except:
                return value
        
        def check_list(value): 
            try: 
                return list(value)
            except: 
                return False

        def skip_whitespace(xml_string, i):
            while i < len(xml_string) and xml_string[i] in " \t\r":
                i += 1
            return i

        i = 0
        storage = {}
        tags = []

        
        while i < len(xml_string):
            i = skip_whitespace(xml_string, i)
            if i >= len(xml_string):
                break
            if xml_string[i] == "<":
                i = skip_whitespace(xml_string, i + 1)
                if xml_string[i] == "/":
                    tag, i, _ = parse_tag(xml_string, i + 1)
                else:
                    tag, i, attr_value_pairs = parse_tag(xml_string, i)
                    if attr_value_pairs:
                        for attr, value in attr_value_pairs:
                            add_val(tag, value)
                        tags += [tag] # Attrs only need one tag 
                    else: 
                        value, i = parse_value(xml_string, i)
                        add_val(tag, value)

                tags += [tag]
            else:
                while i < len(xml_string) and xml_string[i] != "<":
                    i += 1

        return parse_tags(tags, storage)
