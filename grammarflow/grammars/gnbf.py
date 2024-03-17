import json
import re

from llama_cpp import Llama, LlamaGrammar
from pydantic import BaseModel


class GNBF:
    TYPE_RULES = {
        "bool": r'("True" | "False")',
        "number": r'("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)?',
        "integer": r'("-"? ([0-9] | [1-9] [0-9]*))',
        "string": r''' "\"" (
            [^"\\] |
            "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F])
            )* "\""''',
        # 'string': r'"\""   ([^"]*)   "\"" ws',
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
        "toml": [
            r"""
            toml ::= "[" key "]" (key "="  {value})*
            key ::= string
        """,
            ["string", "number", "bool", "none", "array"],
        ],
        "json": [
            r"""
            "{" (key ":" {value} ("," key ":" {value})*)? "}"
            key ::= string
        """,
            ["string", "number", "bool", "none", "array"],
        ],
        "xml": [
            r"""   
        xml ::= "<" tag_name attributes? ">" content "</" tag_name ">"
            tag_name ::= string
            attributes ::= (attribute_name "="  {value})*
            attribute_name ::= string
            content ::= string | xml
        """,
            ["string", "xml", "number", "bool", "none", "array"],
        ],
        "yaml": [
            r"""
            yaml ::= key ":"  {value}
            key ::= string
        """,
            ["string", "number", "bool", "none", "array"],
        ],
    }

    def __init__(self, model: BaseModel):
        self.json_obj = model.schema()
        self.rules = {"ws": r"[ \t\n]*"}
        self.used_data_types = set()
        self.grammar_entries = []

    def sanitize_rule_name(self, name):
        return re.sub(r"[^a-zA-Z0-9-]+", "-", name)

    def add_rule(self, name, definition):
        sanitized_name = self.sanitize_rule_name(name)
        if sanitized_name not in self.rules or self.rules[sanitized_name] == definition:
            self.rules[sanitized_name] = definition
            return sanitized_name

    def format_literal(self, literal):
        if isinstance(literal, str):
            return r'"\"' + literal.replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r") + r"\""
        return json.dumps(literal) + " ws"

    def convert_type(self, json_type):
        if json_type not in self.used_data_types:
            self.used_data_types.add(json_type)
        return json_type

    def handle_schema(self, schema, name="root"):
        if name == "root" and "definitions" in schema:
            for definition_name, definition_schema in schema["definitions"].items():
                self.handle_schema(definition_schema, definition_name)

        if "items" in schema and "$ref" in schema["items"]:
            return schema["items"]["$ref"].split("/")[-1]

        schema_type = schema.get("type")
        if schema_type:
            schema_type = schema_type.lower()

        if not schema_type:
            if "anyOf" in schema:
                types = [self.handle_schema(sub_schema, name) for sub_schema in schema["anyOf"]]

                self.add_rule(name, " | ".join(types))
                return name

        if "properties" in schema and schema_type == "object":
            properties = schema["properties"]
            prop_definitions = []
            for prop, prop_schema in properties.items():
                prop_name = self.format_literal(prop)
                prop_type = self.handle_schema(prop_schema, prop)
                if prop_type == None:
                    print(prop_schema)
                prop_definitions.append(f'{prop_name}:" ws {prop_type}')
            properties_rule = r' "," ws '.join(prop_definitions)
            rule = f'"{{" ws {properties_rule} "}}" ws'
            if name == "root":
                self.grammar_entries.insert(0, f"{self.json_obj['title']} ::= {rule}")
                self.grammar_entries.insert(0, f"{name} ::= {self.json_obj['title']} ws")
            else:
                self.add_rule(name, rule)
        elif schema_type in self.TYPE_RULES:
            self.add_rule(schema_type, self.TYPE_RULES[schema_type])
            return self.convert_type(schema_type)
        elif schema_type in self.OBJECT_RULES:
            rule, types = self.OBJECT_RULES[schema_type]
            rule = rule.format(value=f"{name}-value").strip()

            if "items" in schema and schema["items"]:
                types = [self.handle_schema(schema["items"], name)]
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

    def generate_grammar(self):
        self.handle_schema(self.json_obj)
        self.grammar_entries += [f"{name} ::= {rule}" for name, rule in self.rules.items()]
        return "\n".join(self.grammar_entries).lower().replace("_", "-")

    @staticmethod
    def verify_grammar(grammar: str):
        return LlamaGrammar.from_string(grammar)
