from collections import deque
from typing import List, Optional

from pydantic import BaseModel

from grammarflow.tools.pydantic import ModelParser


class XML:
    @staticmethod
    def make_format(grammars: List[dict], return_sequence: str) -> str:
        grammar, model_names = "", []
        for task in grammars:
            model = task.get("model")

            if isinstance(model, list):
                if not task.get("query"):
                    name = "_".join([m.__name__ for m in model])
            else:
                if task.get("description"):
                    name = task.get("description")
                elif hasattr(model, "__name__"):
                    name = model.__name__
                model = [model]

            if task.get("query"):
                name = "For query: " + repr(task.get("query"))

            if name:
                model_names.append(name)

            fields, is_nested_model = ModelParser.extract_fields_with_descriptions(model)

            if is_nested_model:
                format_ = XML.generate_prompt_from_fields({name: fields[name]})
                del fields[name]
            else:
                format_ = XML.generate_prompt_from_fields(fields)

            grammar += f"{name}:\n```\n{format_}\n```\n"

            if is_nested_model:
                grammar += "Use the data types given below to fill in the above model\n```\n"
                for nested_model in fields:
                    grammar += f"{XML.generate_prompt_from_fields({nested_model: fields[nested_model]})}\n"
                grammar += "```"

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
                                current[tag] = storage[tag].pop(0)["value"]
                            continue
                        elif isinstance(value, list):
                            # If it's a list, enqueue all items with the current tag
                            for item in value:
                                queue.append((item, tag))
                        else:
                            queue.append((value, tag))
                # Check if the current item is a list and it's not directly under a 'nested' tag
                elif isinstance(current, list) and parent_tag not in ["grammars", "grammars"]:
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
            while xml_string[i] != ">":
                i += 1
            tag = xml_string[start:i]
            try:
                if " " in tag:
                    tag, attr = tag.split(" ", 1)
                    attr = dict(item.split("=") for item in attr.split())
                else:
                    attr = {}
            except:
                attr = {}

            add_val_attr(tag, "", attr)

            return tag, i + 1

        def add_val_attr(tag, value, attr):
            temp = {}
            if value:
                if isinstance(value, str) and value.strip() in ["\n", "", " "]:
                    pass
                else:
                    temp.update({"value": value})
            if attr:
                temp.update({"attributes": {key: value.replace('"', "") for key, value in attr.items()}})

            if tag in storage:
                if temp:
                    storage[tag] = [val for val in storage[tag] if val]
                    storage[tag].append(temp)
            else:
                storage[tag] = [temp]

        def parse_value(xml_string, i):
            start = i
            temp_xml = xml_string.replace(" < ", "lsr")  # In case, '<' is used in the value
            while temp_xml[i] != "<":
                i += 1
            value = temp_xml[start:i].strip()

            if value == "":
                return None, i
            else:
                value = value.replace("lsr", " < ")

                try:
                    if value.lower() == "true":
                        return True, i
                    elif value.lower() == "false":
                        return False, i
                    elif value in ["null", "None"]:
                        return None, i
                    elif value.isdigit():
                        return int(value), i
                    elif "." in value:
                        return float(value), i
                except:
                    pass
                return value, i

        def sanity_check(tag):
            if " " in tag:
                tag, attr = tag.split(" ", 1)
                attr = dict(item.split("=") for item in attr.split())
            else:
                attr = {}
            return tag, attr

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
                if xml_string[i + 1] == "/":
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
