# Constrain: Supercharging agent chains with parseable LLM answers 

## Overview

This repository contains code to abstract the LLM output constraining process. It helps you define your grammar rules using Pydantic and Typing in a pythonic way, and inherently embeds metadata from these dataclasses into the prompt to help it understand the required format. Parsing is enabled in JSON, TOML and XML formats, with custom parsers that avoid the issues faced by `json.loads` (..etc) while parsing direct outputs. It can also GNBF grammr from the same, which is used by the `llama.cpp` package for sampling logits smartly. 

## Getting Started

### Installation

To install Constrain, run the following command in your terminal:

```
pip install constrain
```

### Code Usage 

The demo.ipynb file contains examples of ways in which you can use constrain with results. 

## License

Constrain is released under the MIT License. Please see the LICENSE file for more details.