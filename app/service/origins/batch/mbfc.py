import requests
import json
import re
import tqdm
import unicodedata
import multiprocessing
from multiprocessing.pool import ThreadPool
from bs4 import BeautifulSoup

from ... import utils
from . import OriginBatch


class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self=self,
            id="mbfc",
            name="Media Bias/Fact Check",
            description="We are the most comprehensive media bias resource on the internet. There are currently 2800+ media sources listed in our database and growing every day. Don’t be fooled by Fake News sources.",
            homepage="https://mediabiasfactcheck.com",
            logo="https://i1.wp.com/mediabiasfactcheck.com/wp-content/uploads/2019/09/70594586_2445557865563713_6069591037599285248_n.png?resize=300%2C300&ssl=1",
            default_weight=7,
        )

    def retreive_source_assessments(self):
        return _retrieve_assessments(self.id, self.homepage)
        # return _retrieve_assessments_2(self.id, self.homepage) # 4479


def _retrieve_assessments_2(self_id, homepage):
    # based on github.com/drmikecrowe/mbfcext
    url = "https://raw.githubusercontent.com/drmikecrowe/mbfcext/master/docs/v3/combined.json"
    res = requests.get(url)
    res.raise_for_status()
    data = res.json()
    # to rebuild/interpret assessments
    key_shortener = (
        lambda name: "".join(
            [el[0].upper() for el in name.replace(" ", "-").split("-")]
        )
        if name != "conspiracy"
        else "CP"
    )
    biases_dict = {key_shortener(key): value for key, value in data["biases"].items()}
    reporting_dict = {
        key_shortener(key): value for key, value in data["reporting"].items()
    }
    credibility_dict = data["credibility"]
    results = []
    for source, ass in data["sources"].items():
        bias = ass.get("b", None)
        if not bias:
            if source == "freepress.org":
                bias = "L"
            elif source in ["rightwingnews.com", "redrocktribune.com"]:
                bias = "FN"
            else:
                raise ValueError(source)
        bias = biases_dict[bias]
        domain = ass.get("d", None)
        if not domain:
            if source == "conservativepoliticstoday":
                domain = "https://www.facebook.com/conservativepoliticstoday/"
            elif source == "womensrightsnews":
                domain = "https://www.facebook.com/WOMENSRIGHTSNEWS/"
            elif source == "borowitz-report":
                domain = "https://www.newyorker.com/humor/borowitz-report"
            elif source == "bemidji pioneer":
                domain = "https://www.bemidjipioneer.com/"
            elif source == "elizabethtown new-enterprise":
                domain = "https://www.thenewsenterprise.com/"
            elif source == "thedenverchannel":
                domain = "https://www.thedenverchannel.com/"
            elif source == "wc minnesota news":
                domain = "https://wcminnesotanews.com/"
            else:
                raise ValueError(source)
        name = ass["n"]
        reporting = ass.get("r", None)
        if reporting:
            reporting = reporting_dict[reporting]
        url = ass["u"]
        if "http" not in url:
            url = f"{homepage}/{url}"
        credibility = ass["c"]
        credibility = credibility_dict[credibility]
        original = {
            "bias": bias,
            "domain": domain,
            "name": name,
            "reporting": reporting,
            "url": url,
            "credibility": credibility,
        }
        if reporting:
            reporting_name = reporting["pretty"]
            mapped_credibility = credibility_mapping(reporting_name)
            original_label = reporting_name + " factual reporting"
        elif credibility:
            credibility_name = credibility
            if credibility_name == "N/A":
                bias_name = bias["name"]
                mapped_credibility = credibility_mapping(bias_name)
                original_label = bias_name + " bias"
            else:
                mapped_credibility = credibility_mapping(credibility_name)
                original_label = credibility_name + " credibility"
        else:
            bias_name = bias["name"]
            mapped_credibility = credibility_mapping(bias_name)
            original_label = bias_name + " bias"
        source_homepage = original["domain"]
        source = utils.get_url_source(source_homepage)
        domain = utils.get_url_domain(source_homepage)
        result = {
            "url": original["url"],
            "credibility": mapped_credibility,
            "itemReviewed": source_homepage,
            "original": original,
            "origin_id": self_id,
            "original_label": original_label,
            "domain": domain,
            "source": source,
            "granularity": "source",
        }
        results.append(result)
    return results


