import requests
from bs4 import BeautifulSoup
from collections import defaultdict

from ... import utils
from . import OriginBatch


class Origin(OriginBatch):

    def __init__(self):
        OriginBatch.__init__(
            self = self,
            id = 'adfontesmedia',
            name = 'Ad Fontes Media',
            description = 'Navigate the News Landscape and Contribute to a Healthy Democracy.',
            homepage = 'https://www.adfontesmedia.com/',
            logo = 'https://www.adfontesmedia.com/wp-content/uploads/2018/08/ad-fonts-media-favicon-66x66.png',
            default_weight = 1
        )

    def retreive_urls_assessments(self):
        return _retrieve_assessments(self.id, self.homepage)


def _retrieve_assessments(origin_id, homepage):
    table = _get_table(homepage)
    result_document_level = _interpret_assessments(table, origin_id, homepage)
    return result_document_level


def _get_table(homepage):
    # the csv is here https://www.adfontesmedia.com/
    response = requests.get(f'{homepage}interactive-media-bias-chart/')
    if response.status_code != 200:
        raise ValueError(response.status_code)
    soup = BeautifulSoup(response.text, 'lxml')
    table_element = soup.find('table')
    table_headers = [el.text.strip()
                     for el in table_element.select('thead tr th')]
    results = []
    for tr in table_element.select('tbody tr'):
        fields = [el.text.strip() for el in tr.select('td')]
        row_parsed = {header: value for header,
                      value in zip(table_headers, fields)}
        results.append(row_parsed)

    return results


def _get_credibility_measures(row):
    # vertical rank is quality
    quality = row['Quality']
    quality = float(quality)
    # maximum value is 64 https://www.adfontesmedia.com/white-paper-multi-analyst-ratings-project-august-2019/
    quality_rescaled = (quality / 64 - 0.5) * 2
    return {
        'value': quality_rescaled,
        'confidence': 1.0
    }


def _interpret_assessments(table, origin_id, homepage):
    results = {}

    for ass in table:
        source_name = ass['Source']
        url = ass['Url']
        domain = utils.get_url_domain(url)
        source = utils.get_url_source(url)
        credibility = _get_credibility_measures(ass)

        result = {
            'url': homepage,
            'credibility': credibility,
            'itemReviewed': url,
            'original': ass,
            'origin_id': origin_id,
            'domain': domain,
            'source': source,
            'granularity': 'url'
        }
        results[url] = result

    return results.values()
