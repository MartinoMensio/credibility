import requests
from bs4 import BeautifulSoup

from .. import utils, persistence

WEIGHT = 1


ID = 'realorsatire'
NAME = 'Real or Satire'
DESCRIPTION = 'Tired of sharing an article that filled you with righteous indignation, only to be scolded by your social media circle for posting fake news? Tired of living in constant fear that the ‘news’ you read isn’t actually news? Wish there was a one-stop shop to check if a site is ‘satirical’ or submit a site to be labeled as ‘satire’? Well, now there’s Real or Satire.'

HOMEPAGE = 'https://realorsatire.com'


def get_source_credibility(source):
    return persistence.get_source_assessment(ID, source)

def get_domain_credibility(domain):
    return persistence.get_domain_assessment(ID, domain)

def get_url_credibility(url):
    return None

def update():
    table = download_from_source()
    result_source_level = interpret_table(table)
    result_domain_level = utils.aggregate_domain(result_source_level, ID)
    print(ID, 'retrieved', len(result_domain_level), 'domains', len(result_source_level), 'sources', 'assessments') # , len(result_document_level), 'documents'
    all_assessments = list(result_source_level) + list(result_domain_level) # list(result_document_level) +
    persistence.save_assessments(ID, all_assessments)
    return len(all_assessments)


def interpret_table(table):
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
            'origin_id': ID,
            'domain': domain,
            'source': source,
            'granularity': 'source'
        }

        results.append(interpreted)

    return results


def download_from_source():
    response = requests.get(HOMEPAGE)
    if response.status_code != 200:
        raise ValueError(response.status_code)

    soup = BeautifulSoup(response.text, 'lxml')

    categories = soup.select('li.cat-item a')
    results = []
    for c in categories:
        category_url = c['href']
        category_name = c.text

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
