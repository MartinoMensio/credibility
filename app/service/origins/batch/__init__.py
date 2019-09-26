from .. import OriginBase
from ... import persistence, utils


class OriginBatch(OriginBase):
    def __init__(self, id, name, description, homepage, logo, default_weight):
        OriginBase.__init__(
            self,
            id=id,
            name=name,
            description=description,
            homepage=homepage,
            logo=logo,
            origin_type='batch',
            default_weight=default_weight
        )

    def update(self):
        assessments_urls = self.retreive_urls_assessments()
        assessments_sources = self.retreive_source_assessments()
        assessments_domains = self.retreive_domain_assessments()

        # now let's combine together at coarser granularity
        assessments_urls_aggregated_by_source = utils.aggregate_source(
            assessments_urls, self.id)
        assessments_urls_aggregated_by_domain = utils.aggregate_domain(
            assessments_urls, self.id)
        assessments_sources_aggregated_by_domain = utils.aggregate_domain(
            assessments_sources, self.id)

        counts = {
            'native_urls': len(assessments_urls),
            'native_source': len(assessments_sources),
            'native_domains': len(assessments_domains),
            'urls_by_source': len(assessments_urls_aggregated_by_source),
            'urls_by_domain': len(assessments_urls_aggregated_by_domain),
            'sources_by_domain': len(assessments_sources_aggregated_by_domain),
        }

        print(f'batch update report for {self.id}:', counts)

        all_assessments = list(assessments_urls) + \
            list(assessments_sources) + \
            list(assessments_domains) + \
            list(assessments_urls_aggregated_by_source) + \
            list(assessments_urls_aggregated_by_domain) + \
            list(assessments_sources_aggregated_by_domain)

        if not all_assessments:
            raise ValueError(f'no assessments for {self.id}')

        persistence.save_assessments(self.id, all_assessments, drop=True)
        return counts

    # override this method if the origin provides domain assessments

    def retreive_domain_assessments(self):
        return []

    # override this method if the origin provides source assessments
    def retreive_source_assessments(self):
        return []

    # override this method if the origin provides urls assessments
    def retreive_urls_assessments(self):
        return []
