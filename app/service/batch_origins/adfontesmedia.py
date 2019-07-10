import requests
from bs4 import BeautifulSoup

from .. import utils, persistence

WEIGHT = 1

MY_NAME = 'adfontesmedia'

HOMEPAGE = 'https://www.adfontesmedia.com/'

def get_source_credibility(source):
    return persistence.get_domain_assessment(MY_NAME, source)

def update():
    table = get_table()
    result = interpret_assessments(table)
    print(MY_NAME, 'retrieved', len(result), 'assessments')
    persistence.save_origin(MY_NAME, result)
    return len(result)



def get_table():
    # the csv is here https://www.adfontesmedia.com/
    response = requests.get(HOMEPAGE)
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
    quality = row['Vertical Rank']
    return {
        'value': (float(quality) - 50) / 50,
        'confidence': 1.0
    }

def interpret_assessments(table):
    results = {}

    for ass in table:
        source_name = ass['News Source']
        source = utils.name_domain_map[source_name]
        domain = utils.get_url_domain(source)
        credibility = get_credibility_measures(ass)

        result = {
            'url': HOMEPAGE,
            'credibility': credibility,
            'itemReviewed': source,
            'original': ass,
            'origin': MY_NAME,
            'domain': domain
        }
        results[source] = result
    return results.values()
