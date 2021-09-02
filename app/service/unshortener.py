import os
import json
import multiprocessing
import requests
import time
import tqdm
import signal
import sys
import re
# import urlexpander
import string
from urllib.parse import urlsplit, parse_qsl, quote, unquote, urlencode
from posixpath import normpath

from multiprocessing.pool import ThreadPool
from bs4 import BeautifulSoup


from . import persistence
from . import utils

shortening_domains = [
    # https://bit.do/list-of-url-shorteners.php
    't.co',
    'bit.do',
    'lnkd.in',
    'db.tt',
    'qr.ae',
    'adf.ly',
    'goo.gl',
    'bitly.com',
    'curl.tv',
    'tinyurl.com',
    'ow.ly',
    'bit.ly',
    'ity.im',
    'q.gs',
    'is.gd',
    'po.st',
    'bc.vc',
    'twitthis.com',
    'u.to',
    'j.mp',
    'buzurl.com',
    'cutt.us',
    'u.bb',
    'yourls.org',
    'x.co',
    'prettylinkpro.com',
    'scrnch.me',
    'filoops.info',
    'vzturl.com',
    'qr.net',
    '1url.com',
    'tweez.me',
    'v.gd',
    'tr.im',
    'link.zip.net',
    'tinyarrows.com',
    '➡.ws',
    '/✩.ws',
    'vai.la',
    'go2l.ink',
    'ibit.ly'
]

