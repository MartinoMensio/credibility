from multiprocessing.pool import ThreadPool
import tqdm

from .realtime_origins import newsguard, mywot
from .batch_origins import ntt, ifcn, opensources, adfontesmedia, mbfc, lemonde_decodex, fakenewscodex, realorsatire, reporterslab
from .batch_origins import factchecking_report
from . import utils, persistence

POOL_SIZE = 30

batch_origins = {
    'ntt': ntt,
    'ifcn': ifcn,
    'opensources': opensources,
    'adfontesmedia': adfontesmedia,
    'mbfc': mbfc,
    'factchecking_report': factchecking_report,
    'lemonde_decodex': lemonde_decodex,
    'fakenewscodex': fakenewscodex,
    'realorsatire': realorsatire,
    'reporterslab': reporterslab
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
    #source = utils.get_url_domain(source)
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

        final_weight = credibility_confidence * origin_weight
        confidence_and_weights_sum += final_weight
        #confidence_sum +=
        credibility_sum += credibility_value * origin_weight * credibility_confidence
        weights_sum += origin_weight

        assessment['origin_id'] = origin_id
        assessment['origin'] = get_origin(origin_id)
        assessment['weights'] = {
            'origin_weight': origin_weight,
            'final_weight': final_weight
        }

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
        'assessments': list(assessments.values()),
        'itemReviewed': source
    }

def get_source_credibility_tuple_wrap(argument):
    """This method wraps another method giving back a tuple of (argument, result)"""
    result = get_source_credibility(argument)
    return (argument, result)

def get_source_credibility_parallel(sources):
    sources = set(sources)
    results = {}
    with ThreadPool(POOL_SIZE) as pool:
        for result_tuple in tqdm.tqdm(pool.imap_unordered(get_source_credibility_tuple_wrap, sources), total=len(sources)):
            source, result = result_tuple
            if result:
                results[source] = result
    return results


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
        'name': origin.NAME,
        'description': origin.DESCRIPTION,
        'origin_type': origin_type,
        'assessments_count': persistence.get_origin_assessments_count(origin_id)
    }

def get_origins():
    result = []

    for origin_id in origins.keys():
        result.append(get_origin(origin_id))

    return result
