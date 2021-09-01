import os
import pymongo
from typing import List

MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost:27017')
MONGO_USER = os.environ.get('MONGO_USER', None)
MONGO_PASS = os.environ.get('MONGO_PASS', None)
if MONGO_USER and MONGO_PASS:
    MONGO_URI = f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}'
else:
    MONGO_URI = f'mongodb://{MONGO_HOST}'
print('MONGO_URI', MONGO_URI)
client = pymongo.MongoClient(MONGO_URI)

db_credibility = client['credibility']
# TODO use db claimreview_scraper instead of datasets_resources
claimreviews_collection = client['claimreview_scraper']['claim_reviews']

def save_assessments(origin_name: str, assessments: list, drop: bool = False, replace_existing: bool = True):
    """Saves all the assessments for the specified origin. With drop, it clears before insertion.
    With replace_existing it will overwrite the existing item with same itemReviewed and granularity"""
    if not assessments:
        # an empty array of values could mean failure, prevent it
        raise ValueError('there are no assessments!!!')
    collection = db_credibility[origin_name]

    # if len(set(ass['itemReviewed'] for ass in assessments)) < len(assessments):
    #     done = set()
    #     for ass in assessments:
    #         el = ass['itemReviewed']
    #         if el in done:
    #             raise ValueError('check the assessments, they are evaluating the same item!!!', el)
    #         done.add(el)
    # for ass in assessments:
    #     ass['_id'] = ass['itemReviewed']
        # TODO add date of last update
        # ass['updated'] =

    if drop:
        collection.drop()
        replace_existing = False
        # collection.create_index([('domain', pymongo.ASCENDING)], name='domain_index')
        # collection.create_index([('source', pymongo.ASCENDING)], name='source_index')
        # collection.create_index([('itemReviewed', pymongo.ASCENDING)], name='itemReviewed_index')

    if replace_existing:
        # TODO would be better to do a replace_many
        for ass in assessments:
            add_origin_assessment(origin_name, ass)
    else:
        return collection.insert_many(assessments)

def add_origin_assessment(origin_name, ass):
    """Adds a single assessment to the collection identified by origin_name. This is for realtime assessments cache"""
    collection = db_credibility[origin_name]
    ass['_id'] = ass['itemReviewed']
    return collection.replace_one({'_id': ass['_id']}, ass, upsert=True)

def get_origin_assessments(origin_name):
    """Returns all the assessments by the specified origin"""
    collection = db_credibility[origin_name]
    return collection.find()

def get_origin_assessments_count(origin_name):
    """Returns how many assessments are stored from the specified origin"""
    collection = db_credibility[origin_name]
    return {
        'total': collection.count(),
        'sources': len(collection.distinct('source', {'granularity': 'source'})),
        'domains': len(collection.distinct('domain', {'granularity': 'domain'})),
        'urls': len(collection.distinct('itemReviewed', {'granularity': 'itemReviewed'}))
    }

def get_domain_assessment(origin_name: str, domain: str):
    """Returns the domain assessment from the specified origin about the domain"""
    collection = db_credibility[origin_name]
    # TODO deal with multiple matches
    match = collection.find_one({'domain': domain, 'granularity': 'domain'})
    return match

def get_source_assessment(origin_name: str, source: str):
    """Returns the domain assessment from the specified origin about the source"""
    collection = db_credibility[origin_name]
    # TODO deal with multiple matches (they should have been merged before!!!)
    match = collection.find_one({'source': source, 'granularity': 'source'})
    return match

def get_url_assessment(origin_name: str, url: str):
    """Returns the domain assessment from the specified origin about the source"""
    collection = db_credibility[origin_name]
    # TODO deal with multiple matches (they should have been merged before!!!)
    match = collection.find_one({'itemReviewed': url, 'granularity': 'itemReviewed'})
    return match


def get_tweet_assessments(origin_name: str, tweet_id: str):
    """Returns the domain assessments from the specified origin about the source"""
    collection = db_credibility[origin_name]
    # TODO deal with multiple matches (they should have been merged before!!!)
    match = collection.find({'itemReviewed': {'$regex': f'^https://twitter\.com/[A-Za-z0-9_]+/status/{tweet_id}'}, 'granularity': 'itemReviewed'})
    return match

def get_domain_assessment_multiple(origin_name: str, domains: List[str]):
    """Same as get_domain_assessment, but allows faster execution for multiple lookups"""
    collection = db_credibility[origin_name]
    matches = collection.find({'itemReviewed': {'$in': domains}, 'granularity': 'domain'})
    return matches

def get_source_assessment_multiple(origin_name: str, domains: List[str]):
    """Same as get_source_assessment, but allows faster execution for multiple lookups"""
    collection = db_credibility[origin_name]
    matches = collection.find({'itemReviewed': {'$in': domains}, 'granularity': 'source'})
    return matches

def get_source_assessments_all(origin_name: str):
    collection = db_credibility[origin_name]
    matches = collection.find({'granularity': 'source'})
    return matches

def get_domain_assessments_all(origin_name: str):
    collection = db_credibility[origin_name]
    matches = collection.find({'granularity': 'domain'})
    return matches

def get_url_assessment_multiple(origin_name: str, urls: List[str]):
    """Find multiple"""
    print(origin_name)
    collection = db_credibility[origin_name]
    # TODO deal with multiple matches
    matches = collection.find({'itemReviewed': {'$in': urls}, 'granularity': 'itemReviewed'})
    return matches

# this relies on the dataset of the factchecker scraper
def get_claimreviews():
    return claimreviews_collection.find()

def ping_db():
    return db_credibility.command('ping')