import requests
from bs4 import BeautifulSoup

from ... import utils
from . import OriginBatch

class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self = self,
            id = 'fakenewscodex',
            name = 'The Fake News Codex',
            description = 'This site was created to identify “news” sites that are fake, extremely misleading, or satirical. There’s no shortage of similar resources purporting to list fake news sites but they are often infrequently updated, politically slanted, or difficult to use. The Fake News Codex does not include sites that merely have a clear political or ideological bias – Daily Kos and Breitbart will not appear here. We do include sites that are not necessarily intended to mislead (such as The Onion and its legion of imitators), but that can be misunderstood by naive readers.  These are marked with the “satire” tag.',
            homepage = 'http://www.fakenewscodex.com/',
            logo = 'https://logo.clearbit.com/fakenewscodex.com',
            default_weight = 2
        )

    def retreive_source_assessments(self):
        return _retrieve_assessments(self.id, self.homepage)

def _retrieve_assessments(origin_id, homepage):
    table = _download_from_source(homepage)
    result_source_level = _interpret_table(table, origin_id)
    return result_source_level


def _interpret_table(table, origin_id):
    results = []
    for row in table:
        itemReviewed = row['homepage']
        domain = utils.get_url_domain(itemReviewed)
        source = utils.get_url_source(itemReviewed)

        credibility = _get_credibility_measures(row)

        label = row['badge'].replace('badge--', '').capitalize()

        interpreted = {
            'url': row['details_url'],
            'credibility': credibility,
            'itemReviewed': itemReviewed,
            'original': row,
            'origin_id': origin_id,
            'original_label': label,
            'domain': domain,
            'source': source,
            'granularity': 'source'
        }

        results.append(interpreted)

    return results


def _download_from_source(homepage):
    response = requests.get(homepage)
    response.raise_for_status()

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

def _get_credibility_measures(row):
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
