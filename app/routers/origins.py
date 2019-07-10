from fastapi import APIRouter

from ..service import credibility

router = APIRouter()

@router.get('/')
def get_origins():
    """Returns all the origins"""
    return credibility.get_origins()

@router.post('/')
def update_batch_origins():
    """Updates all the origins"""
    return credibility.update_batch_origins()

@router.get('/{origin_id}')
def get_origin(origin_id):
    return credibility.get_origin(origin_id)

@router.post('/{origin_id}')
def update_origin(origin_id):
    return credibility.update_batch_origin(origin_id)