from pydantic import BaseModel
from typing import List, Optional
from constrain.tools.pydantic import ModelParser
from collections import deque

class XML:
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
                forma = XML.generate_prompt_from_variables({name: variables[name]})
                del variables[name]
            else: 
                forma = XML.generate_prompt_from_variables(variables)

            grammar += f"{name}:\n```\n{forma}\n```\n"

            if nested_models:
                grammar += "Use the data types given below to fill in the above model\n```\n"
                for variable in variables:
                    grammar += f"{XML.generate_prompt_from_variables({variable: variables[variable]})}\n"
                grammar += "```"

        return grammar, instruct

    @staticmethod
    def generate_prompt_from_variables(variables_info: dict) -> str:
        prompt_lines = []
        for model_name, fields in variables_info.items():
            prompt_lines.append(f"<{model_name}>")
            for var_name, details in fields.items():
                line = f'<{var_name}>'
                if 'value' in details:
                    line += f' {details["value"]} </{var_name}>'
                else:
                    line += f' #{details["type"]}# </{var_name}>'
                    if details.get('description'):
                        line += f' # {details["description"]}'
                    if str(details.get("default")) not in ['PydanticUndefined', 'None']:
                        line += f' # Default: "{details["default"]}"'
                prompt_lines.append(line)
            prompt_lines.append(f"</{model_name}>\n")

        return "\n".join(prompt_lines)

    def parse(xml_string):

        def build_structure(tags):
            result = {}  # The resulting structure
            stack = []  # Stack to keep track of the hierarchy and context
            objects = {}  # Temporary storage for ongoing construction of objects

            for tag in tags:
                if not stack or stack[-1] != tag:  # Opening tag
                    if tag not in objects:  # First occurrence of this tag
                        objects[tag] = []
                    stack.append(tag)
                    # Create a new dictionary for this tag instance
                    new_obj = {}
                    objects[tag].append(new_obj)
                    # Nest the new_obj correctly
                    if len(stack) > 1:  # Not at the root
                        parent_tag = stack[-2]
                        # Get the last instance of the parent object
                        parent_obj = objects[parent_tag][-1]
                        if tag in parent_obj:  # Already exists, ensure it's a list
                            if not isinstance(parent_obj[tag], list):
                                parent_obj[tag] = [parent_obj[tag]]  # Convert existing to list
                            parent_obj[tag].append(new_obj)
                        else:
                            parent_obj[tag] = new_obj  # Add as a single instance for now
                else:  # Closing tag
                    stack.pop()  # Finished with this tag level

            result[tag] = objects[tags[0]]
            return result

        def populate_structure(structure, storage):
            # Initialize a queue with the structure's items
            queue = deque([(structure, None)])

            while queue:
                current, parent_tag = queue.popleft()

                # Check if the current item is a dict and process accordingly
                if isinstance(current, dict):
                    for tag, value in current.items():
                        # If value is a dict and not meant to be populated, enqueue it for further traversal
                        if isinstance(value, dict) and not value:
                            if tag in storage and storage[tag]:
                                current[tag] = storage[tag].pop(0)['value']
                            continue
                        elif isinstance(value, list):
                            # If it's a list, enqueue all items with the current tag
                            for item in value:
                                queue.append((item, tag))
                        else:
                            queue.append((value, tag))
                # Check if the current item is a list and it's not directly under a 'nested' tag
                elif isinstance(current, list) and parent_tag not in ['tasks', 'Tasks']:
                    # Assume lists at this level are homogeneous and represent multiple instances of an item
                    for item in current:
                        if isinstance(item, dict):
                            queue.append((item, parent_tag))

        def parse_tags(tags, storage):
            # Step 1: Build the structure
            structure = build_structure(tags)

            # Step 2: Populate the structure with values from storage
            populate_structure(structure, storage)

            return structure

        def parse_tag(xml_string, i):
            start = i
            while xml_string[i] != '>':
                i += 1
            tag = xml_string[start:i]
            try: 
                if ' ' in tag:
                    tag, attr = tag.split(' ', 1)
                    attr = dict(item.split('=') for item in attr.split())
                else:
                    attr = {}
            except: 
                attr = {}

            add_val_attr(tag, '', attr)

            return tag, i + 1

        def add_val_attr(tag, value, attr):
            temp = {}
            if value and value.strip() not in ['\n', '', ' ']:
                temp.update({'value': value})
            if attr:
                temp.update({'attributes': {key: value.replace('\"', '')
                            for key, value in attr.items()}})

            if tag in storage:
                if temp:
                    storage[tag] = [val for val in storage[tag] if val]
                    storage[tag].append(temp)
            else:
                storage[tag] = [temp]

        def parse_value(xml_string, i):
            start = i
            temp_xml = xml_string.replace(' < ', 'lsr')
            while temp_xml[i] != '<':
                i += 1
            value = temp_xml[start:i].strip()
            if value == '':
                return None, i
            else:
                return value.replace(' lsr ', ' < '), i

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
            if i >= len(xml_string):
                break
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
