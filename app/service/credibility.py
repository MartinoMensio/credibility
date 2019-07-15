from .realtime_origins import newsguard, mywot
from .batch_origins import ntt, ifcn, opensources, adfontesmedia, mbfc, fact_checkers
from . import utils, persistence

batch_origins = {
    'ntt': ntt,
    'ifcn': ifcn,
    'opensources': opensources,
    'adfontesmedia': adfontesmedia,
    'mbfc': mbfc,
    'fact_checkers': fact_checkers
}
#batch_origins = {**batch_origins, **fact_checkers.get_factcheckers()}

realtime_origins = {
    'newsguard': newsguard,
    'mywot': mywot,
}

origins = {**batch_origins, **realtime_origins}

def get_source_credibility(source):
    """retrieve the credibility score for the source, by using the origins available"""
    # TODO be sure to be at the source level, e.g. use utils.get_domain but be careful to facebook/twitter/... platforms
    source = utils.get_url_domain(source)
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
        # there is something useful in the origins
        credibility_weighted = credibility_sum / (confidence_and_weights_sum)
        confidence_weighted = confidence_and_weights_sum / weights_sum
    else:
        # TODO maybe return a 404? For now we assume the client will look at the confidence
        credibility_weighted = 0.
        confidence_weighted = 0.

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
        print(f'origin {origin_id} not found')
        return None
    origin = origins[origin_id]
    if origin_id in batch_origins:
        origin_type = 'batch'
    else:
        origin_type = 'realtime'
    return {
        'id': origin_id,
        'weight': origin.WEIGHT,
        'homepage': origin.HOMEPAGE,
        'origin_type': origin_type,
        'assessments_count': persistence.get_origin_assessments_count(origin_id)
    }

def get_origins():
    result = []

    for origin_id in origins.keys():
        result.append(get_origin(origin_id))

    return result
