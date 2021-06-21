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
    'WorldTruth.Tv': 'https://worldtruth.tv/',
    '70 News': 'https://70news.wordpress.com/',
    'ABCnews.com.co': 'http://abcnews.com.co/',
    'American News': 'http://americannews.com/',
    'Before It\'s News': 'http://beforeitsnews.com/',
    'bients.com': 'https://bients.com/',
    'bizstandardnews.com': 'http://bizstandardnews.com/',
    'Bloomberg.ma': 'http://bloomberg.ma/',
    'The Boston Tribune': 'http://thebostontribune.com/',
    'Breaking-CNN.com': 'http://breaking-cnn.com/',
    'BVA News': 'http://bvanews.com/',
    'Celebtricity': 'http://www.celebtricity.com/',
    'cnn-trending.com': 'http://cnn-trending.com/',
    'Conservative 101': 'http://conservative101.com/',
    'Conservative Frontline': 'https://conservativefrontline.com/',
    'CountyNewsroom.info': 'http://countynewsroom.info/',
    'Daily Buzz Live': 'http://dailybuzzlive.com/',
    'Daily USA Update': 'http://dailyusaupdate.com/',
    'DC Gazette': 'http://thedcgazette.com/',
    'Denver Guardian': 'http://denverguardian.com/',
    'Disclose TV': 'http://disclose.tv/',
    'DrudgeReport.com.co': 'http://drudgereport.com.co/',
    'Empire Herald': 'http://empireherald.com/',
    'Empire News': 'empirenews.org',
    'Empire Sports': 'http://www.empiresports.co/',
    'Fox-news24.com': 'http://fox-news24.com/',
    'Global Associated News': 'http://www.globalassociatednews.com/',
    'Globalresearch.ca': 'http://globalresearch.ca/',
    'Gossip Mill Mzansi': 'http://gossipmillsa.com/',
    'Guerilla News': 'http://guerilla.news/',
    'Gummy Post': 'http://gummypost.com/',
    'Houston Chronicle TV': 'http://houstonchronicle-tv.com/',
    'Huzlers': 'http://huzlers.com/',
    'ΚΒΟΙ2.comКВОІ2.com': 'http://xn--2-0lbvc0a.com/',
    'KMT 11 News': 'http://kmt11.com/',
    'The Last Line of Defense': 'http://thelastlineofdefence.org/',
    'Liberal Society': 'http://liberalsociety.com/',
    'Liberty Writers News': 'https://libertywriters.com/',
    'LinkBeef': 'http://linkbeef.com/',
    'Naha Daily': 'http://nahadaily.com/',
    'National Insider Politics': 'http://nationalinsiderpolitics.com/',
    'NationalReport.net': 'http://nationalreport.net/',
    'Natural News': 'http://naturalnews.com/',
    'NBCNews.com.co': 'http://nbcnews.com.co/',
    'News Breaks Here': 'http://newsbreakshere.com/',
    'NewsBuzzDaily': 'http://www.newsbuzzdaily.com/',
    'News Examiner': 'http://newsexaminer.net/',
    'News Hound': 'http://news-hound.com/',
    'The News Nerd': 'http://thenewsnerd.com/',
    'NewsPunch': 'http://newspunch.com/',
    'NewsWatch33': 'http://newswatch33.com/',
    'The New York Evening': 'http://thenewyorkevening.com/',
    'Now 8 News': 'http://now8news.com/',
    'The Predicted': 'http://thepredicted.com/',
    'Prntly': 'http://prntly.com/',
    'React 365': 'http://react365.com/',
    'Red Flag News': 'http://redflagnews.com/',
    'The Reporterz': 'http://thereporterz.com/',
    'Snoopack': 'http://snoopack.com/',
    'Spin Zone': 'http://spinzon.com/',
    'St George Gazette': 'http://stgeorgegazette.com/',
    'Stuppid': 'http://stuppid.com/',
    'Super Station 95': 'https://www.superstation95.com/',
    'TrueTrumpers.com': 'http://truetrumpers.com/',
    'UConservative': 'http://www.uconservative.net/',
    'UndergroundNewsReport.com': 'http://undergroundnewsreport.com/',
    'United Media Publishing': 'http://unitedmediapublishing.com/',
    'USA Daily Info': 'http://usadailyinfo.com/',
    'usatoday.com.co': 'http://usatoday.com.co/',
    'US Postman': 'http://uspostman.com/',
    'washingtonpost.com.co': 'http://washingtonpost.com.co/',
    'World Truth TV': 'http://worldtruth.tv/',
    'World News Daily Report': 'http://worldnewsdailyreport.com/',
    'El Koshary Today': 'http://elkoshary.com/',
    'Fognews': 'http://fognews.ru/',
    'Islamica News': 'http://www.islamicanews.com/',
    'Le Journal de Mourréal': 'http://www.journaldemourreal.com',
    'Nordpresse': 'http://www.nordpresse.be/',
    'SatireWire': 'http://www.satirewire.com/',
    'Zaytung': 'http://www.zaytung.com/',
    'Centre for Research on Globalization': 'https://www.globalresearch.ca/',
    'CliffsNotes': 'http://www.cliffsnotes.com/',
    # 'Scriptural texts': ??
    'CNN Video': 'https://edition.cnn.com/videos',
    'The Root': 'https://www.theroot.com/',
    'The Weather Channel': 'https://weather.com/',
    'CBSnews.com.co': 'https://cbsnews.com.co/',
    'GlobalSecurity.org': 'https://www.globalsecurity.org/',
    'Exposition Daily': 'https://expositiondaily.com/',
    'OpIndia': 'https://www.opindia.com/',
    'The Grayzone': 'https://thegrayzone.com/',
    'Next News Network': 'https://www.youtube.com/user/NextNewsNetwork/',
    'Christwire': 'http://christwire.org/',
    'Topeka News': 'https://www.cjonline.com/',
    'The Buffalo Chronicle': 'https://buffalochronicle.com/',
    'OANN (One America News Network)': 'https://www.oann.com/',
    'Postcard News': 'https://postcard.news/',
    'CNN Cable TV News Network': 'https://cnn.com/',
    'Fox News TV Cable Network': 'https://www.foxnews.com/',
    'OAN Network': 'https://www.oann.com/',
    'Law Enforcement Today': 'https://www.lawenforcementtoday.com/',
    'Peerage websites': 'https://thepeerage.com', # royalark.net, thepeerage.com, worldstatesmen.org)
    'StarsUnfolded': 'https://starsunfolded.com/',
    'Walking Eagle News': 'https://walkingeaglenews.com/',
    'News Break': 'https://www.newsbreak.com/',
    'Oneworld.press': 'https://oneworld.press/',
    'Peace Data': 'https://peacedata.net/',
    'Fair Observer': 'https://www.fairobserver.com/',
    'ΚΒΟΙ2.com': 'http://ΚΒΟΙ2.com/',
    'Battery University': 'https://batteryuniversity.com/',
    'Global Times': 'https://www.globaltimes.cn/',
    'Zero Hedge': 'https://www.zerohedge.com/',
    'The California Globe': 'https://californiaglobe.com/',
    'Metal-experience.com': 'https://metal-experience.com/',
    'Our Campaigns': 'https://www.ourcampaigns.com/',
    'Religion News Service': 'https://religionnews.com/',
    'Weather2Travel.com': 'https://www.weather2travel.com/',
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
    else:
        result = '.'.join([ext.domain, ext.suffix])
    if result.startswith('www.'):
            # sometimes the www is there, sometimes not
            result = result[4:]
    return result.lower()

