from grammarflow.tools.llm import LocalLlama
from grammarflow.constrain import Constrain
from grammarflow.prompt.template import * 
from grammarflow.tools.response import Response
import json 
from grammarflow.grammars.gnbf import GNBF
from grammars import *

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

def StrategyQA(model_name, get_prompt, llm, verbose=False, **kwargs):
  file_ = json.load(open('./data/strategy_qa.json'))

  logs = {'n_badcalls': 0, 'n_calls': 0, 'n_goodcalls': 0, 'n_matchedcall': 0, 'responses': [], 'expected': []}

  for ind, example in enumerate(file_['examples'][:n]): 
    with Constrain(get_prompt(**kwargs)) as manager: 
      manager.set_config(
        format='xml'
      )
      manager.format_prompt(
        placeholders={
          "instructions": file_['description'],
          "prompt": example['input']
        },
        grammars=[{
          'description': 'Response', 
          'model': StrategyQAModel
        }],
      )

      if verbose: 
        print(manager.prompt)
        print('-------------------')
      response = llm(manager.prompt, grammar=manager.get_grammar(StrategyQAModel), stop_at=manager.stop_at)
      if response: 
        if verbose:
          print(response)
          print('-------------------')
        logs['responses'].append(response)
        logs['n_calls'] += 1
        response = manager.parse(response)
        if verbose:
          print(response)
          print('-------------------')
        if isinstance(response, Response):
          logs['n_goodcalls'] += 1
        else: 
          logs['n_badcalls'] += 1
          
        del example['input']
        logs['expected'].append({'StrategyQAModel': example})

        if check_response(response, {'StrategyQAModel': example}): 
          logs['n_matchedcall'] += 1
      else:
        continue

    print(f'Step {ind}: [n_goodcalls: {logs["n_goodcalls"]}, n_badcalls: {logs["n_badcalls"]}, n_matchedcall: {logs["n_matchedcall"]}]')
    save(logs, f'{model_name}_stategyqa.json')

  return logs

def LogicGridPuzzle(model_name, get_prompt, llm, verbose=False, **kwargs):
  file_ = json.load(open('./data/logic_grid_puzzle.json'))

  logs = {'n_badcalls': 0, 'n_calls': 0, 'n_goodcalls': 0, 'n_matchedcall': 0, 'responses': [], 'expected': []} 

  for ind, example in enumerate(file_['examples'][:n]): 
    with Constrain(get_prompt(**kwargs)) as manager: 
      manager.set_config(
        format='xml'
      )
      manager.format_prompt(
        placeholders={
          "instructions": file_['description'],
          "prompt": example['input']
        },
        grammars=[{
          'description': 'Response', 
          'model': LogicGridPuzzleModel
        }],
      )

      if verbose: 
        print(manager.prompt)
        print('-------------------')
      response = llm(manager.prompt, grammar=manager.get_grammar(LogicGridPuzzleModel), stop_at=manager.stop_at)
      if response: 
        if verbose:
          print(response)
          print('-------------------')
        logs['responses'].append(response)
        logs['n_calls'] += 1
        response = manager.parse(response)
        if verbose:
          print(response)
          print('-------------------')
        if isinstance(response, Response):
          logs['n_goodcalls'] += 1
        else: 
          logs['n_badcalls'] += 1
          
        del example['input']
        logs['expected'].append({'LogicGridPuzzleModel': example})

        # Response object always uses Model name at the topmost level. This is required for context-based multi-TOML parsing.
        # I'm adding 'h' to the keys to match the model. Pydantic doesn't let me allot numbers as field names. 
        if check_response(response, {'LogicGridPuzzleModel': example}): 
          logs['n_matchedcall'] += 1
      else: 
        continue 

    print(f'Step {ind}: [n_goodcalls: {logs["n_goodcalls"]}, n_badcalls: {logs["n_badcalls"]}, n_matchedcall: {logs["n_matchedcall"]}]')

    save(logs, f'{model_name}_logicgridpuzzle.json')

  return logs

def PhysicsQuestions(model_name, get_prompt, llm, verbose=False, **kwargs):
  file_ = json.load(open('./data/physics_questions.json'))

  logs = {'n_badcalls': 0, 'n_calls': 0, 'n_goodcalls': 0, 'n_matchedcall': 0, 'responses': [], 'expected': []} 

  for ind, example in enumerate(file_['examples'][:n]): 
    with Constrain(get_prompt(**kwargs)) as manager: 
      manager.set_config(
        format='xml'
      )
      manager.format_prompt(
        placeholders={
          "instructions": file_['description'],
          "prompt": example['input']
        },
        grammars=[{
          'description': ' ', 
          'model': PhysicsQuestionsModel
        }],
      )

      if verbose: 
        print('-------------------')
      response = llm(manager.prompt, grammar=manager.get_grammar(PhysicsQuestionsModel), stop_at=manager.stop_at)
      if response: 
        if verbose:
          print(response)
          print('-------------------')
        logs['responses'].append(response)
        logs['n_calls'] += 1
        response = manager.parse(response)
        if verbose:
          print(response)
          print('-------------------')
        if isinstance(response, Response):
          logs['n_goodcalls'] += 1
        else: 
          logs['n_badcalls'] += 1
          
        del example['input']
        logs['expected'].append({'PhysicsQuestionsModel': example})

        # Response object always uses Model name at the topmost level. This is required for context-based multi-TOML parsing.
        # I'm adding 'h' to the keys to match the model. Pydantic doesn't let me allot numbers as field names. 
        if check_response(response, {'PhysicsQuestionsModel': example}): 
          logs['n_matchedcall'] += 1
      else: 
        continue

    print(f'Step {ind}: [n_goodcalls: {logs["n_goodcalls"]}, n_badcalls: {logs["n_badcalls"]}, n_matchedcall: {logs["n_matchedcall"]}]')
    save(logs, f'{model_name}_physicsquestions.json')

  return logs

if __name__ == '__main__':
  models = { 
    'Mistral-7B': (Mistral, LocalLlama(gguf_path='/depot/euge/data/araviki/llama/gguf/mistral-7b-instruct-v0.2.Q5_K_M.gguf', llama_cpp_path='/depot/euge/data/araviki/llama/llama.cpp'), {'ignore':True}), 
    'CodeLlama2-13B': (Llama2Instruct, LocalLlama(gguf_path='/depot/euge/data/araviki/llama/gguf/codellama-13b-instruct.Q5_K_M.gguf', llama_cpp_path='/depot/euge/data/araviki/llama/llama.cpp'), {'size':'13B'}), 
    'Llama2-70B': (Llama2Instruct, LocalLlama(gguf_path='/depot/euge/data/araviki/llama/gguf/upstage-llama-2-70b-instruct-v2.Q5_K_M.gguf', llama_cpp_path='/depot/euge/data/araviki/llama/llama.cpp'), {'size':'70B'})
  }

  logs = {} 

  for model_name, meta in models.items():
    (get_prompt, llm, kwargs_)  = meta 
    print(f'Running for {model_name}')
    logs[model_name] = {} 
    logs[model_name]['StrategyQA'] = StrategyQA(model_name, get_prompt, llm, verbose=False, **kwargs_)
    logs[model_name]['LogicGridPuzzle'] = LogicGridPuzzle(model_name, get_prompt, llm, verbose=False, **kwargs_)
    logs[model_name]['PhysicsQuestions'] = PhysicsQuestions(model_name, get_prompt, llm, verbose=False, **kwargs_)
    print('-------------------')
  
  print('-------------------------')
  print(json.dumps(logs, indent=2))
  print('-------------------------')