def credibility_mapping(label):
    confidence = 1.0
    label = label.replace("-", " ").upper().replace("CREDIBILITY", "").strip()
    # from the values reported here https://mediabiasfactcheck.com/methodology/
    # using value = (10 - mean(score) - 5)/5
    # that corresponds to flipping [0;10] and linearly transposing to [-1;1]
    # where mean(score) is the mean value
    # e.g. HIGH --> score in 1-3 --> mean(score) = 2 --> value = 0.6
    if label == "VERY HIGH":
        credibility = 1.0
    elif label == "HIGH":
        credibility = 0.6
    elif label == "MOSTLY FACTUAL":
        credibility = 0.3
    elif label in ["MIXED", "MEDIUM"]:
        credibility = 0.0
    elif label in ["LOW", "CONSPIRACY PSEUDOSCIENCE", "QUESTIONABLE SOURCES"]:
        credibility = -0.6
    elif label == "VERY LOW":
        credibility = -1.0
    else:
        # print(mbfc_assessment)
        # the scraper didn't manage to find it, so we don't know
        credibility = 0.0
        confidence = 0.0
    result = {"value": credibility, "confidence": confidence}
    return result


_POOL_SIZE = 30

# these sources don't have a link to the homepage in the assessment
_save_me_dict = {
    "seventeen": "https://www.seventeen.com/",
    "the-fucking-news": "http://thefingnews.com/",
    "denver-westword": "https://www.westword.com/",
    "kyiv-post": "https://www.kyivpost.com/",
    "philadelphia-tribune": "https://www.phillytrib.com/",
    "biloxi-sun-herald": "https://www.sunherald.com/",
    "bozeman-daily-chronicle": "https://www.bozemandailychronicle.com/",
    "south-bend-tribune": "https://www.southbendtribune.com/",
    "california-globe": "https://californiaglobe.com/",
    "lubbock-avalanche-journal": "https://www.lubbockonline.com/",
    "eagle-pass-news-leader": "https://www.epnewsleader.com/",
    "significance-magazine": "https://www.significancemagazine.com/",
    "ghost-report": "https://ghost.report/",
    "right-wing-tribune": "https://rightwingtribune.com/",
    "sports-pickle": "https://sportspickle.com",
    "the-daily-news-uk": "http://www.the-daily-news.co.uk/",
    "aptn-news": "https://aptnnews.ca/",
    "elko-daily-free-press": "https://elkodaily.com/",
    "journal-gazette-times-courier": "https://jg-tc.com/",
    "polipace": "http://polipace.com/",
    "borowitz-report": "https://www.newyorker.com/humor/borowitz-report",
    "american-psychological-association-apa": "https://www.apa.org/",
    "law-com": "https://www.law.com/",
    "unbiased-america": "http://www.unbiasedamerica.com/",  # TODO but also https://www.facebook.com/pg/UnbiasedAmerica/
    "the-liberty-daily": "https://thelibertydaily.com",
    "united-nations-environment-programme-unep": "https://www.unenvironment.org/",
    "genesius-times": "https://genesiustimes.com/",
    "la-repubblica": "https://www.repubblica.it/",
    "disrn": "https://disrn.com/",
    "philly-voice": "https://www.phillyvoice.com/",
    "elle-magazine": "https://www.elle.com/",
    "refinery29": "https://www.refinery29.com/",
    "algemeen-dagblad": "https://www.ad.nl/",
    "il-giornale": "https://www.ilgiornale.it/",
    "herb": "https://herb.co/",
    "shafaq-news": "https://www.shafaaq.com/",
    "kcra-3": "https://www.kcra.com/",
    "the-political-tribune": "https://www.thepoliticaltribune.com/",
    "cbs-los-angeles-kcbs": "https://losangeles.cbslocal.com/",
    "wamu-fm": "https://wamu.org/",
    "real-raw-news": "https://realrawnewstoday.com/",
    "rumble": "https://rumble.com/",
    "alt-right-tv": "https://altrighttv.com/",
    "sc-connecticut-news": "https://scconnnews.com/",
    "we-love-trump": "https://welovetrump.com/",
    "anewspost-com": "https://anewspost.com/",
    "online-updates": "https://online-updates.net/",
    "the-vaccine-reaction": "https://thevaccinereaction.org/",
    "american-conservative-movement-acm": "https://americanconservativemovement.com/",
    "christians-for-truth": "https://christiansfortruth.com/",
    "dan-bongino-bias-rating": "https://bongino.com/",
    "the-intergovernmental-panel-on-climate-change-ipcc": "https://www.ipcc.ch/",
    "borowitz-report": "https://www.newyorker.com/humor/borowitz-report",
    "der-standard-bias": "https://www.derstandard.at/",
    "4chan-bias": "https://www.4chan.org/",
    "covidanalysis-network-c19early-com-bias": "https://c19early.com/",
    "national-alliance": "https://natall.com/",
    "riposte-laique-bias": "https://ripostelaique.com/",
    "the-grayzone": "https://thegrayzone.com/",
    "rachel-maddow-bias-rating-2": "https://www.msnbc.com/rachel-maddow-show",
    "giffords-law-center-to-prevent-gun-violence-bias": "https://giffords.org/",
}


