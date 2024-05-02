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
    assessments = _get_signatories_info()
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


def _get_signatories_info():
    url = "https://ifcn-cop-prod-server-8q9x7.ondigitalocean.app/api/organization/signatories"
    response = requests.get(url)
    if response.status_code != 200:
        print("error retrieving list")
        raise ValueError(response.status_code)
    data = response.json()

    # card_body_containers = soup.select('.card div.card-body')
    # verified_signatories = card_body_containers[0]
    # expired_signatories = card_body_containers[1]

    result = []

    for el in data["organizations"]:
        slug = el["slug"]
        badge_hash = el["badge_hash"]
        signatory_status = el["signatory_status"]
        expired = signatory_status == "Expired Signatory"
        signatory = {
            "assessment_url": f"https://ifcncodeofprinciples.poynter.org/profile/{slug}",
            "id": slug,
            "name": el["slug"],
            "avatar": f"https://cdn.ifcncodeofprinciples.poynter.org/storage/badges/{badge_hash}.png",
            "issued_on": el["signatory_status_approval_date"],
            # "expires_on": expires_on,
            "expired": expired,
            # "country": country,
            # "language": language,
            "website": el["organization_owner"]["website"],
            "skills": [],
        }
        result.append(signatory)

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
