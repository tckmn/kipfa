import datetime
import json
import os
import random
import re
import shutil
import subprocess
import time

# pyrogram
from pyrogram import InputMediaPhoto

# pocketsphinx
import speech_recognition as sr

# network
import requests

# local modules
from util import *
import admin
import commands
import data
import parse
import puzzle
import zendo

def xtoi(s):
    s = s[1:]
    for (x, i) in zip(data.xsIn, data.ipaOut): s = s.replace(x, i)
    return s

def ordinal(n):
    return '{}{}'.format(n,
            'th' if n//10 % 10 == 1 else
            'st' if n % 10 == 1 else
            'nd' if n % 10 == 2 else
            'rd' if n % 10 == 3 else
            'th')

class Bot:

    def __init__(self, client):
        self.client = client
        with connect() as conn: conn.executescript(data.schema)

        self.chain = dict()
        self.dailies = []
        self.extprefix = '!!'
        self.frink = subprocess.Popen('java -cp tools/frink/frink.jar:tools/frink SFrink'.split(),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.no_meems = []
        self.no_tools = []
        self.prefix = '!'
        self.quota = '(unknown)'
        self.ratelimit = {}
        self.recog = sr.Recognizer()
        self.seguess = None
        self.soguess = None
        self.starttime = time.time()
        self.tgguess = None
        self.tioerr = ''
        self.wpm = dict()
        self.wump = None

    def checkwebsites(self):
        if hasattr(self, 'feeds'):
            for feed in self.feeds:
                for msg in feed.go():
                    for room in feed.rooms: client.send_message(room, msg)
        else:
            client.send_message(Chats.testing, 'WARNING: feeds not initialized @'+admin.username)
            self.feeds = []

    def check_chain(self, msg, threshold=3):
        chat = msg.chat.id
        if chat not in self.chain: self.chain[chat] = []

        # add message to backlog
        rmsg = self.get_reply(msg)
        rmsg = rmsg.message_id if rmsg else -1
        self.chain[chat].append({'txt': msg.text or msg.caption, 'reply': rmsg, 'user': msg.from_user.id})
        txt = [x['txt'] for x in self.chain[chat]]

        # test for "what what"
        if len(self.chain[chat]) > 1 and txt[-1] == 'what' == txt[-2] and \
                self.chain[chat][-2]['user'] != msg.from_user.id:
            return ('in the', -1)

        # check to see if a chain can be made
        if len(self.chain[chat]) < threshold: return
        self.chain[chat] = self.chain[chat][-threshold:]
        if any(x['reply'] != rmsg for x in self.chain[chat]): return
        # if len(set(x['user'] for x in self.chain[chat])) != len(self.chain[chat]): return
        if len(set(x['user'] for x in self.chain[chat])) != threshold: return
        txt = [x['txt'] for x in self.chain[chat]]

        # test for simple repetition with optional prefix/suffix
        if txt[-2] in txt[-1]:
            start = txt[-1].index(txt[-2])
            prefix = txt[-1][:start]
            suffix = txt[-1][start + len(txt[-2]):]
            if all(prefix+a+suffix == b for (a,b) in zip(txt, txt[1:])):
                return (prefix+txt[-1]+suffix, rmsg)

        # test for permutation
        if len(txt[-1]) > 2 and len(set(txt)) == len(txt) and \
                all(sorted(x) == sorted(txt[-1]) for x in txt[:-1]):
            thing = txt[-1]
            while thing in txt:
                thing = ''.join(random.sample(txt[-1], len(txt[-1])))
            return (thing, rmsg)

        # test for increasing capitalization or character
        if len(txt[-2]) == len(txt[-1]):
            pairs = [(a,b) for (a,b) in zip(txt[-2], txt[-1]) if a != b]
            pos = [i for (x,y) in [(-3,-2),(-2,-1)]
                     for (i,(a,b)) in enumerate(zip(txt[x],txt[y]))
                     if a != b]
            if len(pairs) == 1 and len(pos) == 2:
                delta = ord(pairs[0][1]) - ord(pairs[0][0])
                idelta = pos[1] - pos[0]
                if all(0<=n<len(a) and (a[:n] + chr(ord(a[n])+delta) + a[n+1:] == b)
                        for (i,(a,b)) in enumerate(zip(txt, txt[1:]))
                        for n in [pos[1]-(len(txt)-2-i)*idelta]):
                    (t, n) = (txt[-1], pos[1]+idelta)
                    if 0<=n<len(t): return (t[:n] + chr(ord(t[n])+delta) + t[n+1:], rmsg)

    def get_reply(self, msg):
        return msg.reply_to_message if hasattr(msg, 'reply_to_message') else None

    def reply(self, msg, txt, reply_msg=None):
        print(txt)
        txt = txt.strip()
        if not txt: txt = '[reply empty]'
        if len(txt) > 1048576:
            self.reply(msg, '[reply >1MB]', reply_msg)
        elif len(txt) > 4096:
            fname = '/tmp/r' + str(random.random())[2:7] + '.txt'
            with open(fname, 'w') as f: f.write(txt)
            self.client.send_document(msg.chat.id, fname, reply_to_message_id=reply_msg or msg.message_id)
            os.remove(fname)
        else:
            self.client.send_message(msg.chat.id, txt, reply_to_message_id=reply_msg or msg.message_id)

    def reply_photo(self, msg, path):
        print(path)
        self.client.send_photo(msg.chat.id, path, reply_to_message_id=msg.message_id)

    def process_message(self, msg):
        if msg.from_user.id == 777000 and msg.text and msg.text[:10] == 'Login code': return

        # log
        self.client.forward_messages(Chats.ppnt, msg.chat.id, [msg.message_id])
        if msg.edit_date: return

        # check for notable message count
        sid = str(msg.message_id)
        if msg.chat.id not in self.no_meems and \
                len(str(msg.message_id)) > 3 and ( \
                len(set(sid)) == 1 or \
                list(map(abs, set(map(lambda x: int(x[1])-int(x[0]), zip(sid,sid[1:]))))) == [1] or \
                msg.message_id % 10000 == 0):
            self.reply(msg, '{} message hype'.format(ordinal(msg.message_id)))

        txt = msg.text
        if not txt: return

        # frink
        if msg.chat.id == Chats.frink:
            self.reply(msg, commands.cmd_frink(self, msg, txt, ''))
            return

        # zendo
        if msg.chat.id == Chats.zendo and msg.from_user.id != admin.userid:
            ans = zendo.test(txt)
            if ans is not None: self.reply(msg, str(ans), reply_msg=-1)

        # chains
        chain = self.check_chain(msg)
        if msg.chat.id not in self.no_meems and chain:
            self.reply(msg, chain[0], reply_msg=chain[1])
            self.chain[msg.chat.id] = []

        # command processing
        is_cmd = txt[:len(self.prefix)] == self.prefix
        is_ext = txt[:len(self.extprefix)] == self.extprefix
        if is_cmd or is_ext:
            rmsg = self.get_reply(msg)
            buf = (rmsg.text or rmsg.caption) if rmsg else ''
            idx = len(self.extprefix) if is_ext else len(self.prefix)
            resp = parse.parse(self, txt[idx:], buf, msg, is_ext)
            if resp is not None: self.reply(msg, resp)

        # wpm
        elif msg.from_user.id in self.wpm:
            (start, end, n) = self.wpm[msg.from_user.id]
            n += len(msg.text) + 1
            self.wpm[msg.from_user.id] = (start, msg.date, n)

        # admin command processing
        if txt[:len(admin.prefix)] == admin.prefix and msg.from_user.id == admin.userid:
            cmd, *args = txt[len(admin.prefix):].split(' ', 1)
            cmd = 'cmd_' + cmd
            args = (args or [None])[0]
            if hasattr(admin, cmd): self.reply(msg, getattr(admin, cmd)(self, args) or 'done')
            else: self.reply(msg, 'Unknown admin command.')

        if msg.chat.id not in self.no_tools:

            # X-SAMPA to IPA
            matches = re.findall(r'\bx/[^/]*/|\bx\[[^]]*\]', txt)
            if matches:
                self.reply(msg, '\n'.join(map(xtoi, matches)))

            # latex to image
            latexes = [x for x in txt.split('$')[1:-1:2] if x]
            dirs = ['l{}'.format(random.random()) for _ in latexes]
            for (l, d) in zip(latexes, dirs): latex(l, d)
            good = [d+'/a.png' for d in dirs if os.path.exists(d+'/a.png')]
            if len(good) == 1:
                self.reply_photo(msg, good[0])
            elif 2 <= len(good) <= 10:
                self.client.send_media_group(msg.chat.id, [
                    InputMediaPhoto(x) for x in good
                    ], reply_to_message_id=msg.message_id)
            elif 10 < len(good):
                self.reply(msg, '[too many latexes]')
            for d in dirs: shutil.rmtree(d)

        # check triggers
        if msg.chat.id not in self.no_meems:
            for (pat, prob, mention, resp) in data.triggers:
                if re.search(pat, txt) and random.random() < prob and (msg.mentioned or not mention):
                    self.reply(msg, resp(txt))

    def callback(self, client, update):
        print(update)
        self.process_message(update)

    def tick(self):
        # dailies
        lt = time.localtime()
        for d in dailies:
            dailyid, hour, minute, msg, chat, dailied = d
            if lt.tm_hour == hour and lt.tm_min == minute:
                if not dailied:
                    self.client.send_message(chat, msg)
                    d[-1] = True
            else: d[-1] = False

        # rate limiting cooldowns
        for u in self.ratelimit:
            if self.ratelimit[u] > 0: self.ratelimit[u] -= 1
