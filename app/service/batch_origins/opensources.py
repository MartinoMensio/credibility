#!/usr/bin/env python

import requests

from .. import utils, persistence

WEIGHT = 1

ID = 'opensources'
NAME = 'Open Sources'
DESCRIPTION = 'Curated lists of credible and non-credible online sources, available for public use.'
HOMEPAGE = 'https://github.com/OpenSourcesGroup/opensources/' #http://www.opensources.co/'

source_url = 'https://raw.githubusercontent.com/OpenSourcesGroup/opensources/master/sources/sources.json'


tag_to_scores = {
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

def get_source_credibility(source):
    return persistence.get_source_assessment(ID, source)

def get_domain_credibility(domain):
    return persistence.get_domain_assessment(ID, domain)

def get_url_credibility(url):
    return None

def update():
    assessments = download_source_list()
    result_source_level = interpret_assessments(assessments)
    result_domain_level = utils.aggregate_domain(result_source_level, ID)
    print(ID, 'retrieved', len(result_domain_level), 'domains', len(result_source_level), 'sources', 'assessments') # , len(result_document_level), 'documents'
    all_assessments = list(result_source_level) + list(result_domain_level) # list(result_document_level) +
    persistence.save_assessments(ID, all_assessments)
    return len(all_assessments)


def download_source_list():
    response = requests.get(source_url)
    if response.status_code != 200:
        raise ValueError(response.status_code)
    data = response.json()
    return data

def get_credibility_measures(original_evaluation):
    properties = ['type', '2nd type', '3rd type']
    looking_at = [prop_value for prop_name, prop_value in original_evaluation.items() if prop_name in properties and prop_value]
    credibility = 0
    for el in looking_at:
        credibility += tag_to_scores[el.lower().strip()]
    # saturate
    credibility = min(credibility, 1.0)
    credibility = max(credibility, -1.0)
    return {'value': credibility, 'confidence': 1.0}

def interpret_assessments(assessments):
    results = []
    for source_raw, ass in assessments.items():
        source_raw = source_raw.lower()
        source_domain = utils.get_url_domain(source_raw)
        source = utils.get_url_source(source_raw)
        credibility = get_credibility_measures(ass)
        result = {
            'url': HOMEPAGE,
            'credibility': credibility,
            'itemReviewed': source_raw,
            'original': ass,
            'origin_id': ID,
            'domain': source_domain,
            'source': source,
            'granularity': 'source'
        }
        results.append(result)

    return results
