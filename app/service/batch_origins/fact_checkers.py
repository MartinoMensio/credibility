from collections import defaultdict
import re
import json

from .. import utils
from . import ifcn
from .. import persistence

MY_NAME = 'fact_checkers'
# TODO this is the homepage of ifcn!!!
HOMEPAGE = 'https://ifcncodeofprinciples.poynter.org/signatories'
WEIGHT = 2

claimreviews_by_fc_domain = {}

def get_factcheckers():
    """returns the list of factcheckers, intended as objects with the following attributes:
    - HOMEPAGE
    - WEIGHT
    - id
    - get_source_credibility(source)
    - update()

    Now this list is based purely on the IFCN list of signatories
    """
    # TODO this needs to be done with the graph propagation and default nodes
    result = {}
    signatories_assessments = ifcn.get_all_sources_credibility()
    for sa in signatories_assessments:
        homepage = sa['original']['website']
        # TODO this is kinda of the formula for propagation (warning negative weights? mapping function?)
        weight = sa['credibility']['value'] * sa['credibility']['confidence'] * ifcn.WEIGHT
        fact_checker = FactChecker(homepage, weight)
        print(fact_checker.id, fact_checker.WEIGHT)
        result[fact_checker.id] = fact_checker

    return result


class FactChecker(object):
    HOMEPAGE: str
    WEIGHT: float
    id: str
    origin_type: str

    def __init__(self, homepage, weight):
        self.HOMEPAGE = homepage
        self.WEIGHT = weight
        self.id = utils.get_url_domain(homepage)

    def get_source_credibility(self, source):
        return get_source_credibility_from(source, self.id)

    def update(self):
        domain_assessments = retrieve_and_group_claimreviews()
        my_group = claimreviews_by_fc_domain[self.id]
        print(self.id, 'has', len(my_group), 'claimReviews')
        # with open('temp_fc.json', 'w') as f:
        #     json.dump(domain_assessments, f, indent=2)
        # return 0
        #domain_assessments = get_domain_assessments_from_claimreviews(my_group)

def retrieve_and_group_claimreviews():
    global claimreviews_by_fc_domain
    all_claimreviews = [el for el in persistence.get_claimreviews()]
    claimreviews_by_fc_domain = defaultdict(list)
    for cr in all_claimreviews:
        fc_url = cr['url']
        fc_domain = utils.get_url_domain(fc_url)
        claimreviews_by_fc_domain[fc_domain].append(cr)

    print('all_claimreviews', len(all_claimreviews))
    domain_assessments = get_domain_assessments_from_claimreviews(all_claimreviews)
    print('domain_assessments', len(domain_assessments))

    persistence.save_origin_assessments(MY_NAME, domain_assessments.values())
    return domain_assessments





def get_source_credibility(source):
    return persistence.get_domain_assessment(MY_NAME, source)

def update():
    result =retrieve_and_group_claimreviews()
    return len(result)


def get_domain_assessments_from_claimreviews(claimreviews):
    """assessments is a dict {domain: list of assessments}"""
    assessments = defaultdict(list)
    # final_credibility is {domain: aggregated credibility}
    final_credibility = {}
    for cr in claimreviews:
        #print('claimreview', cr)
        review_url = cr['url']
        credibility = claimreview_interpret_rating(cr)
        original = cr
        #serialisation issues with mongo objectid
        del original['_id']
        origin = utils.get_url_domain(review_url)
        for appearance in claimreview_get_claim_appearances(cr):
            itemReviewed = appearance
            if not itemReviewed:
                print('itemReviewed', itemReviewed, 'in' , cr['url'])
                continue
            domain = utils.get_url_domain(itemReviewed)
            assessments[domain].append({
                'url': review_url,
                'credibility': credibility,
                'original': original,
                'origin': origin,
                'itemReviewed': itemReviewed,
                'domain': domain
            })


    #print(assessments)
    for domain, asssessments in assessments.items():
        credibility_sum = 0
        weights_sum = 0
        # accumulator for the trust*confidence
        confidence_and_weights_sum = 0

        factcheck_positive_cnt = 0 # taken from the mapped value
        factcheck_negative_cnt = 0
        factcheck_neutral_cnt = 0
        for assessment in asssessments:
            if not assessment:
                continue
            credibility_value = assessment['credibility']['value']
            if credibility_value > 0:
                factcheck_positive_cnt += 1
            elif credibility_value < 0:
                factcheck_negative_cnt += 1
            else:
                factcheck_neutral_cnt += 1
            credibility_confidence = assessment['credibility']['confidence']
            origin = fact_checkers.get(assessment['origin'], None)
            if not origin:
                # not an IFCN signatory, invalid
                continue
            origin_weight = origin.WEIGHT
            # TODO negative fact-check counts more?
            confidence_and_weights_sum += credibility_confidence * origin_weight
            #confidence_sum +=
            credibility_sum += credibility_value * origin_weight * credibility_confidence
            weights_sum += origin_weight

        if confidence_and_weights_sum:
            # there is something useful in the origins
            credibility_weighted = credibility_sum / (confidence_and_weights_sum)
            confidence_weighted = confidence_and_weights_sum / weights_sum
        else:
            # TODO maybe return a 404? For now we assume the client will look at the confidence
            credibility_weighted = 0.
            confidence_weighted = 0.

        final_credibility[domain] = {
            'credibility': {
                'value': credibility_weighted,
                'confidence': confidence_weighted
            },
            'original': {
                'factcheck_positive_cnt': factcheck_positive_cnt,
                'factcheck_negative_cnt': factcheck_negative_cnt,
                'factcheck_neutral_cnt': factcheck_neutral_cnt,
                'assessments': assessments[domain]
            },
            'url': 'http://todo.todo',
            'itemReviewed': domain,
            'origin': MY_NAME,
            'domain': domain,
            'granularity': 'source'
        }
    return final_credibility




