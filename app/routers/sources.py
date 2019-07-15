from fastapi import APIRouter

from ..service import credibility
from ..models import classes

router = APIRouter()

@router.get('/{source}', response_model=classes.AggregatedAssessment)
def get_source(source: str):
    return credibility.get_source_credibility(source)
