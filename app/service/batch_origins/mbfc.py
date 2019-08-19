import requests
import json
import re
import tqdm
import multiprocessing
from multiprocessing.pool import ThreadPool
from bs4 import BeautifulSoup

from .. import persistence, utils

WEIGHT = 7

HOMEPAGE = 'https://mediabiasfactcheck.com/'
MY_NAME = 'mbfc'
POOL_SIZE = 30

# these sources don't have a link to the homepage in the assessment
save_me_dict = {
    'seventeen': 'https://www.seventeen.com/',
    'the-fucking-news': 'http://thefingnews.com/',
    'denver-westword': 'https://www.westword.com/',
    'kyiv-post': 'https://www.kyivpost.com/',
    'philadelphia-tribune': 'https://www.phillytrib.com/',
    'biloxi-sun-herald': 'https://www.sunherald.com/',
    'bozeman-daily-chronicle': 'https://www.bozemandailychronicle.com/',
    'south-bend-tribune': 'https://www.southbendtribune.com/',
    'california-globe': 'https://californiaglobe.com/',
    'lubbock-avalanche-journal': 'https://www.lubbockonline.com/',
    'eagle-pass-news-leader': 'https://www.epnewsleader.com/',
    'significance-magazine': 'https://www.significancemagazine.com/',
    'ghost-report': 'https://ghost.report/',
    'right-wing-tribune': 'https://rightwingtribune.com/',
    'sports-pickle': 'https://sportspickle.com',
    'the-daily-news-uk': 'http://www.the-daily-news.co.uk/',
    'aptn-news': 'https://aptnnews.ca/',
    'elko-daily-free-press': 'https://elkodaily.com/',
    'journal-gazette-times-courier': 'https://jg-tc.com/',
    'polipace': 'http://polipace.com/',
    'borowitz-report': 'https://www.newyorker.com/humor/borowitz-report',
    'american-psychological-association-apa': 'https://www.apa.org/'
}

def get_source_credibility(source):
    return persistence.get_domain_assessment(MY_NAME, source)

def update():
    assessments = scrape()
    with open('temp_mbfc_responses.json', 'w') as f:
        json.dump(assessments, f, indent=2)
    result = interpret_assessments(assessments)
    print(MY_NAME, 'retrieved', len(result), 'assessments')
    persistence.save_origin_assessments(MY_NAME, result)
    return len(result)

def scrape():
    categories = get_categories()
    assessments = {}
    for c in categories:
        if c['label'] == 're-evaluated-sources':
            # these sources are already in other lists
            continue
        assessments_urls = get_assessments_urls(c)
        print(c['url'], len(assessments_urls))
        for ass_url in assessments_urls:#[:3]:
            assessment = {
                'bias': c['label'],
                'url': ass_url
            }
            # put in a dict just to remove duplicate assessment URLs
            assessments[ass_url] = assessment
    assessments = assessments.values()

    assessments_scraped = []
    with ThreadPool(POOL_SIZE) as pool:
        for assessment_scraped in tqdm.tqdm(pool.imap_unordered(scrape_assessment, assessments), total=len(assessments)):
            #print(assessment_scraped)
            if assessment_scraped:
                assessments_scraped.append(assessment_scraped)

    # for these sources, there are two different urls:
    # https://www.americandailynews.org/ :
    #   http://mediabiasfactcheck.com/american-news/ (extreme-right)
    #   https://mediabiasfactcheck.com/american-news-24-7/ (right, factual=MIXED)
    # https://www.macleans.ca :
    #   http://mediabiasfactcheck.com/macleans-magazine/ (listed in the leftcenter: correct, but redirects to the https)
    #   https://mediabiasfactcheck.com/macleans-magazine/ (listed in the right-center: wrong class but correct URL)
    # http://washingtonmonthly.com/ :
    #   http://mediabiasfactcheck.com/washington-monthly/
    #   https://mediabiasfactcheck.com/washington-monthly/
    result = []
    for el in assessments_scraped:
        # discard these
        if el['url'] == 'http://mediabiasfactcheck.com/american-news/' \
            or el['url'] == 'https://mediabiasfactcheck.com/american-news/' \
            or el['url'] == 'https://mediabiasfactcheck.com/macleans-magazine/'\
            or el['url'] == 'http://mediabiasfactcheck.com/washington-monthly/':
            pass
        else:
            result.append(el)


    return result
    #return len(assessments)


def get_categories():
    response = requests.get(HOMEPAGE)
    if response.status_code != 200:
        raise ValueError(response.status_code)

    soup = BeautifulSoup(response.text, features='lxml')
    biases = soup.select('ul#mega-menu-info_nav a.mega-menu-link')
    return [{
        'url': b['href'],
        'name': b.text,
        'path': get_path_from_full_url(b['href']),
        'label': get_path_from_full_url(b['href']).replace('/', '')
    } for b in biases]

def get_path_from_full_url(full_url):
    return full_url.replace(HOMEPAGE, '/').replace('http://mediabiasfactcheck.com/', '/')

def get_assessments_urls(category):
    response = requests.get(category['url'])
    if response.status_code != 200:
        raise ValueError(response.status_code)

    soup = BeautifulSoup(response.text, features='lxml')
    name =  soup.select_one('.page > h1.page-title').text
    description = ''.join([el.text.strip() for el in soup.select('div.entry p')[:2]])
    description = re.sub('see also:', '', description, flags=re.IGNORECASE).strip()
    #print(description)
    # they are in a table-container (not anymore in a list)
    #source_urls_list = soup.select('div.entry p[style="text-align: center;"] a')
    source_urls_tables = soup.select('table[id="mbfc-table"] tr td a')

    category['name'] = name
    category['description'] = description

    source_urls =  source_urls_tables # + source_urls_list
    source_urls = [el['href'] for el in source_urls]
    # there are some spurious elements, e.g. https://www.hermancain.com/
    source_urls = [el for el in source_urls if 'mediabiasfactcheck.com' in el]

    return source_urls

