import requests
from fastapi import APIRouter, HTTPException
from typing import List, Dict

from ..service import credibility
from ..models import output_classes, input_classes

router = APIRouter()

@router.get('/', response_model=output_classes.AggregatedAssessment)
def get_source(source: str):
    return credibility.get_source_credibility(source)

@router.post('/', response_model=Dict[str, output_classes.AggregatedAssessment])
def get_sources(request_body: input_classes.BatchSourceRequest):
    sources = request_body.sources
    try:
        return credibility.get_source_credibility_parallel(sources)
    except requests.exceptions.ConnectionError:
        raise HTTPException(422, {'message': 'ConnectionError with some of the realtime APIs', 'suggestion': 'perform requests in smaller chunks, like 400'})
