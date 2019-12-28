from multiprocessing.pool import ThreadPool
import tqdm
from collections import defaultdict

from .origins.batch import factchecking_report
from .origins.realtime import mywot, newsguard
from .origins.batch import adfontesmedia, fakenewscodex, ifcn, lemonde_decodex, mbfc, ntt, opensources, realorsatire, reporterslab, disinfo_eu_indian_net, wikipedia_lists

from . import utils, persistence

POOL_SIZE = 30

batch_origins = {
    'ntt': ntt.Origin(),
    'ifcn': ifcn.Origin(),
    'opensources': opensources.Origin(),
    'adfontesmedia': adfontesmedia.Origin(),
    'mbfc': mbfc.Origin(),
    'factchecking_report': factchecking_report.Origin(),
    'lemonde_decodex': lemonde_decodex.Origin(),
    'fakenewscodex': fakenewscodex.Origin(),
    'realorsatire': realorsatire.Origin(),
    'reporterslab': reporterslab.Origin(),
    'disinfo_eu_indian_net': disinfo_eu_indian_net.Origin(),
    'wikipedia_lists': wikipedia_lists.Origin()
}
# # TODO define this as a class
# for o in batch_origins.values():
#     # TODO see if the origin supports that level of evaluation
#     o.get_source_credibility = 'TODO'

realtime_origins = {
    'newsguard': newsguard.Origin(),
    'mywot': mywot.Origin(),
}

origins = {**batch_origins, **realtime_origins}

def get_domain_credibility(domain):
    get_fn_to_call = lambda el: el.get_domain_credibility
    return get_weighted_credibility(domain, get_fn_to_call)

def get_source_credibility(source):
    get_fn_to_call = lambda el: el.get_source_credibility
    return get_weighted_credibility(source, get_fn_to_call)

def get_url_credibility(url):
    get_fn_to_call = lambda el: el.get_url_credibility
    return get_weighted_credibility(url, get_fn_to_call)

def get_weighted_credibility(item, get_fn_to_call):
    """retrieve the credibility score for the source, by using the origins available"""
    # TODO be sure to be at the source level, e.g. use utils.get_domain but be careful to facebook/twitter/... platforms
    #source = utils.get_url_domain(source)
    assessments = {}
    # TODO make it an array, sort by final weight
    credibility_sum = 0
    weights_sum = 0
    # accumulator for the trust*confidence
    confidence_and_weights_sum = 0

    for origin_id, origin in origins.items():
        fn_to_call = get_fn_to_call(origin)
        assessment = fn_to_call(item)
        if not assessment:
            continue
        # TODO source evaluation, now is a fixed value
        origin_weight = origin.default_weight
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
        'itemReviewed': item
    }

def get_source_credibility_tuple_wrap(argument):
    """This method wraps another method giving back a tuple of (argument, result)"""
    # TODO: to avoid lots of calls, here we should allow cached results
    result = get_source_credibility(argument)
    return (argument, result)

def get_urls_credibility_tuple_wrap(argument):
    """This method wraps another method giving back a tuple of (argument, result)"""
    result = get_url_credibility(argument)
    return (argument, result)

def get_domain_credibility_multiple(domains):
    domains = list(set(domains))
    results = {}

    db_results_by_origin_id = defaultdict(dict)
    for origin_id, origin in origins.items():
        res_origin = persistence.get_domain_assessment_multiple(origin_id, domains)
        for r in res_origin:
            db_results_by_origin_id[origin_id][r['itemReviewed']] = r

    def performance_trick_query_already_done(origin):
        origin_id = origin.id
        def get_assessment(domain):
            result = db_results_by_origin_id[origin_id].get(domain, None)
            # TODO ask with a parameter whether to retrieve new evaluation or not if missing
            # if not result:
            #     if origin.origin_type == 'realtime':
            #         result = origin.retrieve_source_credibility(source)
            return result
        return get_assessment

    for domain in tqdm.tqdm(domains):
        results[domain] = get_weighted_credibility(domain, performance_trick_query_already_done)
    return results

def get_source_credibility_multiple(sources):
    sources = list(set(sources))
    results = {}

    db_results_by_origin_id = defaultdict(dict)
    for origin_id, origin in origins.items():
        res_origin = persistence.get_source_assessment_multiple(origin_id, sources)
        for r in res_origin:
            db_results_by_origin_id[origin_id][r['itemReviewed']] = r

    def performance_trick_query_already_done(origin):
        origin_id = origin.id
        def get_assessment(source):
            result = db_results_by_origin_id[origin_id].get(source, None)
            # TODO ask with a parameter whether to retrieve new evaluation or not if missing
            # if not result:
            #     if origin.origin_type == 'realtime':
            #         result = origin.retrieve_source_credibility(source)
            return result
        return get_assessment

    for source in tqdm.tqdm(sources):
        results[source] = get_weighted_credibility(source, performance_trick_query_already_done)
    return results

def get_url_credibility_parallel(urls):
    # TODO this seriously needs to query mongo more efficiently (no realtime checking, just batch. Need to refactor a bit!)
    urls = list(set(urls))
    results = {}

    db_results_by_origin_id = defaultdict(dict)
    for origin_id, origin in origins.items():
        res_origin = persistence.get_url_assessment_multiple(origin_id, urls)
        for r in res_origin:
            db_results_by_origin_id[origin_id][r['itemReviewed']] = r

    def performance_trick_query_already_done(origin):
        origin_id = origin.id
        def get_assessment(url):
            return db_results_by_origin_id[origin_id].get(url, None)
        return get_assessment


    for url in urls:
        results[url] = get_weighted_credibility(url, performance_trick_query_already_done)
    return results

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
    return {
        'id': origin_id,
        'weight': origin.default_weight,
        'homepage': origin.homepage,
        'name': origin.name,
        'description': origin.description,
        'origin_type': origin.origin_type,
        'logo': origin.logo,
        'assessments_count': persistence.get_origin_assessments_count(origin_id)
    }

def get_origins():
    result = []

    for origin_id in origins.keys():
        result.append(get_origin(origin_id))

    # sort by weight descending
    result = sorted(result, key=lambda el: el['weight'], reverse=True)

    return result
