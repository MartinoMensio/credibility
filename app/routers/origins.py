from typing import List
from fastapi import APIRouter, HTTPException

from ..service import credibility
from ..models import output_classes

router = APIRouter()

@router.get('/', response_model=List[output_classes.Origin])
def get_origins():
    """Returns all the origins"""
    return credibility.get_origins()

@router.post('/')
def update_batch_origins():
    """Updates all the origins of type batch"""
    return credibility.update_batch_origins()

@router.get('/{origin_id}', response_model=output_classes.Origin)
def get_origin(origin_id):
    """returns the details about an origin identified by the `origin_id`"""
    return credibility.get_origin(origin_id)

@router.post('/{origin_id}')
def update_batch_origin(origin_id):
    """Updates the origin of type batch corresponding to `origin_id`"""
    result = credibility.update_batch_origin(origin_id)
    if not result:
        raise HTTPException(404, {'message': 'Origin not found', 'suggestion': 'see the origin_id allowed values from GET /origins'})
    return result