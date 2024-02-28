from constrain.prompt.builder import Prompt, PromptBuilder
from constrain.grammars.json import JSON
from constrain.grammars.toml import TOML
from constrain.grammars.xml import XML

class Constrainer:
    def __init__(self):
        self.config = {}
        self.prompt = None

    def track_prompt(self, prompt):
        self.prompt = prompt

    def set_config(self, serialize, tasks, return_sequence):
        self.config['serialize'] = serialize
        self.config['tasks'] = tasks
        self.config['return_sequence'] = return_sequence

    def format_prompt(self, variables = None):
        if not self.prompt:
            raise ValueError('Prompt is not set!')
        
        if isinstance(self.prompt, Prompt): 
            if not variables: 
                raise ValueError('If providing `prompt_template`, you need to provide `variables` too!')
            filled_prompt = self.prompt.fill(**variables)
        elif isinstance(self.prompt, PromptBuilder):
            filled_prompt = self.prompt.build(self.config).fill(**variables)
        elif isinstance(self.prompt, str): 
            prompt_config = PromptBuilder() 
            prompt_config.add_editable_section('grammar', text="{grammar}", placeholder='grammar', define_grammar=True)
            prompt_config.add_editable_section('user_query', text="{query}", placeholder='query')
            filled_prompt = prompt_config.build(self.config).fill(grammar="", query=self.prompt)
        self.prompt = filled_prompt
    
    def parse(self, return_value): 
        if not self.config['serialize']:
            raise ValueError('Serialization type is not set!')

        if isinstance(return_value, str):
            returned_objects = [bru.replace('\n', '') for bru in return_value.split('```')[1::2] if bru.replace('\n', '').strip()]
        else: 
            returned_objects = return_value

        if len(returned_objects) == 1:
            return_value = returned_objects[0]
            print('return value', return_value)
            if self.config['serialize'] == 'json':
                return JSON.parse(return_value)
            elif self.config['serialize'] == 'toml':
                return TOML.parse(return_value)
            elif self.config['serialize'] == 'xml':
                return XML.parse(return_value)
        elif not returned_objects:
            return [self.parse([return_value.replace('```', '')])]
        else:
            to_return = []
            for value in returned_objects: 
                to_return += [self.parse([value])]
            return to_return

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass 