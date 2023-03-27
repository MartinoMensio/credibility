import os
import tldextract
import re
from collections import defaultdict

from . import unshortener

# some mapping between news outlet name and homepage,
# this is useful for some origins that reference outlets by name
name_domain_map = {
    "#MediaBuzz": "https://www.foxnews.com/shows/media-buzz",
    "60 Minutes": "https://www.cbs.com/shows/60_minutes/",
    "@ Night with Shannon Bream": "https://www.foxnews.com/shows/fox-news-night",
    "ABC": "https://abcnews.go.com/",
    "ABC News": "https://abcnews.go.com/",
    "ABC This Week with George Stephanopoulos": "https://abcnews.go.com/ThisWeek",
    "ABC World News Tonight with David Muir": "https://abc.com/shows/world-news-tonight",
    "Abe Lincoln’s Top Hat": "https://www.lastpodcastnetwork.com/abe-lincolns-top-hat",
    "Alex Witt Reports": "https://www.msnbc.com/weekends-with-alex",
    "All In with Chris Hayes": "https://www.msnbc.com/all",
    "Amanpour": "https://edition.cnn.com/shows/amanpour",
    "America Dissected": "https://crooked.com/podcast-series/america-dissected/",
    "America First with Sebastian Gorka Podcast": "https://salemnewschannel.com/host/sebastian-gorka/",
    "America Right Now": "https://www.newsmaxtv.com/Shows/America-Right-Now",
    "American Greatness": "https://amgreatness.com/",
    "American Voices with Alicia Menendez": "https://www.msnbc.com/american-voices-alicia-menendez",
    "Amicus with Dahlia Lithwick": "https://slate.com/podcasts/amicus",
    "Anderson Cooper 360": "https://edition.cnn.com/shows/ac-360",
    "Andrea Mitchell Reports": "https://www.msnbc.com/andrea-mitchell",
    "Apple News Today": "https://www.apple.com/apple-news/",
    "Armchair Expert with Dax Shepard": "https://armchairexpertpod.com/",
    "Associated Press": "https://www.ap.org/",
    "At this Hour with Kate Bolduan": "https://edition.cnn.com/shows/at-this-hour",
    "Atlanta Journal-Constitution": "https://www.ajc.com/",
    "Axios Re:Cap": "https://www.axios.com/podcasts/recap",
    "Ayman": "https://www.msnbc.com/ayman-mohyeldin",
    "Bannon’s War Room": "https://warroom.org/",
    "Banfield": "https://www.newsnationnow.com/banfield/",
    "Bad Faith": "https://badfaith.libsyn.com/",
    "BBC World News America": "https://www.bbc.co.uk/programmes/n13xtmgh",
    "Bloomberg": "https://www.bloomberg.com/",
    "Boom Bust": "https://www.rt.com/shows/boom-bust/",
    "Boston Globe": "https://www.bostonglobe.com/",
    "Brian Kilmeade Show": "https://radio.foxnews.com/fox-news-talk/brian-kilmeade/",
    "BuzzFeed": "https://www.buzzfeednews.com/",
    "BuzzFeed News": "https://www.buzzfeednews.com/",
    "Candace Owens": "https://candaceowens.com/",
    "Cape Up with Jonathan Capehart": "https://www.washingtonpost.com/podcasts/capehart/",
    "Cavuto Live": "https://www.foxnews.com/shows/cavuto-live",
    "Cavuto: Coast to Coast": "https://www.foxbusiness.com/shows/cavuto-coast-to-coast",
    "CBS": "https://www.cbs.com/",
    "CBS Evening News with Norah O’Donnell": "https://www.cbs.com/shows/cbs_evening_news/",
    "CBS Morning News": "https://www.cbsnews.com/cbs-mornings/",
    "CBS News": "https://www.cbs.com/",
    "CBS Sunday Morning": "https://www.cbsnews.com/sunday-morning/",
    "Chapo Trap House": "https://www.chapotraphouse.com/",
    "Chicago Tribune": "http://www.chicagotribune.com/",
    "Chicks on the Right Podcast": "https://www.spreaker.com/show/mock-and-daisys-common-sense-cast",
    "Christian Science Monitor": "https://www.csmonitor.com/",
    "CNN": "https://edition.cnn.com/",
    "CNN 5 Things": "https://edition.cnn.com/audio/podcasts/5-things",
    "CNN Newsroom with Jim Acosta": "https://edition.cnn.com/profiles/jim-acosta-profile",
    "Code Switch": "https://www.npr.org/sections/codeswitch/",
    "Consider This from NPR": "https://www.npr.org/podcasts/510355/considerthis",
    "CrossTalk": "https://rt.com/shows/crosstalk/",
    "Cuomo": "https://www.newsnationnow.com/cuomo-show/",
    "Cuomo Prime Time": "https://edition.cnn.com/audio/podcasts/cuomo-prime-time",
    "Daily Beast": "https://www.thedailybeast.com/",
    "Dallas Morning News": "https://www.dallasnews.com/",
    "Dan Abrams Live": "https://www.newsnationnow.com/danabramslive/",
    "Dark to Light with Frank & Beanz": "https://radioinfluence.com/category/dark-to-light/",
    "Deadline White House": "https://www.msnbc.com/deadline-white-house",
    "Deconstructed": "https://theintercept.com/podcasts/deconstructed/",
    "Deep State Radio": "https://thedsrnetwork.com/",
    "Democracy Now! TV Program": "https://freespeech.org/shows/democracy-now/",
    "Denver Post": "https://www.denverpost.com/",
    "Detroit Free Press": "https://www.freep.com/",
    "Diamond and Silk Crystal Clear": "https://www.diamondandsilkinc.com/",
    "Dollar and Sense Podcast": "https://www.brookings.edu/series/dollar-and-sense-podcast/",
    "Don Lemon Tonight": "https://edition.cnn.com/shows/cnn-tonight",
    "Early Start with Christine Romans": "https://edition.cnn.com/shows/early-start",
    "Erin Burnett OutFront": "https://edition.cnn.com/shows/erin-burnett-out-front",
    "East Bay Times": "https://www.eastbaytimes.com/",
    "Face the Nation": "https://www.cbs.com/shows/face-the-nation/",
    "Facts Matter with Roman Balmakov": "https://www.theepochtimes.com/c-facts-matter",
    "Fareed Zakaria GPS": "https://edition.cnn.com/shows/fareed-zakaria-gps",
    "Fast Money": "https://www.cnbc.com/fastmoney/",
    "Firebrand with Matt Gaetz": "https://gaetz.house.gov/firebrand",
    "Firing Line with Margaret Hoover": "https://www.pbs.org/wnet/firing-line/",
    "FiveThirtyEight Politics": "https://fivethirtyeight.com/politics/",
    "Forward with Andrew Yang": "https://www.andrewyang.com/podcast",
    "Fox": "https://www.foxnews.com/",
    "Fox & Friends": "https://www.foxnews.com/shows/fox-and-friends",
    "Fox & Friends First": "https://www.foxnews.com/shows/fox-friends-first",
    "Fox Business Tonight": "https://www.foxbusiness.com/shows/fox-business-tonight",
    "Fox News": "https://www.foxnews.com/",
    "Fox News Primetime": "https://www.foxnews.com/shows/fox-news-primetime",
    "Fox News Rundown": "https://radio.foxnews.com/podcast/fox-news-rundown/",
    "Fox News Sunday with Chris Wallace": "https://www.foxnews.com/shows/fox-news-sunday",
    "Frangela: The Final Word": "https://www.foxnews.com/shows/fox-news-sunday",
    "Freakonomics Radio": "https://freakonomics.com/",
    "Fresh Air": "https://www.npr.org/programs/fresh-air/",
    "Frontline": "https://www.pbs.org/wgbh/frontline/",
    "Full Measure": "https://fullmeasure.news/",
    "Full Frontal with Samantha Bee": "https://www.tbs.com/archives/shows/full-frontal-with-samantha-bee",
    "Gaslit Nation": "https://gaslitnation.libsyn.com/",
    "Glenn TV": "https://www.blazetv.com/series/6h9e60TbKWdu-glenn-tv?channel=series",
    "Graham Allen’s Dear America Podcast": "https://podcasts.apple.com/us/podcast/graham-allens-dear-america-podcast/id1456850698",
    "Greg Kelly Reports": "https://cms.megaphone.fm/channel/gregkellyreports",
    "Guardian": "https://www.theguardian.com/",
    "Hacks on Tap": "https://www.hacksontap.com/",
    "Hallie Jackson Reports": "https://www.msnbc.com/msnbc-live-hallie-jackson",
    "Hard Factor News": "https://hardfactor.com/",
    "The Guardian": "https://www.theguardian.com/",
    "Hearst Television": "http://www.hearst.com/",
    "Heavy.com": "https://heavy.com/",
    "Hodgetwins": "https://officialhodgetwins.com/",
    "Hold These Truths with Dan Crenshaw": "https://holdthesetruthswithdancrenshaw.libsyn.com/",
    "Huckabee": "https://www.tbn.org/programs/huckabee",
    "HuffPost": "https://www.huffingtonpost.com/",
    "In the Bubble with Andy Slavitt": "https://lemonadamedia.com/show/inthebubble/",
    "Independent Journal Review": "https://ijr.com/",
    "Inside Politics With Abby Phillip": "https://edition.cnn.com/audio/podcasts/inside-politics",
    "Inside Politics with John King": "https://edition.cnn.com/audio/podcasts/inside-politics",
    "Inside Story": "https://www.aljazeera.com/program/inside-story/",
    "Inside the Hive Podcast": "https://www.vanityfair.com/podcast/inside-the-hive",
    "Intelligence Squared US": "https://www.intelligencesquaredus.org/",
    "IJR": "https://ijr.com/",
    "Jesse Watters Primetime": "https://www.foxnews.com/shows/jesse-watters-primetime",
    "John Bachman Now": "https://www.newsmaxtv.com/Shows/John-Bachman-Now",
    "John Solomon Reports": "https://justthenews.com/podcasts/john-solomon-reports",
    "Jose Diaz-Balart Reports": "https://www.msnbc.com/jose-diaz-balart",
    "Justice with Judge Jeanine": "https://www.foxnews.com/category/shows/justice-with-judge-jeanine",
    "Kansas City Star": "https://www.kansascity.com/",
    "Kasich & Klepper": "https://www.treefort.fm/series/kasich-klepper",
    "Katy Tur Reports": "https://www.msnbc.com/msnbc-live-katy-tur",
    "Kennedy Saves the World": "https://radio.foxnews.com/podcast/kennedy-saves-the-world/s",
    "Last Week Tonight with John Oliver": "https://www.hbo.com/last-week-tonight-with-john-oliver",
    "Lawrence Jones Cross Country": "https://www.foxnews.com/shows/lawrence-jones-cross-country",
    "Left, Right & Center": "https://www.kcrw.com/news/shows/left-right-center",
    "Let’s Talk Elections": "https://www.youtube.com/channel/UCZ0H9_lidl67AqiC9-RxfvA",
    "LevinTV": "https://www.blazetv.com/category/levintv",
    "Life, Liberty and Levin": "https://www.foxnews.com/shows/life-liberty-levin",
    "Lindell TV": "https://frankspeech.com/live-stream/watch-lindell-tv-live-247",
    "Los Angeles Times": "https://www.latimes.com/",
    "Lost Debate": "https://lostdebate.com/",
    "Louder With Crowder": "https://www.louderwithcrowder.com/",
    "Lovett or Leave It": "https://crooked.com/podcast-series/lovett-or-leave-it/",
    "LA Times": "https://www.latimes.com/",
    "Mad Money": "https://www.cnbc.com/mad-money/",
    "Majority 54": "https://www.wondermedianetwork.com/originals/majority-54",
    "Make Me Smart": "https://www.marketplace.org/shows/make-me-smart/",
    "Making Money with Charles Payne": "https://www.foxbusiness.com/shows/making-money-with-charles-payne",
    "Making Sense with Sam Harris": "https://www.samharris.org/podcasts",
    "Marketplace": "https://www.marketplace.org/",
    "Mea Culpa with Michael Cohen": "https://www.audioup.com/shows/meaculpa",
    "Meet the Press": "https://www.nbcnews.com/meet-the-press",
    "Meet the Press NOW": "https://www.nbcnews.com/meet-the-press",
    "Miami Herald": "http://www.miamiherald.com/",
    "Minneapolis Star Tribune": "http://www.startribune.com/",
    "Morning Joe": "https://www.msnbc.com/morning-joe",
    "Mother Jones": "https://www.motherjones.com/",
    "Mueller, She Wrote": "https://muellershewrote.com/",
    "NBC News": "https://www.nbcnews.com/",
    "New York Post": "https://nypost.com/",
    "New York Times": "https://www.nytimes.com/",
    "Newsweek": "https://www.newsweek.com/",
    "NPR": "https://www.npr.org/",
    "Orange County Register": "https://www.ocregister.com/",
    "Oregonian": "https://www.oregonianmediagroup.com/",
    "PBS": "https://www.pbs.org/",
    "Politico": "https://www.politico.com/",
    "ProPublica": "https://www.propublica.org/",
    "Reuters": "https://www.reuters.com/",
    "Reveal": "https://www.revealnews.org/",
    "Seattle Times": "https://www.seattletimes.com/",
    "Slate": "https://slate.com/",
    "The Atlantic": "https://www.theatlantic.com/",
    "Atlantic": "https://www.theatlantic.com/",
    "The Economist": "https://www.economist.com/",
    "Economist": "https://www.economist.com/",
    "The Hill": "https://thehill.com/",
    "Hill": "https://thehill.com/",
    "The Mercury News": "https://www.mercurynews.com/",
    "Mercury News": "https://www.mercurynews.com/",
    "Time": "http://time.com/",
    "USA Today": "https://www.usatoday.com/",
    "VICE News": "https://www.vice.com/",
    "Vice": "https://www.vice.com/",
    "Voice of Orange County": "https://voiceofoc.org/",
    "Wall Street Journal": "https://www.wsj.com/",
    "Washington Post": "https://www.washingtonpost.com/",
    "Washington Times": "https://www.washingtontimes.com/",
    "Wisconsin Watch": "https://www.wisconsinwatch.org/",
    "AFP": "https://www.afp.com/",
    "Al Jazeera US/Canada News": "https://www.aljazeera.com/topics/regions/us-canada.html",
    "Alternet": "https://www.alternet.org/",
    "AP": "https://www.apnews.com/",
    "Axios": "https://www.axios.com/",
    "BBC": "https://www.bbc.co.uk/",
    "Bipartisan Report": "https://bipartisanreport.com/",
    "Breitbart": "https://www.breitbart.com/",
    "Business Insider": "https://www.businessinsider.com/",
    "Conservative Tribune": "https://www.westernjournal.com/ct/",
    "CSPAN": "https://www.c-span.org/",
    "Daily Caller": "https://dailycaller.com/",
    "Daily Kos": "https://www.dailykos.com/",
    "Daily Mail": "https://www.dailymail.co.uk/",
    "Daily Signal": "https://www.dailysignal.com/",
    "Daily Wire": "https://www.dailywire.com/",
    "David Wolfe": "https://www.davidwolfe.com/",
    "Democracy Now": "https://www.democracynow.org/",
    "Drudge Report": "https://www.drudgereport.com/",
    "Financial Times": "https://www.ft.com/",
    "Fiscal Times": "https://www.thefiscaltimes.com/",
    "Forbes": "https://www.forbes.com/",
    "Foreign Policy": "https://foreignpolicy.com/",
    "Fortune": "http://fortune.com/",
    "Forward Progressives": "http://www.forwardprogressives.com/",
    "FreeSpeech TV": "https://freespeech.org/",
    "Guacamoley": "https://guacamoley.com/",
    "Huffington Post": "https://www.huffpost.com/",
    "InfoWars": "https://www.infowars.com/",
    "Intercept": "https://theintercept.com/",
    "Jacobin": "https://jacobinmag.com/",
    "Marketwatch": "https://www.marketwatch.com/",
    "Mic": "https://www.mic.com/",
    "MSNBC": "https://www.msnbc.com/",
    "National Enquirer": "https://www.nationalenquirer.com/",
    "National Review": "https://www.nationalreview.com/",
    "NBC": "https://www.nbc.com/",
    "New Republic": "https://newrepublic.com/",
    "News and Guts": "https://www.newsandguts.com/",
    "NewsMax": "https://www.newsmax.com/",
    "OAN": "https://www.oann.com/",
    "Occupy Democrats": "http://occupydemocrats.com/",
    "OZY": "https://www.ozy.com/",
    "Palmer Report": "https://www.palmerreport.com/",
    "Patribotics": "https://patribotics.blog/",
    "PJ Media": "https://pjmedia.com/",
    "Quartz": "https://qz.com/",
    "Reason": "https://reason.com/",
    "RedState": "https://www.redstate.com/",
    "Second Nexus": "https://secondnexus.com/",
    "ShareBlue": "https://shareblue.com/",
    "Talking Points Memo": "https://talkingpointsmemo.com/",
    "The Advocate": "https://www.advocate.com/",
    "The American Conservative": "https://www.theamericanconservative.com/",
    "The Blaze": "https://www.theblaze.com/",
    "The Federalist": "https://thefederalist.com/",
    "The Gateway Pundit": "https://www.thegatewaypundit.com/",
    "The Nation": "https://www.thenation.com/",
    "The New Yorker": "https://www.newyorker.com/",
    "The Skimm": "https://theskimm.com/",
    "The Week": "https://theweek.com/",
    "The Weekly Standard": "https://www.weeklystandard.com/",
    "The Young Turks": "https://tyt.com/",
    "Think Progress": "https://thinkprogress.org/",
    "Truthout": "https://truthout.org/",
    "Twitchy": "https://twitchy.com/",
    "Vanity Fair": "https://www.vanityfair.com/",
    "Vox": "https://www.vox.com/",
    "Washington Examiner": "https://www.washingtonexaminer.com/",
    "Washington Free Beacon": "https://freebeacon.com/",
    "Washington Monthly": "https://washingtonmonthly.com/",
    "WND": "https://www.wnd.com/",
    "Wonkette": "https://www.wonkette.com/",
    "WorldTruth.Tv": "https://worldtruth.tv/",
    "70 News": "https://70news.wordpress.com/",
    "ABCnews.com.co": "http://abcnews.com.co/",
    "American News": "http://americannews.com/",
    "Before It's News": "http://beforeitsnews.com/",
    "bients.com": "https://bients.com/",
    "bizstandardnews.com": "http://bizstandardnews.com/",
    "Bloomberg.ma": "http://bloomberg.ma/",
    "The Boston Tribune": "http://thebostontribune.com/",
    "Breaking-CNN.com": "http://breaking-cnn.com/",
    "BVA News": "http://bvanews.com/",
    "Celebtricity": "http://www.celebtricity.com/",
    "cnn-trending.com": "http://cnn-trending.com/",
    "Conservative 101": "http://conservative101.com/",
    "Conservative Frontline": "https://conservativefrontline.com/",
    "CountyNewsroom.info": "http://countynewsroom.info/",
    "Daily Buzz Live": "http://dailybuzzlive.com/",
    "Daily USA Update": "http://dailyusaupdate.com/",
    "DC Gazette": "http://thedcgazette.com/",
    "Denver Guardian": "http://denverguardian.com/",
    "Disclose TV": "http://disclose.tv/",
    "DrudgeReport.com.co": "http://drudgereport.com.co/",
    "Empire Herald": "http://empireherald.com/",
    "Empire News": "empirenews.org",
    "Empire Sports": "http://www.empiresports.co/",
    "Fox-news24.com": "http://fox-news24.com/",
    "Global Associated News": "http://www.globalassociatednews.com/",
    "Globalresearch.ca": "http://globalresearch.ca/",
    "Gossip Mill Mzansi": "http://gossipmillsa.com/",
    "Guerilla News": "http://guerilla.news/",
    "Gummy Post": "http://gummypost.com/",
    "Houston Chronicle TV": "http://houstonchronicle-tv.com/",
    "Huzlers": "http://huzlers.com/",
    "ΚΒΟΙ2.comКВОІ2.com": "http://xn--2-0lbvc0a.com/",
    "KMT 11 News": "http://kmt11.com/",
    "The Last Line of Defense": "http://thelastlineofdefence.org/",
    "Liberal Society": "http://liberalsociety.com/",
    "Liberty Writers News": "https://libertywriters.com/",
    "LinkBeef": "http://linkbeef.com/",
    "Naha Daily": "http://nahadaily.com/",
    "National Insider Politics": "http://nationalinsiderpolitics.com/",
    "NationalReport.net": "http://nationalreport.net/",
    "Natural News": "http://naturalnews.com/",
    "NBCNews.com.co": "http://nbcnews.com.co/",
    "News Breaks Here": "http://newsbreakshere.com/",
    "NewsBuzzDaily": "http://www.newsbuzzdaily.com/",
    "News Examiner": "http://newsexaminer.net/",
    "News Hound": "http://news-hound.com/",
    "The News Nerd": "http://thenewsnerd.com/",
    "NewsPunch": "http://newspunch.com/",
    "NewsWatch33": "http://newswatch33.com/",
    "The New York Evening": "http://thenewyorkevening.com/",
    "Now 8 News": "http://now8news.com/",
    "The Predicted": "http://thepredicted.com/",
    "Prntly": "http://prntly.com/",
    "React 365": "http://react365.com/",
    "Red Flag News": "http://redflagnews.com/",
    "The Reporterz": "http://thereporterz.com/",
    "Snoopack": "http://snoopack.com/",
    "Spin Zone": "http://spinzon.com/",
    "St George Gazette": "http://stgeorgegazette.com/",
    "Stuppid": "http://stuppid.com/",
    "Super Station 95": "https://www.superstation95.com/",
    "TrueTrumpers.com": "http://truetrumpers.com/",
    "UConservative": "http://www.uconservative.net/",
    "UndergroundNewsReport.com": "http://undergroundnewsreport.com/",
    "United Media Publishing": "http://unitedmediapublishing.com/",
    "USA Daily Info": "http://usadailyinfo.com/",
    "usatoday.com.co": "http://usatoday.com.co/",
    "US Postman": "http://uspostman.com/",
    "washingtonpost.com.co": "http://washingtonpost.com.co/",
    "World Truth TV": "http://worldtruth.tv/",
    "World News Daily Report": "http://worldnewsdailyreport.com/",
    "El Koshary Today": "http://elkoshary.com/",
    "Fognews": "http://fognews.ru/",
    "Islamica News": "http://www.islamicanews.com/",
    "Le Journal de Mourréal": "http://www.journaldemourreal.com",
    "Nordpresse": "http://www.nordpresse.be/",
    "SatireWire": "http://www.satirewire.com/",
    "Zaytung": "http://www.zaytung.com/",
    "Centre for Research on Globalization": "https://www.globalresearch.ca/",
    "CliffsNotes": "http://www.cliffsnotes.com/",
    # 'Scriptural texts': ??
    "CNN Video": "https://edition.cnn.com/videos",
    "The Root": "https://www.theroot.com/",
    "The Weather Channel": "https://weather.com/",
    "CBSnews.com.co": "https://cbsnews.com.co/",
    "GlobalSecurity.org": "https://www.globalsecurity.org/",
    "Exposition Daily": "https://expositiondaily.com/",
    "OpIndia": "https://www.opindia.com/",
    "The Grayzone": "https://thegrayzone.com/",
    "Next News Network": "https://www.youtube.com/user/NextNewsNetwork/",
    "Christwire": "http://christwire.org/",
    "Topeka News": "https://www.cjonline.com/",
    "The Buffalo Chronicle": "https://buffalochronicle.com/",
    "OANN (One America News Network)": "https://www.oann.com/",
    "Postcard News": "https://postcard.news/",
    "CNN Cable TV News Network": "https://cnn.com/",
    "Fox News TV Cable Network": "https://www.foxnews.com/",
    "OAN Network": "https://www.oann.com/",
    "Law Enforcement Today": "https://www.lawenforcementtoday.com/",
    "Peerage websites": "https://thepeerage.com",  # royalark.net, thepeerage.com, worldstatesmen.org)
    "StarsUnfolded": "https://starsunfolded.com/",
    "Walking Eagle News": "https://walkingeaglenews.com/",
    "News Break": "https://www.newsbreak.com/",
    "Oneworld.press": "https://oneworld.press/",
    "Peace Data": "https://peacedata.net/",
    "Fair Observer": "https://www.fairobserver.com/",
    "ΚΒΟΙ2.com": "http://ΚΒΟΙ2.com/",
    "Battery University": "https://batteryuniversity.com/",
    "Global Times": "https://www.globaltimes.cn/",
    "Zero Hedge": "https://www.zerohedge.com/",
    "The California Globe": "https://californiaglobe.com/",
    "Metal-experience.com": "https://metal-experience.com/",
    "Our Campaigns": "https://www.ourcampaigns.com/",
    "Religion News Service": "https://religionnews.com/",
    "Weather2Travel.com": "https://www.weather2travel.com/",
    "The College Fix": "https://www.thecollegefix.com/",
    "CFO": "https://www.cfo.com/",
    "Financial Buzz": "https://www.financialbuzz.com/",
    "Cuomo Prime Time": "https://edition.cnn.com/shows/cuomo-prime-time",
    "Hannity": "https://www.foxnews.com/shows/hannity",
    "The Daily": "https://www.nytimes.com/column/the-daily",
    "The Lead with Jake Tapper": "https://edition.cnn.com/shows/the-lead",
    "The Rachel Maddow Show": "https://www.msnbc.com/rachel-maddow-show",
    "This American Life": "https://www.thisamericanlife.org/",
    "Timesnewroman.ro": "https://www.timesnewroman.ro/",
    "Centre for Research on Globalisation": "https://www.globalresearch.ca/",
    "MEAWW": "https://meaww.com/",
    "bestgore.com": "https://bestgore.com/",
    "NewsBlaze": "https://newsblaze.com/",
}

# this regex works for facebook and twitter and extracts the source as account name
# TODO for youtube extract the channel name as in the second answer here https://stackoverflow.com/questions/17806944/how-to-get-youtube-channel-name
social_regex = r"^(https?:\/\/)?([a-z-]+\.)*(?P<res>(facebook\.com|facebook\.com\/pages|twitter\.com|youtube\.com)\/([A-Za-z0-9_.]*))(\/.*)?"


def add_protocol(url):
    """when the URL does not have http://"""
    if not re.match(r"[a-z]+://.*", url):
        # default protocol
        url = "https://" + url
    return url


def get_url_domain(url, only_tld=True):
    """Returns the domain of the URL"""
    if not url:
        return ""
    ext = tldextract.extract(url)
    if not only_tld:
        result = ".".join(part for part in ext if part)
    else:
        result = ".".join([ext.domain, ext.suffix])
    if result.startswith("www."):
        # sometimes the www is there, sometimes not
        result = result[4:]
    return result.lower()


def get_url_source(url):
    """Returns the source of the URL (may be different from domain)"""
    match = re.search(social_regex, url)
    if match:
        result = match.group("res")
        print(url, "-->", result)
        return result
    else:
        return get_url_domain(url, only_tld=False)


def aggregate_source(doc_level, origin_name):
    return aggregate_by(doc_level, origin_name, "source")


