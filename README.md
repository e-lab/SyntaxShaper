<div align="center">

# 🪢 GrammarFlow


<!-- [![Tests](https://github.com/abetlen/llama-cpp-python/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/abetlen/llama-cpp-python/actions/workflows/test.yaml) -->
[![PyPI](https://img.shields.io/pypi/v/grammarflow)](https://pypi.org/project/grammarflow/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/grammarflow)](https://pypi.org/project/grammarflow) [![License](https://img.shields.io/github/license/e-lab/SyntaxShaper)](https://img.shields.io/github/license/e-lab/SyntaxShaper)


🚀 Supercharging Agent Chains with Constrained LLM outputs 🚀


</div>

# Table of contents
1. [What is this](https://github.com/e-lab/SyntaxShaper/tree/main?tab=readme-ov-file#-what-is-this)
2. [Quick Install](https://github.com/e-lab/SyntaxShaper/tree/main?tab=readme-ov-file#-quick-install)
3. [Code Usage](https://github.com/e-lab/SyntaxShaper/tree/main?tab=readme-ov-file#-code-usage)
4. [Examples (@ samples/)](https://github.com/e-lab/SyntaxShaper/tree/main?tab=readme-ov-file#examples--samples)
5. [GNBF Grammar](https://github.com/e-lab/SyntaxShaper/tree/main?tab=readme-ov-file#gnbf-grammar)
6. [Remarks!](https://github.com/e-lab/SyntaxShaper/tree/main?tab=readme-ov-file#remarks)
7. [Citation](https://github.com/e-lab/SyntaxShaper/tree/main?tab=readme-ov-file#citation)


## 🤔 What is this?

This repository contains code to abstract the LLM output constraining process. It helps you define your grammar rules using Pydantic and Typing in a pythonic way, and inherently embeds metadata from these dataclasses into the prompt. Parsing is enabled in JSON, TOML and XML formats, with custom parsers that avoid the issues faced by `json.loads` (..etc) while parsing direct outputs. It can also create GNBF grammr from the same, which is used by the [llama.cpp](https://github.com/ggerganov/llama.cpp/) package for sampling logits smartly. 

The goal of this package was to overcome the issues faced when using langchain's output parsers with instruct language models. While GPT-4 produces consistent results in returning the correct formats, Llama-7B would cause parsing errors in my testing chains with more complex prompts. 

> Please reach out to `araviki [at] purdue [dot] edu` or open an issue on Github if you have any questions or inquiry related to GrammarFlow and its usage.

## Results: 

GrammarFlow was tested against popular LLM datasets, with a focus on constraining model outputs. The goal was to ensure that the final parsed output matched both the *structure and data types* of the ground truth. 

[Logic Grid Puzzle](https://github.com/google/BIG-bench/blob/main/bigbench/benchmark_tasks/logic_grid_puzzle/) - Simple grammar (Nested Objects with lists), large prompts. 500 words+.

[StrategyQA](https://github.com/google/BIG-bench/blob/main/bigbench/benchmark_tasks/strategyqa/task.json) - Simplest grammar (Nested Objects with str/int). 

[ReasoningAboutColors](https://github.com/google/BIG-bench/blob/main/bigbench/benchmark_tasks/reasoning_about_colored_objects/) - Requires handling multiple fields in grammar (Single object with list). 

```
|------------------------------------------------------------------------------------------------------|
|    Model Name   |Parameters|Logic Grid Puzzle (n=200)|StrategyQA (n=200)|ReasoningAboutColors (n=200)|
|-----------------+----------+-------------------------+------------------+----------------------------|
|    Mistral-7B   |    7B    |          100.0          |       100.0      |            100.0           |
|-----------------+----------+-------------------------+------------------+----------------------------|
|  CodeLlama2-13B |    13B   |          100.0          |       100.0      |            100.0           |
|-----------------+----------+-------------------------+------------------+----------------------------|
|    Llama2-70B   |    70B   |          100.0          |       100.0      |            100.0           |
+------------------------------------------------------------------------------------------------------|
```

[PrOntoQA](https://github.com/Ber666/llm-reasoners/blob/main/examples/prontoqa/data/345hop_random_true.json) - Chain of Thought reasoning, with randomly-scattered supporting facts in prompt. Taken from [llm-reasoners](https://github.com/Ber666/llm-reasoners/). Tests the ability to place specific reasoning statements in the right place. 

[HotPotQA](http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_train_v1.1.json) - Multi-hop questions, with strong supervision for supporting facts. Integrated within the first ReAct prompting paper's [code](https://github.com/ysymyth/ReAct). Incremental steps, leading to large prompts.

```
|------------------------------------------------------------------------------+-------------------------|
|    Model Name   |Parameters|PrOntoQA Parsing (n=200)|PrOntoQA Accuracy (n=200)|HotPotQA Parsing (n=200)|
|-----------------+----------+------------------------+-------------------------+------------------------|
|    Mistral-7B   |    7B    |           99           |           88.5          |          99.0          |
|-----------------+----------+------------------------+-------------------------+------------------------|
|  CodeLlama2-13B |    13B   |          97.5          |           55.5          |          100.0         |
|-------------------------------------------------------------------------------+------------------------|
|    Llama2-70B   |    70B   |          96.5          |           81.9          |          99.0          |
|-------------------------------------------------------------------------------+------------------------|
```

## ⚡ Quick Install

`pip install grammarflow`

## 📃 Code Usage 

Map out what your agent chain is doing. Understand what it's goals are and what data needs to be carried forward from one step to the next. 
For example, consider the [ReAct prompting framework](https://react-lm.github.io/). In every call, we want to pass in the Action and subsequent Observation to the next call. 


```python
from grammarflow import * 
from grammarflow.prompt.template import Agent 
from grammarflow.grammars.template import AgentStep
from grammarflow.tools.LLM import LocalLlama

llm = LocalLlama() 
prompt = Agent() 
# prompt.placeholders lists out what you can pass into the prompt. 

system_context = """Your goal is to think and plan out how to solve questions using agent tools provided to you. Think about all aspects of your thought process."""
user_message = """Who is Vladmir Putin?"""

with Constrain(prompt, 'xml') as manager:
    # Makes the changes to the prompt
    manager.format_prompt(
        placeholders={'prompt': user_message, 'instructions': system_context},
        grammars=[{'model': AgentStep}]
    )

    llm_response = llm(manager.prompt, temperature=0.01)

    # Parse the response into a custom dataclass for holding values
    response = manager.parse(llm_response)

observation = PerformSomeAction(
  action = response.AgentStep.action, 
  action_input = response.AgentStep.action_input
) 
```

## Features

GrammarFlow is mainly meant to be an add-on to your existing LLM applications. It works on the input to and output from your `llm()` call, treating everything in between as a black box. It contains pre-made template prompts for local GGUF models like [Llama2 (70B, 13B, 7B)](https://huggingface.co/TheBloke/Upstage-Llama-2-70B-instruct-v2-GGUF), [Mistral](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF), [Mixtral](https://huggingface.co/TheBloke/Synthia-MoE-v3-Mixtral-8x7B-GGUF) and has template grammars for common tasks. Making these prompts and grammars are trivial and require minimal effort, as long as you know the format of what you're building. 

- [X] **GBNF Support**: Converts any Pydantic model to GNBF grammar for using with [llama.cpp](https://github.com/ggerganov/llama.cpp/)'s token-based sampling. Enables adding regex patterns directly. 
- [x] **Easy Integration**: Integrates with any package or stack by just manipulating the prompt and decoding the result into a pythonic data abstractor. Treats everything in between as a **black box**.
- [x] **Handles Complex Grammars**: Can handle typing objects ('List', 'Dict', etc.) and nested Pydantic logic with complex data-types. 
- [x] **Experiments with different 'formats'**: Defines grammar rules in XML, JSON and TOML formats. JSON is the standard, while XML is best for (+3) nested parsing and TOML is best when you want to get multiple models parsed simulatenously. Each has it's own usecase as described in the demo.
- [x] **Reduces hallucinations or garbage results during sampling**: GBNF grammars allow for controlled whitespacing/identation and model generation ordering, while parsing logic allows for ignoring incorrect terminal symbols.  

### Examples (@ samples/)
1. For a general overview of what GrammarFlow can do, look at [demo.ipynb](https://github.com/e-lab/SyntaxShaper/blob/main/samples/demo.ipynb). 
2. For my modification to [ReAct's](https://github.com/ysymyth/ReAct) evaluation code on [HotPotQA](https://hotpotqa.github.io/), look at [hotpotqa_modified](https://github.com/e-lab/SyntaxShaper/blob/main/samples/hotpotqa/hotpotqa_modified.ipynb).
3. I've also added an implementation of a [data annotator](https://github.com/e-lab/SyntaxShaper/blob/main/samples/bert_finetuning/annotator.ipynb) for this [BERT fine-tuning guide](https://www.datasciencecentral.com/how-to-fine-tune-bert-transformer-with-spacy-3/).

### GNBF Grammar 

> "GBNF (GGML BNF) is a format for defining formal grammars to constrain model outputs in llama.cpp. For example, you can use it to force the model to generate valid JSON, or speak only in emojis."
> Read more about it here: https://github.com/ggerganov/llama.cpp/blob/master/grammars/README.md


```python
# Define your model 
class TeamMember(BaseModel):
    name: str
    role: str

class TaskUpdate(BaseModel):
    update_time: float
    comment: Optional[str] = None
    status: bool

class Task(BaseModel):
    title: str
    description: str
    assigned_to: List[TeamMember]
    due_date: List[str]
    updates: List[TaskUpdate]

class Project(BaseModel):
    name: str
    description: str
    project_url: Optional[str] = None
    team_members: List[TeamMember]
    grammars: Task

# Convert to grammar
from grammarflow import GNBF

grammar = GNBF(Project).generate_grammar()

# Verify with LlamaGrammar
GNBF.verify_grammar(grammar)
```

Results: 
```
root ::= project ws
project ::= "{" ws "\"name\":" ws string "," ws "\"description\":" ws string "," ws "\"project-url\":" ws string "," ws "\"team-members\":" ws teammember "," ws "\"grammars\":" ws grammars "}" ws
ws ::= [ \t\n]*
string ::=  "\"" (
            [^"\\] |
            "\\" (["\\/bfnrt] | "u" [0-9a-fa-f] [0-9a-fa-f] [0-9a-fa-f] [0-9a-fa-f])
            )* "\""
teammember ::= "{" ws "\"name\":" ws string "," ws "\"role\":" ws string "}" ws
number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([ee] [-+]? [0-9]+)?
taskupdate ::= "{" ws "\"update-time\":" ws number "," ws "\"comment\":" ws string "," ws "\"status\":" ws status "}" ws
array ::= "[" ws (
                due-date-value
                ("," ws due-date-value)*
            )? "]" ws
due-date-value ::= string
task ::= "{" ws "\"title\":" ws string "," ws "\"description\":" ws string "," ws "\"assigned-to\":" ws teammember "," ws "\"due-date\":" ws array "," ws "\"updates\":" ws taskupdate "}" ws
```

You can use this grammar to pass into [llama.cpp](https://github.com/ggerganov/llama.cpp/) through a barebones LLM class that is provided. 

```python
llm = LocalLlama() 
response = llm(manager.prompt, grammar=manager.get_grammar(CoT), stop_at=manager.stop_at)
```

## Remarks!

Please keep in mind that this package is purely software driven and aims to make developers lives a little simpler. It can work across model families and parameter counts with great success in parsing. 

However, with an increase in complexity of the prompt, the accuracy and 'performance' of the model's thinking capability will fail. This is attributed to the greater possibility 

## Citation

We appreciate it if you would please cite this repo if you found the library useful for your work:

```
@software{GrammarFlow,
  author = {Ravikiran, Akshath Raghav and Culurciello, Eugenio},
  title = {GrammarFlow: Powering Agent Chains by Constraining LLM Outputs},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/e-lab/GrammarFlow}}, 
  version = {0.1.1}
}
```

