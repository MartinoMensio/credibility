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

    # TODO double check this gets called also by multiple check
    def get_url_credibility(self, url):
        domain = utils.get_url_domain(url)
        if domain == 'twitter.com':
            match = re.search(r'https://twitter\.com/[A-Za-z0-9_]+/status/(?P<tweet_id>[0-9]+).*', url)
            if not match:
                # cannot do this twitter thing, go back to the other condition
                result = persistence.get_url_assessment(self.id, url)
            else:
                tweet_id = match.group('tweet_id')
                # also match with URLs that have more content
                results = persistence.get_tweet_assessments(self.id, tweet_id)
                results = list(results)
                if len(results):
                    # this is merging multiple results
                    # original = defaultdict(lambda: defaultdict(set))
                    reports = defaultdict(list)
                    # TODO this needs to be changed, in aggregation function (utils.py). Allow to see the single labels from fact-checkers
                    for el in results:
                        for report in el['reports']:
                            reports[report['report_url']].append(report)
                        # for k1, v1 in el['original'].items():
                        #     for k2, v2 in v1.items():
                        #         original[k1][k2].update(v2)
                    # set to list, without duplicates
                    # original = {k1: {k2: list(v2) for k2, v2 in v1.items()} for k1, v1 in original.items()}
                    # again to list without duplicates
                    reports_cleaned = []
                    for k, l in reports.items():
                        labels = set(el['coinform_label'] for el in l)
                        if len(labels) > 1:
                            raise ValueError('Reports not agreeing!!!!')
                        # just append one for each claimreview URL (no duplicates)
                        reports_cleaned.append(l[0])
                    result = {
                        'url': 'http://todo.todo',
                        'credibility': { # TODO proper average accounting for confidence???
                            'value': sum(el['credibility']['value'] for el in results) / len(results),
                            'confidence': sum(el['credibility']['confidence'] for el in results) / len(results),
                        },
                        'itemReviewed': tweet_id,
                        'reports': reports_cleaned,
                        'origin_id': 'factchecking_report',
                        'granularity': 'itemReviewed'
                    }
                else:
                    result = None
        else:
            result = persistence.get_url_assessment(self.id, url)
        return result
        # use regex search 
        # db.getCollection('factchecking_report').find({'itemReviewed': { $regex : /^https:\/\/twitter\.com\/wvdemocrats\/status\/1016745675642556417/ }})

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
        assessment_url = sa['url']
        name = sa['original']['name']
        domain = utils.get_url_domain(homepage)
        # TODO this is kinda of the formula for propagation (warning negative weights? mapping function?)
        weight = sa['credibility']['value'] * sa['credibility']['confidence'] * ifcn.Origin().default_weight
        fact_checker = FactChecker(homepage, id, weight, assessment_url, name)
        print(fact_checker.id, fact_checker.WEIGHT)
        result[domain] = fact_checker

    return result