def _retrieve_assessments(origin_id, homepage):
    assessments = _scrape(homepage)
    with open("temp_mbfc_responses.json", "w") as f:
        json.dump(assessments, f, indent=2)
    result_source_level = _interpret_assessments(assessments, origin_id)
    return result_source_level


def _scrape(homepage):
    categories = _get_categories(homepage)
    assessments = {}
    for c in categories:
        print(c)
        if c["label"] == "re-evaluated-sources":
            # these sources are already in other lists
            continue
        assessments_urls = get_assessments_urls(c, homepage)
        print(c["url"], len(assessments_urls))
        for ass_url in assessments_urls:  # [:3]:
            assessment = {"bias": c["label"], "url": ass_url}
            # put in a dict just to remove duplicate assessment URLs
            assessments[ass_url] = assessment
    assessments = assessments.values()

    def scrape_assessment_wrapper(ass):
        try:
            return scrape_assessment(ass, homepage)
        except Exception as e:
            print("EXPLODING EXCEPTION: ", e)
            print(ass)
            # debug which assessment is causing problems
            raise ValueError(ass["url"])

    assessments_scraped = []
    with ThreadPool(_POOL_SIZE) as pool:
        for assessment_scraped in tqdm.tqdm(
            pool.imap_unordered(scrape_assessment_wrapper, assessments),
            total=len(assessments),
        ):
            # print(assessment_scraped)
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
        if (
            el["url"] == "http://mediabiasfactcheck.com/american-news/"
            or el["url"] == "https://mediabiasfactcheck.com/american-news/"
            or el["url"] == "https://mediabiasfactcheck.com/macleans-magazine/"
            or el["url"] == "http://mediabiasfactcheck.com/washington-monthly/"
        ):
            pass
        else:
            result.append(el)

    return result


def _get_categories(homepage):
    response = requests.get(homepage)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, features="lxml")
    biases = soup.select("ul#mega-menu-main_nav .mega-menu-link")
    categories = []
    for b in biases:
        url = b["href"] if b["href"].startswith("https") else f"{homepage}{b['href']}"
        path = url.replace(homepage, "")
        categories.append(
            {"url": url, "name": b.text, "path": path, "label": path.replace("/", "")}
        )
    # this page is a dictionary of terms
    categories = [el for el in categories if el["path"] != "/pseudoscience-dictionary/"]
    return categories


def _get_path_from_full_url(full_url, homepage):
    return full_url.replace(homepage, "/").replace(
        "http://mediabiasfactcheck.com/", "/"
    )


def get_assessments_urls(category, homepage):
    response = requests.get(category["url"])
    response.raise_for_status()

    soup = BeautifulSoup(response.text, features="lxml")
    name = soup.select_one("h1.entry-title.page-title")
    if not name:
        print("no name")
        return []
    name = name.text.strip()
    # TODO description is in a span, not p
    description = "".join(
        [el.text.strip() for el in soup.select("div.entry-content p")[:2]]
    )
    description = re.sub("see also:", "", description, flags=re.IGNORECASE).strip()
    # print(description)
    # they are in a table-container (not anymore in a list)
    # source_urls_list = soup.select('div.entry p[style="text-align: center;"] a')
    source_urls_tables = soup.select('table[id="mbfc-table"] tr td a')

    category["name"] = name
    category["description"] = description

    source_urls = source_urls_tables  # + source_urls_list
    sources_names = [el.getText() for el in source_urls_tables]
    source_urls = [el["href"] for el in source_urls]
    # there are some spurious elements, e.g. https://www.hermancain.com/
    source_urls_valid_indices = [
        True if el.startswith("/") or homepage in el else False for el in source_urls
    ]
    # source_urls = [el for el in source_urls if el.startswith('/') or homepage in el]
    source_urls = [
        f"{homepage}{el}" if el.startswith("/") else el for el in source_urls
    ]

    # fix some entries that have errors
    sources_fixes = {
        "Freedom Outpost (freedomoutpost.com)": "https://mediabiasfactcheck.com/freedom-outpost/",
    }
    for k, v in sources_fixes.items():
        if k in sources_names:
            print("fixed", k)
            source_urls[sources_names.index(k)] = v

    vald_source_urls = [
        el for i, el in enumerate(source_urls) if source_urls_valid_indices[i]
    ]

    return vald_source_urls


