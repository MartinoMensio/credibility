from fastapi import APIRouter

from ..service import credibility

router = APIRouter()

@router.get('/{source}')
def get_source(source: str):
    return credibility.get_source_credibility(source)