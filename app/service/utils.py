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
    "Daily Torch": "https://dailytorch.com/",
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
    "Good Morning America": "https://abcnews.go.com/GMA",
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
    "Let’s Talk Elections": "https://www.youtube.com/@LetsTalkElections",
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
    "National Report": "https://www.newsmaxtv.com/Shows/National-Report",
    "NBC: Today": "https://www.nbc.com/today",
    "NBC News": "https://www.nbcnews.com/",
    "NBC Nightly News": "https://www.nbcnews.com/nightly-news",
    "NBC Nightly News with Lester Holt": "https://www.nbcnews.com/nightly-news",
    "New York Post": "https://nypost.com/",
    "New York Times": "https://www.nytimes.com/",
    "NewsNation Prime": "https://www.newsnationnow.com/prime/",
    "NewsNation: Morning in America": "https://www.newsnationnow.com/morninginamerica/",
    "Newsweek": "https://www.newsweek.com/",
    "Newt’s World": "https://www.gingrich360.com/podcasts/newts-world/",
    "Nightline": "https://abcnews.go.com/Nightline",
    "No Agenda": "https://www.noagendashow.net/",
    "No Lie with Brian Tyler Cohen": "https://briantylercohen.com/podcast/",
    "NPR": "https://www.npr.org/",
    "NPR News Now": "https://www.npr.org/podcasts/500005/npr-news-now",
    "On Balance with Leland Vittert": "https://www.newsnationnow.com/on-balance-with-leland-vittert/",
    "On Point": "https://www.wbur.org/radio/programs/onpoint",
    "On the Media": "https://www.wnycstudios.org/podcasts/otm",
    "One Nation w/ Brian Kilmeade": "https://www.foxnews.com/shows/one-nation-with-brian-kilmeade",
    "Orange County Register": "https://www.ocregister.com/",
    "Oregonian": "https://www.oregonianmediagroup.com/",
    "Outnumbered": "https://www.foxnews.com/shows/outnumbered",
    "Panorama": "https://www.bbc.co.uk/programmes/b006t14n",
    "Pantsuit Politics": "https://www.pantsuitpoliticsshow.com/",
    "Part of the Problem": "https://gasdigitalnetwork.com/gdn-show-channels/part-of-the-problem/",
    "Pat Gray Unleashed": "https://www.theblaze.com/podcasts/pat-gray-unleashed",
    "PBS": "https://www.pbs.org/",
    "PBS Newshour": "https://www.pbs.org/newshour/",
    "People & Power": "https://www.aljazeera.com/program/people-power/",
    "Pivot": "https://podcasts.voxmedia.com/show/pivot",
    "Planet Money": "https://www.npr.org/podcasts/510289/planet-money",
    "Pod is a Woman": "https://www.johannamaska.com/pod-is-a-woman",
    "Pod Save America": "https://crooked.com/podcast-series/pod-save-america/",
    "Pod Save the People": "https://crooked.com/podcast-series/pod-save-the-people/",
    "Pod Save the World": "https://crooked.com/podcast-series/pod-save-the-world/",
    "Political Gabfest": "https://slate.com/podcasts/political-gabfest",
    "Politically Re-Active with W. Kamau Bell & Hari Kondabolu": "https://www.topic.com/politically-re-active",
    "Politico": "https://www.politico.com/",
    "Politico Playbook Daily Briefing": "https://www.politico.com/podcasts/playbook-daily-briefing",
    "Politicology": "https://politicology.com/",
    "Politico’s Pulse Check": "https://www.politico.com/podcasts/pulse-check",
    "Politics War Room with James Carville & Al Hunt": "https://www.politicon.com/podcast-title/politics-war-room-with-james-carville-and-al-hunt/",
    "PoliticsNation with Al Sharpton": "https://www.msnbc.com/politicsnation",
    "ProPublica": "https://www.propublica.org/",
    "QAnon Anonymous": "https://www.qanonanonymous.com/",
    "Rational Security": "https://www.lawfareblog.com/topic/rational-security",
    "Real America": "https://www.oann.com/shows/realamerica/",
    "Real Coffee With Scott Adams": "https://www.youtube.com/@RealCoffeewithScottAdams",
    "Real Time with Bill Maher": "https://www.hbo.com/real-time-with-bill-maher",
    "Red Eagle Politics": "https://www.youtube.com/@RedEaglePolitics",
    "Relatable with Allie Beth Stuckey": "https://alliebethstuckey.com/",
    "Reliable Sources": "https://www.cnn.com/shows/reliable-sources",
    "Reuters": "https://www.reuters.com/",
    "Reveal": "https://www.revealnews.org/",
    "Rob Schmitt Tonight": "https://www.newsmaxtv.com/Shows/Rob-Schmitt-Tonight",
    "Ron Paul Liberty Report": "https://www.youtube.com/@RonPaulLibertyReport",
    "Rough Translation": "https://www.npr.org/podcasts/510324/rough-translation",
    "Rudy Giuliani’s Common Sense": "https://rudygiulianics.com/",
    "RT News": "https://www.rt.com/",
    "Rumble with Michael Moore": "https://rumble.media/",
    "Ruthless": "https://tylerperry.com/tyler/archive/all/ruthless/",
    "Saturday Agenda": "https://www.newsmaxtv.com/Shows/Saturday-Agenda",
    "Save the Nation": "https://www.newsmax.com/",
    "Seattle Times": "https://www.seattletimes.com/",
    "Sekulow": "https://www.tbn.org/people/jay-sekulow",
    "Shadowproof Bias and Reliability": "https://shadowproof.com/",
    "Skimm This": "https://www.theskimm.com/skimm-this",
    "Slate": "https://slate.com/",
    "SmartLess": "https://www.smartless.com/",
    "Smerconish": "https://www.smerconish.com/",
    "Special Report w/Bret Baier": "https://www.foxnews.com/shows/special-report",
    "Spicer & Co.": "https://seanspicer.com/spicer-co/",
    "Stand Up! with Pete Dominick": "https://standupwithpete.com/",
    "Start Here": "https://abcaudio.com/podcasts/start-here/",
    "State of the Union with Jake Tapper and Dana Bash": "https://edition.cnn.com/shows/state-of-the-union",
    "Stay Tuned with Preet": "https://cafe.com/stay-tuned-podcast/",
    "Staying Home with Josh Fox": "https://tyt.com/shows/stayinghome",
    "Stephanie Ruhle Reports": "https://www.msnbc.com/stephanie-ruhle",
    "Stephanie Miller’s Happy Hour": "https://sexyliberal.com/stephanie-millers-happy-hour-podcast/",
    "Stinchfield": "https://www.newsmax.com/",
    "Stories of our times": "https://www.thetimes.co.uk/podcasts/stories-of-our-times",
    "Stuff You Should Know": "https://www.iheart.com/podcast/105-stuff-you-should-know-26940277/",
    "Stu Does America": "https://www.blazetv.com/series/QeocD1zKeSP0-stu-does-america?channel=series",
    "Sunday Papers": "https://gregfitzsimmons.com/podcast/tag/sunday+papers",
    "Sunday Night in America with Trey Gowdy": "https://www.fox.com/sunday-night-in-america-with-trey-gowdy/",
    "Sunday Today with Willie Geist": "https://www.today.com/sunday-today",
    "Symone": "https://www.msnbc.com/symone",
    "The 11th Hour with Brian Williams": "https://www.msnbc.com/11th-hour",
    "The 11th Hour With Stephanie Ruhle": "https://www.msnbc.com/11th-hour",
    "The Al Franken Podcast": "https://alfranken.com/listen",
    "The Alex Jones Show": "https://www.infowars.com/show/american-journal/",
    "The Andrew Klavan Show": "https://www.dailywire.com/show/the-andrew-klavan-show",
    "The Argument": "https://www.nytimes.com/column/the-argument",
    "Atlantic": "https://www.theatlantic.com/",
    "The Atlantic": "https://www.theatlantic.com/",
    "The Axe Files with David Axelrod": "https://edition.cnn.com/audio/podcasts/axe-files",
    "The Ben Ferguson Podcast": "https://www.premierenetworks.com/shows/ben-ferguson-podcast",
    "The Ben Shapiro Show": "https://www.dailywire.com/show/the-ben-shapiro-show",
    "The Beat with Ari Melber": "https://www.msnbc.com/the-beat-with-ari-melber",
    "The Big Sunday Show": "https://www.fox.com/the-big-sunday-show/",
    "The Bottom Line": "https://www.aljazeera.com/program/the-bottom-line/",
    "The Breakdown with Shaun King": "https://thebreakdown.thenorthstar.com/",
    "The Breakfast Club": "https://www.iheart.com/podcast/the-breakfast-club-24992238/",
    "The Briefing": "https://albertmohler.com/the-briefing",
    "The Brilliant Idiots": "https://www.youtube.com/@BrilliantIdiotsPod",
    "The Bulwark Podcast": "https://www.thebulwark.com/podcast/the-bulwark-podcast/",
    "The Candace Owens Show": "https://www.prageru.com/series/candace",
    "The Chad Prather Show": "https://www.watchchad.com/",
    "The Charlie Kirk Show": "https://thecharliekirkshow.com/",
    "The Cross Connection with Tiffany Cross": "https://www.msnbc.com/cross-connection",
    "The Daily Beans": "https://www.dailybeanspod.com/",
    "The Damage Report with John Iadarola": "https://tyt.com/shows/the-damage-report/about",
    "The Daily Punch": "https://shows.cadence13.com/podcast/daily-punch",
    "The Daily Show With Trevor Noah: Ears Edition": "https://www.stitcher.com/show/the-daily-show-with-trevor-noah-ears-edition",
    "The Dan Bongino Show": "https://www.westwoodone.com/programs/news-and-talk/daily-talk/the-dan-bongino-show/",
    "The David Pakman Show": "https://www.youtube.com/@thedavidpakmanshow",
    "The Debate": "https://www.newsweek.com/the-debate",
    "The Dershow": "https://www.youtube.com/@TheDershowWithAlanDershowitz",
    "The Devin Nunes Podcast": "https://www.devinnunes.com/listen",
    "The Dinesh D’Souza Podcast": "https://salempodcastnetwork.com/podcasts/dinesh-d-souza-podcast",
    "The Donlon Report": "https://www.newsnationnow.com/the-donlon-report/",
    "The Economist": "https://www.economist.com/",
    "Economist": "https://www.economist.com/",
    "The Economist Asks": "https://www.economist.com/podcasts",
    "The Ezra Klein Show": "https://www.nytimes.com/column/ezra-klein-podcast",
    "The Faulkner Focus": "https://www.foxnews.com/shows/the-faulkner-focus",
    "The Fifth Column": "https://wethefifth.com/",
    "The Five": "https://www.foxnews.com/shows/the-five",
    "The Fourth Watch Podcast": "http://fourthwatch.media/",
    "The Gist": "https://www.thegistsports.com/",
    "The Glenn Beck Program": "https://www.glennbeck.com/",
    "The Gorka Reality Check": "https://www.newsmaxtv.com/Shows/The-Gorka-Reality-Check",
    "The Hartmann Report": "https://www.thomhartmann.com/",
    "The Hill": "https://thehill.com/",
    "Hill": "https://thehill.com/",
    "The Holy Post": "https://www.holypost.com/",
    "The Holy Post Podcast": "https://www.holypost.com/",
    "The Ingraham Angle": "https://www.foxnews.com/shows/ingraham-angle",
    "The Jimmy Dore Show": "https://www.youtube.com/@thejimmydoreshow",
    "The Joe Rogan Experience": "https://www.joerogan.com/",
    "The Journal.": "https://www.wsj.com/podcasts/the-journal",
    "The Journal Editorial Report": "https://www.foxnews.com/shows/journal-editorial-report",
    "The Katie Phang Show": "https://www.msnbc.com/katie-phang",
    "The Larry Elder Show": "https://larryelder.com/",
    "The Larry Kudlow Show": "https://wabcradio.com/podcast/larry-kudlow/",
    "The Last Word with Lawrence O’Donnell": "https://www.msnbc.com/the-last-word",
    "The Lawfare Podcast": "https://www.lawfareblog.com/topic/lawfare-podcast",
    "The Libertarian": "https://www.hoover.org/publications/defining-ideas/libertarian",
    "The Lincoln Project": "https://lincolnproject.us/",
    "The Listening Post": "https://www.aljazeera.com/program/the-listening-post/",
    "The Majority Report with Sam Seder": "https://majorityreportradio.com/",
    "The Mark Levin Show": "https://www.marklevinshow.com/",
    "The Mary Trump Show": "https://www.politicon.com/podcast-title/the-mary-trump-show/",
    "The Matt Walsh Show": "https://www.dailywire.com/show/the-matt-walsh-show",
    "The McCarthy Report": "https://www.nationalreview.com/podcasts/the-mccarthy-report/",
    "The Media Roundtable with Dan Granger": "https://www.mediaroundtable.com/",
    "The Megyn Kelly Show": "https://www.youtube.com/@MegynKelly",
    "The Mehdi Hasan Show": "https://www.msnbc.com/mehdi-hasan",
    "The MeidasTouch Podcast": "https://www.meidastouch.com/podcast",
    "The Mercury News": "https://www.mercurynews.com/",
    "Mercury News": "https://www.mercurynews.com/",
    "The Michael Knowles Show": "https://www.dailywire.com/show/the-michael-knowles-show",
    "The Michael Savage Show": "https://cms.megaphone.fm/channel/WWO2453800973",
    "The Mother Jones Podcast": "https://www.motherjones.com/podcasts/",
    "The New Abnormal": "https://www.thedailybeast.com/franchise/the-new-abnormal",
    "The New Yorker Radio Hour": "https://www.wnycstudios.org/podcasts/tnyradiohour",
    "The News & Why It Matters": "https://www.theblaze.com/podcasts/the-news-and-why-it-matters",
    "The News with Shepard Smith": "https://www.cnbc.com/shepard-smith/",
    "The Next Revolution with Steve Hilton": "https://www.fox.com/the-next-revolution-with-steve-hilton/",
    "The NPR Politics Podcast": "https://www.npr.org/podcasts/510310/npr-politics-podcast",
    "The PoliticsGirl Podcast": "https://www.politicsgirl.com/",
    "The Problem With Jon Stewart": "https://tv.apple.com/us/show/the-problem-with-jon-stewart/umc.cmc.4fcexvzqezr25p9weks6sxpob",
    "The President’s Inbox": "https://www.cfr.org/podcasts/presidents-inbox",
    "The Real Story": "https://www.bbc.co.uk/programmes/p02dbd4m",
    "The Realignment": "https://the-realignment.simplecast.com/",
    "The Reason Roundtable": "https://reason.com/podcasts/the-reason-roundtable/",
    "The Record with Greta Van Susteren": "https://www.newsmaxtv.com/Shows/The-Record",
    "The ReidOut": "https://www.msnbc.com/reidout",
    "The Remnant": "https://thedispatch.com/podcast/remnant/",
    "The Rubin Report": "https://www.blazetv.com/series/8oHZJGqX8aaN-the-rubin-report?channel=series",
    "The Sean Hannity Show": "https://hannity.com/",
    "The Sharyl Attkisson Podcast": "http://sharylattkisson.com/",
    "The Situation Room": "https://edition.cnn.com/shows/situation-room",
    "The Skepticrat": "https://audioboom.com/channel/the-skepticrat",
    "The Smerconish Podcast": "https://www.smerconish.com/podcasts/",
    "The Story with Martha MacCallum": "https://www.foxnews.com/shows/the-story",
    "The Stream TV Show": "https://www.streamtvshow.com/",
    "The Sunday Show with Jonathan Capehart": "https://www.msnbc.com/capehart",
    "The Trish Regan Show": "https://podcasts.apple.com/us/podcast/the-trish-regan-show/id1526687124",
    "The Takeout": "https://www.cbsnews.com/news/political-podcast-the-takeout/",
    "The Trey Gowdy Podcast": "https://radio.foxnews.com/podcast/trey-gowdy/",
    "The View": "https://abc.com/shows/the-view",
    "The Water Cooler with David Brody": "https://justthenews.com/tv/the-water-cooler-david-brody",
    "The Weeds": "https://www.vox.com/the-weeds",
    "The Week on the Hill": "https://wtop.com/shows/week-on-the-hill/",
    "The World According to Jesse": "https://www.rt.com/",
    "The World and Everything In It": "https://wng.org/podcasts/the-world-and-everything-in-it",
    "Tim Pool Daily Show": "https://www.redseatventures.com/tim-pool-podcasts",
    "Time": "http://time.com/",
    "TIME’s The Brief": "https://time.com/tag/the-brief/",
    "Tipping Point": "https://www.youtube.com/@tippingpointwithlizwheeler6863",
    "Today in Focus": "https://www.theguardian.com/news/series/todayinfocus",
    "Today with Hoda & Jenna": "https://www.today.com/hoda-and-jenna",
    "Today, Explained": "https://www.vox.com/today-explained-podcast",
    "Truth Over News": "https://www.theepochtimes.com/c-truth-over-news",
    "Tucker Carlson Today": "https://nation.foxnews.com/tucker-carlson-today/",
    "Tucker Carlson Tonight": "https://www.foxnews.com/shows/tucker-carlson-tonight",
    "Turley Talks": "https://www.ewtn.com/tv/shows/turley-talks",
    "TYT: The Conversation": "https://tyt.com/shows/the-conversation",
    "UNDISTRACTED with Brittany Packnett Cunningham": "https://wearethemeteor.com/work/undistracted/",
    "Unfiltered with Dan Bongino": "https://www.fox.com/unfiltered-with-dan-bongino/",
    "Unlocking Us with Brene Brown": "https://brenebrown.com/podcast-show/unlocking-us/",
    "Up First": "https://www.npr.org/podcasts/510318/up-first",
    "UpFront": "https://www.aljazeera.com/program/upfront/",
    "USA Today": "https://www.usatoday.com/",
    "Useful Idiots": "https://www.rollingstone.com/t/useful-idiots/",
    "Verdict with Ted Cruz": "https://verdictwithtedcruz.locals.com/",
    "VICE News": "https://www.vice.com/",
    "Vice": "https://www.vice.com/",
    "Voice of Orange County": "https://voiceofoc.org/",
    "Wake Up America": "https://www.newsmaxtv.com/Shows/Wake-Up-America",
    "Wait Wait … Don’t Tell Me": "https://www.npr.org/programs/wait-wait-dont-tell-me/",
    "Wall Street Journal": "https://www.wsj.com/",
    "Washington Journal": "https://www.c-span.org/series/?washingtonJournal",
    "Washington Post": "https://www.washingtonpost.com/",
    "Washington Times": "https://www.washingtontimes.com/",
    "Washington Week": "https://www.pbs.org/weta/washingtonweek/",
    "Watters’ World": "https://www.foxnews.com/shows/watters-world",
    "What A Day": "https://crooked.com/podcast-series/what-a-day/",
    "What the Hell is Going On?": "https://www.aei.org/tag/what-the-hell-podcast/",
    "What Next": "https://slate.com/podcasts/what-next",
    "What’s News": "https://www.wsj.com/podcasts/whats-news",
    "White Flag with Joe Walsh": "https://podcasts.apple.com/us/podcast/white-flag-with-joe-walsh/id1590913798",
    "Why Is This Happening? with Chris Hayes": "https://www.msnbc.com/msnbc-podcast/why-is-this-happening-chris-hayes",
    "Why It Matters": "https://www.cfr.org/podcasts/why-it-matters",
    "Wisconsin Watch": "https://www.wisconsinwatch.org/",
    "Witness": "https://www.aljazeera.com/program/witness/",
    "World News Roundup": "https://podcasts.apple.com/us/podcast/cbs-news-roundup/id172902754",
    "X22 Report": "https://x22report.com/",
    "You and Me Both with Hillary Clinton": "https://podcasts.apple.com/us/podcast/you-and-me-both-with-hillary-clinton/id1531768983",
    "Your Money Briefing": "https://www.wsj.com/podcasts/your-money-matters",
    "Your World with Neil Cavuto": "https://www.foxnews.com/shows/your-world-cavuto",
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
    "Next News Network": "https://www.youtube.com/@NextNewsNetwork",
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
social_regex = r"^(https?:\/\/)?([a-z-]+\.)*(?P<res>(facebook\.com|facebook\.com\/pages|twitter\.com|youtube\.com)\/([A-Za-z0-9_@.]*))(\/.*)?"


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
    try:
        ext = tldextract.extract(url)
        if not only_tld:
            result = ".".join(part for part in ext if part)
        else:
            result = ".".join([ext.domain, ext.suffix])
        if result.startswith("www."):
            # sometimes the www is there, sometimes not
            result = result[4:]
    except Exception as e:
        print('get_url_domain', url, e)
        raise ValueError(url)
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
            # happens with wikipedia_lists or with adfontesmedia
            print(
                "HOHOHO multiple assessment URLs, now picking the first one",
                assessment_urls,
            )
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
