import os
import json
import requests

from ... import utils
from . import OriginRealtime

class Origin(OriginRealtime):
    api_key: str
    api_endpoint: str

    def __init__(self):
        OriginRealtime.__init__(
            self = self,
            id = 'mywot',
            name = 'Web Of Trust',
            description = 'Ever wondered how to check if a website is safe? Get the community to do the website security checks for you.',
            homepage = 'https://mywot.com/',
            logo = 'https://www.mywot.com/images/logo.png',
            default_weight = 5
        )
        self.api_key = os.environ['MYWOT_KEY']
        self.api_userid = os.environ['MYWOT_USERID']
        self.api_endpoint = 'http://scorecard.api.mywot.com/v3/targets'

    def retrieve_domain_credibility(self, domain):
        return _retrieve_assessment(domain, self.api_endpoint, self.api_key, self.api_userid, self.id)

    def retrieve_source_credibility(self, source):
        return _retrieve_assessment(source, self.api_endpoint, self.api_key, self.api_userid, self.id)

    def retrieve_domain_credibility_multiple(self, domains):
        return _retrieve_assessment_multiple(domains, self.api_endpoint, self.api_endpoint, self.id)



def _retrieve_assessment(source, api_endpoint, api_key, api_userid, origin_id):
    api_response = _query_api([source], api_endpoint, api_key, api_userid).get(source, {})
    return _pack_response(api_response, origin_id)


def _retrieve_assessment_multiple(sources, api_endpoint, api_key, api_userid, origin_id):
    # the API allows up to 100 targets for each call
    all_results = {}
    for chunk in _split_in_chunks(sources, 100):
        api_response = _query_api(chunk, api_endpoint, api_key, api_userid)
        all_results = {**all_results, **api_response}

    packed_response = {k: _pack_response(v, origin_id) for k, v in all_results.items()}
    return packed_response

def _pack_response(response, origin_id):
    # condition for 'not evaluated'
    if 'target' not in response:
        return None
    target = response['target']
    review_url = f'https://www.mywot.com/en/scorecard/{target}'
    credibility = _get_credibility_measures(response)
    result = {
        'url': review_url,
        'credibility': credibility,
        'itemReviewed': target,
        'domain': utils.get_url_domain(target),
        'source': utils.get_url_source(target),
        'original': response,
        'origin_id': origin_id,
        'granularity': 'source'
    }
    return result


def _get_credibility_measures(assessment):
    safety_component = assessment.get('safety', {'reputations': 50, 'confidence': 0})
    credibility = (safety_component['reputations'] - 50) / 50
    confidence = safety_component['confidence'] / 100
    result = {
        'value': credibility,
        'confidence': confidence
    }
    return result

def _query_api(hosts, api_endpoint, api_key, api_userid):
    """maximum 100 hosts per request https://www.mywot.com/wiki/index.php/API"""
    if len(hosts) > 100:
        raise ValueError(f'API only allows up to 100 hosts per request! Received call with {len(hosts)}')
    # hosts_param = '/'.join(hosts) + '/'
    response = requests.get(api_endpoint, params={'t': hosts}, headers={
        'x-api-key': api_key,
        'x-user-id': api_userid
    })
    response.raise_for_status()
    json_string = response.text
    content = json.loads(json_string)
    # return dict by host
    result = {el['target']: el for el in content}
    return result

def _get_reputation_range(reputation_value):
    reputation_groups = ['Very poor', 'Poor', 'Unsatisfactory', 'Good', 'Excellent']
    index = min(reputation_value, 99) * len(reputation_groups) // 100
    return reputation_groups[index]

def _split_in_chunks(iterable, chunk_size):
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i:i+chunk_size]
