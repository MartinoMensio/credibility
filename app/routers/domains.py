import json
from typing import List
from fastapi import APIRouter, HTTPException

from ..service import credibility
from ..models import output_classes

router = APIRouter()

@router.get('/', response_model=output_classes.AggregatedAssessment) # response_model=List[output_classes.domain]
def get_domain_credibility(url):
    """Returns the domain credibility"""
    return credibility.get_domain_credibility(url)

@router.get('/all', response_model=List[output_classes.AggregatedAssessment]) # response_model=List[output_classes.domain]
def get_all_domains():
    result = credibility.get_all_domains_evaluations()
    result = [output_classes.AggregatedAssessment(**el).dict() for el in result]
    with open('all_domains.json', 'w') as f:
        json.dump(result, f)
