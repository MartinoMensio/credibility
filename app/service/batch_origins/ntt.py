import requests
from bs4 import BeautifulSoup

from .. import utils, persistence

WEIGHT = 8


ID = 'ntt'
NAME = 'Newsroom Transparency Tracker'
DESCRIPTION = 'The Newsroom Transparency Tracker shares the information published by media outlets with respect to four Trust Indicators, transparency standards that provide clarity on a media outlet’s ethics codes and related commitments, how it does its work, and the expertise of its journalists. Developed collaboratively by over 100 senior news executives within the Trust Project network, Trust Indicators are rooted in core journalistic values and based on in-depth research capturing what the public trusts and wants in news.'

HOMEPAGE = 'https://www.newsroomtransparencytracker.com/'
API_ENDPOINT = 'https://www.newsroomtransparencytracker.com/wp-admin/admin-ajax.php'

columns = [
    'id', 'Newsroom', 'Ethics Policy', 'Ownership/ Funding', 'Mission/ Coverage Priorities', 'Verification/ Fact-checking',
    'Corrections Policy', 'Unnamed Sources Policy', 'Masthead/ Leadership', 'Founding Date', 'Newsroom Contact Info',
    'Author/ Reporter Bios', 'Byline Attribution', 'Type of Work Labels', 'Diverse Voices Statement', 'Diverse Staffing Report', 'Trust Project Partner', 'reportanissue'
]

def get_source_credibility(source):
    return persistence.get_source_assessment(ID, source)

def get_domain_credibility(domain):
    return persistence.get_domain_assessment(ID, domain)

def get_url_credibility(url):
    return None

def update():
    table = download_from_source()
    result_source_level = interpret_table(table)
    result_domain_level = utils.aggregate_domain(result_source_level, ID)
    print(ID, 'retrieved', len(result_domain_level), 'domains', len(result_source_level), 'sources', 'assessments') # , len(result_document_level), 'documents'
    all_assessments = list(result_source_level) + list(result_domain_level) # list(result_document_level) +
    persistence.save_assessments(ID, all_assessments)
    return len(all_assessments)


def interpret_table(table):
    results = []
    for row in table['data']:
        row_parsed = {columns[idx]: get_compliacy(el) for idx, el in enumerate(row)}
        source_name = row_parsed['Newsroom']

        source_raw = utils.name_domain_map[source_name]
        domain = utils.get_url_domain(source_raw)
        source = utils.get_url_source(source_raw)

        credibility = get_credibility_measures(row_parsed)

        interpreted = {
            'url': HOMEPAGE,
            'credibility': credibility,
            'itemReviewed': source,
            'original': row_parsed,
            'origin_id': ID,
            'domain': domain,
            'source': source,
            'granularity': 'source'
        }

        results.append(interpreted)

    return results


