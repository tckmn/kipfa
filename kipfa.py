#!/usr/bin/python3

from collections import Counter
from threading import Thread
import datetime
import os
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
    apspanish = 1123178155
    haxorz    = 1059322065
    schmett   = 1032618176
    testing   = 1178303268

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

def chat_id(msg):
    if isinstance(msg, types.Message):
        return msg.to_id.channel_id
    else:
        return msg.chat_id

def usernamify(idtoname):
    return lambda x: '@'+idtoname[x] if x in idtoname else str(x)

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
            'restart':     (self.cmd_restart,     Perm([admin], []))
        }
        self.uotd = getuotd()
        self.review = getreview()
        self.bda = getbda()
        self.xkcd = getxkcd()
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

    def cmd_help(self, msg, args):
        self.reply(msg, 'This is @KeyboardFire\'s bot. Type {}commands for a list of commands. Source code: https://github.com/KeyboardFire/kipfa'.format(self.prefix))

    def cmd_commands(self, msg, args):
        self.reply(msg, ', '.join(self.commands.keys()))

    def cmd_prefix(self, msg, args):
        if args:
            self.prefix = args
            self.reply(msg, 'Prefix updated.')
        else:
            self.reply(msg, 'Please specify a prefix to set.')

    def cmd_getperm(self, msg, args):
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
        self.reply(msg, os.popen("""node -e 'var Sandbox = require("./node_modules/sandbox"), s = new Sandbox(); s.options.timeout = 2000; s.run("{}", function(x) {{ console.log(x.result == "TimeoutError" ? "2 second timeout reached." : x.result); }});'""".format(args.replace('\\', '\\\\').replace("'", "'\\''").replace('"', '\\"'))).read())

    def cmd_steno(self, msg, args):
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
        args = args.lower()
        if any(not ch.islower() for ch in args):
            self.reply(msg, 'Letters only please.')
        elif len(args) > 10:
            self.reply(msg, 'Maximum of 10 letters allowed.')
        else:
            self.reply(msg, ' '.join([os.popen("grep '^{}[a-z]*$' /usr/share/dict/words | shuf -n1".format(ch)).read().strip() for ch in args]))

    def cmd_bash(self, msg, args):
        # quote = BeautifulSoup(requests.get('http://bash.org/?random1').text, 'html.parser').find('p', class_='qt').text
        quote = max(BeautifulSoup(requests.get('http://bash.org/?random1').text, 'html.parser').find_all('p', class_='quote'), key=lambda x: int(x.font.text)).next_sibling.text
        self.reply(msg, '```\n{}\n```'.format(quote))

    def cmd_uptime(self, msg, args):
        self.reply(msg, str(datetime.timedelta(seconds=int(time.time() - self.starttime))))

    def cmd_frink(self, msg, args):
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
        self.reply(msg, 'Puzzles solved so far by: ' +
                ', '.join(map(usernamify(self.idtoname), self.puzhist)))

    def cmd_leaderboard(self, msg, args):
        data = sorted(Counter(map(usernamify(self.idtoname), self.puzhist)).items(), key=lambda x: -x[1])
        maxlen = max(len(x[0]) for x in data)
        self.reply(msg, '```\n'+'\n'.join('{:<{}} {}'.format(a, maxlen, b) for a, b in data)+'\n```')

    def cmd_restart(self, msg, args):
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
            self.client.send_message(Chats.apspanish, 'https://www.voanoticias.com'+self.bda)

        newxkcd = getxkcd()
        if newxkcd[0] and self.xkcd[0] != newxkcd[0]:
            self.xkcd = newxkcd
            r = requests.get('http:' + newxkcd[0], stream=True)
            with open('xkcd.png', 'wb') as f: shutil.copyfileobj(r.raw, f)
            self.client.send_photo(Chats.haxorz, 'xkcd.png', self.xkcd[1])
            os.remove('xkcd.png')

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

        matches = re.findall(r'\bx/[^/]*/|\bx\[[^]]*\]', txt)
        if matches:
            self.reply(msg, '\n'.join(map(xtoi, matches)))

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
