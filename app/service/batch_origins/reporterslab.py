import requests

from .. import utils, persistence

WEIGHT = 5

ID = 'reporterslab'
NAME = 'Reporters\' Lab'
DESCRIPTION = 'The Reporters’ Lab maintains a database of global fact-checking sites.'

HOMEPAGE = 'https://reporterslab.org/fact-checking/'

def get_source_credibility(source):
    return persistence.get_source_assessment(ID, source)

def get_domain_credibility(domain):
    return persistence.get_domain_assessment(ID, domain)

def get_url_credibility(url):
    return None

def update():
    print('called update')
    table = download_from_source()
    result_source_level = interpret_table(table)
    result_domain_level = utils.aggregate_domain(result_source_level, ID)
    print(ID, 'retrieved', len(result_domain_level), 'domains', len(result_source_level), 'sources', 'assessments') # , len(result_document_level), 'documents'
    all_assessments = list(result_source_level) + list(result_domain_level) # list(result_document_level) +
    persistence.save_assessments(ID, all_assessments)
    return len(all_assessments)

def download_from_source():
    source_url = 'https://spreadsheets.google.com/feeds/list/10nFzJbHbPho7_kMFCRoX7VsQLSNIB3EaUh4ITDlsV0M/1/public/values?alt=json'

    response = requests.get(source_url)
    if response.status_code != 200:
        raise ValueError(response.status_code)
    data = response.json()
    return data

def interpret_table(table):
    results = []

    for row in table['feed']['entry']:

        properties = {k[4:].replace('.', '_'): v['$t'].strip() for k, v in row.items() if k.startswith('gsx$')}
        itemReviewed = properties['url']
        if itemReviewed == 'no website':
            continue
        domain = utils.get_url_domain(itemReviewed)
        source = utils.get_url_source(itemReviewed)

        credibility = get_credibility_measures(row)

        interpreted = {
            'url': HOMEPAGE, # there is no deep linking
            'credibility': credibility,
            'itemReviewed': itemReviewed,
            'original': properties,
            'origin_id': ID,
            'domain': domain,
            'source': source,
            'granularity': 'source'
        }

        results.append(interpreted)

    return results

def get_credibility_measures(row):
    value = 1.
    confidence = 1.

    return {
        'value': value,
        'confidence': confidence
    }