def scrape_assessment(assessment):
    response = requests.get(assessment['url'])
    if response.status_code != 200:
        # These 6 pages return HTTP 404
        # https://mediabiasfactcheck.com/euromaiden-press/
        # http://mediabiasfactcheck.com/liberty-unyielding/
        # https://mediabiasfactcheck.com/conservative-opinion/
        # http://mediabiasfactcheck.com/council-of-concerned-citizens/
        # http://mediabiasfactcheck.com/freedom-outpost/
        # http://mediabiasfactcheck.com/the-constitution/
        return None

    soup = BeautifulSoup(response.text, features='lxml')
    article_element = soup.select_one('article')
    if not article_element.get('id'):
        raise ValueError(assessment['url'])
    id = article_element['id'].replace('page-', '')

    #print(assessment['url'], assessment['bias'])
    name = soup.select_one('article.page > h1.page-title').text

    # searching the homepage
    paragraphs = soup.select('p')
    homepage = None
    # usually is in a paragraph...
    for m in paragraphs:
        par_text = m.text.replace('"','')
        # that starts with a specific string
        if par_text.startswith('Source:') or par_text.startswith('Sources:'):
            homepage = m.select_one('a')
            if homepage:
                homepage = homepage['href']
                break
    if not homepage:
        # or sometimes starting with 'Notes:' but has to contain an <a> and no other text
        for m in paragraphs:
            #print('p', m)
            par_text = m.text.replace('"','')
            not_nested = ''.join(m.find_all(text=True, recursive=False)).strip()
            #print('par_text', par_text)
            #print('nn', not_nested)
            not_nested = not_nested.replace('Notes:', '').strip()
            #print('nn2', not_nested)
            if par_text.startswith('Notes:') and m.select_one('a') and not not_nested:
                link = m.select_one('a')['href']
                if not 'mediabiasfactcheck.com' in link:
                    # https://mediabiasfactcheck.com/rare-news/ has a 'Notes:' in <em> that makes all the previous conditions to match
                    homepage = link
                    break
    # some instead have the homepage in a div instead than a p
    if not homepage:
        for m in soup.select('div'):
            par_text = m.text.replace('"','')
            if par_text.startswith('Source:') or par_text.startswith('Sources:'):
                homepage = m.select_one('a')
                if homepage:
                    homepage = homepage['href']
                    break
    if not homepage:
        # last hope when the assessment does not have the homepage linked
        path = get_path_from_full_url(assessment['url']).replace('/', '')
        # use an handcrafted mapping
        homepage = save_me_dict.get(path, None)
    if not homepage:
        raise ValueError(assessment['url'])
    factual = None
    for m in paragraphs:
        if m.text.startswith('Factual Reporting:'):
            factual = m.text.replace('Factual Reporting:', '')
            factual = factual.split('\n')[0]
            factual = factual.strip()
            break
    if not factual:
        print('no factuality rating in', assessment['url'])

    # the ones in questionable (fake-news) have an attribute called "reasoning"
    reasoning = None
    for m in paragraphs:
        if m.text.startswith('Reasoning:'):
            reasoning = m.text.replace('Reasoning:', '')
            reasoning = reasoning.split('\n')[0]
            reasoning = reasoning.strip()
            break

    result = {
        'url': assessment['url'],
        'bias': assessment['bias'],
        'id': id,
        'name': name,
        'homepage': homepage,
        'factual': factual
    }

    if reasoning:
        result['reasoning'] = reasoning

    return result


def get_credibility_measures(mbfc_assessment):
    confidence = 1.0
    factual_level = mbfc_assessment.get('factual', None)
    # from the values reported here https://mediabiasfactcheck.com/methodology/
    # using value = (10 - mean(score) - 5)/5
    # that corresponds to flipping [0;10] and linearly transposing to [-1;1]
    # where mean(score) is the mean value
    # e.g. HIGH --> score in 1-3 --> mean(score) = 2 --> value = 0.6
    if factual_level == 'VERY HIGH':
        credibility = 1.0
    elif factual_level == 'HIGH':
        credibility = 0.6
    elif factual_level == 'MOSTLY FACTUAL':
        credibility = 0.3
    elif factual_level == 'MIXED':
        credibility = 0.0
    elif factual_level == 'LOW':
        credibility = -0.6
    elif factual_level == 'VERY LOW':
        credibility = -1.0
    else:
        #print(mbfc_assessment)
        # the scraper didn't manage to find it, so we don't know
        credibility = 0.0
        confidence = 0.0
    result = {
        'value': credibility,
        'confidence': confidence
    }
    return result

def interpret_assessments(assessments):
    results = []
    for ass in assessments:
        assessment_url = ass['url']
        credibility = get_credibility_measures(ass)
        homepage = ass['homepage']
        homepage_domain = utils.get_url_domain(homepage)
        if not assessment_url:
            raise ValueError(ass)

        result = {
            'url': assessment_url,
            'credibility': credibility,
            'itemReviewed': homepage,
            'original': ass,
            'origin': MY_NAME,
            'domain': homepage_domain,
            'granularity': 'source'
        }
        results.append(result)
    return results