def scrape_assessment(assessment, mbfc_homepage):
    # ignore these
    if assessment["url"] in [
        "https://mediabiasfactcheck.com/fake-news/",
        "https://mediabiasfactcheck.com/worldpolitics-news/",
    ]:
        return None
    response = requests.get(
        assessment["url"], verify=True
    )  # lots of verification issues when scraping
    if response.status_code != 200:
        # These 6 pages return HTTP 404
        # https://mediabiasfactcheck.com/euromaiden-press/
        # http://mediabiasfactcheck.com/liberty-unyielding/
        # https://mediabiasfactcheck.com/conservative-opinion/
        # http://mediabiasfactcheck.com/council-of-concerned-citizens/
        # http://mediabiasfactcheck.com/freedom-outpost/
        # http://mediabiasfactcheck.com/the-constitution/
        return None

    soup = BeautifulSoup(response.text, features="lxml")
    article_element = soup.select_one("article")
    if not article_element.get("id"):
        raise ValueError(assessment["url"])
    id = article_element["id"].replace("page-", "")

    # print(assessment['url'], assessment['bias'])
    name = soup.select_one("article.page h1.page-title").text

    # some pages require a paid account: https://mediabiasfactcheck.com/jim-acosta-bias-rating/ https://mediabiasfactcheck.com/erin-burnett-bias-rating/ ...
    pro = soup.select("div.pmpro_content_message")
    if pro:
        return None

    # searching the homepage
    paragraphs = soup.select("p")
    source_homepage = None
    # usually is in a paragraph...
    for m in paragraphs:
        par_text = m.text.replace('"', "")
        # that starts with a specific string
        if (
            par_text.strip().startswith("Source:")
            or par_text.strip().startswith(".Source:")
            or par_text.strip().startswith("Sources:")
            or par_text.strip().startswith("Source ")
        ):
            source_homepage = m.select_one("a")
            if source_homepage:
                source_homepage = source_homepage["href"]
                break
    if not source_homepage:
        # or sometimes starting with 'Notes:' but has to contain an <a> and no other text
        for m in paragraphs:
            # print('p', m)
            par_text = m.text.replace('"', "")
            not_nested = "".join(m.find_all(text=True, recursive=False)).strip()
            # print('par_text', par_text)
            # print('nn', not_nested)
            not_nested = not_nested.replace("Notes:", "").strip()
            # print('nn2', not_nested)
            if par_text.startswith("Notes:") and m.select_one("a") and not not_nested:
                link = m.select_one("a")["href"]
                if not "mediabiasfactcheck.com" in link:
                    # https://mediabiasfactcheck.com/rare-news/ has a 'Notes:' in <em> that makes all the previous conditions to match
                    source_homepage = link
                    break
    # some instead have the source_homepage in a div instead than a p
    if not source_homepage:
        for m in soup.select("div"):
            par_text = m.text.replace('"', "")
            if par_text.startswith("Source:") or par_text.startswith("Sources:"):
                source_homepage = m.select_one("a")
                if source_homepage:
                    source_homepage = source_homepage["href"]
                    break
    if not source_homepage:
        # some new sources have a table with all the details (e.g. https://mediabiasfactcheck.com/roanoke-times/)
        table = soup.select_one("article table")
        if table:
            for row in table.select("tr"):
                if span := row.select_one("td span") and span.text == "Source URL:":
                    source_homepage = row.select_one("td a")["href"]
    if not source_homepage:
        # last hope when the assessment does not have the homepage linked
        path = _get_path_from_full_url(assessment["url"], mbfc_homepage).replace(
            "/", ""
        )
        # use an handcrafted mapping
        source_homepage = _save_me_dict.get(path, None)
    if not source_homepage:
        # TODO find a way to signal this without interrupting everything
        raise ValueError(assessment["url"])
    factual_desc = None
    factual = None
    leaning = None
    leaning_desc = None
    imgs = soup.select("article img")
    for img in imgs:
        img_title = img.get("data-image-title", None)
        if not img_title or len(img_title) > 50:
            continue
        img_alt = img["alt"].strip()
        desc = img_alt.split("\n")[0]
        desc = desc.strip()
        if "Factual Reporting" in img_alt:
            # this is the factual label
            factual = img_title
            factual_desc = img_alt
        else:
            leaning = img_title
            leaning_desc = img_alt

    # the ones in questionable (fake-news) have an attribute called "reasoning"
    reasoning = None
    for m in paragraphs:
        if m.text.startswith("Reasoning:") or m.text.startswith(
            "Questionable Reasoning:"
        ):
            reasoning = m.text
            reasoning = unicodedata.normalize("NFKD", reasoning)
            reasoning = reasoning.split("\n")[0]
            reasoning = reasoning.strip()
            break
    detailed_report_fields = [
        {
            "name": "reasoning",
            "prefixes": ["Reasoning:", "Questionable Reasoning:"],
        },
        {
            "name": "bias_rating",
            "prefixes": ["Bias Rating:"],
        },
        {
            "name": "factual_reporting",
            "prefixes": ["Factual Reporting:"],
        },
        {
            "name": "country",
            "prefixes": ["Country:"],
        },
        {
            "name": "press_freedom_rating",
            "prefixes": ["Press Freedom Rating:"],
        },
        {
            "name": "media_type",
            "prefixes": ["Media Type:"],
        },
        {
            "name": "traffic_popularity",
            "prefixes": ["Traffic/Popularity:"],
        },
        {
            "name": "mbfc_credibility_rating",
            "prefixes": ["MBFC Credibility Rating:"],
        },
    ]
    detailed_report = {}
    for m in paragraphs:
        for field in detailed_report_fields:
            for prefix in field["prefixes"]:
                if m.text.lower().startswith(prefix.lower()):
                    value = m.text
                    value = value.split("\n")[0]
                    value = ":".join(value.split(":")[1:])
                    value = value.strip()
                    # split by comma
                    # value = value.split(', ')
                    detailed_report[field["name"]] = value
                    break

    result = {
        "url": assessment["url"],
        "bias": assessment["bias"],
        "id": id,
        "name": name,
        "homepage": source_homepage,
        "factual": factual,
        "factual_desc": factual_desc,
        "leaning": leaning,
        "leaning_desc": leaning_desc,
        "reasoning": reasoning,
        "detailed_report": detailed_report,
    }

    return result


