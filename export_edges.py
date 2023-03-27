import requests
import csv
import flatten_json


res = requests.get(f"http://localhost:20300/utils/all-edges")
res.raise_for_status()

fields = [
    "url",
    "credibility.value",
    "credibility.confidence",
    "itemReviewed",
    "origin_id",
    "source",
    "domain",
    "granularity",
]

with open("edges.tsv", "w") as f:
    writer = csv.DictWriter(f, fields, delimiter="\t")
    writer.writeheader()
    for e in res.json():
        e = flatten_json.flatten(e, separator=".")
        projected = {k: e.get(k) for k in fields}
        writer.writerow(projected)
