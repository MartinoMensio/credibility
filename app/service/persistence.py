import os
import pymongo

MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost:27017')
MONGO_USER = os.environ.get('MONGO_USER', None)
MONGO_PASS = os.environ.get('MONGO_PASS', None)
if MONGO_USER and MONGO_PASS:
    MONGO_URI = 'mongodb://{}:{}@{}'.format(MONGO_USER, MONGO_PASS, MONGO_HOST)
else:
    MONGO_URI = 'mongodb://{}'.format(MONGO_HOST)
print('MONGO_URI', MONGO_URI)
client = pymongo.MongoClient(MONGO_URI)

db_credibility = client['credibility']

def save_origin(origin_name, assessments):
    """Saves all the assessments for the specified origin"""
    collection = db_credibility[origin_name]

    if len(set(ass['itemReviewed'] for ass in assessments)) < len(assessments):
        raise ValueError('check the assessments, they are evaluating the same item!!!')
    for ass in assessments:
        ass['_id'] = ass['itemReviewed']

    collection.drop()
    collection.create_index([('domain', pymongo.ASCENDING)], name='domain_index')
    collection.insert_many(assessments)

def get_origin_assessments(origin_name):
    """Returns all the assessments by the specified origin"""
    collection = db_credibility[origin_name]
    return collection.find()

def get_domain_assessment(origin_name, domain):
    """Returns the domain assessment from the specified origin about the domain"""
    collection = db_credibility[origin_name]
    # TODO deal with multiple matches
    match = collection.find_one({'domain': domain})
    print(domain, match)
    return match
