from collections import defaultdict
import re
import json

from ... import utils, persistence
from . import ifcn

from . import OriginBatch

class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self = self,
            id = 'factchecking_report',
            name = 'Fact-check analysis',
            description = 'From the fact-checks, we retrieve the claim appearances and therefore we evaluate the credibility of the sources involved.',
            homepage = 'http://socsem.kmi.open.ac.uk/misinfo', # TODO double check if appropriate
            logo = 'http://socsem.kmi.open.ac.uk/misinfo/assets/MisinfoMe-icon-square.png',
            default_weight = 2
        )

    def retreive_urls_assessments(self):
        return _retrieve_assessments()

    def update(self):
        # this origin updates differently
        url_assessments_propagated = self.retreive_urls_assessments()

        # Step 3: aggregate by URL, source and domain
        # TODO for now this is the only origin that does this on its own
        result_url_level = utils.aggregate_by(url_assessments_propagated, self.id, 'itemReviewed')
        result_source_level = utils.aggregate_source(url_assessments_propagated, self.id)
        result_domain_level = utils.aggregate_domain(url_assessments_propagated, self.id)
        all_assessments = list(result_url_level) + list(result_source_level) + list(result_domain_level)
        persistence.save_assessments(self.id, all_assessments, drop=True)
        counts = {
            'native_urls': len(url_assessments_propagated),
            'native_source': 0,
            'native_domains': 0,
            'urls_by_source': len(result_source_level),
            'urls_by_domain': len(result_domain_level),
            'sources_by_domain': 0,
        }
        return counts

ID = 'factchecking_report'

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
    # TODO this need to be run after IFCN update (actually need to recall this function)!!!
    result = {}
    signatories_assessments = ifcn.get_all_sources_credibility()
    for sa in signatories_assessments:
        homepage = sa['original']['website']
        id = sa['original']['id']
        domain = utils.get_url_domain(homepage)
        # TODO this is kinda of the formula for propagation (warning negative weights? mapping function?)
        weight = sa['credibility']['value'] * sa['credibility']['confidence'] * ifcn.Origin().default_weight
        fact_checker = FactChecker(homepage, id, weight)
        print(fact_checker.id, fact_checker.WEIGHT)
        result[domain] = fact_checker

    return result


class FactChecker(object):
    HOMEPAGE: str
    WEIGHT: float
    id: str
    origin_type: str

    def __init__(self, homepage, id, weight):
        self.HOMEPAGE = homepage
        self.WEIGHT = weight
        self.id = id#utils.get_url_domain(homepage)

    # def get_source_credibility(self, source):
    #     return get_source_credibility_from(source, self.id)

    # def update(self):
    #     domain_assessments = retrieve_and_group_claimreviews()
    #     my_group = claimreviews_by_fc_domain[self.id]
    #     print(self.id, 'has', len(my_group), 'claimReviews')
        # with open('temp_fc.json', 'w') as f:
        #     json.dump(domain_assessments, f, indent=2)
        # return 0
        #domain_assessments = get_domain_assessments_from_claimreviews(my_group)

# def retrieve_and_group_claimreviews():
#     global claimreviews_by_fc_domain
#     all_claimreviews = [el for el in persistence.get_claimreviews()]
#     claimreviews_by_fc_domain = defaultdict(list)
#     for cr in all_claimreviews:
#         fc_url = cr['url']
#         fc_domain = utils.get_url_domain(fc_url)
#         claimreviews_by_fc_domain[fc_domain].append(cr)

#     # THIS IS TO TEST THE SUBSET
#     # by_fullfact = claimreviews_by_fc_domain['fullfact.org']
#     # assessments_fullfact = get_domain_assessments_from_claimreviews(by_fullfact)
#     # persistence.save_origin_assessments(ID, assessments_fullfact.values())
#     # return assessments_fullfact

#     print('all_claimreviews', len(all_claimreviews))
#     domain_assessments = get_domain_assessments_from_claimreviews(all_claimreviews)
#     print('domain_assessments', len(domain_assessments))

