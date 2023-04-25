import os
import requests
from bs4 import BeautifulSoup

from ... import utils

from . import OriginBatch


class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self=self,
            id="pink_slime",
            name="Pink Slime sources",
            description="“Pink slime” is the name given to low-cost automated news sites, built to look like other credible news sites, but are owned, funded or operated by political-interest groups or “dark money” networks. They are not real news sites, although they may, at times, feature news.\n\nThe sites often feature fake authors, who are listed for countless other sites in the network.\n\nThe names sound like local news outlets. They’re not. They’re not even wholly human. Their articles are mostly harvested by bots, then cloned to hundreds of websites — the opposite of local reporting.",
            homepage="https://iffy.news/2020/your-states-been-pink-slimed/",  # https://www.niemanlab.org/2020/07/hundreds-of-hyperpartisan-sites-are-masquerading-as-local-news-this-map-shows-if-theres-one-near-you/
            logo="https://www.niemanlab.org/wordpress/wp-content/themes/Labby/resources/niemansitelogos/lab-logo-color-tighter.svg",
            default_weight=5,
        )
        # 'https://docs.google.com/spreadsheets/d/1C6k2j1KVDvHU24SykB2VnEorVgLD6p18Hi1Yz7Wzdz8/edit'
        self.spreadsheet_id = "1C6k2j1KVDvHU24SykB2VnEorVgLD6p18Hi1Yz7Wzdz8"
        self.api_key = os.environ["PINKSLIME_SPREADSHEET_KEY"]

    def retreive_source_assessments(self):
        return _retrieve_assessments(
            self.id, self.homepage, self.spreadsheet_id, self.api_key
        )


def _retrieve_assessments(origin_id, homepage, spreadsheet_id, api_key):
    table1 = _get_table(spreadsheet_id, api_key, "USA")
    table2 = _get_table(spreadsheet_id, api_key, "USA-1a")
    table3 = _get_table(spreadsheet_id, api_key, "World")
    results1 = _interpret_table(table1, origin_id, homepage)
    results2 = _interpret_table(table2, origin_id, homepage)
    results3 = _interpret_table(table3, origin_id, homepage)

    return results1 + results2 + results3


def _get_table(spreadsheet_id, api_key, sheet_name):
    response = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_name}?key={api_key}"
    )

    response.raise_for_status()

    table = response.json()

    cleaned_table = []
    column_names = table["values"][0]
    for row in table["values"][1:]:
        properties = {k: v for k, v in zip(column_names, row)}
        cleaned_table.append(properties)
    return cleaned_table


def _interpret_table(table, origin_id, homepage):
    results = []
    for row in table:
        domain_a = row["domain"]
        source_raw = row["url"]
        # print(source_raw)
        domain = utils.get_url_domain(source_raw)
        source = utils.get_url_source(source_raw)
        assert domain_a == domain
        assert domain_a == source

        credibility = {"value": -1.0, "confidence": 0.8}

        interpreted = {
            "url": homepage,
            "credibility": credibility,
            "itemReviewed": domain,
            "original": row,
            "origin_id": origin_id,
            "original_label": "Pink slime",
            "domain": domain,
            "source": source,
            "granularity": "source",
        }

        results.append(interpreted)

    return results
