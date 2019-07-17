# Credibility

The aim is to estimate the credibility of news sources / articles

## Sources

There are two kinds of sources: online and offline. The online ones can be queried in real time. The offline instead are downloaded and updated periodically

### Online query

#### NewsGuard

description: https://www.newsguardtech.com/ratings/rating-process-criteria/
endpoint: https://api.newsguardtech.com/check?url={URL_HERE}
granularity: domain-level

### MyWOT

description: https://www.mywot.com/wiki/index.php/API
endpoint: http://api.mywot.com/0.4/public_link_json2
granularity: domain-level

### Offline / Batch update

TODO: this is currently done by misinfome_datasets: decide what to do

#### MediaBiasFactCheck

description: https://mediabiasfactcheck.com/methodology/
method: https://github.com/JeffreyATW/mbfc_crawler/
granularity: domain-level

TODO re-implement in python

#### Newsroom Transparency Tracker

description: https://www.newsroomtransparencytracker.com/
method: scraping the table at https://www.newsroomtransparencytracker.com/wp-admin/admin-ajax.php
granularity: domain-level

#### International Fact-Checking Network

TODO

#### Le Monde - Decodeux

description:
method: https://www.lemonde.fr/webservice/decodex/updates and https://s1.lemde.fr/mmpub/data/decodex/hoax/hoax_debunks.json
granularity: source-level and article-level

#### Fact-Checker crawling

TODO


## Requirements

You need a [MyWOT key](https://www.mywot.com/api). Once you have it, pass it as environment variable `MYWOT_KEY`. You can create a `.env` file in this folder with the following content:

```bash
MYWOT_KEY=PASTE_HERE_YOUR_KEY
```

## Docker

build the container: `docker build -t mm34834/credibility .`

Run the container:

locally:
```
docker run -dit --restart always --name mm34834_credibility --network=twitter_app_default -p 20300:8000 -e MONGO_HOST=mongo:27017 -v `pwd`:/app --link=twitter_app_mongo_1:mongo mm34834/credibility
```

```
docker run -dit --restart always --name mm34834_credibility -p 127.0.0.1:20300:8000 -e MONGO_HOST=mongo:27017 -v `pwd`:/app --link=mm34834_mongo:mongo mm34834/credibility
```