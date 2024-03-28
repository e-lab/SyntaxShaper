from pydantic import BaseModel, Field
from typing import List 


class AgentStep(BaseModel):
  thought: str = Field(..., description="Concisely describe your thought process in your current thinking step. Use your previous step's output to guide your current step.")
  action: str = Field(..., description="Only return the tool.")
  action_input: str = Field(..., description="Your input to the above action.")  

class CoT(BaseModel): 
  chain_of_thought: List[str] = Field(..., description="Iteratively list out the observations you make in solving your goal. Think out loud.")
  answer: bool = Field(..., description="Options: True OR False.")