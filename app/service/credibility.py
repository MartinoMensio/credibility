from .external_origins import newsguard, mywot
from .batch_origins import ntt
from . import utils

origins = {
    'newsguard': newsguard,
    'mywot': mywot,
    'ntt': ntt,
}

def get_source_credibility(source):
    """retrieve the credibility score for the source, by using the origins available"""
    # TODO be sure to be at the source level, e.g. use utils.get_domain but be careful to facebook/twitter/... platforms
    assessments = {}
    credibility_sum = 0
    weights_sum = 0
    # accumulator for the trust*confidence
    confidence_and_weights_sum = 0

    for k, v in origins.items():
        assessment = v.get_source_credibility(source)
        if not assessment:
            continue
        # TODO source evaluation, now is a fixed value
        origin_weight = v.WEIGHT
        credibility_value = assessment['credibility']['value']
        credibility_confidence = assessment['credibility']['confidence']

        confidence_and_weights_sum += credibility_confidence * origin_weight
        #confidence_sum +=
        credibility_sum += credibility_value * origin_weight * credibility_confidence
        weights_sum += origin_weight

        assessments[k] = assessment
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
    pass