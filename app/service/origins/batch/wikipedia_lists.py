import requests
from bs4 import BeautifulSoup
import re
import tqdm

from ... import utils
from . import OriginBatch


class Origin(OriginBatch):
    def __init__(self):
        OriginBatch.__init__(
            self=self,
            id="wikipedia_lists",
            name="Wikipedia Lists",
            description="Wikipedia has a list of fake websites (https://en.wikipedia.org/wiki/List_of_fake_news_websites), satire (https://en.wikipedia.org/wiki/List_of_satirical_news_websites) and sources whose reliability has been discussed (https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources/Perennial_sources).",
            homepage="https://en.wikipedia.org/",
            logo="https://en.wikipedia.org/static/images/project-logos/enwiki-2x.png",
            default_weight=1,
        )

    def retreive_source_assessments(self):
        return _retrieve_assessments(self.id, self.homepage)


def _retrieve_assessments(self_id, homepage):
    assessments_1 = _get_fake_news_websites(self_id)
    #assessments_2 = _get_satire_news_websites(self_id) # temporarily disabled due to bugs
    #assessments_3 = _get_perennial_sources(self_id) # temporarily disabled due to bugs

    # TODO duplicates?
    return assessments_1 #+ assessments_2 + assessments_3


def _get_fake_news_websites(self_id):
    url_list = "https://en.wikipedia.org/wiki/List_of_fake_news_websites"
    headers_and_tables = _get_wikipedia_tables_with_headers(url_list)

    results = []
    for headers, table in headers_and_tables:
        for row in tqdm.tqdm(table, desc="Fake websites"):
            # print(row.keys())
            name = row["Name"]
            for el in name.select("style"):
                el.decompose()
            name = name.text.strip()
            name = re.sub(r"\s*\([^)]*\)", "", name)
            name = re.sub(r"\s*\[[^)]*\]", "", name)
            #notes = row["Notes"].text.strip()
            if "URL" in headers:
                # the second table also has URLs
                url = f"http://{row['URL'].text.strip()}/"
            else:
                if name in utils.name_domain_map:
                    url = utils.name_domain_map[name]
                else:
                    print("wikipedia_lists: no URL found for fake news website:", name)
                    url = None

            if url:
                domain = utils.get_url_domain(url)
                source = utils.get_url_source(url)

                original = {k: v.text.strip() for k, v in row.items()}

                # print(name, notes, url)
                ass = {
                    "url": url_list,
                    "credibility": _default_credibility("fake"),
                    "itemReviewed": url,
                    "original": original,
                    "origin_id": self_id,
                    "original_label": "Fake news website",
                    "domain": domain,
                    "source": source,
                    "granularity": "source",
                }
                results.append(ass)
    return results


def _get_satire_news_websites(self_id):
    url_list = "https://en.wikipedia.org/wiki/List_of_satirical_news_websites"
    headers_and_tables = _get_wikipedia_tables_with_headers(url_list)

    results = []
    for headers, table in headers_and_tables:
        for row in tqdm.tqdm(table, desc="Satire websites"):
            # print(row.keys())
            name = row["Name"].text.strip()
            name = re.sub(r"\s*\([^)]*\)", "", name)
            name = re.sub(r"\s*\[[^)]*\]", "", name)
            if not name:
                continue
            # go to the wikipedia page to find the official website
            href = row["Name"].find("a")["href"]
            if href.startswith("http://") or href.startswith("https://"):
                # absolute URL, to another language
                details_url = href
            else:
                # relative URL
                details_url = f"https://en.wikipedia.org{href}"
                
            print(f"--{details_url}--")
            if str(details_url) not in ["https://en.wikipedia.org/wiki/Bopress", "https://en.wikipedia.org/w/index.php?title=Bopress&action=edit&redlink=1"]:
                details = requests.get(
                    details_url,
                    headers={
                        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
                    },
                )
                details.raise_for_status()
                soup = BeautifulSoup(details.text, "lxml")
                official_website = soup.select_one("span.official-website a")
                if official_website:
                    url = official_website["href"]
                else:
                    official_website = soup.select_one("table.infobox a.external")
                    if official_website:
                        url = official_website["href"]
                    else:
                        if name in utils.name_domain_map:
                            url = utils.name_domain_map[name]
                        else:
                            print("wikipedia_lists: no URL found for satire website:", name)
                            url = None
            else:
                if name in utils.name_domain_map:
                    url = utils.name_domain_map[name]
                else:
                    print("wikipedia_lists: no URL found for satire website:", name)
                    url = None

            if url:
                domain = utils.get_url_domain(url)
                source = utils.get_url_source(url)

                original = {k: v.text.strip() for k, v in row.items()}

                # print(name, notes, url)
                ass = {
                    "url": url_list,
                    "credibility": _default_credibility("satire"),
                    "itemReviewed": url,
                    "original": original,
                    "origin_id": self_id,
                    "original_label": "Satire website",
                    "domain": domain,
                    "source": source,
                    "granularity": "source",
                }
                results.append(ass)
    return results


