# Credibility

The aim is to estimate the credibility of news sources / articles

## Installation

If you have access to ClaimReview scraper repository, do

```
pip install git+https://github.com/MartinoMensio/MisinfoMe_datasets
pip install -e ../../claimreview-collector
```

## Sources

There are two kinds of sources: online and offline. The online ones can be queried in real time. The offline instead are downloaded and updated periodically

### Online query


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

#### Fact-Checking report

The factuality report is possible thanks to a process that:
1. retrieves a lot of ClaimReview
2. processes them looking at the appearances of the claims and propagating the fact-checker label on the websites (source / domain)

The retrieval of the ClaimReview items is done by using `claimreview_collector`.

The `claimreview_collector` library retrieves fact-checks using:
- datacommons (research and feed)
- google fact-checking tools
- direct retrieval from fact-checking websites

After the ClaimReviews are collected, the process (in this library):
- looks at all the appearances listed of the claim (different fact-checkers use different fields in the `ClaimReview` standard)
- tries to map the `reviewRating` field to a unified scale
- propagates the veracity of the claim to the credibility of the URLs of appearance
- propagates the credibility of the URLs to the source / domain it belongs to (e.g. website X has 3 false claim appearing on it, and 1 true claim, so X's credibility is low)


processing_functions_datasets = {
    'mrisdal_fakenews': mrisdal_fakenews.main,
    'golbeck_fakenews': golbeck_fakenews.main,
    'golbeck_fakenews': golbeck_fakenews.main,
    'liar': liar.main,
    'hoaxy': lambda: None, # TODO
    'buzzface': buzzface.main,
    'fakenewsnet': fakenewsnet.main,
    'rbutr': rbutr.main,
    'hyperpartisan': hyperpartisan.main,
    'domain_list_cbsnews': lambda: domain_list.main('cbsnews'),
    'domain_list_dailydot': lambda: domain_list.main('dailydot'),
    'domain_list_fakenewswatch': lambda: domain_list.main('fakenewswatch'),
    'domain_list_newrepublic': lambda: domain_list.main('newrepublic'),
    'domain_list_npr': lambda: domain_list.main('npr'),
    'domain_list_snopes': lambda: domain_list.main('snopes'),
    'domain_list_thoughtco': lambda: domain_list.main('thoughtco'),
    'domain_list_usnews': lambda: domain_list.main('usnews'),
    'domain_list_politifact': lambda: domain_list.main('politifact'),
    'melissa_zimdars': lambda: opensources.main('melissa_zimdars'),
    'jruvika_fakenews': jruvika_fakenews.main,
    'factcheckni_list': factcheckni_list.main,
    'buzzfeednews': buzzfeednews.main,
    'pontes_fakenewssample': pontes_fakenewssample.main,
    'vlachos_factchecking': vlachos_factchecking.main,
    'hearvox_unreliable_news': lambda: None # TODO
}


## Requirements

You need a [MyWOT key](https://www.mywot.com/api). Once you have it, pass it as environment variable `MYWOT_KEY`. You can create a `.env` file in this folder with the following content:

```bash
MYWOT_KEY=PASTE_HERE_YOUR_KEY
```

## Run

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 20300
```

## Docker

build the container: `docker build -t martinomensio/credibility .`

Run the container:

locally:
```
docker run -it --restart always --name mm35626_credibility -p 20300:8000 -e MONGO_HOST=mongo:27017 -v `pwd`/.env:/app/.env -v `pwd`/app:/app/app --link=mm35626_mongo:mongo martinomensio/credibility
```

server
```
docker run -it --restart always --name mm35626_credibility -p 127.0.0.1:20300:8000 -e MONGO_HOST=mongo:27017 -v `pwd`/.env:/app/.env --link=mm35626_mongo:mongo martinomensio/credibility
```

Trigger the update of the origins:

```
curl -v -X POST http://localhost:20300/origins/
```