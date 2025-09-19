from pydantic import BaseModel, Field
from typing import Dict, List, Union, Literal
from data_model.db_bench_options import DBBenchOptions

class INIConfig(BaseModel):
    Version: Union[List[str], None]
    DBOptions: Union[List[str], None]
    CFOptions: Union[List[str], None]
    TableOptionsBlockBasedTable: Union[List[str], None]

class Action(BaseModel):
    changed_db_options: INIConfig
    changed_db_bench_options: DBBenchOptions
    reason: str

class ActionList(BaseModel):
    actions: List[Action]

class Insights(BaseModel):
    content: str
    property: str
    confidence: float

class InsightsList(BaseModel):
    insights: List[Insights]

class InsightsDecision(BaseModel):
    id: str
    operation: str
    content: str
    property: str
    reasoning: str

