import os
import pymongo

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
claimreviews_collection = client['datasets_resources']['claim_reviews']

def save_origin_assessments(origin_name, assessments):
    """Saves all the assessments for the specified origin. It erases the collection!!!"""
    if not assessments:
        # an empty array of values could mean failure, prevent it
        raise ValueError('there are no assessments!!!')
    collection = db_credibility[origin_name]

    if len(set(ass['itemReviewed'] for ass in assessments)) < len(assessments):
        done = set()
        for ass in assessments:
            el = ass['itemReviewed']
            if el in done:
                raise ValueError('check the assessments, they are evaluating the same item!!!', el)
            done.add(el)
    for ass in assessments:
        ass['_id'] = ass['itemReviewed']
        # TODO add date of last update
        # ass['updated'] =

    collection.drop()
    collection.create_index([('domain', pymongo.ASCENDING)], name='domain_index')
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
    return collection.count()

def get_domain_assessment(origin_name, domain):
    """Returns the domain assessment from the specified origin about the domain"""
    collection = db_credibility[origin_name]
    # TODO deal with multiple matches
    match = collection.find_one({'domain': domain})
    return match


# this relies on the dataset of the factchecker scraper
def get_claimreviews():
    return claimreviews_collection.find()