from enum import Enum
from pydantic import BaseModel, UrlStr
from typing import Dict, List, Any, Optional

class TypeEnum(str, Enum):
    batch = 'batch'
    realtime = 'realtime'

class Origin(BaseModel):
    id: str
    origin_type: TypeEnum
    weight: float
    homepage: UrlStr
    assessments_count: Dict[str, int]
    name: str
    description: str
    logo: str

class Credibility(BaseModel):
    value: float
    confidence: float

class GranularityEnum(str, Enum):
    # a domain can have multiple sources in it
    domain = 'domain'
    # a source can be twitter.com/realDonaldTrump
    source = 'source'
    # a document / url is identified by the full URL
    url = 'url'
    # a claim is identified by the sentence itslef (TODO this is not implemented, and what about the context?)
    claim = 'claim'

class Assessment(BaseModel):
    # who assessed it
    origin_id: str
    # details about the origin
    origin: Origin
    # the URL where the assessment is published
    # TODO rename it to assessment_url
    url: Optional[UrlStr]
    # our conversion
    credibility: Credibility
    # the URL to the item reviewed, the more punctual as possible
    itemReviewed: str
    # the original assessment
    reports: List[Any] = []
    # the domain of the itemReviewed
    domain: Optional[str]
    # the source of the itemReviewed
    source: Optional[str]
    # granularity
    granularity: Any # TODO use again GranularityEnum, as soon as url becomes review_url
    # the weights used
    weights: Any

class AggregatedAssessment(BaseModel):
    # the aggregated credibility
    credibility: Credibility
    assessments: List[Assessment]
    itemReviewed: str