#### utilities for claimReview

def claimreview_get_claim_appearances(claimreview):
    result = []
    itemReviewed = claimreview.get('itemReviewed', None)
    if not itemReviewed:
        itemReviewed = claimreview.get('properties', {}).get('itemReviewed', None)
    if itemReviewed:
        # TODO include appearance but be careful to cases like https://africacheck.org/fbcheck/pineapple-leaves-not-a-wonder-cure/
        # where the appearance is an upload of the screenshot (on the fact-checker website)
        # we don't know the stance of the other appearances!!!
        appearances = [itemReviewed.get('firstAppearance', None)] + itemReviewed.get('appearance', [])
        if appearances:
            # new field appearance in https://pending.schema.org/Claim
            print(appearances)
            result = [el['url'] for el in appearances if el]
        else:
            sameAs = itemReviewed.get('sameAs', None)
            if sameAs:
                result = [itemReviewed['sameAs']]
            else:
                author = itemReviewed.get('author', None)
                if not author:
                    author = itemReviewed.get('properties', {}).get('author', None)
                if author:
                    #exit(0)
                    sameAs = author.get('sameAs', None)
                    if not sameAs:
                        sameAs = author.get('properties', {}).get('sameAs', None)
                    #if sameAs:
                    #    print(sameAs)
                if sameAs:
                    result = [sameAs]
    # TODO also return sameAs if present on the claim directly, other links there!!
    return result
    if type(result) == list:
        # TODO consider multiple values
        result = clean_claim_url(el)
    else:
        result = clean_claim_url(result)
    print('appearance', result)
    return result

def clean_claim_url(url):
    result = url
    # remove the "mm:ss mark of URL" that is used for some videos
    if result:
        result = re.sub(r'.*\s+mark(\sof)?\s+(.+)', r'\2', result)
        domain = utils.get_url_domain(result)
        # some sameAs point to wikipedia page of person/organisation
        if re.match(r'.*wikipedia\.org', domain):
            result = None
        # some sameAs point to twitter.com/screen_name and not to twitter.com/screen_name/status
        elif re.match(r'https?://(www.)?twitter\.com/[^/]*/?', result):
            result = None
    return result

