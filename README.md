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
6. [Remarks!](#https://github.com/e-lab/SyntaxShaper/tree/main?tab=readme-ov-file#remarks)
7. [Citation](https://github.com/e-lab/SyntaxShaper/tree/main?tab=readme-ov-file#citation)


## 🤔 What is this?

This repository contains code to abstract the LLM output constraining process. It helps you define your grammar rules using Pydantic and Typing in a pythonic way, and inherently embeds metadata from these dataclasses into the prompt. Parsing is enabled in JSON, TOML and XML formats, with custom parsers that avoid the issues faced by `json.loads` (..etc) while parsing direct outputs. It can also create GNBF grammr from the same, which is used by the `llama.cpp` package for sampling logits smartly. 

The goal of this package was to overcome the issues faced when using langchain's output parsers with instruct language models. While GPT-4 produces consistent results in returning the correct formats, Llama-7B would cause parsing errors in my testing chains with more complex prompts. 

> Please reach out to `araviki [at] purdue [dot] edu` or open an issue on Github if you have any questions or inquiry related to GrammarFlow and its usage.

## ⚡ Quick Install

`pip install grammarflow`

## 📃 Code Usage 

1. Map out what your agent chain is doing. Understand what it's goals are and what data needs to be carried forward from one step to the next. 
For example, consider the [ReAct prompting framework](https://react-lm.github.io/). In every call, we want to pass in the Action and subsequent Observation to the next call. 

1.1. Load grammarflow 
```
from grammarflow import * 
```

2. Make a Pydantic Model for the above case. Here's a sample: 
```python 
class ThoughtState(BaseModel):
    thought: str
    goal: str
    tool: str = Field(...,
                      description="Choose one of ['Web_QA', 'Web_Search', 'Web_Scraping', 'Web_Automation', 'Web_Research']")
    action: str = Field(...,
                        description="Choose one of ['Create', 'Update', 'Delete', 'Read']")
    action_input: str = Field(..., description="The input data for the action")
    thought_id: Optional[str] = Field(
        None, description="1 if it is the first thought, 0 if it is the final thought.")
```

3. [Optional] Create a prompt template using grammarflow's PromptBuilder. Below is an example of the Llama prompt template. 
```python 
llama_prompt = PromptBuilder()
llama_prompt.add_section(
    text="<s>[INST] <<SYS>>\n{system_context}\n<</SYS>>",
    placeholder="system_context",
    define_grammar=True,
)
llama_prompt.add_section(
    text="{user_message}[/INST]",
    placeholder="user_message",
)
```
You can find an in-depth explanation on making prompts [here](https://github.com/e-lab/SyntaxShaper/blob/main/samples/demo.ipynb)!

4. [Optional] If you decide to make your own template, define your system_context and user_message `placeholders`. 
```python
system_context = """Your goal is to think and plan out how to solve questions using agent tools provided to you. Think about all aspects of your thought process."""
user_message = """Who is Vladmir Putin?"""
```

5. Invoke the `Constrain` block with the prompt. Set the configuration metadata, and format the prompt with the required `grammars` and `placeholders`.
```python
with Constrain(llama_prompt) as manager:
    manager.set_config(
        format='json', # or 'xml', 'toml'. 
        return_sequence='single_response' # or 'multi_response', if you need multiple grammars. 
    )

    # Makes the changes to the prompt
    manager.format_prompt(placeholders={ # if you have placeholders in the prompt
                          'user_message': user_message,
                          'system_context': system_context
                          },
                          grammars=[{
                              'description': 'This format describes your current thinking state', # Description of the response format
                              'model': [ThoughtState]}
                          ]
    )

    # Assume `llm` to be a call to a model
    llm_response = llm.request(manager.prompt, temperature=0.01)

    # Parse the response into a custom dataclass for holding values
    response = manager.parse(llm_response)
```

6. Extract the required values from the response to perform necessary functions on. 

```python 
observation = PerformSomeAction(
  action = response.ThoughtState.action, 
  action_input = response.ThoughtState.action_input
) 
```

7. Continue to the next iteration in your agent chain! 

### Examples (@ samples/)
1. For a general overview of what GrammarFlow can do, look at [demo.ipynb](https://github.com/e-lab/SyntaxShaper/blob/main/samples/demo.ipynb). 
2. For my modification to [ReAct's](https://github.com/ysymyth/ReAct) evaluation code on [HotPotQA](https://hotpotqa.github.io/), look at [hotpotqa_modified](https://github.com/e-lab/SyntaxShaper/blob/main/samples/hotpotqa/hotpotqa_modified.ipynb).
3. I've also added an implementation of a [data annotator](https://github.com/e-lab/SyntaxShaper/blob/main/samples/bert_finetuning/annotator.ipynb) for this [BERT fine-tuning guide](https://www.datasciencecentral.com/how-to-fine-tune-bert-transformer-with-spacy-3/).

### GNBF Grammar 

GrammarFlow also has functionality to convert a pydantic model into GNBF grammar. 
> "GBNF (GGML BNF) is a format for defining formal grammars to constrain model outputs in llama.cpp. For example, you can use it to force the model to generate valid JSON, or speak only in emojis."
> Read more about it here: https://github.com/ggerganov/llama.cpp/blob/master/grammars/README.md

This can then be passed into llama.cpp using llama-cpp-python to ensure that sampling of logits can take place with rules in mind. 

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

# Use it with the model 
with Constrain(llama_prompt) as manager: 
    manager.set_config(...)
    manager.format_prompt(...)

    llm_response = llm(
        manager.prompt,
        grammar=grammar, max_tokens=-1
    )
    response = manager.parse(llm_response)
```

## Remarks!

Please keep in mind that this package is purely software driven and aims to make developers lives a little simpler. Powerful models like GPT, Llama and Mixtral Instruct work well with this package. MoE systems are able to evaluate which model can provide reasoning and constrainability (purely how well it handles 'instructions').

However, with an increase in the complexity of the prompt, most models fail. This has to do with the model itself, and can be improved using token sampling using llama.cpp. But, a purely prompt-based approach cannot solve everything. 

Take, for example, you want to evaluate hotpotqa as explained in this notebook. When you run the scipt, you might find that Mixtral outputs parseable returns for JSON and XML formats in the first 2 runs. Post this, the model gets confused because of the way the prompt itself is constructed + ReAct's helper functions formats. 

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

