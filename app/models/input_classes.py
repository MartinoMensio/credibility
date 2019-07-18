from typing import List
from pydantic import BaseModel

class BatchSourceRequest(BaseModel):
    sources: List[str]
