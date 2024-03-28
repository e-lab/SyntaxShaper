from .grammars.json import JSON
from .grammars.toml import TOML
from .grammars.xml import XML
from .grammars.gnbf import GNBF
from .prompt.builder import Prompt, PromptBuilder
from .tools.response import Response

import re 

class Constrain:
    def __init__(self, prompt):
        self.config = {} 
        # Keeps track of last run for inflation_rate()
        self.initial_prompt = None
        self.inflation = None
        self.stop_at = ""

        if isinstance(prompt, str):
            prompt_config = PromptBuilder()
            prompt_config.add_section(define_grammar=True)
            prompt_config.add_section(add_few_shot_examples=True)
            prompt_config.add_section(text=prompt)
            self.prompt = prompt_config
        elif isinstance(prompt, PromptBuilder) or isinstance(prompt, Prompt):
            self.prompt = prompt
            self.stop_at = prompt.stop_at
        else:
            raise ValueError("Prompt must be a string, a PromptBuilder or a Prompt object.")

    def set_config(self, format='json', return_sequence='single_response'):
        self.config["format"] = format
        self.config["return_sequence"] = return_sequence

    def get_grammar(self, model):
        return GNBF(model).generate_grammar(self.config["format"])

    def format_prompt(self, grammars, placeholders=None, examples=None, enable_on=None):
        if not self.prompt:
            raise ValueError("Prompt is not set!")
        if not grammars:
            raise ValueError("You need to provide a list of grammars to format the prompt!")

        self.config["grammars"] = grammars
        self.config["examples"] = examples
        self.config["enable_on"] = enable_on

        if not placeholders:
            placeholders = {}
        else: 
            placeholders = {key: str(value) for key, value in placeholders.items()}

        if isinstance(self.prompt, Prompt):
            if not self.prompt.placeholders:
                raise ValueError(
                    f"Since your prompt uses placeholders in the template, you need to provide `placeholders` too! Ensure they have these keys: {self.prompt.placeholders}."
                )
            self.initial_prompt = self.prompt.prompt
        elif isinstance(self.prompt, PromptBuilder):
            self.initial_prompt = self.prompt.get_text()
            if placeholders:
                self.initial_prompt += " ".join(list([x for x in placeholders.values() if x]))

            self.prompt = self.prompt.build(self.config)

        self.prompt = self.prompt.fill(**placeholders)

    def parse(self, return_value):
        if not return_value: 
            return None 

        if isinstance(return_value, str): return_value = return_value.replace('\\', '') # Removing escape; quite popular in local llms
        try:
            parsed_response = self.parse_helper(return_value)
        except Exception as e:
            print('Unable to parse: ', e)
            return return_value
        try:
            return Response(parsed_response)  # Custom class for getting values from response
        except Exception as e:
            print('Unable to make Response: ', e)
            return parsed_response

    def parse_helper(self, return_value):
        if not self.config["format"]:
            raise ValueError("Serialization type is not set!")

        if isinstance(return_value, str):
            if '```' in return_value:
                return_value = re.sub(r"```.*?\n", "```", return_value, flags=re.DOTALL)
            else: 
                return_value = f"```{return_value}```"
            returned_objects = [
                split_string.replace("\n", "").strip()
                for split_string in return_value.split("```")[1::2]
                if split_string.replace("\n", "").strip()
            ]  # Splitting between terminals and removing empty strings
        else:
            returned_objects = return_value

        # This is done to handle cases where multiple objects are returned seperately, together, and if terminals are not present.
        if len(returned_objects) == 1:
            return_value = returned_objects[0]
            if self.config["format"] == "json":
                return JSON.parse(return_value)
            elif self.config["format"] == "toml":
                return TOML.parse(return_value)
            elif self.config["format"] == "xml":
                return XML.parse(return_value)
        elif not returned_objects:
            return [self.parse([return_value.replace("```", "")])]
        else:
            to_return = []
            for value in returned_objects:
                to_return += [self.parse([value])]
            return to_return

    def inflation_rate(self):
        if self.inflation:
            return self.inflation

        import tiktoken

        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

        self.inflation = {
            "before": len(encoding.encode(self.initial_prompt)),
            "after": len(encoding.encode(self.prompt)),
        }
        self.inflation["factor"] = (
            f"{((self.inflation['after'] - self.inflation['before']) / self.inflation['before']):.1f}x"
        )

        return self.inflation

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
