import rdflib
import json
from pyld import jsonld
import tqdm
import requests
import multiprocessing

from app.service import persistence

SPARQL_ENDOPOINT = 'http://localhost:7200/repositories/coinform'
# see http://localhost:7200/webapi for the API

def load_claimReviews():
    # claimreviews = [el for el in persistence.get_claimreviews()[:100]]
    claimreviews = [el for el in persistence.get_claimreviews()]
    return claimreviews

def jsonld_to_n3(claimreviews):
    pool_size = 32
    g = rdflib.Graph()
    def cr_parse(cr):
        del cr['_id']
        cr_string = json.dumps(cr)
        g.parse(data=cr_string, format='json-ld')
        return 'ok'

    for cr in tqdm.tqdm(claimreviews):
        # mongo object id
        del cr['_id']
        cr_string = json.dumps(cr)
        # nquads = jsonld.normalize(cr, {'algorithm': 'URDNA2015', 'format': 'application/nquads'})
        # print(nquads)
        # exit(1)
        g.parse(data=cr_string, format='json-ld')

    # with multiprocessing.Pool(pool_size) as pool:
    #     # one-to-one with the url_list
    #     for r in tqdm.tqdm(pool.imap_unordered(cr_parse, claimreviews), total=len(claimreviews)):
    #         pass

    n3 = g.serialize(format='n3').decode()
    with open('cr.n3', 'w') as f:
        f.write(n3)
    return n3

def load_n3_file():
    with open('cr.n3') as f:
        n3 = f.read()
    return n3

def load_n3_sparql(n3):
    response = requests.post(f'{SPARQL_ENDOPOINT}/statements', data=n3.encode('utf-8'), headers={'Content-Type': 'application/x-turtle'})
    print(response.status_code)

def clear_repository():
    response = requests.delete(f'{SPARQL_ENDOPOINT}/statements')
    print(response.status_code)

def main(recompute_n3=True):
    if recompute_n3:
        claimreviews = load_claimReviews()
        n3_result = jsonld_to_n3(claimreviews)
    else:
        n3_result = load_n3_file()
    clear_repository()
    load_n3_sparql(n3_result)

if __name__ == "__main__":
    main()