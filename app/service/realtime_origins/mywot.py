import os
import json
import requests

WEIGHT = 5

MY_NAME = 'mywot'
HOMEPAGE = 'https://mywot.com/'
API_ENDPOINT = 'http://api.mywot.com/0.4/public_link_json2'
MYWOT_KEY = os.environ['MYWOT_KEY']

def get_source_credibility(source):
    api_response = query_api([source])[source]
    interpreted = interpret_api_value(api_response)
    credibility = get_credibility_measures(interpreted)
    review_url = None
    if interpreted['reputation_components']:
        review_url = interpreted['detail_page']
    return {
        'url': review_url,
        'credibility': credibility,
        'itemReviewed': interpreted['target'],
        'original': interpreted,
        'origin': MY_NAME
    }



def get_credibility_measures(assessment):
    trustworthiness_component = assessment['reputation_components'].get('0', {'reputation_value': 50, 'confidence': 0})
    credibility = (trustworthiness_component['reputation_value'] - 50) / 50
    confidence = trustworthiness_component['confidence'] / 100
    result = {
        'value': credibility,
        'confidence': confidence
    }
    return result

def query_api(hosts):
    """maximum 100 hosts per request"""
    hosts_param = '/'.join(hosts) + '/'
    response = requests.get(API_ENDPOINT, params={'hosts': hosts_param, 'key': MYWOT_KEY})
    if response.status_code != 200:
        raise ValueError(response.status_code)
    json_string = response.text
    content = json.loads(json_string)
    return content

def get_reputation_range(reputation_value):
    reputation_groups = ['Very poor', 'Poor', 'Unsatisfactory', 'Good', 'Excellent']
    index = min(reputation_value, 99) * len(reputation_groups) // 100
    return reputation_groups[index]

def interpret_api_value(api_value):
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
                'reputation_scale': get_reputation_range(reputation_item_raw[0]),
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
    result = {
        'target': api_value['target'],
        'reputation_components': reputation_components,
        'categories': {k: {
            'category_group': categories_groups_map[k],
            'description': categories_id_map[k],
            'confidence': v
        } for k,v in api_value.get('categories', {}).items()},
        'blacklists': blacklists,
        'detail_page': 'https://www.mywot.com/en/scorecard/{}'.format(api_value['target'])
    }

    return result