class FactChecker(object):
    HOMEPAGE: str
    WEIGHT: float
    id: str
    origin_type: str

    def __init__(self, homepage, id, weight, assessment_url, name):
        self.HOMEPAGE = homepage
        self.WEIGHT = weight
        self.id = id#utils.get_url_domain(homepage)
        self.assessment_url = assessment_url
        self.name = name

    def serialise(self):
        return {
            'id': self.id,
            'homepage': self.HOMEPAGE,
            'assessment_url': self.assessment_url,
            'weight': self.WEIGHT,
            'name': self.name
        }

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
    # - coinform_label: the original label given by the fact-checker
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
        coinform_label = claimreview_get_coinform_label(cr)
        original_label = cr.get('reviewRating', {}).get('alternateName', None)

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
                'original': cr,
                'coinform_label': coinform_label,
                'original_label': original_label
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
            origin_serialisable = None
        else:
            origin_weight = origin.WEIGHT
            origin_id = origin.id
            origin_serialisable = origin.serialise()

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
            'origin': origin_serialisable,
            'origin_weight': origin_weight,
            'coinform_label': ass['coinform_label'],
            'original_label': ass['original_label']
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
    """from a `ClaimReview`, get all the URLs mentioned as appearances"""
    try:
        factchecker_url = claimreview['url']
        factchecker_domain = utils.get_url_domain(factchecker_url)
        result = []
        itemReviewed = claimreview.get('itemReviewed', None)
        if not itemReviewed:
            itemReviewed = claimreview.get('properties', {}).get('itemReviewed', None)
        if itemReviewed:
            # sometimes the appearances are stored in the correct place
            appearance = itemReviewed.get('appearance', [])
            if isinstance(appearance, str):
                # checkyourfact.com sometimes just puts the url as string
                appearance  = [{'url': appearance}]
            if not isinstance(appearance, list):
                appearance = [appearance]
            # get also the firstAppearance
            firstAppearance = itemReviewed.get('firstAppearance', None)
            if not isinstance(firstAppearance, list):
                firstAppearance = [firstAppearance]
            appearances = firstAppearance + appearance
            if appearances:
                # new field appearance in https://pending.schema.org/Claim
                #print(appearances)
                result = [el['url'] for el in appearances if el]
            else:
                # sometimes instead the appearances are listed in itemReviewed
                sameAs = itemReviewed.get('sameAs', None)
                if sameAs:
                    result = [sameAs]
                else:
                    author = itemReviewed.get('author', None)
                    if not author:
                        author = itemReviewed.get('properties', {}).get('author', None)
                    if author:
                        sameAs = author.get('sameAs', None)
                        if not sameAs:
                            sameAs = author.get('properties', {}).get('sameAs', None)
                    if sameAs:
                        if isinstance(sameAs, list):
                            result = sameAs
                        else:
                            result = [sameAs]
            # sometimes in itemReviewed.url
            itemReviewed_url = itemReviewed.get('url', None)
            if itemReviewed_url:
                #raise ValueError(claimreview['url'])
                result.append(itemReviewed_url)
        # TODO also return sameAs if present on the claim directly, other links there!!

        # split appearances that are a single field with comma or ` and `
        cleaned_result = []
        for el in result:
            if not isinstance(el, str):
                cleaned_result.extend(el)
            if ',' in el:
                els = el.split(',')
                cleaned_result.extend(els)
            if ' ' in el:
                els = el.split(' ')
                cleaned_result.extend(els)
            elif ' and ' in el:
                els = el.split(' and ')
                cleaned_result.extend(els)
            else:
                cleaned_result.append(el)
        # remove spaces around
        cleaned_result = [el.strip() for el in cleaned_result if el]
        # just keep http(s) links
        cleaned_result = [el for el in cleaned_result if re.match('^https?:\/\/.*$', el)]
        # remove loops to evaluation of itself
        cleaned_result = [el for el in cleaned_result if utils.get_url_domain(el) != factchecker_domain]
        return cleaned_result
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


# The following dicts are used to map the labels and the scores coming from the claimReviews

