from grammarflow.tools.llm import LocalLlama
from grammarflow.constrain import Constrain
from grammarflow.prompt.template import * 
from grammarflow.tools.response import Response
import json, random, time 
from grammarflow.grammars.gnbf import GNBF
from grammars import *
import wikienv, wrappers
import requests


def step(env, action, action_input):
    attempts = 0
    while attempts < 10:
        try:
          if not action: 
            action = " " 
          if not action_input:
            action_input = " "
          if 'search' in action:
            action = 'search'
          elif 'lookup' in action:  
            action = 'lookup'
          elif 'finish' in action:
            action = 'finish'
          else: 
            pass 
          return env.step(f"{action}[{action_input}]")
        except requests.exceptions.Timeout:
          attempts += 1

def check_previous_interaction(id_): return id_ > 1

def save(logs, path):
  with open(f'./results/{path}', 'w') as f: 
    f.write(json.dumps(logs, indent=2))

def make_prompt(model): 
  prompt = PromptBuilder() 
  if model == 'Llama2-70B':
    prompt.add_section('### System:\n') 
  elif model == 'Mistral-7B': 
    prompt.add_section(text="<s>[INST]")
  else: 
    prompt.add_section(text="<s>[INST] <<SYS>>\n")
  prompt.add_section(
    text="""
  {question}

  Your goal is to solve the above QA task in steps. First, think about what information you need to answer the question. You have access to tools as defined below:
  1. "search": to get the information you need from WIKIPEDIA. This is not a search engine. This needs a single keyword or noun as input. 
  2. "lookup": to find more information from the paragraph returned by search. This matches the action_input you give to setences in search. 
  3. "finish": to return your final complete answer as input field. Use this if you believe you have enough information to completely answer the task.""", 
    placeholders=["question"]
  ) 
  prompt.add_section(
    define_grammar=True
  ) 
  # prompt.add_section(
  #   text="Example: \n{example}",
  #   placeholders=["example"]
  # )
  if model == 'Llama2-70B':
    prompt.add_section('\n### User:\n') 
  elif model != 'Mistral-7B': 
    prompt.add_section(text="<</SYS>>")

  prompt.add_section(
    text="Use the below Similar: [] keywords for search. Context: \n{history}",
    placeholders=["history"],
    enable_on=check_previous_interaction
  ) 
  prompt.add_section(
    text="Create the next [Step] {id_} using the information available above: ", 
    placeholders=["id_"]
  )
  if model == 'Llama2-70B':
    prompt.add_section('\n### Assistant:\n') 
    prompt.stop_at = "### Assistant:"
  else: 
    prompt.add_section(text="[/INST]")
    prompt.stop_at = "[/INST]"
  return prompt 

def make_example(): 
  to = "" 
  to += f"Question: {example['question']}\n"
  for i, step in enumerate(example['steps'], 1):
    if 'observation' not in step:
          step = {**step, 'observation': ''}
    to += f"""thought: {step['thought']}\naction: {step['action']}\naction_input: {step['action_input']}\nObservation: {step['observation']}\n"""
  return to


# Helper functions 
def load_history(history: dict): 
  return "\n".join([f"""Observation {id_}: {value['observation']}"""
   for id_, value in history.items()])

def log_step(response, observation, id_, to_print=True): 
  if to_print:
    print('--------------------------')
    print('Step {}'.format(id_))
    print('Thought:', response.Step.thought)
    print('Action:', response.Step.action)
    print('Action Input:', response.Step.action_input)
    print('Observation:', observation)
    print('--------------------------')

def webthink(model_name, llm, idx=None, env=None, to_print=False): 
  # Initializing Stateful vars
  thought = None 
  action = None
  observation = None
  id_ = 1
  history, history_ = {}, None
  n_calls, n_goodcalls, n_badcalls = 0, 0, 0

  # Initializing question
  question = env.reset(idx=idx)
  print(question)

  for i in range(7):
    if history:
      history_ = load_history(history) # Initializes history every run 

    # The only major change we've made! 
    with Constrain('json') as manager: 
      template = make_prompt(model_name)
      prompt = manager.format(template, 
        placeholders={ 
          "question": question,
          "history": history_, 
          "example": make_example() , 
          "id_": str(id_), 
        }, 
        grammars=[{
          'description': 'Your thinking state', 
          'model': Step
        }], 
        enable_on={
          'id_':id_ 
        }
      ) 
    
      # print(manager.prompt)
      if len(manager.prompt.split()) > 2000:
        print('Prompt too long. Breaking.')
        done = False 
        break
      response = llm(prompt, grammar=manager.get_grammar(Step), stop_at=template.stop_at)
      n_calls += 1

      resp_ = response

      try: 
        response = manager.parse(response)
        observation, r, done, info = step(env, response.Step.action, response.Step.action_input)
        n_goodcalls += 1
        observation = observation.replace("\\n", " ")

        history[id_] = { 
          "thought": response.Step.thought, 
          "action": response.Step.action, 
          "action_input": response.Step.action_input, 
          "observation": observation
        }
      except Exception as e:
        print(e)
        print(resp_)
        n_badcalls += 1
        observation, done = "Error in parsing. Follow the <Step> format and try again.", False 
        history[id_] = { 
          "thought": "", 
          "action": "Error", 
          "action_input": "Error", 
          "observation": observation
        }

    log_step(response, observation, id_, to_print=to_print)

    print(f'Step {id_}: n_calls: {n_calls}, n_goodcalls: {n_goodcalls}, n_badcalls: {n_badcalls}')
    
    id_ += 1

    if done: 
      break 

  if not done:
      final = "Failed"
      observation, r, done, info = step(env, "finish", "[]")

  info.update({'n_calls': n_calls, 'n_goodcalls': n_goodcalls, 'n_badcalls': n_badcalls, 'steps': id_, 'history': history})

  return r, info

if __name__ == '__main__':
  env = wikienv.WikiEnv()
  env = wrappers.HotPotQAWrapper(env, split="dev")
  env = wrappers.LoggingWrapper(env)
  example = wrappers.EXAMPLE 

  models = { 
    'Mistral-7B': LocalLlama(gguf_path='/depot/euge/data/araviki/llama/gguf/mistral-7b-instruct-v0.2.Q5_K_M.gguf', llama_cpp_path='/depot/euge/data/araviki/llama/llama.cpp'), 
    'CodeLlama2-13B': LocalLlama(gguf_path='/depot/euge/data/araviki/llama/gguf/codellama-13b-instruct.Q5_K_M.gguf', llama_cpp_path='/depot/euge/data/araviki/llama/llama.cpp'), 
    # 'Llama2-70B': LocalLlama(gguf_path='/depot/euge/data/araviki/llama/gguf/upstage-llama-2-70b-instruct-v2.Q5_K_M.gguf', llama_cpp_path='/depot/euge/data/araviki/llama/llama.cpp')
  }
  logs = {} 

  idxs = list(range(200))
  random.Random(165).shuffle(idxs)

  for model_name, llm in models.items():
    print(f'Running for {model_name}')
    rs = []
    infos = [] 
    bad_calls = 0
    for i in idxs:
        old_time = time.time()
        r, info = webthink(model_name, llm, i, env, to_print=False)
        rs.append(info['em'])
        bad_calls += info['n_badcalls']
        save(info, f'{model_name}_{i}.json')
        infos.append(info)
        print('RESULTS: ', sum(rs), len(rs), sum(rs) / len(rs), (time.time() - old_time) / len(rs))
        print('--------------------------')
        print()

