import requests

from .. import utils, persistence

WEIGHT = 10

MY_NAME = 'newsguard'
HOMEPAGE = 'https://www.newsguardtech.com/'
API_ENDPOINT = 'https://api.newsguardtech.com/check'

def get_source_credibility(source):
    original_assessment = get_assessment(source)
    itemReviewed = original_assessment['identifier']
    review_url = None
    credibility = {'value': 0., 'confidence': 0.}
    found = False
    if itemReviewed:
        review_url = f'https://api.newsguardtech.com/{original_assessment["labelToken"]}'
        credibility = get_credibility_measures(original_assessment)
        found = True

    result = {
        'url': review_url,
        'credibility': credibility,
        'itemReviewed': itemReviewed,
        'domain': utils.get_url_domain(itemReviewed),
        'original': original_assessment,
        'origin': MY_NAME,
        'granularity': 'source'
    }
    if found:
        persistence.add_origin_assessment(MY_NAME, result)
    return result

def get_credibility_measures(original_assessment):
    rank = original_assessment['rank']
    confidence = 0.0
    credibility = 0.0
    if rank in ['T', 'N']:
        # positive and negative ranking
        credibility = (original_assessment['score'] - 50) / 50
        confidence = 1.0
    elif rank in ['TK', 'S']:
        # pending or platform
        confidence = 0.0
    elif rank in ['S']:
        # satire
        credibility = 0.0
        confidence = 1.0

    return {
        'value': credibility,
        'confidence': confidence
    }

def get_assessment(url):
    response = requests.get(API_ENDPOINT, params={'url': url})
    if response.status_code != 200:
        print('error for', url)
        return None
        #raise ValueError(response.status_code)
    return response.json()