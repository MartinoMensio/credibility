import requests
from bs4 import BeautifulSoup

from ... import utils
from . import OriginBatch

class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self = self,
            id = 'realorsatire',
            name = 'Real or Satire',
            description = 'Tired of sharing an article that filled you with righteous indignation, only to be scolded by your social media circle for posting fake news? Tired of living in constant fear that the ‘news’ you read isn’t actually news? Wish there was a one-stop shop to check if a site is ‘satirical’ or submit a site to be labeled as ‘satire’? Well, now there’s Real or Satire.',
            homepage = 'https://realorsatire.com',
            logo = 'http://logo.clearbit.com/realorsatire.com',
            default_weight = 1
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
        itemReviewed = row['domain']
        domain = itemReviewed
        source = utils.get_url_source(itemReviewed)

        credibility = get_credibility_measures(row)

        interpreted = {
            'url': row['details_url'],
            'credibility': credibility,
            'itemReviewed': itemReviewed,
            'original': row,
            'origin_id': origin_id,
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

    categories = soup.select('li.cat-item a')
    results = []
    for c in categories:
        category_url = c['href']
        # category_name = c.text

        page = 1
        while True:
            page_url = f'{category_url}page/{page}/'
            response = requests.get(page_url)
            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, 'lxml')

            websites = soup.select('article.post')
            #print(page_url, len(websites))
            for ws in websites:
                a = ws.select_one('h2.entry-title a')
                domain = a.text.strip()
                details_url = a['href']
                category_list = [el.text.strip().lower() for el in ws.select('h3.post-category a')]
                description = ws.select_one('p.lead').text.strip()
                r = {
                    'details_url': details_url,
                    'domain': domain,
                    'category_list': category_list,
                    'description': description,
                }
                results.append(r)
            page += 1

    # remove duplicates (e.g. some items belong to more than one category)
    results = [el for el in {el2['domain']: el2 for el2 in results}.values()]

    return results

def get_credibility_measures(row):
    value = 0.
    confidence = 0.
    categories = row['category_list']
    if 'real' in categories:
        value += 1
        confidence += 1
    if 'satire' in categories:
        pass
    if 'neither' in categories:
        confidence += 1
    if 'biased' in categories:
        value += -0.5
        confidence += 1
    if 'clickbait' in categories:
        value += -0.5
        confidence += 1
    if 'green ink' in categories:
        # how to deal with this?
        pass

    if value:
        value = value / confidence
    if confidence:
        confidence = confidence / len(categories)

    return {
        'value': value,
        'confidence': confidence
    }
