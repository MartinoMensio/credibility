from typing import List, Dict
from fastapi import APIRouter, HTTPException, Query
from tqdm import tqdm

from ..service import credibility
from ..service import persistence


router = APIRouter()

@router.get('/all-domains')
def get_all_domains():
    """Returns all the domains assessed"""
    origin_keys = credibility.origins.keys()
    all_domains = []
    for o in origin_keys:
        print(o)
        assessments = persistence.get_origin_assessments(o)
        domains = [el['itemReviewed'] for el in tqdm(assessments) if el['granularity'] == 'domain']
        all_domains.extend(domains)
    # remove duplicates
    all_domains = list(set(all_domains))
    all_credibility = credibility.get_source_credibility_multiple(all_domains)
    # print(all_credibility)
    return {k: v['credibility'] for k, v in all_credibility.items()}

@router.get('/all-urls')
def get_all_urls():
    """Returns all the urls assessed"""
    assessments = persistence.get_origin_assessments('factchecking_report')
    # simpler and faster than the other, because only fact-checkers review URLs. So no weighting is necessary
    return {el['itemReviewed']: el['credibility'] for el in tqdm(assessments) if el['granularity'] == 'itemReviewed'}

@router.get('/all-edges')
def get_all_edges(): # fields: List[str] = Query(None)
    """Returns all the edges of the graph"""
    credibility_origins = credibility.origins.keys()
    all_a = []
    for o in tqdm(credibility_origins, desc='reading collections'):
        a = persistence.get_origin_assessments(o)
        for el in a:
            del el['_id']
            del el['original']
            all_a.append(el)
    # result = []
    # for a in all_a:
    #     result.append({field_key: a.get(field_key) for field_key in fields})
    return all_a