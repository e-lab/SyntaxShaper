import re
from llama_cpp import LlamaGrammar
from pydantic import BaseModel
from typing import Dict

class GNBF:
    """
    Converts a Pydantic model to GNBF grammar.
    """

    TYPE_RULES = {
        "boolean": r'("True" | "False")',
        "number": r'("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)?',
        "integer": r'("-"? ([0-9] | [1-9] [0-9]*))',
        "string": r''' "\"" (
            [^"\\] |
            "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F])
            )* "\""''',
        "none": r"None",
    }

    OBJECT_RULES = {
        "range": [r'"range(" number "," number "," number ")"', ["number"]],
        "array": [
            r"""
            "[" ws (
                {value}
                ("," ws {value})*
            )? "]" ws""",
            ["string", "number", "bool", "none"],
        ],
    }

    def __init__(self, model: BaseModel):
        self.json_obj = model.schema()
        self.rules = {"ws": r"[ \t\n]", "nl": r"[\n]"}
        self.used_data_types = set()
        self.grammar_entries = []

    def add_rule(self, name: str, definition: str):
        sanitized_name = re.sub(r"[^a-zA-Z0-9-]+", "-", name)
        if sanitized_name not in self.rules or self.rules[sanitized_name] == definition:
            self.rules[sanitized_name] = definition
            return sanitized_name

    def format_literal(self, literal: str, format_: str):
        new_literal = literal.replace(
            '"',
            '\\"').replace(
            "\n",
            "\\n").replace(
            "\r",
            "\\r")

        if format_ == 'json':
            return r'"\"' + new_literal + r"\""
        else:
            return new_literal

    def convert_type(self, json_type: str):
        if json_type not in self.used_data_types:
            self.used_data_types.add(json_type)
        return json_type

    def handle_schema(self, schema: Dict, format_: str, name="root") -> str:
        '''
        Recursively handles the schema and generates the grammar.
        '''

        if name == "root" and "definitions" in schema:
            for definition_name, definition_schema in schema["definitions"].items():
                self.handle_schema(definition_schema,  format_, definition_name)

        if "items" in schema and "$ref" in schema["items"]:
            return schema["items"]["$ref"].split("/")[-1]
        elif "$ref" in schema:
            return schema["$ref"].split("/")[-1]

        schema_type = schema.get('pattern')

        if not schema_type:
            schema_type = schema.get("type")
        else: 
            return f'"{schema_type}"'

        if not schema_type:
            if "anyOf" in schema:
                types = [self.handle_schema(sub_schema,  format_, name) for sub_schema in schema["anyOf"]]

                self.add_rule(name, " | ".join(types))
                return name

        if "properties" in schema and schema_type == "object":
            properties = schema["properties"]
            prop_definitions = []
            for prop, prop_schema in properties.items():
                prop_name = self.format_literal(prop, format_)
                prop_type = self.handle_schema(prop_schema, format_, prop)

                if prop_schema.get('pattern', None): 
                    self.grammar_entries.insert(0, f'{prop} ::= {prop_schema["pattern"]}')
                    prop_type = f"{prop}"

                if format_ == 'json':
                    prop_definitions.append(f'{prop_name}:" ws {prop_type}')
                elif format_ == 'xml': 
                    prop_definitions.append(f'"<{prop_name}>" ws {prop_type} ws "</{prop_name}>"')
                elif format_ == 'toml':
                    if prop_type.strip()[0].islower(): prop_definitions.append(f'"{prop_name}" ws "=" ws {prop_type}')
                    else: prop_definitions.append(f'{prop_type}')

            if format_ == 'json':
                properties_rule = r' "," nl '.join(prop_definitions)
                if name == 'root': rule = f'nl "{{" {self.format_literal(self.json_obj['title'], 'json')}:" ws "{{" ws {properties_rule} "}}" ws "}}"'
                else: rule = f'nl "{{" ws {properties_rule} "}}"'
            elif format_ == 'xml':
                properties_rule = r' ws '.join(prop_definitions)
                if name == 'root': rule = f'"<{self.format_literal(self.json_obj['title'], 'xml')}>" ws {properties_rule} ws "</{self.json_obj['title']}>"'
                else: rule = f'{properties_rule}'
            elif format_ == 'toml':
                properties_rule = r' nl '.join(prop_definitions)
                if name == 'root': rule = f'"[{self.format_literal(self.json_obj['title'], 'toml')}]" nl {properties_rule}'
                else: rule = f'{properties_rule}'

            if name == "root":
                self.grammar_entries.insert(0, f"{self.json_obj['title']} ::= {rule}")
                self.grammar_entries.insert(0, f"{name} ::= ws {self.json_obj['title']}")
            else:
                self.add_rule(name, rule)

        elif schema_type in self.TYPE_RULES:
            self.add_rule(schema_type, self.TYPE_RULES[schema_type])
            return self.convert_type(schema_type)

        elif schema_type in self.OBJECT_RULES:
            rule, types = self.OBJECT_RULES[schema_type]
            rule = rule.format(value=f"{name}-value").strip()

            if "items" in schema and schema["items"]:
                types = [self.handle_schema(schema["items"],  format_, name)]
            else:
                for i, t in enumerate(types):
                    if t not in self.rules:
                        self.add_rule(t, self.TYPE_RULES[t])
                        self.convert_type(t)

            rule += "\n{value} ::= {type}".format(value=f"{name}-value", type=" | ".join(types))

            for t in types:
                self.convert_type(t)

            return self.add_rule(schema_type, rule)

        elif "enum" in schema:
            enum_values = [self.format_literal(v) for v in schema["enum"]]
            return self.add_rule(name, " | ".join(enum_values))

        elif "const" in schema:
            return self.format_literal(schema["const"])

        return name

    def generate_grammar(self, format_: str ='json') -> str:
        self.handle_schema(self.json_obj, format_)
        self.grammar_entries += [f"{name} ::= {rule}" for name,
                                 rule in self.rules.items()]
        return "\n".join(self.grammar_entries).replace("_", "-")

    @staticmethod
    def verify_grammar(grammar: str) -> str:
        return LlamaGrammar.from_string(grammar)
