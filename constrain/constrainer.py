from constrain.prompt.builder import Prompt, PromptBuilder
from constrain.grammars.json import JSON
from constrain.grammars.toml import TOML
from constrain.grammars.xml import XML


class Constrainer:
    def __init__(self, prompt):
        self.config = {}
        if isinstance(prompt, str):
            prompt_config = PromptBuilder()
            prompt_config.add_section(define_grammar=True)
            prompt_config.add_section(text=prompt)
            self.prompt = prompt_config
        elif isinstance(prompt, PromptBuilder) or isinstance(prompt, Prompt):
            self.prompt = prompt
        else:
            raise ValueError(
                'Prompt must be a string, a PromptBuilder or a Prompt object.')

        # Keeps track of last run for inflation_rate()
        self.user_prompt = None
        self.filled_prompt = None
        self.inflation = None

    def set_config(self, format, return_sequence):
        self.config['format'] = format
        self.config['return_sequence'] = return_sequence

    def format_prompt(self, tasks, placeholders=None, examples=None):
        if not self.prompt:
            raise ValueError('Prompt is not set!')
        if not tasks:
            raise ValueError(
                'You need to provide a list of tasks to format the prompt!')

        self.config['tasks'] = tasks
        self.config['examples'] = examples

        if not placeholders:
            placeholders = {}

        print('Prompt is ', type(self.prompt))
        if isinstance(self.prompt, Prompt):
            if not self.prompt.placeholders:
                raise ValueError(
                    f'If your prompt uses placeholders in the template, you need to provide `placeholders` too! Ensure they have these keys: {self.prompt.placeholders}.')
            self.user_prompt = filled_prompt = self.prompt.fill(**placeholders)
        elif isinstance(self.prompt, PromptBuilder):
            built_prompt, self.user_prompt = self.prompt.build(self.config)
            self.user_prompt = self.user_prompt.fill(**placeholders)
            filled_prompt = built_prompt.fill(**placeholders)

        self.prompt = self.filled_prompt = filled_prompt

    def parse(self, return_value):
        if not self.config['format']:
            raise ValueError('Serialization type is not set!')

        if isinstance(return_value, str):
            return_value = return_value.replace('json', '').replace('xml', '').replace('toml', '')
            returned_objects = [bru.replace('\n', '') for bru in return_value.split('```')[
                1::2] if bru.replace('\n', '').strip()]
        else:
            returned_objects = return_value

        if len(returned_objects) == 1:
            return_value = returned_objects[0]
            if self.config['format'] == 'json':
                return JSON.parse(return_value)
            elif self.config['format'] == 'toml':
                return TOML.parse(return_value)
            elif self.config['format'] == 'xml':
                return XML.parse(return_value)
        elif not returned_objects:
            return [self.parse([return_value.replace('```', '')])]
        else:
            to_return = []
            for value in returned_objects:
                to_return += [self.parse([value])]
            return to_return

    def inflation_rate(self):
        if self.inflation:
            if self.inflation['prompt'] == self.filled_prompt:
                return {k: v for k, v in self.inflation.items() if k not in "prompt"}

        import tiktoken

        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

        def get_count(text):
            return len(encoding.encode(text))

        self.inflation = {
            'before': get_count(self.user_prompt),
            'after':  get_count(self.filled_prompt),
        }

        self.inflation['factor'] = f"{((self.inflation['after'] - self.inflation['before']) / self.inflation['before']):.1f}x"
        self.inflation['prompt'] = self.filled_prompt

        return {k: v for k, v in self.inflation.items() if k not in "prompt"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
