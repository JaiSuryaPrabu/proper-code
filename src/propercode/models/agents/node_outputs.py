from enum import Enum
from pydantic import BaseModel,Field
from typing import Optional,List

class ContextNodeOutput(BaseModel):
    '''
    Defines the structured output for the context-gathering agent
    '''
    thought: str = Field(...,description="A detailed explanation of which files were chosen to be read and why they are relevant to the user's request.")
    context: str = Field(...,description="The final, consolidated context string, including the file tree and the content of any files that were read.")

class PlanNodeOutput(BaseModel):
    '''
    Defines the structured output for the planning agent
    '''
    thought:str = Field(...,description="The detailed reasoning and thought process behind the generated plan",max_length=800)
    plan:List[str] = Field(...,description="A list of discrete, actionable steps required to achieve the user's goal. Each step should be clear and concise.",min_length=3,max_length=6)

class CodeNodeOutput(BaseModel):
    '''
    Defines the structured output for the coding agent
    '''
    thought:str = Field(...,description="A brief explanation of the coding approach, including the choice of any libraries or functions, and important implementation details.",max_length=500)
    code:str = Field(...,description="Only the complete, executable code block that correctly implements the given plan.")
    file_name:str = Field(...,description="The suitable file name for the code generated and include path if multi-file project.")
    programming_language:str = Field(...,description="The programming language of the code written")

class Verdict(Enum):
    '''
    An enumeration for the evaluation verdict
    '''
    PASS = "PASS"
    FAIL = "FAIL"

class EvaluationNodeOutput(BaseModel):
    '''
    Defines the structured output for the evaluation agent
    '''
    thought:str = Field(...,description="Detailed reasoning for the verdict. If PASS, explain why the code is correct. If FAIL, explain the specific errors or flaws found.",max_length=600)
    verdict:Verdict = Field(...,description="The final verdict of the code evaluation. Must be either 'PASS' or 'FAIL'.")
    feedback:Optional[str] = Field(default=None,description="If the verdict is 'FAIL', provide specific, actionable feedback and suggestions for how to fix the code. This should be null if the verdict is 'PASS'.",max_length=400) 

class FactOutput(BaseModel):
    '''
    Defines the structured output for the fact extracting agent
    '''
    thought:str = Field(...,description="Reasoning behind identifying the fact")
    facts:str = Field(...,description="A list of discrete, important facts identified from the user's request or previous interactions.")