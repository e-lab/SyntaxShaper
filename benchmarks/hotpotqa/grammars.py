from pydantic import BaseModel, Field

class Step(BaseModel):
    thought: str = Field(..., description="Concisely describe your thought process in your current thinking step. Use your previous step's output to guide your current step.")
    action: str = Field(..., description="You only have 3 options: search | lookup | finish")
    action_input: str = Field(..., description="Your input to the above action.")