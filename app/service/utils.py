import tldextract

# some mapping between news outlet name and homepage,
# this is useful for some origins that reference outlets by name
name_domain_map = {
    'ABC News': 'https://abcnews.go.com/',
    'Associated Press': 'https://www.ap.org/',
    'Atlanta Journal-Constitution': 'https://www.ajc.com/',
    'Bloomberg': 'https://www.bloomberg.com/',
    'Boston Globe': 'https://www.bostonglobe.com/',
    'BuzzFeed': 'https://www.buzzfeednews.com/',
    'CBS News': 'https://www.cbs.com/',
    'Chicago Tribune': 'http://www.chicagotribune.com/',
    'Christian Science Monitor': 'https://www.csmonitor.com/',
    'CNN': 'https://edition.cnn.com/',
    'Daily Beast': 'https://www.thedailybeast.com/',
    'Dallas Morning News': 'https://www.dallasnews.com/',
    'Denver Post': 'https://www.denverpost.com/',
    'Detroit Free Press': 'https://www.freep.com/',
    'East Bay Times': 'https://www.eastbaytimes.com/',
    'Fox News': 'https://www.foxnews.com/',
    'Guardian': 'https://www.theguardian.com/',
    'Hearst Television': 'http://www.hearst.com/',
    'Heavy.com': 'https://heavy.com/',
    'HuffPost': 'https://www.huffingtonpost.com/',
    'Independent Journal Review': 'https://ijr.com/',
    'Kansas City Star': 'https://www.kansascity.com/',
    'Los Angeles Times': 'https://www.latimes.com/',
    'Miami Herald': 'http://www.miamiherald.com/',
    'Minneapolis Star Tribune': 'http://www.startribune.com/',
    'Mother Jones': 'https://www.motherjones.com/',
    'NBC News': 'https://www.nbcnews.com/',
    'New York Post': 'https://nypost.com/',
    'New York Times': 'https://www.nytimes.com/',
    'Newsweek': 'https://www.newsweek.com/',
    'NPR': 'https://www.npr.org/',
    'Orange County Register': 'https://www.ocregister.com/',
    'Oregonian': 'https://www.oregonianmediagroup.com/',
    'PBS': 'https://www.pbs.org/',
    'Politico': 'https://www.politico.com/',
    'ProPublica': 'https://www.propublica.org/',
    'Reuters': 'https://www.reuters.com/',
    'Reveal': 'https://www.revealnews.org/',
    'Seattle Times': 'https://www.seattletimes.com/',
    'Slate': 'https://slate.com/',
    'The Atlantic': 'https://www.theatlantic.com/',
    'Atlantic': 'https://www.theatlantic.com/',
    'The Economist': 'https://www.economist.com/',
    'Economist': 'https://www.economist.com/',
    'The Hill': 'https://thehill.com/',
    'Hill': 'https://thehill.com/',
    'The Mercury News': 'https://www.mercurynews.com/',
    'Mercury News': 'https://www.mercurynews.com/',
    'Time': 'http://time.com/',
    'USA Today': 'https://www.usatoday.com/',
    'VICE News': 'https://www.vice.com/',
    'Voice of Orange County': 'https://voiceofoc.org/',
    'Wall Street Journal': 'https://www.wsj.com/',
    'Washington Post': 'https://www.washingtonpost.com/',
    'Washington Times': 'https://www.washingtontimes.com/',
    'Wisconsin Watch': 'https://www.wisconsinwatch.org/'
}

def get_url_domain(url, only_tld=True):
    """Returns the domain of the URL"""
    if not url:
        return ''
    ext = tldextract.extract(url)
    if not only_tld:
        result = '.'.join(part for part in ext if part)
        if result.startswith('www.'):
            # sometimes the www is there, sometimes not
            result = result[4:]
    else:
        result = '.'.join([ext.domain, ext.suffix])
    return result.lower()