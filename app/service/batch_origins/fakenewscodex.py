import requests
from bs4 import BeautifulSoup

from .. import utils, persistence

WEIGHT = 2


ID = 'fakenewscodex'
NAME = 'The Fake News Codex'
DESCRIPTION = 'This site was created to identify “news” sites that are fake, extremely misleading, or satirical. There’s no shortage of similar resources purporting to list fake news sites but they are often infrequently updated, politically slanted, or difficult to use. The Fake News Codex does not include sites that merely have a clear political or ideological bias – Daily Kos and Breitbart will not appear here. We do include sites that are not necessarily intended to mislead (such as The Onion and its legion of imitators), but that can be misunderstood by naive readers.  These are marked with the “satire” tag.'

HOMEPAGE = 'http://www.fakenewscodex.com/'


def get_source_credibility(source):
    return persistence.get_domain_assessment(ID, source)

def update():
    table = download_from_source()
    result = interpret_table(table)
    print(ID, 'retrieved', len(result), 'assessments')
    persistence.save_origin_assessments(ID, result)
    return len(result)


def interpret_table(table):
    results = []
    for row in table:
        itemReviewed = row['homepage']
        domain = utils.get_url_domain(itemReviewed)
        source = utils.get_url_source(itemReviewed)

        credibility = get_credibility_measures(row)

        interpreted = {
            'url': row['details_url'],
            'credibility': credibility,
            'itemReviewed': itemReviewed,
            'original': row,
            'origin': ID,
            'domain': domain,
            'source': source,
            'granularity': 'source'
        }

        results.append(interpreted)

    # get only the assessment domain level
    results_domain = [el for el in results if el['source'] == el['domain']]

    # TODO do that in more structured way:
    # results_source = utils.aggregate_domain(results, ID)

    return results_domain


def download_from_source():
    response = requests.get(HOMEPAGE)
    if response.status_code != 200:
        raise ValueError(response.status_code)

    soup = BeautifulSoup(response.text, 'lxml')

    source_list = soup.select('ul li[class*=badge--]')
    results = []
    for s in source_list:
        badge = next(c for c in s['class'] if 'badge--' in c)
        a = s.select_one('a.c-sites-list__link')
        name = a.text.strip()
        details_url = a['href']
        homepage = s.select_one('div.c-sites-list__url').text.strip()
        description = s.select_one('p.c-sites-list__excerpt').text.strip()
        r = {
            'badge': badge,
            'name': name,
            'homepage': homepage,
            'description': description,
            'details_url': details_url
        }
        results.append(r)

    # remove duplicates (e.g. 'http://www.thespoof.com' is ranked twice as fake)
    results = [el for el in {el2['homepage']: el2 for el2 in results}.values()]

    return results

def get_credibility_measures(row):
    value = 0.
    confidence = 0.
    badge = row['badge']
    if 'fake' in badge:
        value = -1.
        confidence = 1.
    elif 'satire' in badge:
        pass
    else:
        raise ValueError(badge)

    return {
        'value': value,
        'confidence': confidence
    }
