# https://newsaggregator.oii.ox.ac.uk/methodology.php

# 1. Tweets -> URLs
# 2. URLs -> homepage URL
# 3. Manual annotation
# 4. Junk sources: For the junk news category, there exist five criteria,
#    so if a news source fails to satisfy at least three of these five criteria,
#    it gets classified under this category
# 5. Filter sources with a Facebook page
# 6. This process led to n = 50 junk news sources tracked for the 2018 US midterm elections,
#    and 68 junk news sources tracked for the 2019 EU Parliamentary elections:
#    https://newsaggregator.oii.ox.ac.uk/files/US2018_JN_sources_and_criteria.csv
#    https://newsaggregator.oii.ox.ac.uk/files/EU2019_JN_sources_and_criteria.csv
#    https://newsaggregator.oii.ox.ac.uk/files/JN_Criteria.csv

import requests
import json
import re
import tqdm
import csv

from ... import utils
from . import OriginBatch

class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self = self,
            id = 'junknews_aggregator',
            name = 'Junk News Aggregator',
            description = 'The Junk News Aggregator is a research project of the Computational Propaganda group (COMPROP) of the Oxford Internet Institute (OII) at the University of Oxford.\n\nThe Junk News Aggregator is comprised of three tools: the main interactive Explorer, the interactive Visual Grid, and the Top 10 List . There are intended as tools to help researchers, journalists, and the public see what junk news stories are being shared and engaged with on Facebook, at times of important election events (such as the 2018 US midterm elections, and the 2019 European Parliament election).',
            homepage = 'https://newsaggregator.oii.ox.ac.uk/',
            logo = 'https://newsaggregator.oii.ox.ac.uk/assets/ComProp-logo.svg',
            default_weight = 8
        )

    def retreive_source_assessments(self):
        return _retrieve_assessments(self.id, self.homepage)

def _retrieve_assessments(origin_id, homepage):
    # the methodology is the justification
    methodology_url = 'https://newsaggregator.oii.ox.ac.uk/methodology.php'
    original_items = _download_assessments()
    result_source_level = _interpret_items(original_items, origin_id, methodology_url)
    return result_source_level


def _download_assessments():
    table_2018 = _download_csv('https://newsaggregator.oii.ox.ac.uk/files/US2018_JN_sources_and_criteria.csv')
    table_2019 = _download_csv('https://newsaggregator.oii.ox.ac.uk/files/EU2019_JN_sources_and_criteria.csv')
    return table_2018 + table_2019
    

def _download_csv(url):
    res = requests.get(url)
    res.raise_for_status()
    text = res.text
    reader = csv.DictReader(text.splitlines())
    print(reader.fieldnames)
    return list(reader)

def _interpret_items(items, origin_id, methodology_url):
    results = []
    credibility = {
        'value': -1.,
        'confidence': 1.
    }
    for el in items:
        source = el['Source']
        # source = utils.get_url_source(reviewed_url)
        source_domain = utils.get_url_domain(source)
        result = {
            'url': methodology_url,
            'credibility': credibility,
            'itemReviewed': source,
            'original': {k: v.strip() for k,v in el.items()},
            'origin_id': origin_id,
            'domain': source_domain,
            'source': source,
            'granularity': 'source'
        }
        results.append(result)
    return results