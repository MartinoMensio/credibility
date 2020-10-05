import requests

from ... import utils, persistence
from . import OriginRealtime

class Origin(OriginRealtime):
    def __init__(self):
        OriginRealtime.__init__(
            self = self,
            id = 'newsguard',
            name = 'NewsGuard',
            description = 'NewsGuard uses journalism to fight false news, misinformation, and disinformation. Our trained analysts, who are experienced journalists, research online news brands to help readers and viewers know which ones are trying to do legitimate journalism--and which are not.',
            homepage = 'https://www.newsguardtech.com/',
            logo = 'https://logo.clearbit.com/newsguardtech.com',
            default_weight = 10,
        )
        self.api_endpoint = 'https://api.newsguardtech.com/check'

    def retrieve_domain_credibility(self, domain):
        return _retrieve_assessment(domain, self.api_endpoint, self.id)

    def retrieve_source_credibility(self, source):
        result = _retrieve_assessment(source, self.api_endpoint, self.id)
        # TODO the following does not work because the db _id is on the domain, so only domain-level or source-level can be stored
        # if result:
        #     results_domain = utils.aggregate_domain([result], self.id)
        #     persistence.save_assessments(self.id, results_domain)
        return result

def _retrieve_assessment(source, api_endpoint, origin_id):
    original_assessment = _query_assessment(source, api_endpoint)
    # condition for failure
    if not original_assessment:
        return None
    itemReviewed = original_assessment['identifier']
    # condition for 'not evaluated'
    if not itemReviewed:
        return None
    review_url = f'https://api.newsguardtech.com/{original_assessment["labelToken"]}'
    credibility = _get_credibility_measures(original_assessment)

    result = {
        'url': review_url,
        'credibility': credibility,
        'itemReviewed': itemReviewed,
        'domain': utils.get_url_domain(itemReviewed),
        'source': utils.get_url_source(itemReviewed),
        'original': original_assessment,
        'origin_id': origin_id,
        'granularity': 'source'
    }
    return result

def _get_credibility_measures(original_assessment):
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

def _query_assessment(url, api_endpoint):
    try:
        response = requests.get(api_endpoint, params={'url': url}, timeout=1)
    except requests.exceptions.RequestException:
        return None
    if response.status_code != 200:
        print('error for', url)
        # for some sources (e.g., tinyurl.com) the response is HTTP 500
        return None
    return response.json()
