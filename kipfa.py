#!/usr/bin/python3

from collections import Counter
from threading import Thread
import datetime
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time

from pyrogram import Client
from pyrogram.api import types, functions

import speech_recognition as sr

import requests
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
    schmett  = 1032618176
    testing  = 1178303268

def xtoi(s):
    s = s[1:]
    for (x, i) in zip(data.xsIn, data.ipaOut): s = s.replace(x, i)
    return s

def getuotd():
    r = requests.get('https://lichess.org/training/daily')
    return r.text[r.text.find('og:title')+33:].split()[0]

def getreview():
    r = requests.get('https://www.sjsreview.com/?s=')
    return BeautifulSoup(r.text, 'lxml').find('h2').find('a').attrs['href']

def getbda():
    r = requests.get('https://www.voanoticias.com/z/537')
    return BeautifulSoup(r.text, 'lxml').find('div', id='content').find('div', class_='content').find('a').attrs['href']

def getxkcd():
    r = requests.get('https://xkcd.com/')
    img = BeautifulSoup(r.text, 'lxml').find('div', id='comic').find('img')
    return (img.attrs['src'], img.attrs['title'])

def getkernel():
    r = requests.get('https://kernel.org/')
    return BeautifulSoup(r.text, 'lxml').find('td', id='latest_link').text.strip()

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
            'soguess':     (self.cmd_soguess,     Perm([], [])),
            'restart':     (self.cmd_restart,     Perm([admin], []))
        }
        self.uotd = getuotd()
        self.review = getreview()
        self.bda = getbda()
        self.xkcd = getxkcd()
        self.kernel = getkernel()
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
        self.frink = subprocess.Popen('java -cp frink.jar:. SFrink'.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.soguess = None
        self.quota = '(unknown)'

    def cmd_help(self, msg, args):
        '''
        help helps helpfully, a helper helping helpees.
        '''
        if args is None:
            self.reply(msg, 'This is @KeyboardFire\'s bot. Type {}commands for a list of commands. Source code: https://github.com/KeyboardFire/kipfa'.format(self.prefix))
        else:
            if args in self.commands:
                self.reply(msg, ' '.join(self.commands[args][0].__doc__.format(prefix=self.prefix).split()))
            else:
                self.reply(msg, 'Unknown command. Type {0}help for general information or {0}help COMMAND for help with a specific command.'.format(self.prefix))

    def cmd_commands(self, msg, args):
        '''
        Lists all of the bot's commands.
        '''
        self.reply(msg, ', '.join(self.commands.keys()))

    def cmd_prefix(self, msg, args):
        '''
        Changes the prefix used to run a bot command.
        '''
        if args:
            self.prefix = args
            self.reply(msg, 'Prefix updated.')
        else:
            self.reply(msg, 'Please specify a prefix to set.')

    def cmd_getperm(self, msg, args):
        '''
        Displays the current permissions (whitelist and blacklist) for a given
        command.
        '''
        if args in self.commands:
            self.reply(msg, 'Permissions for command {}: {}.'.format(
                args,
                self.commands[args][1].fmt(self.idtoname)
                ))
        elif args:
            self.reply(msg, 'Unknown command {}.'.format(args))
        else:
            self.reply(msg, 'Please specify a command name.')

    def cmd_js(self, msg, args):
        '''
        Executes (sandboxed) JavaScript code and returns the value of the last
        expression.
        '''
        self.reply(msg, os.popen("""node -e 'var Sandbox = require("./node_modules/sandbox"), s = new Sandbox(); s.options.timeout = 2000; s.run("{}", function(x) {{ console.log(x.result == "TimeoutError" ? "2 second timeout reached." : x.result); }});'""".format(args.replace('\\', '\\\\').replace("'", "'\\''").replace('"', '\\"'))).read())

    def cmd_steno(self, msg, args):
        '''
        Displays the given chord on a steno keyboard.
        '''
        if args is None:
            self.reply(msg, 'Please specify a steno string.')
            return
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
            self.reply(msg, 'Invalid steno.')

    def cmd_expand(self, msg, args):
        '''
        Randomly expands an acronym, e.g. {prefix}expand mfw => mole fluently
        whimpers.
        '''
        args = args.lower()
        if any(not ch.islower() for ch in args):
            self.reply(msg, 'Letters only please.')
        elif len(args) > 10:
            self.reply(msg, 'Maximum of 10 letters allowed.')
        else:
            self.reply(msg, ' '.join([os.popen("grep '^{}[a-z]*$' /usr/share/dict/words | shuf -n1".format(ch)).read().strip() for ch in args]))

    def cmd_bash(self, msg, args):
        '''
        Gives the highest voted out of 50 random bash.org quotes.
        '''
        # quote = BeautifulSoup(requests.get('http://bash.org/?random1').text, 'html.parser').find('p', class_='qt').text
        quote = max(BeautifulSoup(requests.get('http://bash.org/?random1').text, 'html.parser').find_all('p', class_='quote'), key=lambda x: int(x.font.text)).next_sibling.text
        self.reply(msg, '```\n{}\n```'.format(quote))

    def cmd_uptime(self, msg, args):
        '''
        Tells how long the bot has been running since its last restart.
        '''
        self.reply(msg, str(datetime.timedelta(seconds=int(time.time() - self.starttime))))

    def cmd_frink(self, msg, args):
        '''
        Executes Frink code (https://frinklang.org/).
        '''
        if args is None:
            self.reply(msg, 'Please provide Frink code to run.')
        else:
            self.frink.stdin.write(args.encode('utf-8') + b'\n')
            self.frink.stdin.flush()
            r = self.frink.stdout.readline()
            ans = b''
            while True:
                line = self.frink.stdout.readline()
                if line == r: break
                ans += line
            self.reply(msg, ans.decode('utf-8'))

    def cmd_transcribe(self, msg, args):
        '''
        Transcribes voice messages into text (very poorly) with PocketSphinx.
        '''
        rmsg = self.get_reply(msg)
        if rmsg is None or not hasattr(rmsg, 'media'):
            self.reply(msg, 'Please reply to a voice message.')
            return
        media = rmsg.media
        if not isinstance(media, types.MessageMediaDocument):
            self.reply(msg, 'Please reply to a voice message.')
            return
        doc = media.document
        if doc.mime_type != 'audio/ogg':
            self.reply(msg, 'Please reply to a voice message.')
            return
        if doc.size > 1024 * 200:
            self.reply(msg, 'Message too big.')
            return
        fname = '{}_{}_0.jpg'.format(doc.id, doc.access_hash)
        self.client.get_file(doc.dc_id, doc.id, doc.access_hash)
        os.system('ffmpeg -i {} out.wav'.format(fname))
        os.remove(fname)
        with sr.AudioFile('out.wav') as source:
            audio = self.recog.record(source)
        os.remove('out.wav')
        try:
            self.reply(msg, self.recog.recognize_sphinx(audio) or '(lambs)')
        except sr.UnknownValueError:
            self.reply(msg, '(error)')

    def cmd_puzzle(self, msg, args):
        '''
        Puzzles! See the current puzzle by using this command; you can make one
        guess per hour with {prefix}puzzle [guess]. The puzzles won't require
        any in-depth domain-specific knowledge (but use of the internet is
        encouraged and sometimes required). See also: {prefix}puzhist,
        {prefix}leaderboard.
        '''
        if not args:
            self.reply(msg, self.puzdesc())
            return
        if msg.from_id in self.puztime and self.puztime[msg.from_id] > time.time():
            self.reply(msg, 'Max one guess per person per hour.')
            return
        if getattr(puzzle, 'guess'+str(self.puzlevel))(args):
            self.puzlevel += 1
            self.puzhist += [msg.from_id]
            open('puzhist', 'w').write(repr(self.puzhist))
            self.reply(msg, 'Correct! ' + self.puzdesc())
        else:
            self.puztime[msg.from_id] = time.time() + 60*60
            open('puztime', 'w').write(repr(self.puztime))
            self.reply(msg, 'Sorry, that\'s incorrect.')

    def cmd_puzhist(self, msg, args):
        '''
        Returns the list of people in order who have solved the puzzles from
        the {prefix}puzzle command so far.
        '''
        self.reply(msg, 'Puzzles solved so far by: ' +
                ', '.join(map(usernamify(self.idtoname), self.puzhist)))

    def cmd_leaderboard(self, msg, args):
        '''
        Generates a sorted leaderboard of how many puzzles from the
        {prefix}puzzle command each person has solved.
        '''
        data = sorted(Counter(map(usernamify(self.idtoname), self.puzhist)).items(), key=lambda x: -x[1])
        maxlen = max(len(x[0]) for x in data)
        self.reply(msg, '```\n'+'\n'.join('{:<{}} {}'.format(a, maxlen, b) for a, b in data)+'\n```')

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
        self.reply(msg, '(from {}) {}'.format(langs[sl], res))

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
            self.reply(msg, "That's too long. Try something shorter please.")
            return
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
        self.reply(msg, '\n'.join(hist))

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
                    self.reply(msg, 'Guess a tag!\n```\n' + pre.text + '```')
                    qdata = json.loads(requests.get('https://api.stackexchange.com/2.2/questions/{}?order=desc&sort=activity&site=stackoverflow&filter=!4(YqzWIjDDMcfFBmP&key=Oij)9kWgsRogxL0fBwKdCw(('.format(item['question_id'])).text)
                    self.soguess = qdata['items'][0]['tags']
                    self.quota = qdata['quota_remaining']
                    break
            else:
                # somehow no answers matched the criteria
                self.reply(msg, 'Something went horribly wrong')
        else:
            self.reply(msg, 'The correct tags were: ' + ', '.join(self.soguess))
            self.soguess = None

    def cmd_restart(self, msg, args):
        '''
        Restarts the bot.
        '''
        self.reply(msg, 'restarting...')
        self.client.stop()
        os._exit(0)

    def checkwebsites(self):
        newuotd = getuotd()
        if newuotd.isdecimal() and self.uotd != newuotd:
            self.uotd = newuotd
            self.client.send_message(Chats.haxorz, 'obtw new uotd')

        newreview = getreview()
        if newreview and self.review != newreview:
            self.review = newreview
            self.client.send_message(Chats.schmett, self.review)

        newbda = getbda()
        if newbda and self.bda != newbda:
            self.bda = newbda
            self.client.send_message(Chats.mariposa, 'https://www.voanoticias.com'+self.bda)

        newxkcd = getxkcd()
        if newxkcd[0] and self.xkcd[0] != newxkcd[0]:
            self.xkcd = newxkcd
            r = requests.get('http:' + newxkcd[0], stream=True)
            with open('xkcd.png', 'wb') as f: shutil.copyfileobj(r.raw, f)
            self.client.send_photo(Chats.haxorz, 'xkcd.png', self.xkcd[1])
            os.remove('xkcd.png')

        newkernel = getkernel()
        if newkernel and self.kernel != newkernel:
            self.kernel = newkernel
            self.client.send_message(Chats.haxorz, 'kernel '+self.kernel+' released')

    def get_reply(self, msg):
        if not hasattr(msg, 'reply_to_msg_id'): return None
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
        txt = msg.message
        if not txt: return

        if msg.to_id.channel_id == Chats.frink:
            self.commands['frink'][0](msg, txt)
            return

        if txt[:len(self.prefix)] == self.prefix:
            cmd, *args = txt[len(self.prefix):].split(' ', 1)
            args = args[0] if len(args) else None
            if cmd in self.commands:
                (func, perms) = self.commands[cmd]
                if perms.check(msg.from_id):
                    func(msg, args)
                else:
                    self.reply(msg, 'You do not have the permission to execute that command.')

        if txt == '!!debug' and msg.from_id == admin:
            debug = dict(vars(self))
            del debug['commands']
            del debug['idtoname']
            self.reply(msg, repr(debug))
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

        matches = re.findall(r'\bx/[^/]*/|\bx\[[^]]*\]', txt)
        if matches:
            self.reply(msg, '\n'.join(map(xtoi, matches)))

        if re.search(r'\bwhere (are|r) (you|u|y\'?all)\b', txt.lower()):
            self.reply(msg, 'NUMBERS NIGHT CLUB')

        if re.search(r'mountain|\brock|cluster', txt.lower()):
            self.reply(msg, (random.choice(['aftershock','airlock','air lock','air sock','alarm clock','antiknock','arawak','around the clock','atomic clock','authorized stock','baby talk','bach','balk','ballcock','ball cock','bangkok','bedrock','biological clock','bloc','block','boardwalk','bock','brock','building block','calk','capital stock','catwalk','caudal block','caulk','chalk','chalk talk','chicken hawk','chock','chopping block','cinder block','clock','combination lock','common stock','control stock','crock','crosstalk','crosswalk','cuckoo clock','cylinder block','deadlock','doc','dock','double talk','dry dock','eastern hemlock','electric shock','electroshock','engine block','en bloc','fish hawk','flintlock','floating dock','floc','flock','french chalk','frock','gamecock','gawk','goshawk','grandfather clock','gridlock','growth stock','hammerlock','hawk','haycock','heart block','hemlock','hoc','hock','hollyhock','insulin shock','interlock','iraq','jaywalk','jock','johann sebastian bach','john hancock','john locke','kapok','knock','lady\'s smock','laughingstock','letter stock','line block','livestock','loch','lock','locke','manioc','maroc','marsh hawk','matchlock','medoc','mental block','mock','mohawk','mosquito hawk','nighthawk','nock','o\'clock','oarlock','office block','out of wedlock','overstock','padauk','padlock','peacock','penny stock','pigeon hawk','pillow block','pock','poison hemlock','poppycock','post hoc','preferred stock','restock','roadblock','roc','rock','rolling stock','round the clock','sales talk','sauk','schlock','scotch woodcock','shamrock','shell shock','sherlock','shock','sidewalk','sleepwalk','small talk','smock','snatch block','sock','space walk','sparrow hawk','squawk','stalk','starting block','stock','stumbling block','sweet talk','table talk','take stock','talk','time clock','tomahawk','tower block','treasury stock','turkey cock','unblock','undock','unfrock','unlock','vapor lock','voting stock','walk','war hawk','watered stock','water clock','water hemlock','wedlock','wheel lock','widow\'s walk','wind sock','wok','woodcock','writer\'s block','yellow dock']) + ' ' + random.choice(['adjuster','adjuster','adjustor','blockbuster','bluster','buster','cluster','combustor','custard','duster','filibuster','fluster','ghosebuster','ghostbuster','just her','knuckle duster','lackluster','luster','lustre','mustard','muster','thruster','trust her'])).upper())

    def callback(self, update):
        if isinstance(update, types.Update):
            for u in update.updates: self.callback(u)
        elif isinstance(update, types.UpdateNewChannelMessage):
            msg = update.message
            print(msg)
            self.process_message(msg)
        elif isinstance(update, types.UpdateShortChatMessage):
            print(update)
            self.process_message(update)

client = Client('meemerino')
bot = Bot(client)
client.set_update_handler(bot.callback)
client.start()
client.send_message(Chats.testing, 'bot started')

while True:
    try:
        time.sleep(5 * 60)
        thread = Thread(target=bot.checkwebsites)
        thread.start()
    except KeyboardInterrupt:
        break
