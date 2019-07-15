from typing import List
from fastapi import APIRouter

from ..service import credibility
from ..models import classes

router = APIRouter()

@router.get('/', response_model=List[classes.Origin])
def get_origins():
    """Returns all the origins"""
    return credibility.get_origins()

@router.post('/')
def update_batch_origins():
    """Updates all the origins of type batch"""
    return credibility.update_batch_origins()

@router.get('/{origin_id}', response_model=classes.Origin)
def get_origin(origin_id):
    """returns the details about an origin identified by the `origin_id`"""
    return credibility.get_origin(origin_id)

@router.post('/{origin_id}')
def update_batch_origin(origin_id):
    """Updates the origin of type batch corresponding to `origin_id`"""
    return credibility.update_batch_origin(origin_id)