# these come from the analysis of the database collection
more_shortening_domains = {'cnn.it', 'strw.rs', 'to.pbs.org', 'm.eonline.com' 'nyer.cm', 's.nj.com', 'narrative.ly', 'bloom.bg', 'n.pr', 'soc.li', 'wndw.ms', 'mobro.co', 'datapub.cdlib.org', 'm.bbc.co.uk', 'metrolists.org', 'wap.business-standard.com', 'amzn.com', 'gph.is', 'us13.campaign-archive1.com', 'www.lrbshop.co.uk', 'slate.trib.al', 'stanford.io', 'fb.me', 'usapoliticsnow.com', 'cs.pn', 'rnkpr.com', 'yanisvaroufakis.eu', 'uk.businessinsider.com', 'www.teefury.com', 'cbr.st', 'beta.radiooooo.com', 'arcg.is', 'buff.ly', 'warholize.me', 'bust.li', 'statista.com', 'tlvirtualcafe.wikispaces.com', 'www.police.ufl.edu', 'd.gu.com', 'mymsg.eu', 'gma.yahoo.com', 'nextvista.org', 'waynedupree.com', 'on.nyc.gov', 'open.ac.uk', 'bklynlib.org', 'on.nrdc.org', 'stopfake.org', 'nzzl.us', 'www.cue.org', 'www.whitehouse.gov', 'm.foreignaffairs.com', 'nytimes.com', 'go.unimelb.edu.au', 'telegraph.co.uk', 'doajournals.wordpress.com', 'wp.me', 'ahwd.tv', 'glasgow.ac.uk', 'spr.ly', 'gma.abc', 'spoti.fi', 'prn.to', 'www.tonightshow.com', 'et.tv', 'www.sasconfidential.com', 'g.co', 'www.outofprintclothing.com', 'designschool.canva.com', 'www.nlm.nih.gov', 'hdl.handle.net', 'medium.com', 'ht.ly', 'worldcat.org', 'www.thirdspacelearning.com', 'rol.st', 'www.factcheckni.org', 'www.nationallibrariesday.org.uk', 'rewirenews.link', 'cwrld.us', 'littlerebelsaward.wordpress.com', 'on.nypl.org', 'turkeyonthehill.blogspot.co.uk', 'francisgilbert.co.uk', 'boxlun.ch', 'www.orlandosentinel.com', 'www.newschallenge.org', 'urbn.is', 'librarywriting.blogspot.co.uk', 'realtwitter.com', 'sage-ereference.com', 'ebks.to', 'www.foreignpolicy.com', 'wrld.bg', 'www.myindependentbookshop.co.uk', 'www.open.ac.uk', 'pedagogicalpurposes.blogspot.co.uk', 'commonsensemedia.org', 'chess.com', 'houstonchronicle-tv.com', 'lego.build', 'salatino.org', 'igg.me', 'www.aftertherapturepetcare.com', 'on.natgeo.com', 'www.psmag.com', 'theatln.tc', 'www.learningspy.co.uk', 'fancyapint.com', 'hardsci.wordpress.com', 'www.teachprivacy.com', 'www.newedge.com', 'mobile.bloomberg.com', 'www.medats.org.uk', 'deefinch.wordpress.com', 'jrnl.ie', 'marvel.com', 'go.shr.lc', 'm.imgur.com', 'blogs.cfr.org', 'artsawardvoice.com', 'eepurl.com', 'www.ukauthors.com', 'thenational.scot', 'teachingbooks.net', 'www.parent.com', 'ericbolling.com', 'www.westernjournalism.com', 'hvrd.me', 'huff.to', 'the-fa.com', 's.pennlive.com', 'go.usa.gov', 'battlemaps.us', 'm.vice.com', 'www.unlandmarks.com', 'ted.com', 'glo.msn.com', 'on.inc.com', 'www.ala.org', 'trib.al', 'lsul.su', 'theframeblog.wordpress.com', 'reviews.libraryjournal.com', 'www.ufl.eblib.com', 'www.coolinfographics.com', 'gvwy.io', 'www.fleetingmagazine.com', 'hughrundle.net', 'nydn.us', 's.nola.com', 'magazine.good.is', 'foxtrot.com', 'usaa.us', 'wwwatanabe.blogspot.com.au', 'www.bannedbooksweek.org', 'instagr.am', 'wh.gov', 'newyork.sla.org', 'bzfd.it', 'pottermo.re', 'edwk.it', 'www.savvysugar.com', 'guardian.co.uk', 'superhero.namegeneratorfun.com', 'www.bloombergview.com', 'www.mentalfloss.com', 'interc.pt', 'po.st', 'edcampbr.eventbrite.com', 'patreon.com', 'ncdps.gov', 'www.writerscentrenorwich.org.uk', 'nyti.ms', 'www.nsta.org', 'm.io9.com', 'librarian.net', 'my.jou.ufl.edu', 'wamu.fm', 'razo.io', 'crwd.fr', 't.co', 'bos.gl', 'dailyre.co', 'sie.ag', 'intellihub.com', 'ihenow.com', 'www.goldentwits.com', 'mobile.nytimes.com', 'shrtm.nu', 'dat-data.com', 'econ.st', 'capi.tl', 'cbc.ca', 'www.happyplace.com', 'wrd.cm', 'www.guardian.co.uk', 'bobrosslipsum.com', 'edcampglobal.wixsite.com', 'kck.st', 'wapo.st', 'www.slate.com', 'imdb.me', 'www.flelibrary.org', 'search-proquest-com.lp.hscl.ufl.edu', 'ln.is', 'www.theaustralian.com.au', 'www.rbwm.gov.uk', 'm.wdsu.com', 'reut.rs', 'wired.trib.al', 'pw-ne.ws', 'www.google.com', 'candiangeo.info', 'hackingdls.com', 'washex.am', 'on.epi.org', 'android.com', 'poynter.org', 'lockerhullthornton.com', 'www.ingodwetrust.tv', 'ylgunconference-estw.eventbrite.co.uk', 'fortawesome.github.io', 'chroni.cl', 'blogs.gocomics.com', 'm.ustream.tv', 'rviv.ly', 'social.ji.sc', 'newslab.withgoogle.com', 'simplek12.com', 'www.shakeuplearning.com', 'zoeken.felixarchief.be', 'youtube.com', 'www.digitalspy.co.uk', 'surveycompare.net', 'ebx.sh', 'nym.ag', 'zpr.io', 'gspellchecker.wordpress.com', 'newsy.com', 'econ.trib.al', 'intel.ly', 'nbcnews.to', 'yournewswire.com', 'cta.org', 'www.welovethisbook.com', 'wahlclub.com', 'specialcollections.blog.lib.cam.ac.uk', 'www.cvrhs.com', 'slidesha.re', 'www.eclassroomnews.com', 'www.artintheage.com', 'de.millionshort.com', 'hurricanes.gov', 'is.gd', 'invite.overtone.co', 'snpy.tv', 'edcampbr16.eventbrite.com', 'media.rawvoice.com', 'www.radioopensource.org', 'jwatch.us', 'adweek.it', 'hill.cm', 'retweets.realtwitter.com', 'ny.gov', 'badgelist.com', 'lj.libraryjournal.com', 'mbist.ro', 'cnn.com', 'ready.gov', 'tommy-on-tour-2011.blogspot.co.uk', 'cmore.pics', 'ti.me', 'loc.gov', 'dcgov.github.io', 'anglandicus.blogspot.ie', 'ripl.com', 'di.sn', 'aclj.us', 'oxford.ly', 'www.worldmapper.org', 'disq.us', 'via.wtkr.com', 'docs.google.com', 'thehateugive.com', 'ayame-kenoshi.deviantart.com', 'on.today.com', 'on.apa.org', 'deadsp.in', 'www.supplymanagement.com', 'membership.politifact.com', 'www.theonion.com', 'db.tt', 'www.quillandquire.com', 'executive.nd.edu', 'mightylittlelibrarian.com', 'patthomson.wordpress.com', 'hangouts.google.com', 'raisingreaderssite.wordpress.com', 'arvr.kmi.open.ac.uk', 'librariantiffpresents.wikispaces.com', 'www.geeksugar.com', 'www.siobhandowdtrust.com', 'bit.ly', 'pin.it', 'meetu.ps', 'nyp.st', 'sarahmarshall3.tumblr.com', 'undf.td', 'smore.com', 'scribblestreetnews.blogspot.co.uk', 's-media-cache-ak0.pinimg.com', 'bfpne.ws', 'flip.it', 'tgr.ph', 'www.thestagsheadnyc.com', 'f-st.co', 'wpo.st', 'slate.me', 'fosteropenscience.eu', 'tinyurl.com', 'thr.cm', 'tonyv.me', 'selnd.com', 's2.netgalley.com', 'healthcare.gov', 'cat.lib.unimelb.edu.au', 'on.rt.com', 'www.examiner.com', 'urban.melbourne', 'mktplc.org', 'a.msn.com', 'long.fm', 'p.ink.cx', 'cnet.co', 'ntrda.me', 'overstock.com', 'tmblr.co', 'www.justpeachyy.com', 'owl.english.purdue.edu', 'shout.lt', 'groups.freecycle.org', 'flic.kr', 'onforb.es', 'vote411.org', 'www.jisc-content.ac.uk', 'bn.com', 'doi.org', 'm.macys.com', 'www.stratfor.com', 'go.nasa.gov', 'www.suttonguardian.co.uk', 'www.hum.leiden.edu', 'wxch.nl', 'us11.campaign-archive1.com', 'dictionary.com', 'edut.to', 'semantics.cc', 'pinterest.com', 'read.bi', 'redd.it', 'apple.co', 'paidcontent.org', 'conservativetribune.com', 'thebeautifulnecessity.blogspot.co.uk', 'libraries.pewinternet.org', 'snackwebsites.com', 'apne.ws', 'boston.com', 'ryan-p-randall.github.io', 'ow.ly', 'on.ft.com', 'toi.in', 'bkpg.it', 'got.cr', 'onion.com', 'totallybookalicious.blogspot.co.uk', 'sco.lt', 'ala.org', 'nie.mn', 'www.all4ed.org', 'on.mtv.com', 'bloomberg.com', 'www.ibby.org.uk', 'www.breakingnews.com', 'fallenlondon.storynexus.com', 'earther.com', 'wn.nr', 'gu.com', 'some.ly', 'bitly.com', 'blog.eventbrite.com', 'mefi.us', 'atxne.ws', 'news.discovery.com', 'redditgifts.com', 'www.eurasianet.org', 'www.hotmomsclub.com', 'j.mp', 'sibylline.tictail.com', 'lvrj.com', 'minifigures.lego.com', 'dlvr.it', 'tcrn.ch', 'media.bookbub.com', 'abcn.ws', 'bit.do', 'flalib.org', 'www.getbadnews.com', 'd.shpg.org', 'sciencealert.com.au', 'p.ctx.ly', 'sb.stratbz.to', 'careers.timewarner.com', 'literatureforlads.com', 'cbs.com', 'headguruteacher.com', 'www.paulsimon.co.uk', 'www.inspirationgreen.com', 'www.pbs.org', 'whiteboomerang.com', 'poy.nu', 'mgafrica.com', 'mrstrefusis.blogspot.co.uk', 'shr.gs', 'dld.bz', 'startpage.com', 'etsy.me', 'tech.mg', 'm.beforeitsnews.com', 'www.worldbooknight.org', 'www.thriveglobal.com', 'edtru.st', 'battleforthenet.com', 'businesslibrary.uflib.ufl.edu', 'www.leave.eu', 'cnb.cx', 'pens.pe', 'next.srds.com', 'jonmayhem.blogspot.co.uk', 'politifact.com', 'powersource.post-gazette.com', 'cjr.bz', 'on.mash.to', 'guides.uflib.ufl.edu', 'owl.li', 'smithmag.co', 'feedproxy.google.com', 'narnia.com', 'edcampvoice.com', 'www.buzzfeed.com', 'fw.to', 'www.sagepub.com', 'www.scvo.org.uk', 'jstor.info', 'wrld.at', 'nationalcollective.com', 'libcampldn.wikispaces.com', 'thedo.do', 'trendsmap.com', 'm.burnleyexpress.net', 'www.thebookoflife.org', 'i100.io', 'soa.li', 'www.markthomasinfo.co.uk', 'drudge.tw', 'edcampbr17.eventbrite.com', 'ufl.kanopystreaming.com', '53eig.ht', 'adf.ly', 'skills.oecd.org', 'shar.es', 'studenthublive.kmi.open.ac.uk', 's.si.edu', 'wesa.fm', 'conta.cc', 'usatoday.com', 'mooc-list.com', 'deck.ly', 'smarturl.it', 'virl.io', 'usfreedomarmy.com', 's.silive.com', 'www.unisoncambridgeshire.org.uk', 'm.us.wsj.com', 'tomcoxblog.blogspot.co.uk', 'en.itar-tass.com', 'www.pghtechfest.com', 'fxn.ws', 'on.fb.me', 'healthyforgood.heart.org', 'twb.ly', 'sbnation.com', 'wsj.com', 'fannycornforth.blogspot.co.uk', 'met.org', 'politi.co', 'chng.it', 'vult.re', 'elisoriano.com', 'datasciencechallenge.org', 'www.wellcome.ac.uk', 'huffp.st', 'on.learn4startup.com', 'www.centerdigitaled.com', 'buswk.co', '40.media.tumblr.com', 'blogs.forbes.com', 'blogs.law.harvard.edu', 'cfp.cc', 'hub.am', 'mksmart.org', 'windows.microsoft.com', 'ifla.news', 'chronicle.com', 'pages.bloomsbury.com', 'flelibrary.org', 'english.eu2016.nl', 'mailchi.mp', 'youtu.be', 'cbsn.ws', 'dailym.ai', 'lifeartcollide.blogspot.ca', 'engt.co', 'thedaringlibrarianpresents.wikispaces.com', 'screencast.com', 'boston25.com', 'izvestia.ru', 'dailysignal.com', 'www.ppehlab.org', 'cyberoptixtielab.myshopify.com', 'awe.sm', 'yhoo.it', 'scim.ag', 'pythonanywhere.com', 'feedly.com', 'oe.cd', 'lapl.me', 'chinahistorypodcast.com', 'thkpr.gs', 'jobsatturner.com', 'shortyw.in', 'www.webenglishteacher.com', 'localworks.org', 'gop.cm', 'opentrees.org', 'www.tinyurl.com', '1890swriters.blogspot.ca', 'plurk.com', 'wbur.fm', 'pwne.ws', 'thetim.es', 'investinlibraries.org', 'bbc.in', 'www.utsandiego.com', 'unwo.men', 'www.attn.com', 'www.learnnc.org', 'abcnews.com', 'www.perey.com', 'firstdraftnews.com', 'www.flavorwire.com', 'www.eudebateni.org', 'ubm.io', 'skrashen.blogspot.hk', 'thesco.re', 'mnky.in', 'lat.ms', 'on.freep.com', 'www.speakupforlibraries.org', 'www.blackmarket14.eventbrite.co.uk', 'patabot.etsy.com', 'www.lithuaniatribune.com', 'www.nisra.gov.uk', 'elitedaily.com', 'www.aah.org.uk', 'topinfopost.com', 'thebea.st', 'on.khou.com', 'goodreads.com', 'usat.ly', 'www.allout.org', 'www.roalddahlday.info', 'alturl.com', 'shortlist.com', 'www.newrepublic.com', 'goo.gl', 'www.sontagfilm.org', 's.hbr.org', 'on.msnbc.com', 'rdcrss.org', 'eckleburg.org', 'brook.gs', 'm.bbc.com', 'www.literacytrust.org.uk', 'detne.ws', 'go.nature.com', 'nyr.kr', 'essencecom.io', 'ladygeek.com', 'amzn.to', 'amn.st', 'ind.pn', 'roadtrippers.com', 'dx.doi.org', 'www.timeshighereducation.co.uk', 'www.patheos.com', 'paper.li', 'smym.in', 'pure.strath.ac.uk', 'canada.ca', 'www.daedtech.com', 'www.studentbodyuf.com', 'greatparchmentbook.org', 'news360.com', 'tak.pt', 'www.princeton.edu', 'www.tes.co.uk', 'www2.lse.ac.uk', 'tnvge.co', 'us9.campaign-archive1.com', 'tnspk.co', 'on.wsj.com', 'popwatch.ew.com', 'www.adelaidenow.com.au', 'www.rosscoops31.com', 'click.linksynergy.com', 'lnkd.in', 'news.indiana.edu', 'ift.tt', 'spatialsource.com.au', 'm.youtube.com', '45.wh.gov', 'www.caineprize.com', 'www.awesomelibrarians.com', 'bonap.it', 'speedtest.net', 'tern.org.au', 'wef.ch', 'www.publications.parliament.uk', 'digitalnewsreport.org', 'dagmagasinet.com', 'www.foresthillschool.co.uk', 'academia.edu', 'aaihs.org', 'gainesville.com', 'chn.ge', 'downloads.bbc.co.uk', 'www.libraryfreedomproject.org', 'theadventurezonecomic.com', 'www.uflib.ufl.edu', 'www.harpersbazaar.co.uk', 'www.fastcoexist.com', 'rauviel.etsy.com', 't.ted.com', 'votelibraries.nationbuilder.com', 'pewrsr.ch', 'demsoc.org', 'magic.piktochart.com', 'diamondandsilk.com'}