# the values of truthiness for the simplified labels in [0;1] range with None for 'not_verifiable'
simplified_labels_scores = {
    'credible': 1.0, # becomes 1 credibility
    'mostly_credible': 0.75, # becomes 0.5 credibility
    'uncertain': 0.5, # becomes 0 credibility
    'not_credible': 0.0, # becomes -1 credibility
    'not_verifiable': None, # becomes 0 confidence
    # legacy labels
    'true': 1.0,
    'mixed': 0.5,
    'fake': 0.0
}
# simplified to the three cases true/mixed/fake
label_maps = {
    # from buzzface
    'mostly true': 'mostly_credible',
    'mixture of true and false': 'uncertain',
    'mostly false': 'not_credible',
    'no factual content': 'not_credible',
    # from factcheckni
    'Accurate': 'credible',
    'Unsubstantiated': 'not_verifiable', #not true nor false, no proofs
    'Inaccurate': 'not_credible',
    'inaccurate': 'not_credible',
    # from mrisdal, opensources, pontes_fakenewssample
    'fake': 'not_credible',
    'bs': 'not_credible', # bullshit
    'bias': 'uncertain',
    'conspiracy': 'not_credible',
    'junksci': 'not_credible',
    #'hate': 'fake', # hate speech is not necessarily fake
    'clickbait': 'not_credible',
    #'unreliable': 'fake',
    'reliable': 'credible',
    'conspirancy': 'not_credible',
    # from leadstories
    'Old Fake News': 'not_credible',
    'Fake News': 'not_credible',
    'Hoax Alert': 'not_credible',
    # from politifact
    'False': 'not_credible',
    'True': 'credible',
    'Mostly True': 'mostly_credible',
    'Half True': 'uncertain',
    'Half-True': 'uncertain',
    'Mostly False': 'not_credible',
    'Pants on Fire!': 'not_credible',
    'pants on fire': 'not_credible',
    # from golbeck_fakenews
    'Fake': 'not_credible',
    # from liar (politifact-dashed)
    'false': 'not_credible',
    'true': 'credible',
    'mostly-true': 'mostly_credible',
    'mostly-false': 'not_credible',
    'barely-true': 'uncertain',
    'pants-fire': 'not_credible',
    'half-true': 'uncertain',
    # from vlachos_factchecking
    'TRUE': 'credible',
    'FALSE': 'not_credible',
    'MOSTLY TRUE': 'mostly_credible',
    'MOSTLY FALSE': 'not_credible',
    'HALF TRUE': 'uncertain',
    # others from ClaimReviews
    'Accurate': 'credible',
    'Inaccurate': 'not_credible',
    'Wrong': 'not_credible',
    'Not accurate': 'not_credible',
    'Lie of the Year': 'not_credible',
    'Mostly false': 'not_credible',
    # metafact.ai labels
    'Affirmative': 'credible',
    'Negative': 'not_credible',
    'Uncertain': 'uncertain',
    'Not Enough Experts': 'not_verifiable',
    # tempo (indonesian)
    'BENAR' : 'credible',
    'SEBAGIAN BENAR' : 'uncertain',
    'TIDAK TERBUKTI' : 'uncertain', # unproven
    'SESAT' : 'uncertain', # facts are correct, but wrong conclusions (misleading)
    'KELIRU' : 'not_credible',
    'mixture': 'uncertain',
    'somewhat true': 'mostly_credible',
    'somewhat false': 'uncertain',
    'misleading': 'not_credible',
    'ambiguous': 'uncertain',
    # newtral.es
    'falso': 'not_credible',
    # verificat
    'fals': 'not_credible',
    # other things
    ': false': 'not_credible',
    ': true': 'credible',
    ': mixture': 'uncertain',
    'rating: false': 'not_credible',
    'rating by fact crescendo: false': 'not_credible',
    'verdadero': 'credible',
    'verdad a medias': 'uncertain',
    # factnameh
    '\u0646\u0627\u062f\u0631\u0633\u062a': 'not_credible', # false
    '\u0646\u06cc\u0645\u0647 \u062f\u0631\u0633\u062a': 'uncertain', # half true
    '\u06af\u0645\u0631\u0627\u0647\u200c\u06a9\u0646\u0646\u062f\u0647': 'not_credible', # misleading

    # fullfact (this is the beginning of the label, they have very long labels)
    'correct': 'credible',
    'that\u2019s correct': 'credible',
    'incorrect' : 'not_credible',
    'this is false': 'not_credible',
    'roughly correct': 'uncertain',
    'broadly correct': 'uncertain',
    'this isn\'t correct': 'not_credible',
    'this is correct': 'credible',
    'not far off': 'mostly_credible',
    'that\u2019s wrong': 'not_credible',
    'it\u2019s correct': 'credible',
    'this is true': 'credible',
    'this is wrong': 'not_credible',
    'that\'s correct': 'credible',
    'that is correct': 'credible',
    'these aren\u2019t all correct': 'uncertain',

    # teyit.org
    'yanliş': 'not_credible',
    'doğru': 'credible',
    'karma': 'uncertain',
    'belirsiz': 'not_verifiable', #'uncertain'

    # lemonde
    'faux': 'not_credible',

    # istinomer
    'neistina': 'not_credible',
    'skoro neistina': 'uncertain', # almost untrue

    # https://evrimagaci.org ???
    'sahte': 'not_credible',

    # https://verafiles.org
    'mali': 'not_credible',

    # poligrafo
    'verdadeiro': 'credible',
    'engañoso': 'not_credible', # misleading
    'contraditorio': 'uncertain', # contradictory

    # pagella politica
    'vero': 'credible',
    'c’eri quasi': 'mostly_credible', # almost true
    'c\'eri quasi': 'mostly_credible', # almost true
    'pinocchio andante': 'not_credible',
    'panzana pazzesca': 'not_credible',
    'nì': 'uncertain',

    # euvsdisinfo
    'disinfo': 'not_credible',


    # from twitter subset
    'Фейк': 'not_credible',
    # 'usatoday.com'
    'partly false': 'uncertain',
    # factcheck.org
    'baseless claim': 'not_verifiable',
    'mixed.': 'uncertain',
    'experts disagree': 'not_credible',
    'one pinocchio': 'mostly_credible',
    'two pinocchios': 'uncertain',
    'three pinocchios': 'not_credible',
    'four pinocchios': 'not_credible',
    'the statement is false': 'not_credible',
    'erroné': 'not_credible',
    'c\'est faux': 'not_credible',
    'not correct': 'not_credible',
    'not true': 'not_credible',
    'largely accurate': 'mostly_credible',
    'mixed': 'uncertain',
    'partially true': 'uncertain',
    'partly right': 'uncertain',


}

