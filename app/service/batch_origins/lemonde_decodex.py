#!/usr/bin/env python

import requests
from collections import defaultdict

from .. import utils, persistence

WEIGHT = 10

ID = 'lemonde_decodex'
NAME = 'Lemonde - Décodex'
DESCRIPTION = 'Le Décodex est un outil pour vous aider à vérifier les informations qui circulent sur Internet et dénicher les rumeurs, exagérations ou déformations. '
HOMEPAGE = 'https://www.lemonde.fr/verification/'

source_url = 'https://www.lemonde.fr/webservice/decodex/updates'

# TODO decide where to do that, maybe in "datasets" aka "claimreviews"?
debunks_url = 'https://s1.lemde.fr/mmpub/data/decodex/hoax/hoax_debunks.json'


classes = {
    1: {
        'name': 'satire',
        'credibility': 0.,
        'confidence': 0.
    },
    2: {
        'name': 'false',
        'credibility': -1.,
        'confidence': 1.
    },
    3: {
        'name': 'dubious',
        'credibility': 0.,
        'confidence': 1.
    },
    4: {
        'name': 'good',
        'credibility': 1.,
        'confidence': 1.
    }
}

def get_source_credibility(source):
    return persistence.get_domain_assessment(ID, source)

def update():
    assessments = download_source_list()
    result = interpret_assessments(assessments)
    print(ID, 'retrieved', len(result), 'assessments')
    persistence.save_origin_assessments(ID, result)
    return len(result)


def download_source_list():
    response = requests.get(source_url)
    if response.status_code != 200:
        raise ValueError(response.status_code)
    data = response.json()
    return data

def get_credibility_measures(class_info):
    return {'value': class_info['credibility'], 'confidence': class_info['confidence']}

def interpret_assessments(assessments):
    results = []
    for source_raw, id in assessments['urls'].items():
        evaluation = assessments['sites'][str(id)]
        class_id, description, name, path_id = evaluation
        source_domain = utils.get_url_domain(source_raw)
        source = utils.get_url_source(source_raw)
        class_info = classes[class_id]
        credibility = get_credibility_measures(class_info)
        assessment_url = f'https://www.lemonde.fr/verification/source/{path_id}/'
        # TODO find how to manage these cases (account on social media)
        # if '/' in source:
        #     continue
        ass = {
            'id': id,
            'source_name': name,
            'class_id': class_id,
            'source': source_raw,
            'description': description,
            'name': name,
            'path_id': path_id
        }
        result = {
            'url': assessment_url,
            'credibility': credibility,
            'itemReviewed': source_raw,
            'original': ass,
            'origin': ID,
            'domain': source_domain,
            'source': source,
            'granularity': 'source'
        }
        results.append(result)
    results_source = utils.aggregate_domain(results, ID)

    return results_source
