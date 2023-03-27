#!/usr/bin/env python

import requests
from collections import defaultdict

from ... import utils
from . import OriginBatch


class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self=self,
            id="lemonde_decodex",
            name="Le Monde - Décodex",
            description="Le Décodex est un outil pour vous aider à vérifier les informations qui circulent sur Internet et dénicher les rumeurs, exagérations ou déformations.",
            homepage="https://www.lemonde.fr/verification/",
            # logo = 'https://logo.clearbit.com/lemonde.fr',
            logo="https://pbs.twimg.com/profile_images/465825602461634560/sQ-6BEyf_400x400.png",
            default_weight=10,
        )

    def retreive_source_assessments(self):
        return _retrieve_assessments(self.id)


source_url = "https://www.lemonde.fr/webservice/decodex/updates"


def _retrieve_assessments(origin_id):
    assessments = _download_source_list()
    # TODO decide where to do that, maybe in "datasets" aka "claimreviews"?
    # debunks_url = 'https://s1.lemde.fr/mmpub/data/decodex/hoax/hoax_debunks.json'
    result_source_level = _interpret_assessments(assessments, origin_id)
    return result_source_level


_classes = {
    1: {"name": "satire", "credibility": 0.0, "confidence": 0.0},
    2: {"name": "false", "credibility": -1.0, "confidence": 1.0},
    3: {"name": "dubious", "credibility": 0.0, "confidence": 1.0},
    4: {"name": "good", "credibility": 1.0, "confidence": 1.0},
}


def _download_source_list():
    response = requests.get(source_url)
    response.raise_for_status()

    data = response.json()
    return data


def _get_credibility_measures(class_info):
    return {"value": class_info["credibility"], "confidence": class_info["confidence"]}


def _interpret_assessments(assessments, origin_id):
    results = []
    for source_raw, id in assessments["urls"].items():
        evaluation = assessments["sites"][str(id)]
        class_id, description, name, path_id = evaluation
        source_domain = utils.get_url_domain(source_raw)
        source = utils.get_url_source(source_raw)
        class_info = _classes[class_id]
        original_label = class_info["name"]
        credibility = _get_credibility_measures(class_info)
        assessment_url = f"https://www.lemonde.fr/verification/source/{path_id}/"
        ass = {
            "id": id,
            "source_name": name,
            "class_id": class_id,
            "source": source_raw,
            "description": description,
            "name": name,
            "path_id": path_id,
        }
        result = {
            "url": assessment_url,
            "credibility": credibility,
            "itemReviewed": source_raw,
            "original": ass,
            "origin_id": origin_id,
            "original_label": original_label,
            "domain": source_domain,
            "source": source,
            "granularity": "source",
        }
        results.append(result)

    return results
