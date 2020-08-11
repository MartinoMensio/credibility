import requests
import re
from bs4 import BeautifulSoup
from collections import defaultdict

from ... import utils
from . import OriginBatch


class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self = self,
            id = 'covid_national_sources',
            name = 'National information resources on COVID-19',
            description = 'Latest information and advice from the EU/EEA countries and UK on the outbreak of COVID-19',
            homepage = 'https://www.ecdc.europa.eu/en/COVID-19/national-sources',
            logo = 'https://www.ecdc.europa.eu/profiles/custom/ecdc/themes/anthrax/images/logo-ecdc.png',
            default_weight = 8
        )

    def retreive_source_assessments(self):
        return _retrieve_assessments(self.id, self.homepage)

def _retrieve_assessments(origin_id, homepage):
    original_items = _download_assessments(homepage)
    result_source_level = _interpret_items(original_items, origin_id, homepage)
    return result_source_level


def _download_assessments(homepage):
    response = requests.get(homepage)
    response.raise_for_status()
    
    xmlstring = response.text
    # remove namespace that 
    # xmlstring = re.sub(r'\sxmlns="[^"]+"', '', xmlstring, count=1)
    soup = BeautifulSoup(xmlstring, 'lxml')
    # print(soup)
    table_element = soup.find('table')
    table_headers = [el.text.strip()
                     for el in table_element.select('thead tr th')]
    results = []
    for tr in table_element.select('tbody tr'):
        fields = [el for el in tr.select('th') + tr.select('td')]
        row_parsed = {header: value for header,
                      value in zip(table_headers, fields)}
        results.append(row_parsed)
    print(len(results))
    return results

def _interpret_items(original_items, origin_id, homepage):
    results = []
    assessment_url = homepage

    credibility = {
        'value': 1.,
        'confidence': 1.
    }
    for el in original_items:
        print(el)
        websites = el['Website'].select('a')
        for website in websites:
            reviewed_url = website['href']
            source = utils.get_url_source(reviewed_url)
            source_domain = utils.get_url_domain(source)
            result = {
                'url': assessment_url,
                'credibility': credibility,
                'itemReviewed': reviewed_url,
                'original': {k: v.text.strip() for k,v in el.items()},
                'origin_id': origin_id,
                'domain': source_domain,
                'source': source,
                'granularity': 'source'
            }
            results.append(result)

    return results
