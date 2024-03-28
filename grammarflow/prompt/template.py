from .builder import Prompt, PromptBuilder

def Llama2Instruct(size='70B'): 
  if size != '70B':
    prompt = PromptBuilder()
    prompt.add_section(text="<s>[INST] <<SYS>>\n{instructions}", placeholders=["instructions"], define_grammar=True)
    prompt.add_section(add_few_shot_examples=True)
    prompt.add_section(text="<</SYS>>")
    prompt.add_section(text="{prompt}[/INST]", placeholders=["prompt"])
    prompt.stop_at = "[/INST]"
  else: 
    prompt = PromptBuilder()
    prompt.add_section(text="### System:\n{instructions}\n", placeholders=["instructions"], define_grammar=True)
    prompt.add_section(add_few_shot_examples=True)
    prompt.add_section(text="### User:\n{prompt}\n", placeholders=["prompt"])
    prompt.add_section(text="### Assistant:\n")  
    prompt.stop_at = "### Assistant:"
  return prompt

def Mistral(**kwargs): 
  prompt = PromptBuilder()
  prompt.add_section(text="<s>[INST] {instructions}", placeholders=['instructions'], define_grammar=True)
  prompt.add_section(add_few_shot_examples=True)
  prompt.add_section(text="{prompt} [/INST]", placeholders=['prompt'])
  prompt.stop_at = "[/INST]"
  return prompt

def Mixtral(): 
  prompt = PromptBuilder()
  prompt.add_section(text="SYSTEM: {instructions}", placeholders=['instructions'], define_grammar=True)
  prompt.add_section(text="USER: {prompt}", placeholders=['prompt'])
  prompt.add_section(add_few_shot_examples=True)
  prompt.add_section(text="ASSISTANT:")
  return prompt

def ChatML(): 
  prompt = PromptBuilder()
  prompt.add_section(text="<|im_start|>system\n{system_message}", placeholders=['system_message'], define_grammar=True)
  prompt.add_section(add_few_shot_examples=True)  
  prompt.add_section(text="<|im_end|>")
  prompt.add_section(text="<|im_start|>user\n{prompt}<|im_end|>", placeholders=['prompt'])
  prompt.add_section(text="<|im_start|>assistant") 
  return prompt

def ZeroShot(): 
  prompt = PromptBuilder()
  prompt.add_section(text="Your role: {instructions}", placeholders=['instructions'])
  prompt.add_section(define_grammar=True)
  prompt.add_section(text="{prompt}", placeholders=['prompt'])
  return prompt

def FewShot(): 
  prompt = PromptBuilder()
  prompt.add_section(text="Your role: {instructions}", placeholders=['instructions'])
  prompt.add_section(define_grammar=True)
  prompt.add_section(add_few_shot_examples=True)
  prompt.add_section(text="{prompt}", placeholders=['prompt'])
  return prompt

def Agent(enable): 
  prompt = PromptBuilder()
  prompt.add_section(text="Your role: {instructions}", placeholders=['instructions'])
  prompt.add_section(define_grammar=True)
  prompt.add_section(text="Your goal: {prompt}", placeholders=['prompt'])
  prompt.add_section(text="Below is the history of the conversation so far: {history}", placeholders=['history'], enable_on=enable)
  return prompt

def ChainOfThought(**kwargs): 
  prompt = PromptBuilder()
  prompt.add_section(text="You are a professor of various practices. You like to think through the steps you take in solving your goal. You will be presented with a 'goal'. Solve it by iteratively making observations.")
  prompt.add_section(define_grammar=True)
  prompt.add_section(text="Your 'goal': {prompt}", placeholders=['prompt'])
  return prompt

def Instruction(): 
  prompt = PromptBuilder()
  prompt.add_section(text="Here are your Instructions: {instructions}", placeholders=['instructions'])
  prompt.add_section(define_grammar=True)
  prompt.add_section(add_few_shot_examples=True)
  prompt.add_section(text="{prompt}", placeholders=['prompt'])
  return prompt
