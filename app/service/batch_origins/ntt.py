import requests

from .. import utils, persistence

WEIGHT = 8


MY_NAME = 'ntt'

HOMEPAGE = 'https://www.newsroomtransparencytracker.com/'
API_ENDPOINT = 'https://www.newsroomtransparencytracker.com/wp-admin/admin-ajax.php'

columns = [
    'id', 'Newsroom', 'Ethics Policy', 'Ownership/ Funding', 'Mission/ Coverage Priorities', 'Verification/ Fact-checking',
    'Corrections Policy', 'Unnamed Sources Policy', 'Masthead/ Leadership', 'Founding Date', 'Newsroom Contact Info',
    'Author/ Reporter Bios', 'Byline Attribution', 'Type of Work Labels', 'Diverse Voices Statement', 'Diverse Staffing Report', 'Trust Project Partner', 'reportanissue'
]

def get_source_credibility(source):
    return persistence.get_domain_assessment(MY_NAME, source)

def update():
    table = download_from_source()
    result = interpret_table(table)
    print(MY_NAME, 'retrieved', len(result), 'assessments')
    persistence.save_origin(MY_NAME, result)


def interpret_table(table):
    results = []
    for row in table['data']:
        row_parsed = {columns[idx]: get_compliacy(el) for idx, el in enumerate(row)}
        source_name = row_parsed['Newsroom']

        source = utils.name_domain_map[source_name]
        domain = utils.get_url_domain(source)

        credibility = get_credibility_measures(row_parsed)

        interpreted = {
            'url': HOMEPAGE,
            'credibility': credibility,
            'itemReviewed': source,
            'original': row_parsed,
            'origin': MY_NAME,
            'domain': domain
        }

        results.append(interpreted)

    return results


def download_from_source():
    # from https://www.newsroomtransparencytracker.com/
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
        'wdtNonce': '4b4dfdb88d'
    }

    response = requests.request("POST", API_ENDPOINT, data=payload, params=querystring)

    result = response.json()
    print('retrieved')
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
