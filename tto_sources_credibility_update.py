import csv
import tqdm
import time
import requests
from multiprocessing.pool import ThreadPool

sources = set()
with open('tto_data.tsv') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        sources.add(row['source'])

print(len(sources))

def check_source(s, retries=5):
    # res = requests.get(f'https://misinfo.me/misinfo/api/credibility/sources/?source={s}')
    # res.raise_for_status()
    try:
        res = requests.get(f'https://misinfo.me/misinfo/api/credibility/sources/?source={s}')
        # res = requests.get(f'http://localhost:5000/misinfo/api/credibility/sources/?source={s}')
        # res = requests.get(f'http://localhost:20300/sources/?source={s}')
        res.raise_for_status()
    except Exception as e:
        if retries < 1:
            raise e
        else:
            print(f'retrying soon ({retries})...')
            time.sleep(5)
            return check_source(s, retries=retries - 1)
    return res.json()

sources = list(sources)
sources = sources[128000:] ###local
# sources = sources[105000:] ###remote

with ThreadPool(32) as pool:
    for s in tqdm.tqdm(pool.imap_unordered(check_source, sources), desc='Checking sources', total=len(sources)):
        pass
