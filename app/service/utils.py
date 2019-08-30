import tldextract
import re
from collections import defaultdict

# some mapping between news outlet name and homepage,
# this is useful for some origins that reference outlets by name
name_domain_map = {
    'ABC News': 'https://abcnews.go.com/',
    'ABC': 'https://abcnews.go.com/',
    'Associated Press': 'https://www.ap.org/',
    'Atlanta Journal-Constitution': 'https://www.ajc.com/',
    'Bloomberg': 'https://www.bloomberg.com/',
    'Boston Globe': 'https://www.bostonglobe.com/',
    'BuzzFeed': 'https://www.buzzfeednews.com/',\
    'BuzzFeed News': 'https://www.buzzfeednews.com/',
    'CBS News': 'https://www.cbs.com/',
    'CBS': 'https://www.cbs.com/',
    'Chicago Tribune': 'http://www.chicagotribune.com/',
    'Christian Science Monitor': 'https://www.csmonitor.com/',
    'CNN': 'https://edition.cnn.com/',
    'Daily Beast': 'https://www.thedailybeast.com/',
    'Dallas Morning News': 'https://www.dallasnews.com/',
    'Denver Post': 'https://www.denverpost.com/',
    'Detroit Free Press': 'https://www.freep.com/',
    'East Bay Times': 'https://www.eastbaytimes.com/',
    'Fox News': 'https://www.foxnews.com/',
    'Fox': 'https://www.foxnews.com/',
    'Guardian': 'https://www.theguardian.com/',
    'The Guardian': 'https://www.theguardian.com/',
    'Hearst Television': 'http://www.hearst.com/',
    'Heavy.com': 'https://heavy.com/',
    'HuffPost': 'https://www.huffingtonpost.com/',
    'Independent Journal Review': 'https://ijr.com/',
    'IJR': 'https://ijr.com/',
    'Kansas City Star': 'https://www.kansascity.com/',
    'Los Angeles Times': 'https://www.latimes.com/',
    'LA Times': 'https://www.latimes.com/',
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
    'Vice': 'https://www.vice.com/',
    'Voice of Orange County': 'https://voiceofoc.org/',
    'Wall Street Journal': 'https://www.wsj.com/',
    'Washington Post': 'https://www.washingtonpost.com/',
    'Washington Times': 'https://www.washingtontimes.com/',
    'Wisconsin Watch': 'https://www.wisconsinwatch.org/',
    'AFP': 'https://www.afp.com/',
    'Al Jazeera US/Canada News': 'https://www.aljazeera.com/topics/regions/us-canada.html',
    'Alternet': 'https://www.alternet.org/',
    'AP': 'https://www.apnews.com/',
    'Axios': 'https://www.axios.com/',
    'BBC': 'https://www.bbc.co.uk/',
    'Bipartisan Report': 'https://bipartisanreport.com/',
    'Breitbart': 'https://www.breitbart.com/',
    'Business Insider': 'https://www.businessinsider.com/',
    'Conservative Tribune': 'https://www.westernjournal.com/ct/',
    'CSPAN': 'https://www.c-span.org/',
    'Daily Caller': 'https://dailycaller.com/',
    'Daily Kos': 'https://www.dailykos.com/',
    'Daily Mail': 'https://www.dailymail.co.uk/',
    'Daily Signal': 'https://www.dailysignal.com/',
    'Daily Wire': 'https://www.dailywire.com/',
    'David Wolfe': 'https://www.davidwolfe.com/',
    'Democracy Now': 'https://www.democracynow.org/',
    'Drudge Report': 'https://www.drudgereport.com/',
    'Financial Times': 'https://www.ft.com/',
    'Fiscal Times': 'https://www.thefiscaltimes.com/',
    'Forbes': 'https://www.forbes.com/',
    'Foreign Policy': 'https://foreignpolicy.com/',
    'Fortune': 'http://fortune.com/',
    'Forward Progressives': 'http://www.forwardprogressives.com/',
    'FreeSpeech TV': 'https://freespeech.org/',
    'Guacamoley': 'https://guacamoley.com/',
    'Huffington Post': 'https://www.huffpost.com/',
    'InfoWars': 'https://www.infowars.com/',
    'Intercept': 'https://theintercept.com/',
    'Jacobin': 'https://jacobinmag.com/',
    'Marketwatch': 'https://www.marketwatch.com/',
    'Mic': 'https://www.mic.com/',
    'MSNBC': 'https://www.msnbc.com/',
    'National Enquirer': 'https://www.nationalenquirer.com/',
    'National Review': 'https://www.nationalreview.com/',
    'NBC': 'https://www.nbc.com/',
    'New Republic': 'https://newrepublic.com/',
    'News and Guts': 'https://www.newsandguts.com/',
    'NewsMax': 'https://www.newsmax.com/',
    'OAN': 'https://www.oann.com/',
    'Occupy Democrats': 'http://occupydemocrats.com/',
    'OZY': 'https://www.ozy.com/',
    'Palmer Report': 'https://www.palmerreport.com/',
    'Patribotics': 'https://patribotics.blog/',
    'PJ Media': 'https://pjmedia.com/',
    'Quartz': 'https://qz.com/',
    'Reason': 'https://reason.com/',
    'RedState': 'https://www.redstate.com/',
    'Second Nexus': 'https://secondnexus.com/',
    'ShareBlue': 'https://shareblue.com/',
    'Talking Points Memo': 'https://talkingpointsmemo.com/',
    'The Advocate': 'https://www.advocate.com/',
    'The American Conservative': 'https://www.theamericanconservative.com/',
    'The Blaze': 'https://www.theblaze.com/',
    'The Federalist': 'https://thefederalist.com/',
    'The Gateway Pundit': 'https://www.thegatewaypundit.com/',
    'The Nation': 'https://www.thenation.com/',
    'The New Yorker': 'https://www.newyorker.com/',
    'The Skimm': 'https://theskimm.com/',
    'The Week': 'https://theweek.com/',
    'The Weekly Standard': 'https://www.weeklystandard.com/',
    'The Young Turks': 'https://tyt.com/',
    'Think Progress': 'https://thinkprogress.org/',
    'Truthout': 'https://truthout.org/',
    'Twitchy': 'https://twitchy.com/',
    'Vanity Fair': 'https://www.vanityfair.com/',
    'Vox': 'https://www.vox.com/',
    'Washington Examiner': 'https://www.washingtonexaminer.com/',
    'Washington Free Beacon': 'https://freebeacon.com/',
    'Washington Monthly': 'https://washingtonmonthly.com/',
    'WND': 'https://www.wnd.com/',
    'Wonkette': 'https://www.wonkette.com/',
    'WorldTruth.Tv': 'https://worldtruth.tv/'
}

