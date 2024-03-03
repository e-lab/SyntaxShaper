from constrain.grammars.json import JSON 
from constrain.grammars.toml import TOML
from constrain.grammars.xml import XML

class Prompt: 
  def __init__(self, built_prompt, placeholders=[]):
    self.placeholders = placeholders 
    self.prompt = built_prompt
  
  def fill(self, **kwargs):
      """Fill placeholders in the prompt with actual values after the prompt has been built."""
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
      
    def add_section(self, text='', placeholder='', define_grammar=False, remind_grammar=False, add_few_shot_examples=[]):
      type_ = 'fixed'
      if placeholder:
        self.placeholders.append(placeholder)
        type_ = 'editable'
      
      if self.grammar_set and define_grammar: 
        raise ValueError("Only one section can define the grammar.")
      if remind_grammar and not self.grammar_set:
        raise ValueError("You cannot remind about the grammar without defining it.")

      if define_grammar:
        self.grammar_set = True
      if add_few_shot_examples:
        self.examples_set = True
      
      self.sections.append({'type': type_, 'text': text, 'placeholder': placeholder, 'define_grammar': define_grammar, 'remind_grammar': remind_grammar, 'examples': add_few_shot_examples})

    def build(self, config):
        prompt = ""
        user_prompt = "" # Track's user's prompt without any grammar additions 

        for section in self.sections:
            grammar_instruction = ""

            user_prompt += section['text'] + "\n"
            
            if section['define_grammar']:
              if 'tasks' in config:
                grammar_instruction, grammar, reminders = self.make_format(config.get('format', None), config['tasks'], config['return_sequence'])

            if section['type'] == 'fixed':
                # print('section', section)
                section_text = section['text']
                # print('grammar', grammar_instruction, grammar, reminders)
                if grammar_instruction:
                    section_text += "\n" + grammar_instruction + '\n\n' + grammar + reminders[-1]
                
            elif section['type'] == 'editable':
                # print('section', section)
                if section['placeholder'] and grammar_instruction:
                    section['text'] = section['text'].replace(f"{{{section['placeholder']}}}", f"{{{section['placeholder']}}}\n" + grammar_instruction + '\n\n' + grammar + reminders[-1])
                section_text = section['text']
              
            if 'examples' in section and section['examples']:
                _, grammar, _ = self.make_format(config.get('format', None), config['examples'], None)
                section_text += "Here are some examples:\n"
                section_text += f"{grammar}\n"
                
            prompt += section_text + "\n"

        return Prompt(prompt.strip(), placeholders=self.placeholders), Prompt(user_prompt.strip())

    def make_format(self, serialization_type, tasks, return_sequence):
      if serialization_type == 'json':
        formatter = JSON 
      elif serialization_type == 'toml':
        formatter = TOML
      elif serialization_type == 'xml':
        formatter = XML
      else: 
        formatter = JSON

      grammar, instruct = formatter.make_format(tasks, return_sequence)

      if instruct:
        if return_sequence == 'single_response':
          # print(instruct)
          instruction = f"Here is the {serialization_type.upper()} output format you are expected to return your response in."
          reminders = "RETURN ONLY ONE OF {0}. DO NOT FORGET TO COVER YOUR OUTPUTS WITH '```'.".format(', '.join(instruct))
        else: 
          instruction = f"Here are the {serialization_type.upper()} output formats you are expected to return your responses in."
          reminders = "RETURN ALL OF {0}. DO NOT FORGET TO COVER YOUR OUTPUTS WITH '```'".format(', '.join(instruct))
      else: 
        instruction = None 
        reminders = None
      
      return instruction, grammar, [reminders]