# the values of truthiness for the simplified labels
simplified_labels_scores = {
    'true': 1.0,
    'mixed': 0.5,
    'fake': 0.0
}
# simplified to the three cases true/mixed/fake
label_maps = {
    # from buzzface
    'mostly true': 'true',
    'mixture of true and false': 'mixed',
    'mostly false': 'fake',
    'no factual content': None,
    # from factcheckni
    'Accurate': 'true',
    #'Unsubstantiated': not true nor false, no proofs --> discard
    'Inaccurate': 'fake',
    'inaccurate': 'fake',
    # from mrisdal, opensources, pontes_fakenewssample
    'fake': 'fake',
    'bs': 'fake',
    'bias': 'fake',
    'conspiracy': 'fake',
    'junksci': 'fake',
    #'hate': 'fake', # hate speech is not necessarily fake
    'clickbait': 'fake',
    #'unreliable': 'fake',
    'reliable': 'true',
    'conspirancy': 'fake',
    # from leadstories
    'Old Fake News': 'fake',
    'Fake News': 'fake',
    'Hoax Alert': 'fake',
    # from politifact
    'False': 'fake',
    'True': 'true',
    'Mostly True': 'true',
    'Half True': 'mixed',
    'Half-True': 'mixed',
    'Mostly False': 'fake',
    'Pants on Fire!': 'fake',
    'pants on fire': 'fake',
    # from golbeck_fakenews
    'Fake': 'fake',
    # from liar (politifact-dashed)
    'false': 'fake',
    'true': 'true',
    'mostly-true': 'true',
    'mostly-false': 'fake',
    'barely-true': 'fake',
    'pants-fire': 'fake',
    'half-true': 'mixed',
    # from vlachos_factchecking
    'TRUE': 'true',
    'FALSE': 'fake',
    'MOSTLY TRUE': 'true',
    'MOSTLY FALSE': 'fake',
    'HALF TRUE': 'mixed',
    # others from ClaimReviews
    'Accurate': 'true',
    'Inaccurate': 'fake',
    'Wrong': 'fake',
    'Not accurate': 'fake',
    'Lie of the Year': 'fake',
    'Mostly false': 'fake',
    # metafact.ai labels
    'Affirmative': 'true',
    'Negative': 'fake',
    'Uncertain': 'mixed',
    #'Not Enough Experts': ??
    # tempo (indonesian)
    'BENAR' : 'true',
    'SEBAGIAN BENAR' : 'mixed',
    'TIDAK TERBUKTI' : 'mixed', # unproven
    'SESAT' : 'mixed', # facts are correct, but wrong conclusions (misleading)
    'KELIRU' : 'fake',
    'mixture': 'mixed',
    'somewhat true': 'mixed',
    'somewhat false': 'mixed',
    'misleading': 'mixed',
    'ambiguous': 'mixed',
    # newtral.es
    'falso': 'fake',
    # verificat
    'fals': 'fake',
    # other things
    ': false': 'fake',
    ': true': 'true',
    ': mixture': 'mixed',
    'rating: false': 'fake',
    'rating by fact crescendo: false': 'fake',
    'verdadero': 'true',
    'verdad a medias': 'mixed',
    # factnameh
    '\u0646\u0627\u062f\u0631\u0633\u062a': 'fake', # false
    '\u0646\u06cc\u0645\u0647 \u062f\u0631\u0633\u062a': 'mixed', # half true
    '\u06af\u0645\u0631\u0627\u0647\u200c\u06a9\u0646\u0646\u062f\u0647': 'mixed', # misleading

    # random stuff (just set to fake to debug and go on)
    # 'ce sondage n\'existe pas.': 'fake',
    # "New England MP and former Deputy Prime Minister Barnaby Joyce": 'fake',
    # '6': 'fake',
    # 'mh.10.sangli': 'fake',
    # "Le B\u00e9nin est bien class\u00e9 6e pays le plus heureux de l\u2019Afrique subsaharienne selon le \"World Happiness Report\" qui, cependant, n'\u00e9mane pas des Nations Unies.": 'fake',
    # "Bitcoin n\u00e3o \u00e9 uma pir\u00e2mide financeira ou esquema ponzi, o Bitcoin tem um embasamento completamente oposto ao que s\u00e3o esquemas fradulentos. Bitcoin \u00e9 a primeira criptomoeda lan\u00e7ada, as primeiras pessoas que adotaram o bitcoin foram os entusiastas de criptografia, o bitcoin foi anunciado em um grupo cypherpunk em 2008, ou seja, pessoas com um conhecimento avan\u00e7ado em tecnologia e matem\u00e1tica acreditaram no pot\u00eancial da tecnologia.": 'fake',
    # 'no disponible': 'fake',
    # 'at the time indian-pakistan war rajiv gandhi was in india.': 'fake',
    # 'while data on sex workers in ireland is extremely lacking, the figures that are available and most commonly employed by experts do not support this claim. there is no official data documenting the movement of sex workers south across the border, but whatever the scale, an 80% impact in ireland is unlikely.': 'fake',
}

def simplify_label(label):
    label = label.strip().lower()
    label = label.replace('fact crescendo rating: ', '')
    label = label.replace('fact crescendo rating - ', '')
    label = label.replace('fact crescendo rating ', '')
    result = label_maps.get(label, None)
    if not result:
        for k,v in label_maps.items():
            if label.startswith(k.lower()):
                result = v
                break
    if not result:
        print('unmappable alternateName', label)
    return result