def _get_perennial_sources(self_id):
    url_list = (
        "https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources/Perennial_sources"
    )
    headers_and_tables = _get_wikipedia_tables_with_headers(
        url_list, exclude=["Discussions", "Uses"]
    )

    results = []
    for headers, table in headers_and_tables:
        for row in tqdm.tqdm(table, desc="Perennial sources"):
            # print(row.keys())
            name = row["Source"].text.strip()
            name = re.sub(r"\s*\([^)]*\)", "", name)
            name = re.sub(r"\s*\[[^)]*\]", "", name)
            if name in ["Scriptural texts"]:
                # no URL for those
                continue
            last = row["Last"].text.strip()
            summary = row["Summary"].text.strip()

            labels = [el["href"] for el in row["Status(legend)"].select("a")]
            labels = [el.split("#")[-1] for el in labels]
            raw_row = row["_raw_"]
            css_class = raw_row["class"][0]

            try:
                href = row["Source"].find("a")["href"]
                if href.startswith("http://") or href.startswith("https://"):
                    # absolute URL, to another language
                    details_url = href
                else:
                    # relative URL
                    details_url = f"https://en.wikipedia.org{href}"
                details = requests.get(
                    details_url,
                    headers={
                        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
                    },
                )
                details.raise_for_status()
                soup = BeautifulSoup(details.text, "lxml")
                official_website = soup.select_one("span.official-website a")
                if official_website:
                    url = official_website["href"]
                else:
                    official_website = soup.select_one("table.infobox a.external")
                    if official_website:
                        url = official_website["href"]
                    else:
                        if "WP:" in name:
                            # things like 'Scriptural textsWP:RSPSCRIPTURE\xa0📌'
                            continue
                        url = utils.name_domain_map[name]

            except:
                # https://starsunfolded.com/
                url = utils.name_domain_map[name]

            original = {
                "source": name,
                "source_url": url,
                "labels": labels,
                "css_class": css_class,
                "last": last,
                "summary": summary,
            }
            # print(original)

            domain = utils.get_url_domain(url)
            source = utils.get_url_source(url)

            credibility = {
                "s-gr": {
                    # green row, generally reliable
                    "value": 1.0,
                    "confidence": 1.0,
                },
                "s-nc": {
                    # yellow, no consensus
                    "value": 0.0,
                    "confidence": 1.0,
                },
                "s-gu": {
                    # light red, generally unreliable
                    "value": -0.5,
                    "confidence": 1.0,
                },
                "s-d": {
                    # red, deprecated
                    "value": -1.0,
                    "confidence": 1.0,
                },
                "s-b": {
                    # black, blacklisted
                    "value": -1.0,
                    "confidence": 1.0,
                },
            }.get(css_class, {"value": 0.0, "confidence": 0.0})

            original_label = ", ".join(original["labels"])

            ass = {
                "url": url_list,
                "credibility": credibility,
                "itemReviewed": url,
                "original": original,
                "origin_id": self_id,
                "original_label": original_label,
                "domain": domain,
                "source": source,
                "granularity": "source",
            }
            results.append(ass)
    return results


def _default_credibility(label):
    if label == "fake":
        return {"value": -1.0, "confidence": 1.0}
    elif label == "satire":
        return {"value": 0.0, "confidence": 0.0}


def _get_wikipedia_tables_with_headers(url, exclude=[]):
    # retrieves the wikipedia tables at `url`
    response = requests.get(url, headers={
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
    })
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    tables_el = soup.select("table.wikitable")
    results = []
    for t in tables_el:
        headers, table = _parse_table_into_dict(t, exclude=exclude)
        # print(headers)
        # print(table)
        results.append([headers, table])
    return results


def _parse_table_into_dict(table, exclude=[]):
    results = []
    headers = [el.text.strip() for el in table.find_all("th")]
    # exclude can be used with problematic headers, that misalign the cells (e.g. nested at https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources/Perennial_sources)
    headers = [el for el in headers if el not in exclude]
    for row in table.find_all("tr"):
        if "sortbottom" in row.get("class", []):
            continue
        record = {}
        for cell, h in zip(row.find_all("td"), headers):
            record[h] = cell
        if record.keys():
            record["_raw_"] = row
            results.append(record)
    return headers, results
