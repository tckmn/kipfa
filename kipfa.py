#!/usr/bin/python3

from collections import Counter
from threading import Thread
import datetime
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from pyrogram import Client
from pyrogram.api import types, functions

import speech_recognition as sr

import requests
import urllib
from bs4 import BeautifulSoup

import data
sys.path.insert(0, './steno-keyboard-generator')
import keyboard

import puzzle

admin = 212594557
class Chats:
    frink    = 1277770483
    haxorz   = 1059322065
    mariposa = 1053893427
    ppnt     = 1232971188
    schmett  = 1119355580
    testing  = 1178303268
    duolingo = 1105416173
    naclo    = 1088995343
    newdays  = 1211597524

def xtoi(s):
    s = s[1:]
    for (x, i) in zip(data.xsIn, data.ipaOut): s = s.replace(x, i)
    return s

def ordinal(n):
    return '{}{}'.format(n,
            'th' if n//10 % 10 != 0 else
            'st' if n % 10 == 1 else
            'nd' if n % 10 == 2 else
            'rd' if n % 10 == 3 else
            'th')

def getfeed(feed):
    print('getfeed({})'.format(feed))
    text = requests.get(feed).text
    if feed == 'http://www.archr.org/atom.xml':
        text = text.replace(' & ', ' &amp; ')
    text = re.sub(r' xmlns="[^"]+"', '', text)
    return ET.fromstring(text)

def guids(url):
    feed = getfeed(url)
    if feed.tag == 'rss':
        return [x.find('guid').text for x in feed[0].findall('item')]
    else:
        return [x.find('id').text for x in feed.findall('entry')]

def getuotd():
    r = requests.get('https://lichess.org/training/daily')
    return re.search(r'"puzzle":.*?"fen":"([^"]+)', r.text).group(1)

def getreview():
    r = requests.get('https://www.sjsreview.com/?s=')
    return BeautifulSoup(r.text, 'lxml').find('h2').find('a').attrs['href']

def getbda():
    r = requests.get('https://www.voanoticias.com/z/537')
    return BeautifulSoup(r.text, 'lxml').find('div', id='content').find('div', class_='content').find('a').attrs['href']

def getkernel():
    r = requests.get('https://kernel.org/')
    return BeautifulSoup(r.text, 'lxml').find('td', id='latest_link').text.strip()

def getnaclo():
    r = requests.get('http://nacloweb.org/')
    return hashlib.md5(requests.get('http://nacloweb.org/').text.encode('utf-8')).hexdigest()

def chat_id(msg):
    if isinstance(msg, types.Message):
        return msg.to_id.channel_id
    else:
        return msg.chat_id

def usernamify(idtoname):
    return lambda x: '@'+idtoname[x] if x in idtoname else str(x)