shortening_domains.extend(more_shortening_domains)

# def unshorten_broken(url, referer=None, cookies=None):
#     domain = utils.get_url_domain(url)
#     print(url)
#     if domain in shortening_domains:
#         #cached = database.get_url_redirect(url)
#         #if not cached:"""
#         headers = headers = {
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#             'Accept-Encoding': 'gzip, deflate',
#             'Accept-Language': 'en-GB,en;q=0.9,it-IT;q=0.8,it;q=0.7,en-US;q=0.6',
#             'User-Agent': 'Google Chrome Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
#         }
#         if referer:
#             headers['Referer'] = referer
#         response = requests.head(url, headers=headers)
#         location = response.headers.get('location', None)
#         if not location:
#             print(response.headers)
#             print(cookies)
#             # try again with cookies
#             return unshorten_broken(url, referer=url, cookies=response.cookies)
#         print(response.url, location)
#         return unshorten_broken(location, referer=url)
#     #database.save_url_redirect(url, url)
#     return url

def unshorten(url, use_cache=True):
    """If use_cache is False, does not use the cache"""
    if use_cache:
        cached = persistence.get_url_redirect(url)
    else:
        cached = False
    if cached:
        # match found
        result = cached['to']
    else:
        # not found
        domain = utils.get_url_domain(url)
        result = utils.add_protocol(url)
        result = url_normalize(result)
        # print('url_normalize result', result)
        if domain in shortening_domains:
            try:
                res = requests.head(result, allow_redirects=True, timeout=2)
                result = res.url
            except requests.exceptions.Timeout as e:
                # website dead, return the last one
                result = e.request.url
            except requests.exceptions.InvalidSchema as e:
                # something like a ftp link that is not supported by requests
                error_str = str(e)
                found_url = re.sub("No connection adapters were found for '([^']*)'", r'\1', error_str)
                result = found_url
            except requests.exceptions.RequestException as e:
                # other exceptions such as SSLError, ConnectionError, TooManyRedirects
                if e.request and e.request.url:
                    result = e.request.url
                else:
                    # something is really wrong
                    print(e)
            except Exception as e:
                # something like http://ow.ly/yuFE8 that points to .
                print('error for',url)
            # re-normalise
            result = url_normalize(result)
            if use_cache:
                # save in the cache for next calls
                persistence.save_url_redirect(url, result)
    return result


