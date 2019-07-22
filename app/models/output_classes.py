from enum import Enum
from pydantic import BaseModel, UrlStr
from typing import Dict, List, Any

class TypeEnum(str, Enum):
    batch = 'batch'
    realtime = 'realtime'

class Origin(BaseModel):
    id: str
    origin_type: TypeEnum
    weight: float
    homepage: UrlStr
    assessments_count: int

class Credibility(BaseModel):
    value: float
    confidence: float

class GranularityEnum(str, Enum):
    source = 'source'
    document = 'document'
    claim = 'claim'

class Assessment(BaseModel):
    # who assessed it
    origin_id: str
    # the URL where the assessment is published
    url: UrlStr
    # our conversion
    credibility: Credibility
    # the URL to the item reviewed, the more punctual as possible
    itemReviewed: str
    # the original assessment
    original: Any
    # the domain of the itemReviewed
    domain: str
    # granularity
    granularity: GranularityEnum

class AggregatedAssessment(BaseModel):
    # the aggregated credibility
    credibility: Credibility
    assessments: List[Assessment]
    itemReviewed: str