def get_url_source(url):
    """Returns the source of the URL (may be different from domain)"""
    match = re.search(social_regex, url)
    if match:
        result = match.group('res')
        print(url, '-->', result)
        return result
    else:
        return get_url_domain(url, only_tld=False)

def aggregate_source(doc_level, origin_name):
    return aggregate_by(doc_level, origin_name, 'source')

def aggregate_domain(doc_level, origin_name):
    return aggregate_by(doc_level, origin_name, 'domain')

def aggregate_by(doc_level, origin_name, key):
    by_group = defaultdict(list)

    for ass in doc_level:
        by_group[ass[key]].append(ass)

    results = {}

    for k,v in by_group.items():
        credibility_sum = 0.
        confidence_sum = 0.

        # something like {'snopes.com' : {'factcheck_positive_cnt': 3, ...}}}
        cnts_by_factchecker = defaultdict(lambda: defaultdict(list))
        counts = defaultdict(list)
        # TODO convert this to a list of detailed reports (label, which URL was checked, ...)
        reports = []

        assessment_urls = set()
        for el in v:
            credibility_value = el['credibility']['value']
            credibility_confidence = el['credibility']['confidence']
            assessment_urls.add(el['url'])
            credibility_sum += credibility_value * credibility_confidence
            confidence_sum += credibility_confidence
            if origin_name == 'factchecking_report':
                # collect counts of positive, negative, neutral assessments
                reports.append({
                    'report_url': el['url'],
                    'coinform_label': el['coinform_label'],
                    'original_label': el['original_label'],
                    'origin': el['origin']
                })

                # TODO limit the size somehow (same reports about the same item)
                # pymongo.errors.OperationFailure: BSONObj size: 22840637 (0x15C853D) is invalid. Size must be between 0 and 16793600(16MB)
                reports = reports[:500]

            if 'coinform_label' in el:
                label_to_use = 'coinform_label'
            # the mapping for other data, non fact-checks
            label_to_use = 'unknown' if credibility_confidence < 0.4 \
                else 'positive' if credibility_value > 0 \
                    else 'negative' if credibility_value < 0 else 'neutral'
            # TODO just collect counts? nested resource or separate?
            counts[label_to_use].append(el['url'])
            origin_id = el['origin_id']
            # raise ValueError(origin.id)
            # origin_id.replace('.', '_')
            cnts_by_factchecker[origin_id][label_to_use].append(el['url'])
            # add this also inside the object
            cnts_by_factchecker[origin_id]['origin_id'] = origin_id

        if confidence_sum:
            credibility_weighted = credibility_sum / confidence_sum
        else:
            credibility_weighted = 0.0
        if len(v) > 1:
            print(k, 'has', len(v), 'assessments')
            #raise ValueError(k)
        #print(k, len(v), credibility_sum, confidence_sum)

        # see whether there is just one assessment url
        if len(assessment_urls) == 1:
            assessment_url = assessment_urls.pop()
            # TODO should do the same when aggregating on source, keeping the domain
            # TODO: we need to propagate the review URLs and itemReviewed to allow transparency
        else:
            assessment_url = 'http://todo.todo'

        # TODO assign final coinform label from credibility?

        all_counts = cnts_by_factchecker
        cnts_by_factchecker['overall'] = counts

        results[k] = {
            'url': assessment_url,
            'credibility': {
                'value': credibility_weighted,
                'confidence': confidence_sum / len(v)
            },
            'itemReviewed': k,
            'counts': cnts_by_factchecker, # --> RINOMINA campo a "counts" e poi usa reviews/details per metterci roba
            'reports': reports,
            'origin_id': origin_name,
            key: k,
            'granularity': key
        }
    return results.values()