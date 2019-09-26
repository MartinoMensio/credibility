from .. import OriginBase
from ... import persistence

def _cache_wrap_one(func):
    """This decorator takes care of the cache, and is used when there is only one assessment to retrieve"""
    def wrapped(self, *args, **kwargs):
        # TODO check cache if cache allowed
        result = func(self, *args, **kwargs)
        if result:
            persistence.save_assessments(self.id, [result])
        return result
    return wrapped

def _cache_wrap_multiple(func):
    """This decorator takes care of the cache, and is used when there are multiple assessments to retrieve"""
    def wrapped(self, *args, **kwargs):
        # TODO check cache if cache allowed
        results = func(*args, **kwargs)
        if results:
            persistence.save_assessments(self.id, results)
        return results
    return wrapped

class OriginRealtime(OriginBase):

    def __init__(self, id, name, description, homepage, logo, default_weight):
        OriginBase.__init__(
            self,
            id=id,
            name=name,
            description=description,
            homepage=homepage,
            logo=logo,
            origin_type='realtime',
            default_weight=default_weight
        )

    # override this method with proper function to retrieve a domain assessment and interpret it
    def retrieve_domain_credibility(self, domain):
        return None

    # override this method with proper function to retrieve a source assessment and interpret it
    def retrieve_source_credibility(self, domain):
        return None

    # override this method with proper function to retrieve a URL assessment and interpret it
    def retrieve_url_credibility(self, domain):
        return None

    # override this metod to have a faster parallel retrieval
    def retrieve_domain_credibility_multiple(self, domains):
        return {el: self.retrieve_domain_credibility(el) for el in domains if el}

    # override this metod to have a faster parallel retrieval
    def retrieve_source_credibility_multiple(self, domains):
        return {el: self.retrieve_source_credibility(el) for el in domains if el}

    # override this metod to have a faster parallel retrieval
    def retrieve_url_credibility_multiple(self, domains):
        return {el: self.retrieve_url_credibility(el) for el in domains if el}

    @_cache_wrap_one
    def get_domain_credibility(self, domain):
        return self.retrieve_domain_credibility(domain)

    @_cache_wrap_one
    def get_source_credibility(self, source):
        return self.retrieve_source_credibility(source)

    @_cache_wrap_one
    def get_url_credibility(self, url):
        return self.retrieve_source_credibility(url)

    @_cache_wrap_multiple
    def get_domain_credibility_multiple(self, domains):
        return self.retrieve_domain_credibility_multiple(domains)

    @_cache_wrap_multiple
    def get_source_credibility_multiple(self, sources):
        return self.retrieve_source_credibility_multiple(sources)

    @_cache_wrap_multiple
    def get_url_credibility_multiple(self, urls):
        return self.retrieve_source_credibility_multiple(urls)