def download_from_source():
    # from https://www.newsroomtransparencytracker.com/
    response = requests.get(HOMEPAGE)
    if response.status_code != 200:
        raise ValueError(response.status_code)

    soup = BeautifulSoup(response.text, 'lxml')
    wdtNonce = soup.find('input', {'id': 'wdtNonceFrontendEdit'})['value']
    print(wdtNonce)

    # if this script breaks, inspect the source page and look for the column origHeader and displayHeader and the nonce
    querystring = {"action":"get_wdtable","table_id":"7"}

    payload = {
        'draw': '1',
        'columns%5B0%5D%5Bdata%5D': '0',
        'columns%5B0%5D%5Bname%5D': 'wdt_ID',
        'columns%5B0%5D%5Bsearchable%5D': 'true',
        'columns%5B0%5D%5Borderable%5D': 'true',
        'columns%5B0%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B0%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B1%5D%5Bdata%5D': '1',
        'columns%5B1%5D%5Bname%5D': 'newsroom',
        'columns%5B1%5D%5Bsearchable%5D': 'true',
        'columns%5B1%5D%5Borderable%5D': 'true',
        'columns%5B1%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B1%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B2%5D%5Bdata%5D': '2',
        'columns%5B2%5D%5Bname%5D': 'newcolumn1',
        'columns%5B2%5D%5Bsearchable%5D': 'true',
        'columns%5B2%5D%5Borderable%5D': 'false',
        'columns%5B2%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B2%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B3%5D%5Bdata%5D': '3',
        'columns%5B3%5D%5Bname%5D': 'newcolumn3',
        'columns%5B3%5D%5Bsearchable%5D': 'true',
        'columns%5B3%5D%5Borderable%5D': 'false',
        'columns%5B3%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B3%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B4%5D%5Bdata%5D': '4',
        'columns%5B4%5D%5Bname%5D': 'newcolumn6',
        'columns%5B4%5D%5Bsearchable%5D': 'true',
        'columns%5B4%5D%5Borderable%5D': 'false',
        'columns%5B4%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B4%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B5%5D%5Bdata%5D': '5',
        'columns%5B5%5D%5Bname%5D': 'newcolumn7',
        'columns%5B5%5D%5Bsearchable%5D': 'true',
        'columns%5B5%5D%5Borderable%5D': 'false',
        'columns%5B5%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B5%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B6%5D%5Bdata%5D': '6',
        'columns%5B6%5D%5Bname%5D': 'newcolumn2',
        'columns%5B6%5D%5Bsearchable%5D': 'true',
        'columns%5B6%5D%5Borderable%5D': 'false',
        'columns%5B6%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B6%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B7%5D%5Bdata%5D': '7',
        'columns%5B7%5D%5Bname%5D': 'newcolumn8',
        'columns%5B7%5D%5Bsearchable%5D': 'true',
        'columns%5B7%5D%5Borderable%5D': 'false',
        'columns%5B7%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B7%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B8%5D%5Bdata%5D': '8',
        'columns%5B8%5D%5Bname%5D': 'newcolumn5',
        'columns%5B8%5D%5Bsearchable%5D': 'true',
        'columns%5B8%5D%5Borderable%5D': 'false',
        'columns%5B8%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B8%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B9%5D%5Bdata%5D': '9',
        'columns%5B9%5D%5Bname%5D': 'newcolumn4',
        'columns%5B9%5D%5Bsearchable%5D': 'true',
        'columns%5B9%5D%5Borderable%5D': 'false',
        'columns%5B9%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B9%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B10%5D%5Bdata%5D': '10',
        'columns%5B10%5D%5Bname%5D': 'newcolumn9',
        'columns%5B10%5D%5Bsearchable%5D': 'true',
        'columns%5B10%5D%5Borderable%5D': 'false',
        'columns%5B10%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B10%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B11%5D%5Bdata%5D': '11',
        'columns%5B11%5D%5Bname%5D': 'newcolumn11',
        'columns%5B11%5D%5Bsearchable%5D': 'true',
        'columns%5B11%5D%5Borderable%5D': 'false',
        'columns%5B11%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B11%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B12%5D%5Bdata%5D': '12',
        'columns%5B12%5D%5Bname%5D': 'newcolumn12',
        'columns%5B12%5D%5Bsearchable%5D': 'true',
        'columns%5B12%5D%5Borderable%5D': 'false',
        'columns%5B12%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B12%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B13%5D%5Bdata%5D': '13',
        'columns%5B13%5D%5Bname%5D': 'newcolumn13',
        'columns%5B13%5D%5Bsearchable%5D': 'true',
        'columns%5B13%5D%5Borderable%5D': 'false',
        'columns%5B13%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B13%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B14%5D%5Bdata%5D': '14',
        'columns%5B14%5D%5Bname%5D': 'newcolumn14',
        'columns%5B14%5D%5Bsearchable%5D': 'true',
        'columns%5B14%5D%5Borderable%5D': 'false',
        'columns%5B14%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B14%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B15%5D%5Bdata%5D': '15',
        'columns%5B15%5D%5Bname%5D': 'newcolumn15',
        'columns%5B15%5D%5Bsearchable%5D': 'true',
        'columns%5B15%5D%5Borderable%5D': 'false',
        'columns%5B15%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B15%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B16%5D%5Bdata%5D': '16',
        'columns%5B16%5D%5Bname%5D': 'newcolumn10',
        'columns%5B16%5D%5Bsearchable%5D': 'true',
        'columns%5B16%5D%5Borderable%5D': 'false',
        'columns%5B16%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B16%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'columns%5B17%5D%5Bdata%5D': '17',
        'columns%5B17%5D%5Bname%5D': 'reportanissue',
        'columns%5B17%5D%5Bsearchable%5D': 'true',
        'columns%5B17%5D%5Borderable%5D': 'false',
        'columns%5B17%5D%5Bsearch%5D%5Bvalue%5D': '',
        'columns%5B17%5D%5Bsearch%5D%5Bregex%5D': 'false',
        'order%5B0%5D%5Bcolumn%5D': '1',
        'order%5B0%5D%5Bdir%5D': 'asc',
        'start': '0',
        'length': '-1',
        'search%5Bvalue%5D': '',
        'search%5Bregex%5D': 'false',
        'wdtNonce': wdtNonce
    }

    response = requests.request("POST", API_ENDPOINT, data=payload, params=querystring)
    if response.status_code != 200:
        print('error retrieving list')
        raise ValueError(response.status_code)

    result = response.json()
    return result

def get_credibility_measures(row):
    full_compliant_cnt = sum([1 for el in row.values() if el == 'Full'])
    partial_compliant_cnt = sum([1 for el in row.values() if el == 'Partial'])
    none_compliant_cnt = sum([1 for el in row.values() if el == 'None'])
    total = full_compliant_cnt + partial_compliant_cnt + none_compliant_cnt
    score = (full_compliant_cnt + 0.5 * partial_compliant_cnt) / total
    score = score * 2 - 1
    return {
        'value': score,
        'confidence': 1.0
    }

def get_compliacy(html_string):
    if not html_string:
        result = html_string
    elif '"fa fa-circle-o\"' in html_string:
        result = 'None'
    elif '"fa fa-adjust\"' in html_string:
        result = 'Partial'
    elif '"fa fa-circle\"' in html_string:
        result = 'Full'
    else:
        result = html_string
    return result
