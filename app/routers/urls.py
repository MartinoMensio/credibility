from typing import List, Dict
from fastapi import APIRouter, HTTPException

from ..service import credibility
from ..models import output_classes, input_classes

router = APIRouter()

@router.get('/', response_model=output_classes.AggregatedAssessment) # response_model=List[output_classes.url]
def get_url_credibility(url):
    """Returns all the urls"""
    return credibility.get_url_credibility(url)

@router.post('/', response_model=Dict[str, output_classes.AggregatedAssessment])
def get_urls(request_body: input_classes.BatchUrlRequest):
    urls = request_body.urls
    return credibility.get_url_credibility_parallel(urls)