def aggregate_domain(doc_level, origin_name):
    return aggregate_by(doc_level, origin_name, "domain")


def aggregate_by(doc_level, origin_name, key):
    by_group = defaultdict(list)

    for ass in doc_level:
        by_group[ass[key]].append(ass)

    results = {}

    for k, v in by_group.items():
        credibility_sum = 0.0
        confidence_sum = 0.0

        # something like {'snopes.com' : {'factcheck_positive_cnt': 3, ...}}}
        cnts_by_factchecker = defaultdict(lambda: defaultdict(list))
        counts = defaultdict(list)
        # TODO convert this to a list of detailed reports (label, which URL was checked, ...)
        reports = []

        assessment_urls = set()
        original_labels = set()
        coinform_labels = defaultdict(int)
        for el in v:
            credibility_value = el["credibility"]["value"]
            credibility_confidence = el["credibility"]["confidence"]
            assessment_urls.add(el["url"])
            credibility_sum += credibility_value * credibility_confidence
            confidence_sum += credibility_confidence
            if el.get("original_label", None):
                original_labels.add(el["original_label"])
            if origin_name == "factchecking_report":
                if el.get("coinform_label", None):
                    coinform_labels[el["coinform_label"]] += 1
                # collect counts of positive, negative, neutral assessments
                reports.append(
                    {
                        "report_url": el["url"],
                        "coinform_label": el["coinform_label"],
                        "original_label": el["original_label"],
                        "itemReviewed": el["itemReviewed"],
                        "origin": el["origin"],
                    }
                )

                # TODO limit the size somehow (same reports about the same item)
                # pymongo.errors.OperationFailure: BSONObj size: 22840637 (0x15C853D) is invalid. Size must be between 0 and 16793600(16MB)
                reports = reports[:500]

            if "coinform_label" in el:
                label_to_use = el["coinform_label"]
            else:
                # the mapping for other data, non fact-checks
                label_to_use = (
                    "not_verifiable"
                    if credibility_confidence < 0.4
                    else "credible"
                    if credibility_value > 0
                    else "not_credible"
                    if credibility_value < 0
                    else "uncertain"
                )
            # TODO just collect counts? nested resource or separate?
            counts[label_to_use].append(el["url"])
            origin_id = el["origin_id"]
            # raise ValueError(origin.id)
            # origin_id.replace('.', '_')
            cnts_by_factchecker[origin_id][label_to_use].append(el["url"])
            # add this also inside the object
            cnts_by_factchecker[origin_id]["origin_id"] = origin_id

        if confidence_sum:
            credibility_weighted = credibility_sum / confidence_sum
        else:
            credibility_weighted = 0.0
        if len(v) > 1:
            print(k, "has", len(v), "assessments")
            # raise ValueError(k)
        # print(k, len(v), credibility_sum, confidence_sum)

        # see whether there is just one assessment url
        if not len(assessment_urls):
            continue
        if len(assessment_urls) == 1:
            assessment_url = assessment_urls.pop()
            # TODO should do the same when aggregating on source, keeping the domain
            # TODO: we need to propagate the review URLs and itemReviewed to allow transparency
        elif origin_name == "factchecking_report":
            if key in ["source", "domain"]:
                source_path_safe = k.replace("/", "%2F")
                assessment_url = (
                    f"https://misinfo.me/misinfo/credibility/sources/{source_path_safe}"
                )
            # elif key == 'itemReviewed':
            #     assessment_url = 'http://todo.todo'
            # assessment_url = f'https://misinfo.me/misinfo/credibility/?/{k}'
        else:
            # happens with wikipedia_lists? Not really
            print("HOHOHO", assessment_urls)
            assessment_url = assessment_urls.pop()

        if origin_name == "factchecking_report":
            n_factchecks = sum(coinform_labels.values())
            original_label = (
                f'Fact-checked {n_factchecks} time{"s" if n_factchecks > 1 else ""}: '
                + ", ".join(
                    f'{coinform_labels[label]} as {label.replace("_", " ")}'
                    for label in coinform_labels
                )
                + "."
            )
        else:
            original_label = ", ".join(original_labels)

        # TODO assign final coinform label from credibility?

        all_counts = cnts_by_factchecker
        cnts_by_factchecker["overall"] = counts

        results[k] = {
            "url": assessment_url,
            "credibility": {
                "value": credibility_weighted,
                "confidence": confidence_sum / len(v),
            },
            "itemReviewed": k,
            "counts": cnts_by_factchecker,  # --> RINOMINA campo a "counts" e poi usa reviews/details per metterci roba
            "original_label": original_label,
            "reports": reports,
            "origin_id": origin_name,
            key: k,
            "granularity": key,
        }
    return results.values()


def batch(iterable, n=100):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx : min(ndx + n, l)]


def unshorten(url):
    response = unshortener.unshorten(url)
    return response  # ['url_full']
