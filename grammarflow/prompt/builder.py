from grammarflow.grammars.json import JSON
from grammarflow.grammars.toml import TOML
from grammarflow.grammars.xml import XML


class Prompt:
    def __init__(self, built_prompt, placeholders=[]):
        self.placeholders = placeholders
        self.prompt = built_prompt

    def fill(self, **kwargs):
        filled_prompt = self.prompt

        if kwargs:
            filled_prompt = self.prompt
            for key, value in kwargs.items():
                filled_prompt = filled_prompt.replace(f"{{{key}}}", value)

        return filled_prompt


class PromptBuilder:
    def __init__(self):
        self.sections = []
        self.grammar_set = False
        self.examples_set = False
        self.placeholders = []

    def add_section(
        self, text="", placeholder="", define_grammar=False, remind_grammar=False, add_few_shot_examples=[]
    ):
        type_ = "fixed"
        if placeholder:
            self.placeholders.append(placeholder)
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
                "placeholder": placeholder,
                "define_grammar": define_grammar,
                "remind_grammar": remind_grammar,
                "examples": add_few_shot_examples,
            }
        )

    def get_text(self):
        return " ".join([section["text"] for section in self.sections])

    def build(self, config):
        prompt = ""
        user_prompt = ""  # Track's user's prompt without any grammar additions

        for section in self.sections:
            grammar_instruction = ""

            user_prompt += section["text"] + "\n"

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
                if section["placeholder"] and grammar_instruction:
                    section["text"] = section["text"].replace(
                        f"{{{section['placeholder']}}}",
                        f"{{{section['placeholder']}}}\n" + grammar_instruction + "\n\n" + grammar + reminders[-1],
                    )
                section_text = section["text"]

            if section["examples"] and config["examples"]:
                _, grammar, _ = self.make_format(config.get("format"), config["examples"], None)
                section_text += "\nHere are some examples:\n"
                section_text += f"{grammar}\n"

            prompt += section_text + "\n"

        return Prompt(prompt.strip(), placeholders=self.placeholders)

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
            if len(model_names) > 1:
                instruction = f"Here are the {serialization_type.upper()} output formats you are expected to return your responses in."
                reminders = "\nRETURN {} {}. DO NOT FORGET TO COVER YOUR OUTPUTS WITH '```'".format(
                    response_type, ", ".join(model_names)
                )
            else:
                instruction = f"Here is the {serialization_type.upper()} output format you are expected to return your response in."
                reminders = "\nRETURN {} ONE OF {}. DO NOT FORGET TO COVER YOUR OUTPUTS WITH '```'.".format(
                    response_type, ", ".join(model_names)
                )
        else:
            instruction = None
            reminders = None

        return instruction, grammar, [reminders]