#     persistence.save_assessments(ID, domain_assessments.values())
#     return domain_assessments



def _retrieve_assessments():
    #result = retrieve_and_group_claimreviews()
    all_claimreviews = [el for el in persistence.get_claimreviews()]

    # Step 1: get the list of URL assessments with properties:
    # - original: the original assessment (claimReview)
    # - credibility: interpreted from reviewRating
    # - itemReviewed: the appearance URL
    # - review_url: the URL of the assessment
    # - origin_domain: the domain of the review_url
    url_assessments = []
    for cr in all_claimreviews:
        #serialisation issues with mongo objectid
        del cr['_id']
        credibility = claimreview_interpret_rating(cr)
        # review_url = cr['url']
        try:
            review_url = cr['url']
            assert type(review_url) == str
        except:
            print('no url for', cr)
            continue
        origin_domain = utils.get_url_domain(review_url)

        for appearance in claimreview_get_claim_appearances(cr):
            # TODO unshorten appearance
            domain = utils.get_url_domain(appearance)
            source = utils.get_url_source(appearance)
            url_assessments.append({
                'itemReviewed': appearance,
                'granularity': 'url',
                'review_url': review_url,
                'credibility': credibility,
                'origin_domain': origin_domain,
                'domain': domain,
                'source': source,
                'original': cr
            })
    print(len(url_assessments), 'URL assessments')
    # persistence.save_url_assessments(ID, url_assessments)

    # Step 2: propagate the credibility of the assessor, generating objects with the properties:
    # - original: from before
    # - credibility_raw: from credibility of before
    # - itemReviewed: from before
    # - review_url: from before
    # - credibility_propagated: computed with the propagation
    # - origin: details about the origin (Fact-Checker)
    # - origin_weight: the value used for the origin
    url_assessments_propagated = []
    for ass in url_assessments:
        origin_domain = ass['origin_domain']
        origin = _fact_checkers.get(origin_domain, None)
        if not origin:
            # not an IFCN signatory, don't consider it
            # TODO maybe also other factcheckers can be trusted!
            origin_weight = 0
            origin_id = origin_domain.replace('.', '_')
        else:
            origin_weight = origin.WEIGHT
            origin_id = origin.id

        credibility_value = ass['credibility']['value']
        credibility_confidence = ass['credibility']['confidence']

        # TODO redefine the weight maximum value, for now it's 10
        confidence_rescored = credibility_confidence * (float(origin_weight) / 10)

        url_assessments_propagated.append({
            'original': ass['original'],
            'credibility_raw': ass['credibility'],
            'itemReviewed': ass['itemReviewed'],
            'domain': ass['domain'],
            'source': ass['source'],
            'url': ass['review_url'],
            'credibility': {
                'value': credibility_value,
                'confidence': confidence_rescored
            },
            'origin_id': origin_id,
            'origin_weight': origin_weight
        })
    print('propagation done')

    # step 3 is done by another method
    return url_assessments_propagated


    # domain_assessments = get_domain_assessments_from_claimreviews(all_claimreviews)
    # persistence.save_origin_assessments(ID, domain_assessments.values())
    # return len(domain_assessments)

    # claimreviews_by_fc_domain = defaultdict(list)
    # for cr in all_claimreviews:
    #     fc_url = cr['url']
    #     fc_domain = utils.get_url_domain(fc_url)
    #     claimreviews_by_fc_domain[fc_domain].append(cr)
    # processing_stats = []
    # for fc_domain, claimreviews_for_domain in claimreviews_by_fc_domain.items():
    #     claimreview_cnt = len(claimreviews_for_domain)
    #     domain_assessments = get_domain_assessments_from_claimreviews(claimreviews_for_domain)
    #     domain_assessed_cnt = len(domain_assessments)
    #     processing_stats.append({
    #         'fc_domain': fc_domain,
    #         'claimreview_cnt': claimreview_cnt,
    #         'domain_assessed_cnt': domain_assessed_cnt
    #     })


    # return sorted(processing_stats, key=lambda el: el['domain_assessed_cnt'], reverse=True)
    # #return len(result)


