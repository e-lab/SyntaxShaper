from grammarflow.tools.llm import LocalLlama
from grammarflow.constrain import Constrain
from grammarflow.prompt.template import * 
from grammarflow.tools.response import Response

from pydantic import BaseModel, Field
from typing import List, Dict, Any
import json 
from grammarflow.grammars.gnbf import GNBF

with Constrain('bruh') as manager: 
      manager.set_config(
        format='json'
      )

      response = """ 
{"Step": { "thought": "# Observation from previous steps shows that there is no direct match for Eminen or M Phazes, but we found a similar keyword 'Eminem'. We will use this to search further.",
"action": "search",
"action-input": "```./Search: eminem```"} }
"""
      response = manager.parse(response)