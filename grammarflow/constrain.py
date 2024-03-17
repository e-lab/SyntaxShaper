from grammarflow.grammars.json import JSON
from grammarflow.grammars.toml import TOML
from grammarflow.grammars.xml import XML
from grammarflow.prompt.builder import Prompt, PromptBuilder
from grammarflow.tools.response import Response


class Constrain:
    def __init__(self, prompt):
        self.config = {"format": "json", "return_sequence": "single_response"}
        # Keeps track of last run for inflation_rate()
        self.initial_prompt = None
        self.inflation = None

        if isinstance(prompt, str):
            prompt_config = PromptBuilder()
            prompt_config.add_section(define_grammar=True)
            prompt_config.add_section(add_few_shot_examples=True)
            prompt_config.add_section(text=prompt)
            self.prompt = prompt_config
        elif isinstance(prompt, PromptBuilder) or isinstance(prompt, Prompt):
            self.prompt = prompt
        else:
            raise ValueError("Prompt must be a string, a PromptBuilder or a Prompt object.")

    def set_config(self, format, return_sequence):
        self.config["format"] = format
        self.config["return_sequence"] = return_sequence

    def format_prompt(self, grammars, placeholders=None, examples=None):
        if not self.prompt:
            raise ValueError("Prompt is not set!")
        if not grammars:
            raise ValueError("You need to provide a list of grammars to format the prompt!")

        self.config["grammars"] = grammars
        self.config["examples"] = examples

        if not placeholders:
            placeholders = {}

        if isinstance(self.prompt, Prompt):
            if not self.prompt.placeholders:
                raise ValueError(
                    f"Since your prompt uses placeholders in the template, you need to provide `placeholders` too! Ensure they have these keys: {self.prompt.placeholders}."
                )
            self.initial_prompt = self.prompt.prompt
        elif isinstance(self.prompt, PromptBuilder):
            self.initial_prompt = self.prompt.get_text()
            if placeholders:
                self.initial_prompt += " ".join(list(placeholders.values()))

            self.prompt = self.prompt.build(self.config)

        self.prompt = self.prompt.fill(**placeholders)

    def parse(self, return_value):
        parsed_response = self.parse_helper(return_value)
        try:
            return Response(parsed_response)  # Custom class for getting values from response
        except:
            return parsed_response

    def parse_helper(self, return_value):
        if not self.config["format"]:
            raise ValueError("Serialization type is not set!")

        if isinstance(return_value, str):
            return_value = (
                return_value.replace("```json", "```").replace("```xml", "```").replace("```toml", "```")
            )  # Sometimes, name is added next to the terminals
            returned_objects = [
                split_string.replace("\n", "")
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