resolver_url = 'https://unshorten.me/'
# class UnshortenerRemote(object):
#     """This unshortener is based on the https://unshorten.me/ website.
#     Therefore it's deadly slow. Better to use the local unshortener"""
#     def __init__(self):
#         self.session = requests.Session()
#         res_text = self.session.get(resolver_url).text
#         soup = BeautifulSoup(res_text, 'html.parser')
#         csrf = soup.select('input[name="csrfmiddlewaretoken"]')[0]['value']
#         #print(csrf)
#         self.csrf = csrf

#     def unshorten(self, url, handle_error=True):
#         domain = utils.get_url_domain(url)
#         if domain in shortening_domains:
#             cached = database.get_url_redirect(url)
#             if not cached:
#                 res_text = self.session.post(resolver_url, headers={'Referer': resolver_url}, data={'csrfmiddlewaretoken': self.csrf, 'url': url}).text
#                 soup = BeautifulSoup(res_text, 'html.parser')
#                 try:
#                     source_url = soup.select('section[id="features"] h3 code')[0].get_text()
#                 except:
#                     #print('ERROR for', url)
#                     if handle_error:
#                         source_url = url
#                     else:
#                         source_url = None
#                 m = (url, source_url)
#                 #print('unshortened', url, source_url)
#                 #print(m)
#                 #self.mappings[m[0]] = m[1]
#                 database.save_url_redirect(url, source_url)
#             else:
#                 source_url = cached['to']
#         else:
#             # not doing it!
#             source_url = url
#         return source_url

