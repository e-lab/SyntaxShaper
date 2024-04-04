from pydantic import BaseModel, Field
from typing import List


class Score(BaseModel): 
    yes: int = Field(..., description="Options: 1 | 0")
    no: int = Field(..., description="Options: 1 | 0")

class StrategyQAModel(BaseModel): 
    target_scores: Score 
    target: str = Field(..., description="Reasoning for your above answer")

class Houses(BaseModel):
    h1: int = Field(..., description="Options: 1 | 0")
    h2: int = Field(..., description="Options: 1 | 0")
    h3: int = Field(..., description="Options: 1 | 0")
    h4: int = Field(..., description="Options: 1 | 0")
    h5: int = Field(..., description="Options: 1 | 0")

class LogicGridPuzzleModel(BaseModel): 
    target_scores: Houses

class PhysicsQuestionsModel(BaseModel): 
  target: List[str] = Field(..., description="List of example measurements. Example: ['1.2m', '3.4m', '5.6m']")

class Colors(BaseModel): 
    red: int = Field(..., description="Options: 1 | 0")
    orange: int = Field(..., description="Options: 1 | 0")
    yellow: int = Field(..., description="Options: 1 | 0")
    green: int = Field(..., description="Options: 1 | 0")
    blue: int = Field(..., description="Options: 1 | 0")
    brown: int = Field(..., description="Options: 1 | 0")
    magenta: int = Field(..., description="Options: 1 | 0")
    fuchsia: int = Field(..., description="Options: 1 | 0")
    mauve: int = Field(..., description="Options: 1 | 0")
    teal: int = Field(..., description="Options: 1 | 0")
    turquoise: int = Field(..., description="Options: 1 | 0")
    burgundy: int = Field(..., description="Options: 1 | 0")
    silver: int = Field(..., description="Options: 1 | 0")
    gold: int = Field(..., description="Options: 1 | 0")
    black: int = Field(..., description="Options: 1 | 0")
    grey: int = Field(..., description="Options: 1 | 0")
    purple: int = Field(..., description="Options: 1 | 0")
    pink: int = Field(..., description="Options: 1 | 0")



    