# this regex works for facebook and twitter and extracts the source as account name
# TODO for youtube extract the channel name as in the second answer here https://stackoverflow.com/questions/17806944/how-to-get-youtube-channel-name
social_regex = r'^(https?:\/\/)?([a-z-]+\.)*(?P<res>(facebook\.com|facebook\.com\/pages|twitter\.com|youtube\.com)\/([A-Za-z0-9_.]*))(\/.*)?'

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

def get_url_source(url, only_tld=True):
    """Returns the source of the URL (may be different from domain)"""
    match = re.search(social_regex, url)
    if match:
        result = match.group('res')
        print(url, '-->', result)
        return result
    else:
        return get_url_domain(url)

def aggregate_source(doc_level, origin_name):
    return aggregate_by(doc_level, origin_name, 'source')

def aggregate_domain(doc_level, origin_name):
    return aggregate_by(doc_level, origin_name, 'domain')

def aggregate_by(doc_level, origin_name, key):
    by_source = defaultdict(list)

    for ass in doc_level:
        by_source[ass[key]].append(ass)

    results = {}

    for k,v in by_source.items():
        credibility_sum = 0.
        confidence_sum = 0.
        for el in v:
            credibility = el['credibility']['value']
            confidence = el['credibility']['confidence']
            credibility_sum += credibility * confidence
            confidence_sum += confidence
        if confidence_sum:
            credibility_weighted = credibility_sum / confidence_sum
        else:
            credibility_weighted = 0.0
        if len(v) > 1:
            print(k, 'has', len(v), 'assessments')
            #raise ValueError(k)
        #print(k, len(v), credibility_sum, confidence_sum)
        results[k] = {
            'url': 'http://todo.todo',
            'credibility': {
                'value': credibility_weighted,
                'confidence': confidence_sum / len(v)
            },
            'itemReviewed': k,
            'original': {'assessments': v},
            'origin': origin_name,
            'domain': k,
            'granularity': 'source'
        }
    return results.values()