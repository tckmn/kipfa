import datetime
import json
import os
import random
import re
import shutil
import subprocess
import time

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
        self.dailied = False
        self.extprefix = '!!'
        self.frink = subprocess.Popen('java -cp tools/frink/frink.jar:tools/frink SFrink'.split(),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.prefix = '!'
        self.quota = '(unknown)'
        self.recog = sr.Recognizer()
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
        self.chain[chat].append({'txt': msg.text, 'reply': rmsg, 'user': msg.from_user.id})
        txt = [x['txt'] for x in self.chain[chat]]

        # test for permutation
        if len(self.chain[chat]) > 1 and len(txt[-1]) > 2 and \
                self.chain[chat][-2]['reply'] == rmsg and \
                self.chain[chat][-2]['user'] != msg.from_user.id and \
                txt[-2] != txt[-1] and sorted(txt[-2]) == sorted(txt[-1]):
            thing = txt[-1]
            while thing == txt[-2] or thing == txt[-1]:
                thing = ''.join(random.sample(txt[-1], len(txt[-1])))
            return (thing, rmsg)

        # check to see if a chain can be made
        if len(self.chain[chat]) < threshold: return
        self.chain[chat] = self.chain[chat][-threshold:]
        if any(x['reply'] != rmsg for x in self.chain[chat]): return
        # if len(set(x['user'] for x in self.chain[chat])) != len(self.chain[chat]): return
        if len(set(x['user'] for x in self.chain[chat])) == 1: return
        txt = [x['txt'] for x in self.chain[chat]]

        # test for simple repetition with optional prefix/suffix
        if txt[-2] in txt[-1]:
            start = txt[-1].index(txt[-2])
            prefix = txt[-1][:start]
            suffix = txt[-1][start + len(txt[-2]):]
            if all(prefix+a+suffix == b for (a,b) in zip(txt, txt[1:])):
                return (prefix+txt[-1]+suffix, rmsg)

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
        if len(txt) > 4096: txt = '[reply too long]'
        self.client.send_message(msg.chat.id, txt, reply_to_message_id=reply_msg or msg.message_id)

    def reply_photo(self, msg, path):
        print(path)
        self.client.send_photo(msg.chat.id, path, reply_to_message_id=msg.message_id)

    def process_message(self, msg):
        self.client.forward_messages(Chats.ppnt, msg.chat.id, [msg.message_id])
        if msg.edit_date: return

        sid = str(msg.message_id)
        if len(str(msg.message_id)) > 3 and ( \
                len(set(sid)) == 1 or \
                list(map(abs, set(map(lambda x: int(x[1])-int(x[0]), zip(sid,sid[1:]))))) == [1] or \
                msg.message_id % 10000 == 0):
            self.reply(msg, '{} message hype'.format(ordinal(msg.message_id)))

        txt = msg.text
        if not txt: return

        if msg.chat.id == Chats.frink:
            self.reply(msg, commands.frink(self, msg, txt, ''))
            return

        chain = self.check_chain(msg)
        if chain:
            self.reply(msg, chain[0], reply_msg=chain[1])
            self.chain[msg.chat.id] = []

        is_cmd = txt[:len(self.prefix)] == self.prefix
        is_ext = txt[:len(self.extprefix)] == self.extprefix
        if is_cmd or is_ext:
            rmsg = self.get_reply(msg)
            buf = rmsg.text if rmsg else ''
            idx = len(self.extprefix) if is_ext else len(self.prefix)
            self.reply(msg, parse.parse(self, txt[idx:], buf, msg, is_ext))

        elif msg.from_user.id in self.wpm:
            (start, end, n) = self.wpm[msg.from_user.id]
            n += len(msg.text) + 1
            self.wpm[msg.from_user.id] = (start, msg.date, n)

        if txt[:len(admin.prefix)] == admin.prefix and msg.from_user.id == admin.userid:
            cmd, *args = txt[len(admin.prefix):].split(' ', 1)
            cmd = 'cmd_' + cmd
            args = (args or [None])[0]
            if hasattr(admin, cmd): self.reply(msg, getattr(admin, cmd)(self, args) or 'done')
            else: self.reply(msg, 'Unknown admin command.')

        matches = re.findall(r'\bx/[^/]*/|\bx\[[^]]*\]', txt)
        if matches:
            self.reply(msg, '\n'.join(map(xtoi, matches)))

        if txt[0] == '$' and txt[-1] == '$' and len(txt) > 2:
            # TODO adding a timeout is probably a good idea
            r = requests.get('https://latex.codecogs.com/png.latex?'+txt[1:-1], stream=True)
            with open('tex.png', 'wb') as f: shutil.copyfileobj(r.raw, f)
            self.reply_photo(msg, 'tex.png')
            os.remove('tex.png')

        for (pat, prob, resp) in data.triggers:
            if re.search(pat, txt) and random.random() < prob:
                self.reply(msg, resp(txt))

    def callback(self, client, update):
        print(update)
        self.process_message(update)

    def daily(self):
        pass
        #text = open('data/messages.txt').readlines()[datetime.date.today().toordinal()-736764].strip()
        #self.client.send_message(Chats.schmett, text)
        #self.client.send_message(Chats.haxorz, text)
        #self.client.send_message(Chats.duolingo, text)
