import requests
import tqdm
from bs4 import BeautifulSoup

from ... import utils, persistence
from . import OriginBatch


class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self=self,
            id="ifcn",
            name="International Fact-Checking Network",
            description="The code of principles of the International Fact-Checking Network at Poynter is a series of commitments organizations abide by to promote excellence in fact-checking. Nonpartisan and transparent fact-checking can be a powerful instrument of accountability journalism.",
            homepage="https://ifcncodeofprinciples.poynter.org/signatories",
            # logo = 'https://logo.clearbit.com/ifcncodeofprinciples.poynter.org',
            logo="https://pbs.twimg.com/profile_images/1059903297778339842/z6-2Zj_C_400x400.jpg",
            default_weight=10,
        )

    def retreive_source_assessments(self):
        return _retrieve_assessments(self.id, self.homepage)


# TODO scrape the compliances from https://ifcncodeofprinciples.poynter.org/know-more/what-it-takes-to-be-a-signatory


def get_all_sources_credibility():
    """This one is used by factchecking_report"""
    return persistence.get_source_assessments_all("ifcn")


def _retrieve_assessments(origin_id, homepage):
    """Updates all the informations from the signatories"""
    assessments = _get_signatories_info(homepage)
    result = _interpret_assessments(assessments, origin_id)
    return result


def _colors_to_value(style_str):
    color_map = {
        "#4caf50": "fully_compliant",
        "#03a9f4": "partially_compliant",
        "#fff": "empty",
        "#f44336": "none_compliant",
    }
    for k, v in color_map.items():
        if k in style_str:
            return v
    raise ValueError(style_str)


def _extract_signatory_info(detail_url, media_logo):
    response = requests.get(detail_url)
    if response.status_code != 200:
        print(f"error retrieving {detail_url}")
        raise ValueError(response.status_code)

    soup = BeautifulSoup(response.text, "lxml")

    id = detail_url.split("/")[-1]
    name = None
    issued_on = None
    expires_on = None
    expired = None
    country = None
    language = None
    website = None
    skills = []

    card_bodies = soup.select(".card-body")
    for c in card_bodies:
        if "Issued to" in c.text:
            name = c.text.replace("Issued to", "").strip()
        elif "Issued on" in c.text:
            issued_on = c.text.replace("Issued on", "").strip()
        elif "Expires on" in c.text:
            expires_on = c.text.replace("Expires on", "").strip()
            expired = "(Expired)" in expires_on
    details = soup.select(".col-xs-12.col-lg-3.py-1")
    for d in details:
        if "Country:" in d.text:
            country = d.text.replace("Country:", "").strip()
        elif "Language:" in d.text:
            language = d.text.replace("Language:", "").strip()
        elif "Website:" in d.text:
            website = d.text.replace("Website:", "").strip()
    skills_elements = soup.select(".badge.badge-pill.badge-light.my-2.py-2")
    for s in skills_elements:
        skill_name = s.select("small b")[0].text
        circles = s.select("span.circle")
        values = [_colors_to_value(c["style"]) for c in circles]
        skills.append({"name": skill_name, "values": values})
    result = {
        "assessment_url": detail_url,
        "id": id,
        "name": name,
        "avatar": media_logo,
        "issued_on": issued_on,
        "expires_on": expires_on,
        "expired": expired,
        "country": country,
        "language": language,
        "website": website,
        "skills": skills,
    }
    return result


def _get_signatories_info(homepage):
    response = requests.get(homepage)
    if response.status_code != 200:
        print("error retrieving list")
        raise ValueError(response.status_code)
    soup = BeautifulSoup(response.text, "lxml")

    # card_body_containers = soup.select('.card div.card-body')
    # verified_signatories = card_body_containers[0]
    # expired_signatories = card_body_containers[1]

    result = []

    for signatory_el in tqdm.tqdm(soup.select(".card div.card-body div.media")):
        # url = signatory_el.select('a[title]')[0]['href']
        # name = signatory_el.select('div.media-body h5')[0].text.strip()
        # country = signatory_el.select('div.media-body h6')[0].text.strip().replace('from ', '')
        detail_url = signatory_el.select("div.media-body div div div a")[0]["href"]
        media_logo = signatory_el.select_one("img.signatory-avatar")["src"]
        # here get the details
        try:
            signatory = _extract_signatory_info(detail_url, media_logo)
            result.append(signatory)
        except Exception as e:
            print(f"error retrieving {detail_url}")
            print(e)
            continue

    return result


def _interpret_assessments(assessments, origin_id):
    results = []
    for ass in assessments:
        assessment_url = ass["assessment_url"]
        credibility = _get_credibility_measures(ass)
        fact_checker_url = ass["website"]
        fact_checker_domain = utils.get_url_domain(fact_checker_url)
        fact_checker_source = utils.get_url_source(fact_checker_url)

        label = ("Valid" if not ass["expired"] else "Expired") + " IFCN signatory"

        result = {
            "url": assessment_url,
            "credibility": credibility,
            "itemReviewed": fact_checker_source,
            "original": ass,
            "origin_id": origin_id,
            "original_label": label,
            "domain": fact_checker_domain,
            "source": fact_checker_source,
            "granularity": "source",
        }
        results.append(result)
    return results


def _get_credibility_measures(ifcn_assessment):
    credibility = 1.0
    confidence = 1.0
    if ifcn_assessment["expired"]:
        # if IFCN assessment is expired, lower the confidence
        confidence = 0.8  # due to COVID, process is slower (see disclaimer https://ifcncodeofprinciples.poynter.org/signatories)
    for skill in ifcn_assessment["skills"]:
        for value in skill["values"]:
            if value == "partially_compliant":
                credibility -= 0.025
            elif value == "none_compliant":
                credibility -= 0.05
    # credibility is still positive / neutral, not negative
    credibility = max(credibility, 0.0)
    result = {"value": credibility, "confidence": confidence}
    return result