# def get_domain_assessments_from_claimreviews(claimreviews):
#     """TODO aaaa"""

#     # this first loop is on the claimreviews, and produces results grouped by assessed domain
#     # assessments is a dict {domain: list of assessments}
#     assessments = defaultdict(list)
#     for cr in claimreviews:
#         #print('claimreview', cr)
#         review_url = cr['url']
#         credibility = claimreview_interpret_rating(cr)
#         original = cr
#         #serialisation issues with mongo objectid
#         del original['_id']
#         print(review_url)
#         origin = utils.get_url_domain(review_url)
#         for appearance in claimreview_get_claim_appearances(cr):
#             itemReviewed = appearance
#             if not itemReviewed:
#                 print('itemReviewed', itemReviewed, 'in' , cr['url'])
#                 continue
#             domain = utils.get_url_domain(itemReviewed)
#             source = utils.get_url_source(itemReviewed)
#             # TODO also aggregate by source, not only domain
#             assessments[domain].append({
#                 'url': review_url,
#                 'credibility': credibility,
#                 'original': original,
#                 'origin': origin,
#                 'itemReviewed': itemReviewed,
#                 'domain': domain,
#                 'source': source
#             })
#     #print(assessments)

#     # this second loop
#     # final_credibility is {domain: aggregated credibility}
#     final_credibility = {}
#     for source, asssessments in assessments.items():
#         credibility_sum = 0
#         weights_sum = 0
#         # accumulator for the trust*confidence
#         confidence_and_weights_sum = 0

#         factcheck_positive_cnt = 0 # taken from the mapped value
#         factcheck_negative_cnt = 0
#         factcheck_neutral_cnt = 0

#         # something like {'snopes.com' : {'factcheck_positive_cnt': 3, ...}}}
#         cnts_by_factchecker = defaultdict(lambda: defaultdict(list))
#         counts = defaultdict(list)
#         for assessment in asssessments:
#             if not assessment:
#                 continue
#             origin_id = assessment['origin']
#             origin = _fact_checkers.get(origin_id, None)
#             if not origin:
#                 # not an IFCN signatory, invalid
#                 continue
#             origin_weight = origin.WEIGHT

#             credibility_value = assessment['credibility']['value']
#             credibility_confidence = assessment['credibility']['confidence']
#             label_to_use = 'unknown' if credibility_confidence < 0.4 \
#                 else 'positive' if credibility_value > 0 \
#                     else 'negative' if credibility_value < 0 else 'neutral'
#             # TODO just collect counts? nested resource or separate?
#             counts[label_to_use].append(assessment['url'])
#             # origin_id.replace('.', '_')
#             cnts_by_factchecker[origin.id][label_to_use].append(assessment['url'])
#             # add this also inside the object
#             cnts_by_factchecker[origin.id]['origin_id'] = origin.id
#             # TODO negative fact-check counts more?
#             confidence_and_weights_sum += credibility_confidence * origin_weight
#             #confidence_sum +=
#             credibility_sum += credibility_value * origin_weight * credibility_confidence
#             weights_sum += origin_weight

#         if confidence_and_weights_sum:
#             # there is something useful in the origins
#             credibility_weighted = credibility_sum / (confidence_and_weights_sum)
#             confidence_weighted = confidence_and_weights_sum / weights_sum
#         else:
#             # TODO maybe return a 404? For now we assume the client will look at the confidence
#             credibility_weighted = 0.
#             confidence_weighted = 0.

#         all_counts = cnts_by_factchecker
#         cnts_by_factchecker['overall'] = counts

#         final_credibility[source] = {
#             'credibility': {
#                 'value': credibility_weighted,
#                 'confidence': confidence_weighted
#             },
#             'original': all_counts,
#             'url': 'http://todo.todo',
#             'itemReviewed': source,
#             'origin_id': ID,
#             'domain': utils.get_url_domain(source),
#             'source': source,
#             'granularity': 'source'
#         }
#     return final_credibility