langs = {
'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic', 'hy':
'Armenian', 'az': 'Azeerbaijani', 'eu': 'Basque', 'be': 'Belarusian', 'bn':
'Bengali', 'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan', 'ceb':
'Cebuano', 'zh-CN': 'Chinese (Simplified)', 'zh-TW': 'Chinese (Traditional)',
'co': 'Corsican', 'hr': 'Croatian', 'cs': 'Czech', 'da': 'Danish', 'nl':
'Dutch', 'en': 'English', 'eo': 'Esperanto', 'et': 'Estonian', 'fi': 'Finnish',
'fr': 'French', 'fy': 'Frisian', 'gl': 'Galician', 'ka': 'Georgian', 'de':
'German', 'el': 'Greek', 'gu': 'Gujarati', 'ht': 'Haitian Creole', 'ha':
'Hausa', 'haw': 'Hawaiian', 'iw': 'Hebrew', 'hi': 'Hindi', 'hmn': 'Hmong',
'hu': 'Hungarian', 'is': 'Icelandic', 'ig': 'Igbo', 'id': 'Indonesian', 'ga':
'Irish', 'it': 'Italian', 'ja': 'Japanese', 'jw': 'Javanese', 'kn': 'Kannada',
'kk': 'Kazakh', 'km': 'Khmer', 'ko': 'Korean', 'ku': 'Kurdish', 'ky': 'Kyrgyz',
'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian', 'lt': 'Lithuanian', 'lb':
'Luxembourgish', 'mk': 'Macedonian', 'mg': 'Malagasy', 'ms': 'Malay', 'ml':
'Malayalam', 'mt': 'Maltese', 'mi': 'Maori', 'mr': 'Marathi', 'mn':
'Mongolian', 'my': 'Myanmar', 'ne': 'Nepali', 'no': 'Norwegian', 'ny':
'Nyanja', 'ps': 'Pashto', 'fa': 'Persian', 'pl': 'Polish', 'pt': 'Portuguese',
'pa': 'Punjabi', 'ro': 'Romanian', 'ru': 'Russian', 'sm': 'Samoan', 'gd':
'Scots Gaelic', 'sr': 'Serbian', 'st': 'Sesotho', 'sn': 'Shona', 'sd':
'Sindhi', 'si': 'Sinhala', 'sk': 'Slovak', 'sl': 'Slovenian', 'so': 'Somali',
'es': 'Spanish', 'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish', 'tl':
'Tagalog', 'tg': 'Tajik', 'ta': 'Tamil', 'te': 'Telugu', 'th': 'Thai', 'tr':
'Turkish', 'uk': 'Ukrainian', 'ur': 'Urdu', 'uz': 'Uzbek', 'vi': 'Vietnamese',
'cy': 'Welsh', 'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba', 'zu': 'Zulu'
}
def translate(text, tl):
    resp = json.loads(requests.get('https://translate.google.com/translate_a/single', params={
        'client': 'gtx',
        'sl': 'auto',
        'tl': tl,
        'dt': 't',
        'ie': 'UTF-8',
        'oe': 'UTF-8',
        'q': text
        }).text)
    return (resp[0][0][0], resp[2])

class Perm:

    def __init__(self, whitelist, blacklist):
        self.whitelist = whitelist
        self.blacklist = blacklist

    def fmt(self, idtoname):
        return 'whitelist: {}, blacklist: {}'.format(
                ', '.join(map(usernamify(idtoname), self.whitelist)) or '(none)',
                ', '.join(map(usernamify(idtoname), self.blacklist)) or '(none)')

    def check(self, id):
        return (not self.whitelist or id in self.whitelist) and (id not in self.blacklist)