def func(url):
    #url, uns = params
    res = unshorten(url, use_cache=False)
    #print(res)
    return (url, res)


def unshorten_multiprocess(url_list, pool_size=20):
    """Returns a dict, with one (url: resolved) for each url in url_list"""
    # remove duplicates
    url_list = list(set(url_list))
    # check the cache all together
    redirects_found = persistence.get_url_redirects_in(url_list)
    results = {}
    for match in redirects_found:
        results[match['_id']] = match['to']
    url_not_found = list(set(url_list) - set(results.keys()))

    print('unshortening', len(url_not_found))

    # rs = urlexpander.expand(url_not_found, n_workers=pool_size, filter_function=urlexpander.is_short, verbose=1)
    # for r, u in zip(rs, url_not_found):
    #     results[u] = r
    # return results


    # old, difficult to kill
    with ThreadPool(pool_size) as pool:
        # one-to-one with the url_list
        for one_result in tqdm.tqdm(pool.imap_unordered(func, url_not_found), total=len(url_not_found)):
            url, resolved = one_result
            results[url] = resolved
            # save here, in the main process
            persistence.save_url_redirect(url, resolved)
    print('unshortened')
    return results


# inspired from https://github.com/tg123/tao.bb/blob/master/url_normalize.py
SAFE_CHARS = ''.join([c for c in (string.digits + string.ascii_letters + string.punctuation) if c not in '%#'])
VALID_DOMAIN = re.compile('^[a-zA-Z\d-]{1,63}(\.[a-zA-Z\d-]{1,63})*$')

