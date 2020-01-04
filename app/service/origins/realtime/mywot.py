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
        self.api_endpoint = 'http://api.mywot.com/0.4/public_link_json2'

    def retrieve_domain_credibility(self, domain):
        return _retrieve_assessment(domain, self.api_endpoint, self.api_key, self.id)

    def retrieve_source_credibility(self, source):
        return _retrieve_assessment(source, self.api_endpoint, self.api_key, self.id)

    def retrieve_domain_credibility_multiple(self, domains):
        return _retrieve_assessment_multiple(domains, self.api_endpoint, self.api_endpoint, self.id)



def _retrieve_assessment(source, api_endpoint, api_key, origin_id):
    api_response = _query_api([source], api_endpoint, api_key).get(source, {})
    return _pack_response(api_response, origin_id)


def _retrieve_assessment_multiple(sources, api_endpoint, api_key, origin_id):
    # the API allows up to 100 targets for each call
    all_results = {}
    for chunk in _split_in_chunks(sources, 100):
        api_response = _query_api(chunk, api_endpoint, api_key)
        all_results = {**all_results, **api_response}

    packed_response = {k: _pack_response(v, origin_id) for k, v in all_results.items()}
    return packed_response

def _pack_response(response, origin_id):
    interpreted = _interpret_api_value(response)
    credibility = _get_credibility_measures(interpreted)
    # condition for 'not evaluated'
    if not interpreted['reputation_components']:
        return None
    review_url = interpreted['detail_page']
    result = {
        'url': review_url,
        'credibility': credibility,
        'itemReviewed': interpreted['target'],
        'domain': utils.get_url_domain(interpreted['target']),
        'source': utils.get_url_source(interpreted['target']),
        'original': interpreted,
        'origin_id': origin_id,
        'granularity': 'source'
    }
    return result


def _get_credibility_measures(assessment):
    trustworthiness_component = assessment['reputation_components'].get('0', {'reputation_value': 50, 'confidence': 0})
    credibility = (trustworthiness_component['reputation_value'] - 50) / 50
    confidence = trustworthiness_component['confidence'] / 100
    result = {
        'value': credibility,
        'confidence': confidence
    }
    return result

def _query_api(hosts, api_endpoint, api_key):
    """maximum 100 hosts per request https://www.mywot.com/wiki/index.php/API"""
    if len(hosts) > 100:
        raise ValueError(f'API only allows up to 100 hosts per request! Received call with {len(hosts)}')
    hosts_param = '/'.join(hosts) + '/'
    response = requests.get(api_endpoint, params={'hosts': hosts_param, 'key': api_key})
    response.raise_for_status()
    json_string = response.text
    content = json.loads(json_string)
    return content

def _get_reputation_range(reputation_value):
    reputation_groups = ['Very poor', 'Poor', 'Unsatisfactory', 'Good', 'Excellent']
    index = min(reputation_value, 99) * len(reputation_groups) // 100
    return reputation_groups[index]

def _interpret_api_value(api_value):
    # from https://www.mywot.com/wiki/index.php/API
    reputation_component_map = {
        '0': 'Trustworthiness',
        '1': 'Deprecated',
        '2': 'Deprecated',
        '4': 'Child safety'
    }
    reputation_components = {}
    for k, v in reputation_component_map.items():
        reputation_item_raw = api_value.get(k, None)
        if reputation_item_raw:
            reputation_components[k] = {
                'type': v,
                'reputation_value': reputation_item_raw[0],
                'reputation_scale': _get_reputation_range(reputation_item_raw[0]),
                'confidence': reputation_item_raw[1]
            }
    categories_id_map = {
        '101': 'Malware or viruses',
        '102': 'Poor customer experience',
        '103': 'Phishing',
        '104': 'Scam',
        '105': 'Potentially illegal',
        '201': 'Misleading claims or unethical',
        '202': 'Privacy risks',
        '203': 'Suspicious',
        '204': 'Hate, discrimination',
        '205': 'Spam',
        '206': 'Potentially unwanted programs',
        '207': 'Ads / pop-ups',
        '301': 'Online tracking',
        '302': 'Alternative or controversial medicine',
        '303': 'Opinions, religion, politics',
        '304': 'Other',
        '501': 'Good site',
        '401': 'Adult content',
        '402': 'Incidental nudity',
        '403': 'Gruesome or shocking',
        '404': 'Site for kids'
    }
    categories_groups_map = {
        '101': 'Negative',
        '102': 'Negative',
        '103': 'Negative',
        '104': 'Negative',
        '105': 'Negative',
        '201': 'Questionable',
        '202': 'Questionable',
        '203': 'Questionable',
        '204': 'Questionable',
        '205': 'Questionable',
        '206': 'Questionable',
        '207': 'Questionable',
        '301': 'Neutral',
        '302': 'Neutral',
        '303': 'Neutral',
        '304': 'Neutral',
        '501': 'Positive',
        '401': 'Negative',
        '402': 'Questionable',
        '403': 'Questionable',
        '404': 'Positive'
    }
    blacklists_map = {
        'malware': 'Site is blacklisted for hosting malware.',
        'phishing': 'Site is blacklisted for hosting a phishing malware.',
        'scam': 'Site is blacklisted for hosting a scam (e.g. a rouge pharmacy).',
        'spam': 'Site is blacklisted for sending spam or being advertised in spam.'
    }
    blacklists = {k: {
        'description': blacklists_map[k],
        'time': v
    } for k,v in api_value.get('blacklists', {}).items()}
    target = api_value.get('target', None)
    result = {
        'target': target,
        'reputation_components': reputation_components,
        'categories': {k: {
            'category_group': categories_groups_map[k],
            'description': categories_id_map[k],
            'confidence': v
        } for k,v in api_value.get('categories', {}).items()},
        'blacklists': blacklists,
        'detail_page': f'https://www.mywot.com/en/scorecard/{target}'
    }
    return result

def _split_in_chunks(iterable, chunk_size):
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i:i+chunk_size]