def _get_credibility_measures(mbfc_assessment):
    confidence = 1.0
    factual_level = mbfc_assessment.get("factual", None)
    if factual_level:
        factual_level = factual_level.replace("MBFC", "").upper()
    # from the values reported here https://mediabiasfactcheck.com/methodology/
    # using value = (10 - mean(score) - 5)/5
    # that corresponds to flipping [0;10] and linearly transposing to [-1;1]
    # where mean(score) is the mean value
    # e.g. HIGH --> score in 1-3 --> mean(score) = 2 --> value = 0.6
    if factual_level == "VERY HIGH":
        credibility = 1.0
    elif factual_level == "HIGH":
        credibility = 0.6
    elif factual_level == "MOSTLY FACTUAL":
        credibility = 0.3
    elif factual_level == "MIXED":
        credibility = 0.0
    elif factual_level == "LOW":
        credibility = -0.6
    elif factual_level == "VERY LOW":
        credibility = -1.0
    else:
        # print(mbfc_assessment)
        # the scraper didn't manage to find it, so we don't know
        credibility = 0.0
        confidence = 0.0
    result = {"value": credibility, "confidence": confidence}
    return result


def _interpret_assessments(assessments, origin_id):
    results = []
    for ass in assessments:
        assessment_url = ass["url"]
        credibility = _get_credibility_measures(ass)
        source_homepage = ass["homepage"]
        source = utils.get_url_source(source_homepage)
        domain = utils.get_url_domain(source_homepage)
        if not assessment_url:
            raise ValueError(ass)

        result = {
            "url": assessment_url,
            "credibility": credibility,
            "itemReviewed": source_homepage,
            "original": ass,
            "origin_id": origin_id,
            "domain": domain,
            "source": source,
            "granularity": "source",
        }
        results.append(result)
    return results
