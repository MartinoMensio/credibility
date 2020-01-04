#!/usr/bin/env python

import requests

from ... import utils

from . import OriginBatch

class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self = self,
            id = 'opensources',
            name = 'Open Sources',
            description = 'Curated lists of credible and non-credible online sources, available for public use.',
            homepage = 'https://github.com/OpenSourcesGroup/opensources/', #http://www.opensources.co/'
            logo = 'https://web.archive.org/web/20190401110240im_/http://www.opensources.co/assets/opensources-2b0bf881406d4a5ae002b2489278af9240e70cc4e2acc2ac23d9c3be94b896f2.svg',
            default_weight = 1
        )
        self.source_url = 'https://raw.githubusercontent.com/OpenSourcesGroup/opensources/master/sources/sources.json'

    def retreive_source_assessments(self):
        return _retrieve_assessments(self.source_url, self.id, self.homepage)

_tag_to_scores = {
    'fake': -1.0, 'fake news': -1.0,
    'satire': 0.0, 'satirical': 0.0,
    'bias': -0.5,
    'conspiracy': -0.8,
    'rumor': -0.3,
    'state': 0.0,
    'junksci': -0.8,
    'hate': -0.3,
    'clickbait': -0.5,
    'unreliable': 0.0, 'unrealiable': 0.0,
    'political': 0.0,
    'reliable': 1.0,
    'blog': 0.0
}

def _retrieve_assessments(source_url, origin_id, homepage):
    assessments = _download_source_list(source_url)
    result_source_level = _interpret_assessments(assessments, homepage, origin_id)
    return result_source_level


def _download_source_list(source_url):
    response = requests.get(source_url)
    response.raise_for_status()
    
    data = response.json()
    return data

def _get_credibility_measures(original_evaluation):
    properties = ['type', '2nd type', '3rd type']
    looking_at = [prop_value for prop_name, prop_value in original_evaluation.items() if prop_name in properties and prop_value]
    credibility = 0
    for el in looking_at:
        credibility += _tag_to_scores[el.lower().strip()]
    # saturate
    credibility = min(credibility, 1.0)
    credibility = max(credibility, -1.0)
    return {'value': credibility, 'confidence': 1.0}

def _interpret_assessments(assessments, homepage, origin_id):
    results = []
    for source_raw, ass in assessments.items():
        source_raw = source_raw.lower()
        source_domain = utils.get_url_domain(source_raw)
        source = utils.get_url_source(source_raw)
        credibility = _get_credibility_measures(ass)
        result = {
            'url': homepage,
            'credibility': credibility,
            'itemReviewed': source_raw,
            'original': ass,
            'origin_id': origin_id,
            'domain': source_domain,
            'source': source,
            'granularity': 'source'
        }
        results.append(result)

    return results
