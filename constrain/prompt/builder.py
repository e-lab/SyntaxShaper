from constrain.grammars.json import JSON 
from constrain.grammars.toml import TOML
from constrain.grammars.xml import XML

class Prompt: 
  def __init__(self, built_prompt): 
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

    def add_fixed_section(self, section_name, text, define_grammar=False, remind_grammar=False, examples=[]):
        """Add a fixed content section."""
        self.sections.append({'type': 'fixed', 'name': section_name, 'text': text, 'define_grammar': define_grammar, 'remind_grammar': remind_grammar, 'examples': examples})

    def add_editable_section(self, section_name, text="", placeholder="", define_grammar=False, remind_grammar=False, examples=[]):
        """Add an editable section with options for dynamic content and placeholders."""
        self.sections.append({
            'type': 'editable',
            'name': section_name,
            'text': text,
            'placeholder': placeholder,
            'define_grammar': define_grammar,
            'remind_grammar': remind_grammar,
            'examples': examples,
        })

    def build(self, config):
        """Construct the prompt by assembling sections."""        
        prompt = ""

        for section in self.sections:
            grammar_instruction = ""
            
            if section['define_grammar']:
              grammar_instruction, grammar, reminders = self.make_format(config.get('serialize', None), config['tasks'], config['return_sequence'])

            if section['type'] == 'fixed':
                section_text = section['text']
                if grammar_instruction:
                    section_text += "\n" + grammar_instruction + '\n\n' + grammar + reminders[-1]
                
            elif section['type'] == 'editable':
                if section['placeholder'] and grammar_instruction:
                    section['text'] = section['text'].replace(f"{{{section['placeholder']}}}", f"{{{section['placeholder']}}}\n" + grammar_instruction + '\n\n' + grammar + reminders[-1])
                section_text = section['text']
                
            prompt += section_text + "\n\n"
        return Prompt(prompt.strip())

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

      if return_sequence == 'single_response':
        instruction = f"Here is the {serialization_type.upper()} output format you are expected to return your response in."
        reminders = "RETURN ONLY ONE OF {0}. DO NOT FORGET TO COVER YOUR OUTPUTS WITH '```'.".format(', '.join(instruct))
      else: 
        instruction = f"Here are the {serialization_type.upper()} output formats you are expected to return your responses in."
        reminders = "RETURN ALL OF {0}. DO NOT FORGET TO COVER YOUR OUTPUTS WITH '```'".format(', '.join(instruct))
      
      return instruction, grammar, [reminders]