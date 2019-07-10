from .realtime_origins import newsguard, mywot
from .batch_origins import ntt, ifcn, opensources, adfontesmedia
from . import utils

batch_origins = {
    'ntt': ntt,
    'ifcn': ifcn,
    'opensources': opensources,
    'adfontesmedia': adfontesmedia
}

realtime_origins = {
    'newsguard': newsguard,
    'mywot': mywot,
}

origins = {**batch_origins, **realtime_origins}

def get_source_credibility(source):
    """retrieve the credibility score for the source, by using the origins available"""
    # TODO be sure to be at the source level, e.g. use utils.get_domain but be careful to facebook/twitter/... platforms
    assessments = {}
    credibility_sum = 0
    weights_sum = 0
    # accumulator for the trust*confidence
    confidence_and_weights_sum = 0

    for origin_id, origin in origins.items():
        assessment = origin.get_source_credibility(source)
        if not assessment:
            continue
        # TODO source evaluation, now is a fixed value
        origin_weight = origin.WEIGHT
        credibility_value = assessment['credibility']['value']
        credibility_confidence = assessment['credibility']['confidence']

        confidence_and_weights_sum += credibility_confidence * origin_weight
        #confidence_sum +=
        credibility_sum += credibility_value * origin_weight * credibility_confidence
        weights_sum += origin_weight

        assessments[origin_id] = assessment
    # weighted average
    if confidence_and_weights_sum:
        # there is something useful
        credibility_weighted = credibility_sum / (confidence_and_weights_sum)
    else:
        credibility_weighted = 0.
    confidence_weighted = confidence_and_weights_sum / weights_sum
    return {
        'credibility': {
            'value': credibility_weighted,
            'confidence': confidence_weighted
        },
        'assessments': assessments
    }


def get_url_credibility(url):
    # TODO
    raise NotImplementedError()

def update_batch_origin(origin_id):
    if origin_id not in batch_origins:
        return None
    origin = batch_origins[origin_id]
    print('updating', origin_id, '...')
    result = origin.update()
    print('updated', origin_id)
    return result


def update_batch_origins():
    counts = {}
    for origin_id, origin in batch_origins.items():
        counts[origin_id] = update_batch_origin(origin_id)

    return counts

def get_origin(origin_id):
    if origin_id not in origins:
        return None
    origin = origins[origin_id]
    return {
        'id': origin_id,
        'weight': origin.WEIGHT,
        'homepage': origin.HOMEPAGE
    }

def get_origins():
    result = []

    for origin_id, origin in origins.items():
        result.append(get_origin(origin_id))

    return result
