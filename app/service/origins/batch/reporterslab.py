import requests

from ... import utils
from . import OriginBatch

class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self = self,
            id = 'reporterslab',
            name = 'Reporters\' Lab',
            description = 'The Reporters’ Lab maintains a database of global fact-checking sites.',
            homepage = 'https://reporterslab.org/fact-checking/',
            logo = 'http://logo.clearbit.com/reporterslab.org',
            default_weight = 5
        )

    def retreive_source_assessments(self):
        return _retrieve_assessments(self.id, self.homepage)


def _retrieve_assessments(origin_id, homepage):
    print('called update')
    table = _download_from_source()
    result_source_level = _interpret_table(table, origin_id, homepage)
    return result_source_level

def _download_from_source():
    source_url = 'https://spreadsheets.google.com/feeds/list/10nFzJbHbPho7_kMFCRoX7VsQLSNIB3EaUh4ITDlsV0M/1/public/values?alt=json'

    response = requests.get(source_url)
    if response.status_code != 200:
        raise ValueError(response.status_code)
    data = response.json()
    return data

def _interpret_table(table, origin_id, homepage):
    results = []

    for row in table['feed']['entry']:

        properties = {k[4:].replace('.', '_'): v['$t'].strip() for k, v in row.items() if k.startswith('gsx$')}
        itemReviewed = properties['url']
        if itemReviewed == 'no website':
            continue
        domain = utils.get_url_domain(itemReviewed)
        source = utils.get_url_source(itemReviewed)

        credibility = _get_credibility_measures(row)

        interpreted = {
            'url': homepage, # there is no deep linking
            'credibility': credibility,
            'itemReviewed': itemReviewed,
            'original': properties,
            'origin_id': origin_id,
            'domain': domain,
            'source': source,
            'granularity': 'source'
        }

        results.append(interpreted)

    return results

def _get_credibility_measures(row):
    value = 1.
    confidence = 1.

    return {
        'value': value,
        'confidence': confidence
    }