def claimreview_get_rating(claimreview):
    # what to do with these labels? for now returns None so the claims are discarded
    # {'Known since 2008', 'Lacks context', 'Unproven claim', 'Tactics look typical', 'Cannot Be Verified', 'Shift from past position', 'Easily beats the market', 'Includes Hispanic Other Black', 'More words than action', 'By Some Counts Yes', 'Roe grants federal right', 'Not a Muslim migrant', 'Polls depend on wording', 'Had seat at table', "Record doesn't say that", 'Coverage has limits', 'Wrong', 'Not accurate', 'Photo is real', 'Misleads', 'Met half of them', 'Mostly entered before Obama', 'No evidence', 'Wrong use of word', 'Mis- leading', 'Lie of the Year', 'Other spending nears $200M', 'Too soon to say', 'Possible but risky', 'White House not studio', 'Obama Called in 2012', 'Trump ordered new probe', 'Disputed Claim', 'Clinton role still unclear', 'Flip- flop', 'False', 'They are not eligible', 'No such plan', 'Not what GM says', 'In dispute', 'Trump deserves some credit', 'Can still be deported', 'Spinning the facts', 'Revised after backlash', 'Personal tweet taken down', "It's Calif. law", "Japan's leader acted first", 'Mostly false', 'Study in Dispute', 'Salary not only factor', 'No contact', 'Needs Context', 'Old stat', "He's very close", 'Flip- Flop', 'Rates are even higher', 'Staff error', 'In effect since 1965', 'Far from clear', 'Number not that high', 'Claim omits key facts', "Didn't use that word", 'Ignores US GDP size', 'Needs context', 'U.S. has trade surplus', 'Depends on the metric', 'Not the Whole Story', 'Way early to say', 'Numbers are close', 'Trump role emerged later', 'Depends on source', 'No way to verify', 'Effect not clear', 'No way to know', 'Result of Trump policy', 'Twitter fixed a glitch', 'Ignores all tax hikes', 'Vetted by State Dept.', 'His numbers are outdated', 'Fuzzy math', 'Latino numbers much higher', 'Not the same thing', 'Not what Pelosi said', 'Not the whole story', 'Experts question wall impact', 'Flynn talked Russia sanction', 'Lacks Context', 'Under Dispute', 'Supports border tech security', 'Unlikely but possible', 'Could be much worse', 'Lacks Evidence', 'No MS-13 removal data', 'Legal rules unclear', 'She told law schools', 'Not Missouri students', "Don't count your chickens", 'Depends on intent', 'Not that clear cut', 'History poses big hurdle', 'But little impact yet'}

    reviewRating = claimreview.get('reviewRating', None)
    if not reviewRating:
        reviewRating = claimreview.get('properties', {}).get('reviewRating', None)
    if not reviewRating:
        return None
    try:
        if 'properties' in reviewRating:
            reviewRating = reviewRating['properties']
        best = int(reviewRating['bestRating'])
        worst = int(reviewRating['worstRating'])
        value = int(reviewRating['ratingValue'])
        if best == -1 and worst == -1:
            score = None
        else:
            score = (value - worst) / (best - worst)
            # correct errors like: 'bestRating': '10', 'ratingValue': '0', 'worstRating': '1'
            score = min(score, 1.0)
            score = max(score, 0.0)
    except Exception as e:
        score = None
        print('rating numbers not found', reviewRating)
    if score == None:
        try:
            scoreTxt = reviewRating.get('alternateName', None) or reviewRating.get('properties', {}).get('alternateName', None)
        except Exception as e:
            print(reviewRating)
            raise e
        try:
            simplified_label = simplify_label(scoreTxt)
            print(simplified_label)
        except Exception as e:
            print(claimreview['url'])
            print(reviewRating)
            print(score)
            raise e
        if simplified_label:
            score = simplified_labels_scores[simplified_label]
    return score

def claimreview_interpret_rating(claimreview):
    rating = claimreview_get_rating(claimreview)
    if rating is None:
        credibility = 0.0
        confidence = 0.0
    else:
        print(rating, claimreview['reviewRating'])
        credibility = (rating - 0.5) * 2
        confidence = 1.0
    return {'value': credibility, 'confidence': confidence}




fact_checkers = get_factcheckers()
