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
    source_url = 'https://sheets.googleapis.com/v4/spreadsheets/10nFzJbHbPho7_kMFCRoX7VsQLSNIB3EaUh4ITDlsV0M/values/Fact-checking%20sites?alt=json&key=AIzaSyBgCpWxIarQJSW5AuMxjIRIgLSHeDCcC-U'

    response = requests.get(source_url)
    print(response.text)
    response.raise_for_status()
    
    data = response.json()
    return data

def _interpret_table(table, origin_id, homepage):
    results = []

    headers = table['values'][0]

    for row in table['values'][1:]:

        properties = {key.replace('.', '_'): v.strip() for key, v in zip(headers, row)}
        itemReviewed = properties['URL']
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
            'original_label': 'Fact-checker',
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
