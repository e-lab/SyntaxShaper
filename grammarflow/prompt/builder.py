from grammarflow.grammars.json import JSON
from grammarflow.grammars.toml import TOML
from grammarflow.grammars.xml import XML
from grammarflow.grammars.error import ConfigError

from typing import Dict, List, Any


class Prompt:
    """
    Dataclass to store the built prompt.
    """

    def __init__(
            self,
            built_prompt: str,
            placeholders: List = None,
            stop_at: str = ""):
        self.placeholders = placeholders
        self.prompt = built_prompt
        self.stop_at = stop_at

    def fill(self, **kwargs):
        filled_prompt = self.prompt

        if kwargs:
            for key, value in kwargs.items():
                if key in self.placeholders:
                    filled_prompt = filled_prompt.replace(f"{{{key}}}", value)

        return filled_prompt


class PromptBuilder:
    """
    Interface to build Prompts
    Allows for building prompts with multiple sections, placeholders, grammars, and examples.
    Use `enable_on` to conditionally enable sections based on the inputs provided.
    """

    def __init__(self):
        self.sections = []
        self.grammar_set = False
        self.examples_set = False
        self.placeholders = []
        self.stop_at = ""

    # pylint: disable=missing-function-docstring
    def add_section(
            self,
            text: str = "",
            placeholders: List = None,
            define_grammar: bool = False,
            remind_grammar: bool = False,
            add_few_shot_examples: List = None,
            enable_on: Any = None):
        assert isinstance(text, str), "`text` needs to be a `str` type"

        if placeholders: 
            if isinstance(placeholders, str):
                placeholders = [placeholders]
            assert isinstance(
                placeholders, list), "`placeholders` needs to be a `list` type"

        # Marking which sections can be edited by grammarflow
        if placeholders and not enable_on:
            self.placeholders.extend(placeholders)
            type_ = "editable"
        else:
            type_ = "fixed"

        if self.grammar_set and define_grammar:  # Only one section can define the grammar
            raise ConfigError("Only one section can define the grammar.")

        # Reminders were an experimental section, read below. TODO: [Add link
        # from below here.]
        if remind_grammar and not self.grammar_set:
            raise ConfigError(
                "You cannot remind about the grammar without defining it.")

        if define_grammar:
            self.grammar_set = True  # We want grammar to be defined here
        if add_few_shot_examples:
            self.examples_set = True  # We want examples to be added here

        self.sections.append(
            {
                "type": type_,
                "text": text,
                "placeholders": placeholders,
                "define_grammar": define_grammar,
                "remind_grammar": remind_grammar,
                "examples": add_few_shot_examples,
                "enable_on": enable_on
            }
        )

    def get_text(self):  # pylint: disable=missing-function-docstring
        return " ".join([section["text"] for section in self.sections])

    def build(self, config: Dict) -> Prompt:
        '''
        Builds the prompt using the current `config`. Not stateful.
        '''

        prompt = ""

        for section in self.sections:
            # section["enable_on"] must be a function
            if section["enable_on"] and not config['enable_on']:
                raise ConfigError(
                    "You need to provide the inputs to the `enable_on` functions you've defined in PromptBuilder.")
            elif section["enable_on"] and config['enable_on']:
                if not section["enable_on"](**config['enable_on']):
                    continue
                else:
                    self.placeholders.extend(section["placeholders"])

            grammar_instruction, grammar, reminders = "", "", []
            section_text = section["text"]

            # If the section is supposed to define the grammar, we need to
            # extract the grammar from the config
            if section["define_grammar"]:
                if "grammars" in config:
                    grammar_instruction, grammar, reminders = self.make_format(
                        config["grammars"], config.get("format"), config["return_sequence"])

            # If it's fixed, we don't do anything, except grammar addition.
            if section["type"] == "fixed":
                if grammar_instruction:
                    section_text += "\n" + grammar_instruction + \
                        "\n\n" + grammar + reminders[-1]

            # If it's editable, there will be placeholders we can play with.
            # grammar addition can happen here too, but will be placed after
            # placeholder is replaced.
            elif section["type"] == "editable":
                if section["placeholders"]:
                    for placeholder in section["placeholders"]:
                        if grammar: 
                            section_text = section_text.replace(
                                f"{{{placeholder}}}", f"{{{placeholder}}}\n" + grammar_instruction + "\n\n" + grammar + reminders[-1]
                            )
                        else: 
                            section_text = section_text.replace(
                                f"{{{placeholder}}}", f"{{{placeholder}}}\n"
                            )
            
            if section["examples"] and config["examples"]:
                _, grammar, _ = self.make_format(
                    config["examples"], config.get("format"), None)
                section_text += "\n Here is an example:\n"
                section_text += f"{grammar}\n"

            if section_text:
                prompt += section_text + "\n"

        return Prompt(
            prompt.strip(),
            placeholders=self.placeholders,
            stop_at=self.stop_at)

    def make_format(self,
                    grammars: Dict,
                    serialization_type: str = 'json',
                    return_sequence: str = 'single_response') -> List[Any]:

        # Decide which formatter
        if serialization_type == "json":
            formatter = JSON
        elif serialization_type == "toml":
            formatter = TOML
        elif serialization_type == "xml":
            formatter = XML

        grammar, model_names = formatter.make_format(grammars, return_sequence)

        if model_names:
            response_type = "ONLY" if return_sequence == "single_response" else "ALL OF"

            # `reminders` was an idea to test how repeated reminders would help with increasing context size
            # did not find improvement, but keeping it here for future
            # reference
            if len(model_names) > 1:
                instruction = "Here are the custom output formats you are expected to return your responses in"
                reminders = f"\nRETURN {response_type} {", ".join(
                    model_names)}. TERMINALS = Cover output with '```'; End lines with '\n'. \n"
            else:
                instruction = "Here is the custom output format you are expected to return your response in."
                reminders = f"\nRETURN {response_type} ONE OF {", ".join(
                    model_names)}. TERMINALS = Cover output with '```'; End lines with '\n'. \n"
        else:
            instruction = None
            reminders = None

        return instruction, grammar, [reminders]
