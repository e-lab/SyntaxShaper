from grammarflow.tools.llm import LocalLlama
from grammarflow.constrain import Constrain
from grammarflow.prompt.template import * 
from grammarflow.grammars.template import *
from grammarflow.tools.response import Response
import pandas as pd
import json 

n = 200

def check_response(response, example, only_structure=True):
  for key, value in example.items(): 
    try: 
      assert hasattr(response, key), f"Response does not have attribute {key}"
      if not isinstance(getattr(response, key), Response): assert isinstance(getattr(response, key), type(example[key])), f"Response attribute {key} is not of type {type(example[key])}"
      if isinstance(example[key], dict): 
        assert check_response(getattr(response, key), example[key]) == True
    except AssertionError as e: 
      print(e) 
      return False
  return True

def save(logs, path):
  with open(f'./results/{path}', 'w') as f: 
    f.write(json.dumps(logs, indent=2))

def load(path):
  try: 
    with open(f'./results/{path}', 'r') as f: 
      a = json.load(f)
    return a
  except: 
    return None

def RandomTrue(model_name, get_prompt, llm, verbose=False, **kwargs):
  file_ = json.load(open('./data/345_random_true.json'))

  count = 1

  logs = load(f'{model_name}.json')
  if not logs: 
    logs = {'n_badcalls': 0, 'n_calls': 0, 'n_goodcalls': 0, 'n_matchedcall': 0, 'answer': [], 'gt': []}
  
  already_complete = logs['n_calls']

  for example_ in list(file_.keys()):  
    for example__ in file_[example_]:

      if count < already_complete:
        count += 1
        continue

      row = file_[example_][example__]
      
      with Constrain(get_prompt(**kwargs)) as manager: 
        manager.set_config(
          format='json'
        )
        manager.format_prompt(
          placeholders={
            "instructions": "You are a professor of various practices. You like to think through the steps you take in solving your goal. You will be presented with a 'goal'. Solve it by iteratively making observations.",
            "prompt": f"Facts: {row['question']}\n Goal: {row['query']}"
          },
          grammars=[{
            'description': 'Response', 
            'model': CoT
          }],
        )

        if verbose: 
          print(manager.prompt)
          print('-------------------')
        response = llm(manager.prompt, grammar=manager.get_grammar(CoT), stop_at=manager.stop_at)
        if response: 
          if verbose:
            print(response)
            print('-------------------')
          logs['n_calls'] += 1
          response = manager.parse(response)
          if verbose:
            print(response)
            print('-------------------')
          if isinstance(response, Response):
            logs['n_goodcalls'] += 1
          else: 
            with open(f'./results/{model_name}_error.txt', 'a') as f: 
              f.write(f'{row["question"]}\n{row["query"]}\n{response}\n\n')
              f.write('-------------------\n')
            logs['n_badcalls'] += 1
            
          del row['question'], row['query']
          answer = None 

          row['answer'] = eval(row['answer'])
          if check_response(response, {'CoT': row}): 
            logs['n_matchedcall'] += 1
            answer = response.CoT.answer
        else:
          answer = None 
          continue
        
      print(f'Step {count}: [result: {answer}, expected: {row['answer']}, n_goodcalls: {logs["n_goodcalls"]}, n_badcalls: {logs["n_badcalls"]}, n_matchedcall: {logs["n_matchedcall"]}]')
      logs['answer'].append(answer)
      logs['gt'].append(row['answer'])
      
      save(logs, f'{model_name}.json')

      count += 1

      if count > n: 
        return logs 

  return logs 


if __name__ == '__main__':
  models = { 
    # 'Mistral-7B': (Mistral, LocalLlama(gguf_path='/depot/euge/data/araviki/llama/gguf/mistral-7b-instruct-v0.2.Q5_K_M.gguf', llama_cpp_path='/depot/euge/data/araviki/llama/llama.cpp'), {'ignore':True}), 
    # 'CodeLlama2-13B': (Llama2Instruct, LocalLlama(gguf_path='/depot/euge/data/araviki/llama/gguf/codellama-13b-instruct.Q5_K_M.gguf', llama_cpp_path='/depot/euge/data/araviki/llama/llama.cpp'), {'size':'13B'}), 
    'Llama2-70B': (Llama2Instruct, LocalLlama(gguf_path='/depot/euge/data/araviki/llama/gguf/upstage-llama-2-70b-instruct-v2.Q5_K_M.gguf', llama_cpp_path='/depot/euge/data/araviki/llama/llama.cpp'), {'size':'70B'})
  }

  logs = {} 

  for model_name, meta in models.items():
    (get_prompt, llm, kwargs_)  = meta 
    print(f'Running for {model_name}')
    logs[model_name] = {} 
    logs[model_name]['RandomTrue'] = RandomTrue(model_name, get_prompt, llm, verbose=False, **kwargs_)
    print('-------------------')
  
  print('-------------------------')
  print(json.dumps(logs, indent=2))
  print('-------------------------')