class Bot:

    def __init__(self, client):
        self.client = client
        self.prefix = '!'

        self.commands = {
            'help':        (self.cmd_help,        Perm([], [])),
            'commands':    (self.cmd_commands,    Perm([], [])),
            'prefix':      (self.cmd_prefix,      Perm([admin], [])),
            'getperm':     (self.cmd_getperm,     Perm([], [])),
            'js':          (self.cmd_js,          Perm([], [])),
            'steno':       (self.cmd_steno,       Perm([], [])),
            'expand':      (self.cmd_expand,      Perm([], [])),
            'bash':        (self.cmd_bash,        Perm([], [])),
            'uptime':      (self.cmd_uptime,      Perm([], [])),
            'frink':       (self.cmd_frink,       Perm([], [])),
            'transcribe':  (self.cmd_transcribe,  Perm([], [])),
            'puzzle':      (self.cmd_puzzle,      Perm([], [])),
            'puzhist':     (self.cmd_puzhist,     Perm([], [])),
            'leaderboard': (self.cmd_leaderboard, Perm([], [])),
            'translate':   (self.cmd_translate,   Perm([], [])),
            'flipflop':    (self.cmd_flipflop,    Perm([], [])),
            'flepflap':    (self.cmd_flepflap,    Perm([], [])),
            'soguess':     (self.cmd_soguess,     Perm([], [])),
            'ddg':         (self.cmd_ddg,         Perm([], [])),
            'wpm':         (self.cmd_wpm,         Perm([], [])),
            'Flypflap':    (self.cmd_flypflap,    Perm([], [])),
            'restart':     (self.cmd_restart,     Perm([admin], []))
        }

        self.triggers = [

            (r'(?i)\bwhere (are|r) (you|u|y\'?all)\b|\bwhere (you|u|y\'?all) at\b',
             1,
             lambda _: 'NUMBERS NIGHT CLUB'),

            (r'(?i)mountain|\brock|cluster',
             1,
             lambda _: (random.choice(['aftershock','airlock','air lock','air sock','alarm clock','antiknock','arawak','around the clock','atomic clock','authorized stock','baby talk','bach','balk','ballcock','ball cock','bangkok','bedrock','biological clock','bloc','block','boardwalk','bock','brock','building block','calk','capital stock','catwalk','caudal block','caulk','chalk','chalk talk','chicken hawk','chock','chopping block','cinder block','clock','combination lock','common stock','control stock','crock','crosstalk','crosswalk','cuckoo clock','cylinder block','deadlock','doc','dock','double talk','dry dock','eastern hemlock','electric shock','electroshock','engine block','en bloc','fish hawk','flintlock','floating dock','floc','flock','french chalk','frock','gamecock','gawk','goshawk','grandfather clock','gridlock','growth stock','hammerlock','hawk','haycock','heart block','hemlock','hoc','hock','hollyhock','insulin shock','interlock','iraq','jaywalk','jock','johann sebastian bach','john hancock','john locke','kapok','knock','lady\'s smock','laughingstock','letter stock','line block','livestock','loch','lock','locke','manioc','maroc','marsh hawk','matchlock','medoc','mental block','mock','mohawk','mosquito hawk','nighthawk','nock','o\'clock','oarlock','office block','out of wedlock','overstock','padauk','padlock','peacock','penny stock','pigeon hawk','pillow block','pock','poison hemlock','poppycock','post hoc','preferred stock','restock','roadblock','roc','rock','rolling stock','round the clock','sales talk','sauk','schlock','scotch woodcock','shamrock','shell shock','sherlock','shock','sidewalk','sleepwalk','small talk','smock','snatch block','sock','space walk','sparrow hawk','squawk','stalk','starting block','stock','stumbling block','sweet talk','table talk','take stock','talk','time clock','tomahawk','tower block','treasury stock','turkey cock','unblock','undock','unfrock','unlock','vapor lock','voting stock','walk','war hawk','watered stock','water clock','water hemlock','wedlock','wheel lock','widow\'s walk','wind sock','wok','woodcock','writer\'s block','yellow dock']) + ' ' + random.choice(['adjuster','adjuster','adjustor','blockbuster','bluster','buster','cluster','combustor','custard','duster','filibuster','fluster','ghosebuster','ghostbuster','just her','knuckle duster','lackluster','luster','lustre','mustard','muster','thruster','trust her'])).upper() + ' ' + ''.join(random.choice('˥˦˧˨˩') for _ in range(50))),

            (r'(?i)\bgo\b',
             0.2,
             lambda _: 'lol no generics')

        ]

        self.feeds = dict([x, guids(x)] for x in [
            'http://xkcd.com/rss.xml',
            'http://what-if.xkcd.com/feed.atom',
            'http://www.smbc-comics.com/rss.php',
            'http://feeds.feedburner.com/PoorlyDrawnLines?format=xml',
            'http://www.commitstrip.com/en/feed/',
            'https://mathwithbaddrawings.com/feed/',
            'http://feeds.feedburner.com/InvisibleBread',
            'http://www.archr.org/atom.xml',
            'http://existentialcomics.com/rss.xml',
            'http://feeds.feedburner.com/codinghorror?format=xml',
            'http://thecodelesscode.com/rss',
            'https://lichess.org/blog.atom',
            'http://keyboardfire.com/blog.xml'
            ])

        self.uotd = getuotd()
        self.review = getreview()
        self.bda = getbda()
        self.kernel = getkernel()
        self.naclo = getnaclo()

        self.recog = sr.Recognizer()

        try: self.puztime = eval(open('puztime').read())
        except FileNotFoundError: self.puztime = {}
        try: self.puzhist = eval(open('puzhist').read())
        except FileNotFoundError: self.puzhist = []
        self.puzlevel = len(self.puzhist) + 1

        try: self.nametoid = eval(open('nametoid').read())
        except FileNotFoundError: self.nametoid = {}
        self.idtoname = dict(reversed(x) for x in self.nametoid.items())

        self.starttime = time.time()

        self.frink = subprocess.Popen('java -cp frink.jar:. SFrink'.split(),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        self.soguess = None
        self.quota = '(unknown)'

        self.wpm = dict()

        self.dailied = False

    def cmd_help(self, msg, args):
        '''
        help helps helpfully, a helper helping helpees.
        '''
        if args is None:
            return 'This is @KeyboardFire\'s bot. Type {}commands for a list of commands. Source code: https://github.com/KeyboardFire/kipfa'.format(self.prefix)
        else:
            if args in self.commands:
                return ' '.join(self.commands[args][0].__doc__.format(prefix=self.prefix).split())
            else:
                return 'Unknown command. Type {0}help for general information or {0}help COMMAND for help with a specific command.'.format(self.prefix)

    def cmd_commands(self, msg, args):
        '''
        Lists all of the bot's commands.
        '''
        return ', '.join(sorted(self.commands.keys()))

    def cmd_prefix(self, msg, args):
        '''
        Changes the prefix used to run a bot command.
        '''
        if args:
            self.prefix = args
            return 'Prefix updated.'
        else:
            return 'Please specify a prefix to set.'

    def cmd_getperm(self, msg, args):
        '''
        Displays the current permissions (whitelist and blacklist) for a given
        command.
        '''
        if args in self.commands:
            return 'Permissions for command {}: {}.'.format(
                args,
                self.commands[args][1].fmt(self.idtoname)
                )
        elif args:
            return 'Unknown command {}.'.format(args)
        else:
            return 'Please specify a command name.'

    def cmd_js(self, msg, args):
        '''
        Executes (sandboxed) JavaScript code and returns the value of the last
        expression.
        '''
        return os.popen("""node -e 'var Sandbox = require("./node_modules/sandbox"), s = new Sandbox(); s.options.timeout = 2000; s.run("{}", function(x) {{ console.log(x.result == "TimeoutError" ? "2 second timeout reached." : x.result); }});'""".format(args.replace('\\', '\\\\').replace("'", "'\\''").replace('"', '\\"'))).read()

    def cmd_steno(self, msg, args):
        '''
        Displays the given chord on a steno keyboard.
        '''
        if args is None:
            return 'Please specify a steno string.'
        m = re.search(r'[AO*\-EU]+', args)
        if re.fullmatch(r'S?T?K?P?W?H?R?A?O?\*?-?E?U?F?R?P?B?L?G?T?S?D?Z?', args) and m:
            dups = 'SPTR'
            keyboard.draw_keyboard_to_png(
                    [s+('-' if s in dups else '') for s in args[:m.start()]] +
                    [s for s in m.group() if s != '-'] +
                    [('-' if s in dups else '')+s for s in args[m.end():]],
                    'tmp.png')
            self.reply_photo(msg, 'tmp.png')
            os.remove('tmp.png')
        else:
            return 'Invalid steno.'

    def cmd_expand(self, msg, args):
        '''
        Randomly expands an acronym, e.g. {prefix}expand mfw => mole fluently
        whimpers.
        '''
        args = args.lower()
        if any(not ('a' <= ch <= 'z') for ch in args):
            return 'Letters only please.'
        elif len(args) > 10:
            return 'Maximum of 10 letters allowed.'
        else:
            return ' '.join([os.popen("grep '^{}[a-z]*$' /usr/share/dict/words | shuf -n1".format(ch)).read().strip() for ch in args])

    def cmd_bash(self, msg, args):
        '''
        Gives the highest voted out of 50 random bash.org quotes.
        '''
        # quote = BeautifulSoup(requests.get('http://bash.org/?random1').text, 'html.parser').find('p', class_='qt').text
        quote = max(BeautifulSoup(requests.get('http://bash.org/?random1').text, 'html.parser').find_all('p', class_='quote'), key=lambda x: int(x.font.text)).next_sibling.text
        return '```\n{}\n```'.format(quote)

    def cmd_uptime(self, msg, args):
        '''
        Tells how long the bot has been running since its last restart.
        '''
        return str(datetime.timedelta(seconds=int(time.time() - self.starttime)))

    def cmd_frink(self, msg, args):
        '''
        Executes Frink code (https://frinklang.org/).
        '''
        if args is None:
            return 'Please provide Frink code to run.'
        self.frink.stdin.write(args.encode('utf-8') + b'\n')
        self.frink.stdin.flush()
        r = self.frink.stdout.readline()
        ans = b''
        while True:
            line = self.frink.stdout.readline()
            if line == r: break
            ans += line
        return ans.decode('utf-8')

    def cmd_transcribe(self, msg, args):
        '''
        Transcribes voice messages into text (very poorly) with PocketSphinx.
        '''
        rmsg = self.get_reply(msg)
        if rmsg is None or not hasattr(rmsg, 'media'):
            return 'Please reply to a voice message.'
        media = rmsg.media
        if not isinstance(media, types.MessageMediaDocument):
            return 'Please reply to a voice message.'
        doc = media.document
        if doc.mime_type != 'audio/ogg':
            return 'Please reply to a voice message.'
        if doc.size > 1024 * 200:
            return 'Message too big.'
        fname = '{}_{}_0.jpg'.format(doc.id, doc.access_hash)
        self.client.get_file(doc.dc_id, doc.id, doc.access_hash)
        os.system('ffmpeg -i {} out.wav'.format(fname))
        os.remove(fname)
        with sr.AudioFile('out.wav') as source:
            audio = self.recog.record(source)
        os.remove('out.wav')
        try:
            return self.recog.recognize_sphinx(audio) or '(lambs)'
        except sr.UnknownValueError:
            return '(error)'

    def cmd_puzzle(self, msg, args):
        '''
        Puzzles! See the current puzzle by using this command; you can make one
        guess per hour with {prefix}puzzle [guess]. The puzzles won't require
        any in-depth domain-specific knowledge (but use of the internet is
        encouraged and sometimes required). See also: {prefix}puzhist,
        {prefix}leaderboard.
        '''
        if not args:
            return self.puzdesc()
        if msg.from_id in self.puztime and self.puztime[msg.from_id] > time.time():
            return 'Max one guess per person per hour.'
        if getattr(puzzle, 'guess'+str(self.puzlevel))(args):
            self.puzlevel += 1
            self.puzhist += [msg.from_id]
            open('puzhist', 'w').write(repr(self.puzhist))
            return 'Correct! ' + self.puzdesc()
        else:
            self.puztime[msg.from_id] = time.time() + 60*60
            open('puztime', 'w').write(repr(self.puztime))
            return 'Sorry, that\'s incorrect.'

    def cmd_puzhist(self, msg, args):
        '''
        Returns the list of people in order who have solved the puzzles from
        the {prefix}puzzle command so far.
        '''
        return 'Puzzles solved so far by: ' + \
                ', '.join(map(usernamify(self.idtoname), self.puzhist))

    def cmd_leaderboard(self, msg, args):
        '''
        Generates a sorted leaderboard of how many puzzles from the
        {prefix}puzzle command each person has solved.
        '''
        data = sorted(Counter(map(usernamify(self.idtoname), self.puzhist)).items(), key=lambda x: -x[1])
        maxlen = max(len(x[0]) for x in data)
        return '```\n'+'\n'.join('{:<{}} {}'.format(a, maxlen, b) for a, b in data)+'\n```'

    def cmd_translate(self, msg, args):
        '''
        Translates its argument into English by default; to translate into
        another language, use e.g. {prefix}translate es: This is Spanish.
        '''
        m = re.match(r'([a-z-]*):', args)
        tl = 'en'
        if m:
            tl = m.group(1)
            args = args[args.find(':')+1:]
        (res, sl) = translate(args, tl)
        return '(from {}) {}'.format(langs[sl], res)

    def cmd_flipflop(self, msg, args):
        '''
        Translates from English to another language and back repeatedly until
        reaching a fixed point. Specify a language with e.g. {prefix}flipflop
        ja: A towel is about the most massively useful thing an interstellar
        hitchhiker can have. If no language is specified, a random one will be
        chosen.
        '''
        m = re.match(r'([a-z-]*):', args)
        hist = []
        tl = random.choice(list(langs.keys()))
        if m:
            tl = m.group(1)
            args = args[args.find(':')+1:].strip()
        else:
            hist += ['(chose '+langs[tl]+')']
        if len(args) > 100:
            return "That's too long. Try something shorter please."
        hist += [args]
        while 1:
            (res, sl) = translate(args, tl)
            if res in hist:
                hist += [res]
                break
            hist += [res]
            (res2, sl2) = translate(res, 'en')
            if res2 in hist:
                hist += [res2]
                break
            hist += [res2]
            args = res2
        return '\n'.join(hist)

    def cmd_flepflap(self, msg, args):
        '''
        Translates repeatedly from English to different languages and back for
        a fixed number of iterations. Specify a list of languages with e.g.
        {prefix}flepflap ja es ko: (message), or a number of iterations with
        {prefix}flepflap 3: (message). If neither a list nor a number is given,
        5 iterations will be used by default.
        '''
        m = re.match(r'([0-9a-z- ]*):', args)
        hist = []
        if m is None: m = '5'
        else:
            m = m.group(1)
            args = args[args.find(':')+1:].strip()
        tls = [tl for x in m.split() for tl in (random.sample(list(langs.keys()), int(x)) if x.isdigit() else [x])]
        if len(tls) > 8:
            return "That's too many languages. You may provide a maximum of 8."
        if len(args) > 100:
            return "That's too long. Try something shorter please."
        hist += [args]
        for tl in tls:
            (res, sl) = translate(args, tl)
            hist += ['[{}] {}'.format(tl, res)]
            (res2, sl2) = translate(res, 'en')
            hist += [res2]
            args = res2
        return '\n'.join(hist)

    def cmd_soguess(self, msg, args):
        '''
        Run this command once to get a code snippet from a random answer on
        Stack Overflow. Then guess the tags of the question and run it again to
        see if you were right.
        '''
        if self.soguess is None:
            data = json.loads(requests.get('https://api.stackexchange.com/2.2/answers?page={}&pagesize=100&order=desc&sort=activity&site=stackoverflow&filter=!-.3J6_JIMYrq&key=Oij)9kWgsRogxL0fBwKdCw(('.format(random.randint(100, 1000))).text)
            for item in sorted(data['items'], key=lambda x: -x['score']):
                pre = BeautifulSoup(item['body'], 'html.parser').find('pre')
                if pre is not None and 10 < len(pre.text) < 500:
                    qdata = json.loads(requests.get('https://api.stackexchange.com/2.2/questions/{}?order=desc&sort=activity&site=stackoverflow&filter=!4(YqzWIjDDMcfFBmP&key=Oij)9kWgsRogxL0fBwKdCw(('.format(item['question_id'])).text)
                    self.soguess = qdata['items'][0]['tags']
                    self.quota = qdata['quota_remaining']
                    return 'Guess a tag!\n```\n' + pre.text + '```'
            # somehow no answers matched the criteria
            return 'Something went horribly wrong'
        else:
            resp = 'The correct tags were: ' + ', '.join(self.soguess)
            self.soguess = None
            return resp

    def cmd_ddg(self, msg, args):
        '''
        Returns a link to the first search result on DuckDuckGo for a given
        query.
        '''
        if args is None:
            return 'Please provide a search query.'
        url = 'https://duckduckgo.com/html/?q=' + urllib.parse.quote(args)
        res = BeautifulSoup(requests.get(url).text, 'lxml').find('div', class_='web-result')
        link = urllib.parse.unquote(res.find('a').attrs['href'][15:])
        return link if link else 'No results.'

    def cmd_wpm(self, msg, args):
        '''
        Calculates the WPM starting from when you run this command to the
        moment you send the last message before running the command again.
        '''
        uid = msg.from_id
        if uid in self.wpm:
            (start, end, n) = self.wpm[uid]
            del self.wpm[uid]
            if start == end:
                return "Please type for longer than a second."
            return '{:.3f} WPM'.format(n / ((end - start) / 60.0) / 5)
        else:
            self.wpm[uid] = (msg.date, msg.date, 0)

    def cmd_flypflap(self, msg, args):
        '''
        Flypflap
        '''
        return random.choice(['Go to the top', 'Flip-valve', 'Flytrap'])

    def cmd_restart(self, msg, args):
        '''
        Restarts the bot.
        '''
        self.reply(msg, 'restarting...')
        self.client.stop()
        os._exit(0)

    def checkwebsites(self):
        for url in self.feeds:
            feed = getfeed(url)
            if feed.tag == 'rss':
                for item in feed[0].findall('item'):
                    guid = item.find('guid').text
                    if guid not in self.feeds[url]:
                        self.client.send_message(Chats.haxorz, item.find('link').text)
                        self.feeds[url].append(guid)
            else:
                for item in feed.findall('entry'):
                    guid = item.find('id').text
                    if guid not in self.feeds[url]:
                        self.client.send_message(Chats.haxorz, item.find('link').attrib['href'])
                        self.feeds[url].append(guid)

        newuotd = getuotd()
        if newuotd and self.uotd != newuotd:
            self.uotd = newuotd
            self.client.send_message(Chats.haxorz, 'obtw new uotd\n```\n'+re.sub(r'!', lambda x: '▓░'[x.start()%2], re.sub(r'\d', lambda n: '!'*int(n.group()), self.uotd.split()[0].translate(str.maketrans('kqrbnpKQRBNP/','♔♕♖♗♘♙♚♛♜♝♞♟\n'))))+'\n```')

        newreview = getreview()
        if newreview and self.review != newreview:
            self.review = newreview
            self.client.send_message(Chats.schmett, self.review)

        newbda = getbda()
        if newbda and self.bda != newbda:
            self.bda = newbda
            self.client.send_message(Chats.mariposa, 'https://www.voanoticias.com'+self.bda)

        newkernel = getkernel()
        if newkernel and self.kernel != newkernel:
            self.kernel = newkernel
            self.client.send_message(Chats.haxorz, 'kernel '+self.kernel+' released')

        newnaclo = getnaclo()
        if newnaclo and self.naclo != newnaclo:
            self.naclo = newnaclo
            self.client.send_message(Chats.naclo, '@KeyboardFire it changed')

    def get_reply(self, msg):
        if not hasattr(msg, 'reply_to_msg_id') or msg.reply_to_msg_id is None: return None
        return self.client.send(
                functions.channels.GetMessages(
                    self.client.peers_by_id[msg.to_id.channel_id],
                    [msg.reply_to_msg_id]
                    )
                ).messages[0]

    def reply(self, msg, txt):
        print(txt)
        self.client.send_message(chat_id(msg), txt, reply_to_msg_id=msg.id)

    def reply_photo(self, msg, path):
        print(path)
        self.client.send_photo(chat_id(msg), path#, reply_to_msg_id=msg.id)
                )

    def puzdesc(self):
        return 'Level {}: {}'.format(
                self.puzlevel,
                getattr(puzzle, 'desc'+str(self.puzlevel))
                )

    def process_message(self, msg):
        self.client.forward_messages(Chats.ppnt, msg.to_id.channel_id, [msg.id])
        sid = str(msg.id)
        if len(str(msg.id)) > 3 and ( \
                len(set(sid)) == 1 or \
                list(map(abs, set(map(lambda x: int(x[1])-int(x[0]), zip(sid,sid[1:]))))) == [1] or \
                msg.id % 10000 == 0):
            self.reply(msg, '{} message hype'.format(ordinal(msg.id)))

        txt = msg.message
        if not txt: return

        if msg.to_id.channel_id == Chats.frink:
            self.commands['frink'][0](msg, txt)
            return

        if txt[:len(self.prefix)] == self.prefix:
            if txt[len(self.prefix)] == '|':
                rmsg = self.get_reply(msg)
                buf = rmsg.message if rmsg else ''
                for part in re.split(r'(?<!\\)\|', txt[len(self.prefix)+1:]):
                    cmd, *args = part.split(' ', 1)
                    args = args[0] if len(args) else '{}'
                    if '{}' not in args: args += ' {}'
                    args = args.replace('{}', buf)
                    if cmd in self.commands:
                        (func, perms) = self.commands[cmd]
                        if perms.check(msg.from_id):
                            buf = func(msg, args) or ''
                        else:
                            self.reply(msg, 'You do not have the permission to execute the {} command.'.format(cmd))
                            break
                    else:
                        self.reply(msg, 'The command {} does not exist.'.format(cmd))
                        break
                else:
                    self.reply(msg, buf)
            else:
                cmd, *args = txt[len(self.prefix):].split(' ', 1)
                args = args[0] if len(args) else None
                if cmd in self.commands:
                    (func, perms) = self.commands[cmd]
                    if perms.check(msg.from_id):
                        resp = func(msg, args)
                        if resp: self.reply(msg, resp)
                    else:
                        self.reply(msg, 'You do not have the permission to execute that command.')
        elif msg.from_id in self.wpm:
            (start, end, n) = self.wpm[msg.from_id]
            n += len(msg.message) + 1
            self.wpm[msg.from_id] = (start, msg.date, n)

        if txt == '!!debug' and msg.from_id == admin:
            print(repr(vars(self)))
        elif txt == '!!updateusers' and msg.from_id == admin:
            self.nametoid = {**self.nametoid, **dict(map(lambda u: [u.username, u.id], self.client.send(
                functions.channels.GetParticipants(
                    self.client.peers_by_id[msg.to_id.channel_id],
                    types.ChannelParticipantsRecent(),
                    0, 0, 0
                    )
                ).users))}
            open('nametoid', 'w').write(repr(self.nametoid))
            self.idtoname = dict(reversed(x) for x in self.nametoid.items())
            self.reply(msg, 'updated {} users'.format(len(self.nametoid)))
        elif txt == '!!quota' and msg.from_id == admin:
            self.reply(msg, str(self.quota))
        elif txt == '!!daily' and msg.from_id == admin:
            self.daily()

        matches = re.findall(r'\bx/[^/]*/|\bx\[[^]]*\]', txt)
        if matches:
            self.reply(msg, '\n'.join(map(xtoi, matches)))

        if txt[0] == '$' and txt[-1] == '$' and len(txt) > 2:
            r = requests.get('https://latex.codecogs.com/png.latex?'+txt[1:-1], stream=True)
            with open('tex.png', 'wb') as f: shutil.copyfileobj(r.raw, f)
            self.reply_photo(msg, 'tex.png')
            os.remove('tex.png')

        for (pat, prob, resp) in self.triggers:
            if re.search(pat, txt) and random.random() < prob:
                self.reply(msg, resp(txt))

    def callback(self, update):
        if isinstance(update, types.Update):
            for u in update.updates: self.callback(u)
        elif isinstance(update, types.UpdateNewChannelMessage):
            msg = update.message
            print(msg)
            self.process_message(msg)
        elif isinstance(update, types.UpdateEditChannelMessage):
            msg = update.message
            print(msg)
            self.client.forward_messages(Chats.ppnt, msg.to_id.channel_id, [msg.id])
        elif isinstance(update, types.UpdateShortChatMessage):
            print(update)
            self.process_message(update)

    def daily(self):
        pass
        #text = open('messages.txt').readlines()[datetime.date.today().toordinal()-736764].strip()
        #self.client.send_message(Chats.schmett, text)
        #self.client.send_message(Chats.haxorz, text)
        #self.client.send_message(Chats.duolingo, text)

client = Client('meemerino')
bot = Bot(client)
client.set_update_handler(bot.callback)
client.start()
client.send_message(Chats.testing, 'bot started')

tick = 0
while True:
    tick += 1
    try:
        time.sleep(1)
        lt = time.localtime()
        if lt.tm_hour == 20 and lt.tm_min == 0:
            if not bot.dailied:
                bot.daily()
                bot.dailied = True
        else:
            bot.dailied = False
        if tick % 300 == 0:
            thread = Thread(target=bot.checkwebsites)
            thread.start()
    except KeyboardInterrupt:
        break