def escape(unescaped_str):
    unquoted = unquote(unescaped_str)
    while unquoted != unescaped_str:
        unescaped_str = unquoted
        unquoted = unquote(unquoted)
    return quote(unquoted, SAFE_CHARS)

def url_normalize(url):
    # print('url normalize called', url)
    url = url.replace('\t', '').replace('\r', '').replace('\n', '')
    url = url.strip()
    testurl = urlsplit(url)
    if testurl.scheme == '':
        url = urlsplit('http://' + url)
    elif testurl.scheme in ['http', 'https']:
        url = testurl
    else:
        return None

    scheme = url.scheme

    if url.netloc:
        try:
            hostname = url.hostname.rstrip(':')

            port = None
            try:
                port = url.port
            except ValueError:
                pass

            username = url.username
            password = url.password

            hostname = [part for part in hostname.split('.') if part]

            # # convert long ipv4
            # # here will fail domains like localhost
            # if len(hostname) < 2:
            #     hostname = [socket.inet_ntoa(struct.pack('!L', long(hostname[0])))]

            hostname = '.'.join(hostname)
            # hostname = hostname.decode('utf-8').encode('idna').lower()

            if not VALID_DOMAIN.match(hostname):
                return None

        except:
            return None


        netloc = hostname
        if username:
            netloc = '@' + netloc    
            if password:
                netloc = ':' + password + netloc
            netloc = username + netloc

        if port:
            if scheme == 'http':
                port = '' if port == 80 else port
            elif scheme == 'https':
                port = '' if port == 443 else port

            if port:
                netloc += ':' + str(port)
        
        path = netloc + normpath('/' + url.path + '/').replace('//', '/')
    else:
        return None


    query = parse_qsl(url.query, True)
    query = dict(query)
    # ignore tracking stuff
    query = {k:v for k,v in query.items() if k not in ['fbclid', 'mc_cid', 'mc_eid', 'refresh_count', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']}
    query = sorted(query.items())
    query = urlencode(query)

    fragment = url.fragment

    return (('%s://%s?%s#%s' % (scheme, escape(path), query, escape(fragment))).rstrip('?#/ '))


if __name__ == "__main__":
    # with open('data/aggregated_urls.json') as f:
    #     data = json.load(f)
    # urls = data.keys()
    # unshorten_multiprocess(urls)
    unshorten('http://bit.ly/rR1us')