#### utilities for claimReview

def claimreview_get_claim_appearances(claimreview):
    try:
        result = []
        itemReviewed = claimreview.get('itemReviewed', None)
        if not itemReviewed:
            itemReviewed = claimreview.get('properties', {}).get('itemReviewed', None)
        if itemReviewed:
            # TODO include appearance but be careful to cases like https://africacheck.org/fbcheck/pineapple-leaves-not-a-wonder-cure/
            # where the appearance is an upload of the screenshot (on the fact-checker website)
            # we don't know the stance of the other appearances!!!
            appearance = itemReviewed.get('appearance', [])
            if isinstance(appearance, str):
                # checkyourfact.com sometimes just puts the url as string
                appearance  = [{'url': appearance}]
            appearances = [itemReviewed.get('firstAppearance', None)] + appearance
            if appearances:
                # new field appearance in https://pending.schema.org/Claim
                #print(appearances)
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
                        if isinstance(sameAs, list):
                            result = sameAs
                        else:
                            result = [sameAs]
            # itemReviewed.url
            itemReviewed_url = itemReviewed.get('url', None)
            if itemReviewed_url:
                #raise ValueError(claimreview['url'])
                result.append(itemReviewed_url)
        # TODO also return sameAs if present on the claim directly, other links there!!
        return [el for el in result if el]
    except Exception as e:
        print(claimreview)
        raise(e)

def clean_claim_url(url):
    result = url
    # remove the "mm:ss mark of URL" that is used for some videos
    if result:
        result = re.sub(r'.*\s+mark(\sof)?\s+(.+)', r'\2', result)
        # domain = utils.get_url_domain(result)
        # # some sameAs point to wikipedia page of person/organisation
        # if re.match(r'.*wikipedia\.org', domain):
        #     result = None
        # # some sameAs point to twitter.com/screen_name and not to twitter.com/screen_name/status
        # elif re.match(r'https?://(www.)?twitter\.com/[^/]*/?', result):
        #     result = None
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

    # fullfact
    'correct': 'true',
    'that\u2019s correct': 'true',
    'incorrect' : 'fake',
    'this is false': 'fake',
    'roughly correct': 'mixed',
    'broadly correct': 'mixed',
    'this isn\'t correct': 'fake',
    'this is correct': 'true',
    'not far off': 'mixed',
    'that\u2019s wrong': 'mixed',
    'it\u2019s correct': 'true',
    'this is true': 'true',
    'this is wrong': 'fake',
    'that\'s correct': 'true',
    'that is correct': 'true',
    'these aren\u2019t all correct': 'mixed',

    # teyit.org
    'yanliş': 'fake',
    'doğru': 'true',
    'karma': 'mixed',
    'belirsiz': None, #'uncertain'

    # lemonde
    'faux': 'fake',

    # istinomer
    'neistina': 'fake',
    'skoro neistina': None, # almost untrue

    # https://evrimagaci.org ???
    'sahte': 'fake',

    # https://verafiles.org
    'mali': 'fake',

    # poligrafo
    'verdadeiro': 'true',
    'engañoso': 'fake', # misleading
    'contraditorio': None, # contradictory

    # pagella politica
    'vero': 'true',
    'c’eri quasi': 'mixed', # almost true
    'pinocchio andante': 'fake',
    'panzana pazzesca': 'fake',

    # euvsdisinfo
    'disinfo': 'fake',



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
            scoreTxt = reviewRating.get('alternateName', '') or reviewRating.get('properties', {}).get('alternateName', '')
            if isinstance(scoreTxt, dict):
                scoreTxt = scoreTxt['@value']
        except Exception as e:
            print(reviewRating)
            raise e
        try:
            simplified_label = simplify_label(scoreTxt)
            #print(simplified_label)
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
        #print(rating, claimreview['reviewRating'])
        credibility = (rating - 0.5) * 2
        confidence = 1.0
    return {'value': credibility, 'confidence': confidence}




_fact_checkers = get_factcheckers()
