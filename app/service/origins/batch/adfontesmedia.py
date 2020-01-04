import requests
import tqdm
from bs4 import BeautifulSoup
from collections import defaultdict
from multiprocessing.pool import ThreadPool

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
        return _retrieve_urls_assessments(self.id, self.homepage)

    def retreive_source_assessments(self):
        return _retrieve_source_assessments(self.id, self.homepage)

    def update(self):
        # the credibility of the source is already aggregated by AdFontesMedia, so the first two flags are disabled.
        # The source-to-domain is enabled instead
        return super().update(False, False, True)
        


def _retrieve_urls_assessments(origin_id, homepage):
    table = _get_table(homepage)
    result_document_level = _interpret_assessments(table, origin_id, homepage)
    return result_document_level

def _retrieve_source_assessments(origin_id, homepage):
    scores = _get_sources_scores(homepage)
    return scores

def _get_credibility_measures(row):
    # vertical rank is quality
    quality = row.get('Quality', None)
    if quality:
        quality = float(quality)
        # maximum value is 64 https://www.adfontesmedia.com/white-paper-multi-analyst-ratings-project-august-2019/
        value = (quality / 64 - 0.5) * 2
    else:
        # reliability value in 0-64 scale, bias in -42 to +42
        reliability = row['Reliability']
        value = (reliability / 64 - 0.5) * 2
    return {
        'value': value,
        'confidence': 1.0
    }

def _get_sources_scores(homepage):
    response = requests.get(f'{homepage}rankings-by-individual-news-source/')
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    eval_urls = [el['href'] for el in soup.select('article h2 a')]
    results = []
    with ThreadPool(5) as pool:
        for assessment_scraped in tqdm.tqdm(pool.imap_unordered(_scrape_source_assessment, eval_urls), total=len(eval_urls)):
            if assessment_scraped:
                results.append(assessment_scraped)
    return results

def _scrape_source_assessment(url):
    origin_id = 'adfontesmedia'
    # retrieves and maps a single assessment
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    title = soup.select_one('h1.entry-title')
    # print(title)
    if not title:
        raise ValueError(url)
    source_name = title.text.replace(' Bias and Reliability', '')
    source_name = source_name.replace('–', '')
    source_name = source_name.strip()
    first_url = soup.select_one('table td a')
    if first_url:
        first_url = first_url['href']
        source = utils.get_url_source(first_url)
        domain = utils.get_url_source(first_url)
    else:
        # no table, search with the mappings
        source_url = utils.name_domain_map[source_name]
        source = utils.get_url_source(source_url)
        domain = utils.get_url_source(source_url)

    ps = soup.select('div.post-content p')
    reliability = None
    bias = None
    for p in ps:
        text = p.text.strip()
        if text.startswith('Reliability: '):
            reliability = float(text.replace('Reliability: ', ''))
        elif text.startswith('Bias: '):
            bias = float(text.replace('Bias: ', ''))
    if reliability == None:
        # some don't have a score yet (https://www.adfontesmedia.com/nbc-bias-and-reliability/)
        return None
    row = {'Reliability': reliability, 'Bias': bias, 'url': url, 'source_name': source_name}
    credibility = _get_credibility_measures(row)

    return {
        'url': url,
        'credibility': credibility,
        'itemReviewed': url,
        'original': row,
        'origin_id': origin_id,
        'domain': domain,
        'source': source,
        'granularity': 'source'
    }


def _get_table(homepage):
    # deprecated: the csv is here https://www.adfontesmedia.com/
    response = requests.get(f'{homepage}interactive-media-bias-chart/')
    response.raise_for_status()

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

def _interpret_assessments(table, origin_id, homepage):
    # deprecated
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
