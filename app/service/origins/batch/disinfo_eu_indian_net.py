import requests
import re
from bs4 import BeautifulSoup
from collections import defaultdict

from ... import utils
from . import OriginBatch


class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self=self,
            id="disinfo_eu_indian_net",
            name="Disinfo.eu fake media",
            description="Coordinated fake local media outlets serving Indian interests",
            homepage="https://www.disinfo.eu/publications/uncovered-265-coordinated-fake-local-media-outlets-serving-indian-interests/",
            logo="https://www.disinfo.eu/wp-content/uploads/2019/01/Disinfo-Logo-on-white-rgb-400.jpg",
            default_weight=1,
        )

    def retreive_source_assessments(self):
        return _retrieve_assessments(self.id, self.homepage)


def _retrieve_assessments(origin_id, homepage):
    original_items = _download_from_source()
    result_source_level = _interpret_items(original_items, origin_id)
    return result_source_level


def _download_from_source():
    kml_url = "https://www.google.com/maps/d/kml?mid=1-_KpPuAyLGUhz_R84V12Hu5C_i2oJPSs&forcekml=1"
    response = requests.get(kml_url)
    response.raise_for_status()

    xmlstring = response.text
    # remove namespace that
    # xmlstring = re.sub(r'\sxmlns="[^"]+"', '', xmlstring, count=1)
    soup = BeautifulSoup(xmlstring, "lxml")
    # print(soup)
    placemarks = soup.select("document folder placemark")
    print(len(placemarks))
    results = []
    for pm in placemarks:
        result = {}
        result["name"] = pm.select_one("name").text.strip()
        result["address"] = pm.select_one("address").text.strip()
        result["description"] = pm.select_one("description").text.strip()
        result["place_names"] = [
            el.text.strip()
            for el in pm.select('extendeddata data[name="Place names"] value')
        ]
        result["twitter_account"] = pm.select_one(
            'extendeddata data[name="Twitter account"] value'
        ).text.strip()
        result["original_outlet"] = pm.select_one(
            'extendeddata data[name="Original outlet"] value'
        ).text.strip()
        result["original_outlet_link"] = pm.select_one(
            'extendeddata data[name="Link to original outlet"] value'
        ).text.strip()
        results.append(result)

    return results


def _interpret_items(original_items, origin_id):
    results = []
    assessment_url = "https://www.google.com/maps/d/viewer?ll=2.1715328525318753%2C0&z=2&mid=1-_KpPuAyLGUhz_R84V12Hu5C_i2oJPSs"

    for el in original_items:
        credibility = {"value": -1.0, "confidence": 1.0}
        itemReviewed = [el["name"]]
        if "twitter.com/" in el["twitter_account"]:
            # some have value 'warning website' instead
            account = el["twitter_account"]
            account = account.replace("https://", "")
            account = account.replace("http://", "")
            # add the review of the twitter account too
            itemReviewed.append(account)
        if el["original_outlet"] == "Zombie":
            label = "Zombie: named after an extinct local newspaper"
        elif el["original_outlet"] == "New":
            label = "New: media outlets that never existed"
        else:
            # Misleading
            label = (
                "Misleading: media outlets name close to actual running media outlets"
            )
        for source in itemReviewed:
            source_domain = utils.get_url_domain(source)
            result = {
                "url": assessment_url,
                "credibility": credibility,
                "itemReviewed": source,
                "original": el,
                "origin_id": origin_id,
                "original_label": label,
                "domain": source_domain,
                "source": source,
                "granularity": "source",
            }
            results.append(result)

    return results
