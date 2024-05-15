from .grammars.json import JSON
from .grammars.toml import TOML
from .grammars.xml import XML
from .grammars.gnbf import GNBF
from .grammars.error import ParsingError, ConfigError  # pylint: disable=unused-import
from .prompt.builder import Prompt, PromptBuilder
from .tools.response import Response

import re 
from typing import Union, Dict, List 
from pydantic import BaseModel 


class Constrain:
    ''' 
    Context Manager initialized using `with` statement. 
    ''' 


    def __init__(self, format_: str ='json', return_sequence: str ='single_response'):
        """ 
        Initializes the Constrain class.

        Args: 
            format_ (str): Serialization type. Default is 'json'.
            return_sequence (str): Return sequence. Default is 'single_response'.
        Returns: 
            Constrain context manager object. 
        """ 

        self.config = {} 
        
        assert format_ in ['json', 'toml', 'xml'], "Serialization type must be one of 'json', 'toml', 'xml'."
        assert return_sequence in ['single_response', 'multi_response'], "Return sequence must be one of 'single_response', 'multi_response'."

        self.config["format"] = format_
        self.config["return_sequence"] = return_sequence

        self.history = {} 
        self.initial_prompt = None
        self.inflation = None
        self.stop_at = ""
        self.idx = 1 

    def get_grammar(self, model: BaseModel) -> str:
        '''
        Pydantic -> GNBF String
        ''' 
        return GNBF(model).generate_grammar(self.config["format"])

    def format(self, prompt: Union[str, PromptBuilder, Prompt], grammars: Union[Dict, List], placeholders: Dict = None, examples: Dict = None, enable_on: Dict = None):
        ''' 
        Formats the prompt with the grammars provided.
        ''' 

        if isinstance(prompt, str):
            prompt_config = PromptBuilder()
            prompt_config.add_section(define_grammar=True)
            prompt_config.add_section(add_few_shot_examples=True)
            prompt_config.add_section(text=prompt)
            prompt = prompt_config
        elif not (isinstance(prompt, PromptBuilder) or isinstance(prompt, Prompt)):
            raise ConfigError("Prompt must be a string, a PromptBuilder or a Prompt object.")

        if not grammars:
            raise ConfigError("You need to provide grammars to format the prompt!")

        if isinstance(grammars, dict): 
            grammars = [grammars]
        elif not isinstance(grammars, list): 
            raise ConfigError("`grammars` must be a dictionary or a list of dictionaries.")

        if examples: 
            if isinstance(examples, dict): 
                examples = [examples]
            elif not isinstance(examples, list): 
                raise ConfigError("`examples` must be a dictionary or a list of dictionaries.")

        if not placeholders:
            placeholders = {}
        else: 
            placeholders = {key: str(value) for key, value in placeholders.items()}

        config = {} 
        config["format"] = self.config["format"]
        config["return_sequence"] = self.config["return_sequence"]
        config["grammars"] = grammars
        config["examples"] = examples
        config["enable_on"] = enable_on

        self.history[self.idx] = {} 
        
        if isinstance(prompt, Prompt):
            if prompt.placeholders and not placeholders:
                raise ConfigError("Since your prompt uses placeholders in the template, you need to provide `placeholders` parameter too! Ensure they have these keys: {prompt.placeholders} in this format - {'placeholder': 'value'}"
                )
            self.history[self.idx]['initial_prompt'] = prompt.prompt
        elif isinstance(prompt, PromptBuilder):
            if placeholders:
                self.history[self.idx]['initial_prompt'] = prompt.get_text() 
            else: 
                self.history[self.idx]['initial_prompt'] = prompt.get_text()
            prompt = prompt.build(config)

        for key, value in placeholders.items():
            if key in prompt.placeholders:
                self.history[self.idx]['initial_prompt'] = self.history[self.idx]['initial_prompt'].replace(f"{{{key}}}", value)

        prompt = prompt.fill(**placeholders)
        
        self.history[self.idx]['filled_prompt'] = prompt

        self.idx += 1

        return prompt 

    def parse(self, return_value: str):
        if not return_value: 
            return None 

        parsed_response = self.parse_helper(return_value)
        return Response(parsed_response)  # Custom class for getting values from response

    def parse_helper(self, return_value: Union[str, List]): # pylint: disable=missing-function-docstring
        if not self.config["format"]:
            raise ConfigError("Serialization type is not set!")

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

    def inflation_rate(self, idx: int = -1):  # pylint: disable=missing-function-docstring
        if idx == -1: idx = self.idx - 1

        import tiktoken  # pylint: disable=import-outside-toplevel

        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

        inflation = {
            "before": len(encoding.encode(self.history[idx]['initial_prompt'])),
            "after": len(encoding.encode(self.history[idx]['filled_prompt'])),
        }

        inflation["factor"] = (
            f"{((inflation['after'] - inflation['before']) / inflation['before']):.1f}x"
        )

        return inflation

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
