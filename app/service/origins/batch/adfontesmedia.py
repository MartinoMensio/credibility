import requests
import tqdm
from bs4 import BeautifulSoup
from collections import defaultdict
from multiprocessing.pool import ThreadPool
from requests.exceptions import TooManyRedirects

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
    page = 1 # TODO check domains from page 4 
    all_urls = []
    while True:
        response = requests.get(f'{homepage}rankings-by-individual-news-source/{page}')
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        eval_urls = [el['href'] for el in soup.select('article h3 a')]
        print(f'adfontesmedia: page {page} {len(eval_urls)} eval_urls')
        if not eval_urls:
            break
        all_urls.extend(eval_urls)
        page += 1
    results = []
    needing_attention = []
    with ThreadPool(5) as pool:
        for assessment_scraped, url in tqdm.tqdm(pool.imap_unordered(_scrape_source_assessment, all_urls), total=len(all_urls)):
            if assessment_scraped:
                results.append(assessment_scraped)
            else:
                needing_attention.append(url)
    return results

def _scrape_source_assessment(url):
    origin_id = 'adfontesmedia'
    # retrieves and maps a single assessment
    try:
        response = requests.get(url)
    except TooManyRedirects:
        print('Too many redirects for', url)
        return None, url
    except Exception as e:
        print(e)
        print(url)
        raise ValueError(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    title = soup.select_one('h2.elementor-heading-title')
    # print(title)
    if not title:
        raise ValueError(url)
    source_name = title.text.replace(' Bias and Reliability', '')
    source_name = source_name.replace('–', '')
    source_name = source_name.strip()
    first_url = soup.select_one('table td a')
    if first_url:
        first_url = first_url['onclick'].split("'")[1]
        source = utils.get_url_source(first_url)
        domain = utils.get_url_source(first_url)
    else:
        # no table, search in the description
        homepage = soup.select_one('.post-content a')
        if homepage:
            homepage_url = homepage['href']
            source = utils.get_url_source(homepage_url)
            domain = utils.get_url_source(homepage_url)
        else:
            # search with the mappings
            source_url = utils.name_domain_map.get(source_name)
            if source_url == None:
                print('adfontesmedia: no source_url for', source_name, 'skipping')
                return None, url
            source = utils.get_url_source(source_url)
            domain = utils.get_url_source(source_url)

    ps = soup.select('div p strong')
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
        print('adfontesmedia: no score for', url, source_name, source, domain, 'skipping')
        return None
    row = {'Reliability': reliability, 'Bias': bias, 'url': url, 'source_name': source_name}
    credibility = _get_credibility_measures(row)

    score = row['Reliability']

    return {
        'url': url,
        'credibility': credibility,
        'itemReviewed': source,
        'original': row,
        'original_label': f'Reliability: {score} out of 64',
        'origin_id': origin_id,
        'domain': domain,
        'source': source,
        'granularity': 'source'
    }, url


def _get_table(homepage):
    # deprecated: the csv is here https://www.adfontesmedia.com/
    # https://docs.google.com/spreadsheets/d/1nmUD5CglEuHq6airlHWI8AWtsQ5XjIdKRxUHF4IVUDM/edit#gid=24078135
    source_url = 'https://sheets.googleapis.com/v4/spreadsheets/1nmUD5CglEuHq6airlHWI8AWtsQ5XjIdKRxUHF4IVUDM/values/Articles?alt=json&key=AIzaSyBgCpWxIarQJSW5AuMxjIRIgLSHeDCcC-U'

    response = requests.get(source_url)
    response.raise_for_status()
    
    table = response.json()

    headers = table['values'][0]

    cleaned_table = []
    for row in table['values'][1:]:
        properties = {key.replace('.', '_'): v.strip() for key, v in zip(headers, row)}
        cleaned_table.append(properties)
    return cleaned_table

    # response = requests.get(f'{homepage}interactive-media-bias-chart/')
    # response.raise_for_status()

    # soup = BeautifulSoup(response.text, 'lxml')
    # table_element = soup.find('table')
    # table_headers = [el.text.strip()
    #                  for el in table_element.select('thead tr th')]
    # results = []
    # for tr in table_element.select('tbody tr'):
    #     fields = [el.text.strip() for el in tr.select('td')]
    #     row_parsed = {header: value for header,
    #                   value in zip(table_headers, fields)}
    #     results.append(row_parsed)
    #
    # return results

def _interpret_assessments(table, origin_id, homepage):
    # deprecated
    results = {}

    for ass in table:
        source_name = ass['Source']
        url = ass['Url']
        domain = utils.get_url_domain(url)
        source = utils.get_url_source(url)
        credibility = _get_credibility_measures(ass)

        score = ass.get('Quality', None)

        result = {
            'url': homepage,
            'credibility': credibility,
            'itemReviewed': url,
            'original': ass,
            'origin_id': origin_id,
            'original_label': f'Quality: {score} out of 64',
            'domain': domain,
            'source': source,
            'granularity': 'url'
        }
        results[url] = result

    return results.values()
