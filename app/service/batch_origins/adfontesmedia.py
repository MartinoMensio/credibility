import requests
from bs4 import BeautifulSoup
from collections import defaultdict

from .. import utils, persistence

WEIGHT = 1

MY_NAME = 'adfontesmedia'

HOMEPAGE = 'https://www.adfontesmedia.com/'

def get_source_credibility(source):
    return persistence.get_domain_assessment(MY_NAME, source)

def update():
    table = get_table()
    result_doc_level = interpret_assessments(table)
    result_source_level = utils.aggregate_domain(result_doc_level, MY_NAME)
    print(MY_NAME, 'retrieved', len(result_source_level), 'assessments')
    persistence.save_origin_assessments(MY_NAME, result_source_level)
    return len(result_source_level)



def get_table():
    # the csv is here https://www.adfontesmedia.com/
    response = requests.get(f'{HOMEPAGE}interactive-media-bias-chart/')
    if response.status_code != 200:
        raise ValueError(response.status_code)
    soup = BeautifulSoup(response.text, 'lxml')
    table_element = soup.find('table')
    table_headers = [el.text.strip() for el in table_element.select('thead tr th')]
    results = []
    for tr in table_element.select('tbody tr'):
        fields = [el.text.strip() for el in tr.select('td')]
        row_parsed = {header: value for header, value in zip(table_headers, fields)}
        results.append(row_parsed)
    return results

    raise NotImplementedError()

def get_credibility_measures(row):
    # vertical rank is quality
    quality = row['Quality']
    quality = float(quality)
    # maximum value is 64 https://www.adfontesmedia.com/white-paper-multi-analyst-ratings-project-august-2019/
    quality_rescaled = (quality / 64 - 0.5) * 2
    return {
        'value': quality_rescaled,
        'confidence': 1.0
    }

def interpret_assessments(table):
    results = {}

    for ass in table:
        source_name = ass['Source']
        url = ass['Url']
        domain = utils.get_url_domain(url)
        source = utils.get_url_source(url)
        credibility = get_credibility_measures(ass)

        result = {
            'url': HOMEPAGE,
            'credibility': credibility,
            'itemReviewed': url,
            'original': ass,
            'origin': MY_NAME,
            'domain': domain,
            'source': source,
            'granularity': 'document'
        }
        results[url] = result

    return results.values()
