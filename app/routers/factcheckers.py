from typing import List
from fastapi import APIRouter, HTTPException

from ..service import credibility
from ..models import output_classes
from ..service.origins.batch import ifcn

router = APIRouter()


@router.get("/")
def get_origins():
    """Returns all the factcheckers"""
    result = list(ifcn.get_all_sources_credibility())
    for r in result:
        del r["_id"]
    return result
