from grammarflow.grammars.json import JSON
from grammarflow.grammars.toml import TOML
from grammarflow.grammars.xml import XML


class Prompt:
    def __init__(self, built_prompt, placeholders=[], stop_at=""):
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
    def __init__(self):
        self.sections = []
        self.grammar_set = False
        self.examples_set = False
        self.placeholders = []
        self.stop_at = ""

    def add_section(
        self, text="", placeholders=[], define_grammar=False, remind_grammar=False, add_few_shot_examples=[], enable_on=None
    ):
        type_ = "fixed"
        if placeholders and not enable_on:
            self.placeholders.extend(placeholders)
            type_ = "editable"

        if self.grammar_set and define_grammar:
            raise ValueError("Only one section can define the grammar.")
        if remind_grammar and not self.grammar_set:
            raise ValueError("You cannot remind about the grammar without defining it.")

        if define_grammar:
            self.grammar_set = True
        if add_few_shot_examples:
            self.examples_set = True

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

    def get_text(self):
        return " ".join([section["text"] for section in self.sections])

    def build(self, config):
        prompt = ""
        user_prompt = ""  

        for section in self.sections:
            # section["enable_on"] is meant to be a function 
            if section["enable_on"] and not config['enable_on']:
                raise ValueError("You need to provide the inputs to the enable_on functions you've defined in PromptBuilder.")
            elif section["enable_on"] and config['enable_on']:
                if not section["enable_on"](**config['enable_on']):
                    continue
                else: 
                    self.placeholders.extend(section["placeholders"])

            grammar_instruction = ""

            if section["define_grammar"]:
                if "grammars" in config:
                    grammar_instruction, grammar, reminders = self.make_format(
                        config.get("format"), config["grammars"], config["return_sequence"]
                    )

            if section["type"] == "fixed":
                section_text = section["text"]
                if grammar_instruction:
                    section_text += "\n" + grammar_instruction + "\n\n" + grammar + reminders[-1]

            elif section["type"] == "editable":
                if section["placeholders"] and grammar_instruction:
                    for placeholder in section["placeholders"]:
                        section["text"] = section["text"].replace(
                            f"{{{placeholder}}}", f"{{{placeholder}}}\n" + grammar_instruction + "\n\n" + grammar + reminders[-1]
                        )
                section_text = section["text"]

            if section["examples"] and config["examples"]:
                _, grammar, _ = self.make_format(config.get("format"), config["examples"], None)
                section_text += "\nHere are some examples:\n"
                section_text += f"{grammar}\n"

            if section_text: prompt += section_text + "\n"

        return Prompt(prompt.strip(), placeholders=self.placeholders, stop_at=self.stop_at)

    def make_format(self, serialization_type, grammars, return_sequence):
        if serialization_type == "json":
            formatter = JSON
        elif serialization_type == "toml":
            formatter = TOML
        elif serialization_type == "xml":
            formatter = XML
        else:
            formatter = JSON

        grammar, model_names = formatter.make_format(grammars, return_sequence)

        if model_names:
            response_type = "ONLY" if return_sequence == "single_response" else "ALL OF"
            newline = "\\n"
            if len(model_names) > 1:
                instruction = f"Here are the custom output formats you are expected to return your responses in"
                reminders = "\nRETURN {} {}. TERMINALS = Cover output with '```'; End lines with newline. \n".format(
                    response_type, ", ".join(model_names), newline
                )
            else:
                instruction = f"Here is the custom output format you are expected to return your response in."
                reminders = "\nRETURN {} ONE OF {}. TERMINALS = Cover output with '```'; End lines with newline. \n".format(
                    response_type, ", ".join(model_names), newline
                )
        else:
            instruction = None
            reminders = None

        return instruction, grammar, [reminders]    