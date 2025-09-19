from pydantic import BaseModel, Field
from typing import Dict, List, Union, Literal

class Decision(BaseModel):
    node_id: str
    action: str