### MAPPING FUNCTIONS

def claimreview_get_coinform_label(cr):
    """takes a ClaimReviews and outputs a CoInform score"""
    # unify to the score (easier to work with numbers)
    score = claimreview_get_rating(cr)
    # and then map the score to the labels
    mapped_label = get_coinform_label_from_score(score)
    return mapped_label

def simplify_label(label):
    """maps from the fact-checker label to the coinform label"""
    # normalise string to lowercase and strip spaces around
    label = label.strip().lower()
    label = label.replace('fact crescendo rating: ', '')
    label = label.replace('fact crescendo rating - ', '')
    label = label.replace('fact crescendo rating ', '')
    # first look for the full label
    result = label_maps.get(label, None)
    # then if the label begins with something known
    if not result:
        for k,v in label_maps.items():
            if label.startswith(k.lower()):
                result = v
                break
    if not result:
        # return None which will get mapped
        pass
    return result

def get_coinform_label_from_score(score):
    """The inverse function of `simplified_labels_scores`"""
    if score is None:
        return 'not_verifiable'
    if score > 0.8:
        return 'credible'
    if score > 0.6:
        return 'mostly_credible'
    if score > 0.4:
        return 'uncertain'
    return 'not_credible'

def claimreview_get_rating(claimreview):
    """takes a claimReviews and outputs a score of truthfulness between [0;1] or None if not verifiable"""
    # take the reviewRating
    reviewRating = claimreview.get('reviewRating', None)
    if not reviewRating:
        # sometimes reviewRating is inside "properties"
        reviewRating = claimreview.get('properties', {}).get('reviewRating', None)
    if not reviewRating:
        # nothing to say
        return None
    

    if 'properties' in reviewRating:
        reviewRating = reviewRating['properties']

    score = None

    # first take the textual label
    try:
        scoreTxt = reviewRating.get('alternateName', '') or reviewRating.get('properties', {}).get('alternateName', '')
        if isinstance(scoreTxt, dict):
            scoreTxt = scoreTxt['@value']
    except Exception as e:
        print(reviewRating)
        raise e
    try:
        # map it to the coinform labels
        simplified_label = simplify_label(scoreTxt)
    except Exception as e:
        print(claimreview['url'])
        print(reviewRating)
        raise e
    if simplified_label:
        # get the numerical score
        score = simplified_labels_scores[simplified_label]

    # second strategy: if the textual label is unknown, take the rating value
    if score == None:
        try:
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
            # in the case the numbers are not found, there is not any information that can be used to map the rating
            score = None

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
