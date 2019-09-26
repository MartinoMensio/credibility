from typing import List
from .. import persistence


class OriginBase(object):
    id: str
    name: str
    description: str
    homepage: str
    logo: str
    origin_type: str  # batch or realtime
    default_weight: float

    def __init__(self, id: str, name: str, description: str, homepage: str, logo: str, origin_type: str, default_weight: float):
        self.id = id
        self.name = name
        self.description = description
        self.homepage = homepage
        self.logo = logo
        self.origin_type = origin_type
        self.default_weight = default_weight

    def get_source_credibility(self, source: str):
        return persistence.get_source_assessment(self.id, source)

    def get_domain_credibility(self, domain: str):
        return persistence.get_domain_assessment(self.id, domain)

    def get_url_credibility(self, url: str):
        return persistence.get_url_assessment(self.id, url)

    def get_source_credibility_multiple(self, sources: List[str]):
        return persistence.get_source_assessment_multiple(self.id, sources)

    def get_domain_credibility_multiple(self, domains: List[str]):
        return persistence.get_domain_assessment_multiple(self.id, domains)

    def get_url_credibility_multiple(self, urls: List[str]):
        return persistence.get_url_assessment_multiple(self.id, urls)

    def update(self):
        # is overridden by batch origins
        pass

    def _save_assessment(self, assessments: list):
        return persistence.save_assessments(self.id, assessments)


# TODO HERE ADD THE START NODE
