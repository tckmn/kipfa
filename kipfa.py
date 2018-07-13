#!/usr/bin/python3

from io import StringIO
from threading import Thread
import datetime
import json
import os
import random
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

# pyrogram
from pyrogram import Client, MessageHandler
from pyrogram.api import types, functions

# pocketsphinx
import speech_recognition as sr

# network
from bs4 import BeautifulSoup
import requests

# local modules
import data
import commands
import puzzle
from util import *

admin = 212594557
class Chats:
    frink    = -1001277770483
    haxorz   = -1001059322065
    mariposa = -1001053893427
    ppnt     = -1001232971188
    schmett  = -1001119355580
    testing  = -1001178303268
    duolingo = -1001105416173
    naclo    = -1001088995343
    newdays  = -1001211597524

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

def getfeed(feed):
    print('getfeed({})'.format(feed))
    text = requests.get(feed).text
    if feed == 'http://www.archr.org/atom.xml':
        text = text.replace(' & ', ' &amp; ')

    # https://stackoverflow.com/a/33997423/1223693
    it = ET.iterparse(StringIO(text))
    for _, el in it:
        el.tag = el.tag[el.tag.find('}')+1:]
        for at in el.attrib.keys():
            if '}' in at:
                el.attrib[at[at.find('}')+1:]] = el.attrib[at]
                del el.attrib[at]

    return it.root

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
    return BeautifulSoup(r.text, 'lxml').find('h2').find('a').attrs['href'].replace(' ', '%20')

def getbda():
    r = requests.get('https://www.voanoticias.com/z/537')
    return BeautifulSoup(r.text, 'lxml').find('div', id='content').find('div', class_='content').find('a').attrs['href']

def getkernel():
    r = requests.get('https://kernel.org/')
    return BeautifulSoup(r.text, 'lxml').find('td', id='latest_link').text.strip()

def perm_check(cmd, userid):
    return connect().execute('''
    SELECT NOT EXISTS(SELECT 1 FROM perm WHERE
        ((rule = :b AND (cmd = 'ALL' OR cmd = :cmd) AND userid  = :userid) OR
         (rule = :w AND (cmd = 'ALL' OR cmd = :cmd) AND userid != :userid)) AND
        duration > (julianday('now')-2440587.5)*86400.0
    )
    ''', {'cmd': cmd, 'userid': userid, 'w': PERM_W, 'b': PERM_B}).fetchone()[0]

class Bot:

    def __init__(self, client):
        self.client = client
        self.prefix = '!'
        self.extprefix = '!!'

        self.triggers = [

            (r'(?i)\bwhere (are|r) (you|u|y\'?all)\b|\bwhere (you|u|y\'?all) at\b',
             0.5,
             lambda _: 'NUMBERS NIGHT CLUB'),

            (r'(?i)mountain|\brock|cluster',
             0.3,
             lambda _: (random.choice(['aftershock','airlock','air lock','air sock','alarm clock','antiknock','arawak','around the clock','atomic clock','authorized stock','baby talk','bach','balk','ballcock','ball cock','bangkok','bedrock','biological clock','bloc','block','boardwalk','bock','brock','building block','calk','capital stock','catwalk','caudal block','caulk','chalk','chalk talk','chicken hawk','chock','chopping block','cinder block','clock','combination lock','common stock','control stock','crock','crosstalk','crosswalk','cuckoo clock','cylinder block','deadlock','doc','dock','double talk','dry dock','eastern hemlock','electric shock','electroshock','engine block','en bloc','fish hawk','flintlock','floating dock','floc','flock','french chalk','frock','gamecock','gawk','goshawk','grandfather clock','gridlock','growth stock','hammerlock','hawk','haycock','heart block','hemlock','hoc','hock','hollyhock','insulin shock','interlock','iraq','jaywalk','jock','johann sebastian bach','john hancock','john locke','kapok','knock','lady\'s smock','laughingstock','letter stock','line block','livestock','loch','lock','locke','manioc','maroc','marsh hawk','matchlock','medoc','mental block','mock','mohawk','mosquito hawk','nighthawk','nock','o\'clock','oarlock','office block','out of wedlock','overstock','padauk','padlock','peacock','penny stock','pigeon hawk','pillow block','pock','poison hemlock','poppycock','post hoc','preferred stock','restock','roadblock','roc','rock','rolling stock','round the clock','sales talk','sauk','schlock','scotch woodcock','shamrock','shell shock','sherlock','shock','sidewalk','sleepwalk','small talk','smock','snatch block','sock','space walk','sparrow hawk','squawk','stalk','starting block','stock','stumbling block','sweet talk','table talk','take stock','talk','time clock','tomahawk','tower block','treasury stock','turkey cock','unblock','undock','unfrock','unlock','vapor lock','voting stock','walk','war hawk','watered stock','water clock','water hemlock','wedlock','wheel lock','widow\'s walk','wind sock','wok','woodcock','writer\'s block','yellow dock']) + ' ' + random.choice(['adjuster','adjuster','adjustor','blockbuster','bluster','buster','cluster','combustor','custard','duster','filibuster','fluster','ghosebuster','ghostbuster','just her','knuckle duster','lackluster','luster','lustre','mustard','muster','thruster','trust her'])).upper() + ' ' + ''.join(random.choice('˥˦˧˨˩') for _ in range(50))),

            (r'(?i)\bgo\b',
             0.1,
             lambda _: 'lol no generics')

        ]

        self.uotd = getuotd()
        self.review = getreview()
        self.bda = getbda()
        self.kernel = getkernel()
        self.dailied = False

        with connect() as conn:
            conn.executescript('''
            CREATE TABLE IF NOT EXISTS nameid (
                name    TEXT UNIQUE NOT NULL,
                userid  INTEGER UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS perm (
                rule        TEXT NOT NULL,
                cmd         TEXT NOT NULL,
                userid      INTEGER NOT NULL,
                duration    REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS puztime (
                userid      INTEGER UNIQUE NOT NULL,
                nextguess   REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS puzhist (
                level   INTEGER PRIMARY KEY,
                userid  INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS shocks (
                name    TEXT UNIQUE NOT NULL,
                num     INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alias (
                src     TEXT UNIQUE NOT NULL,
                dest    TEXT NOT NULL
            );
            ''')

        self.recog = sr.Recognizer()
        self.starttime = time.time()
        self.frink = subprocess.Popen('java -cp tools/frink/frink.jar:tools/frink SFrink'.split(),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.soguess = None
        self.quota = '(unknown)'
        self.wpm = dict()
        self.wump = None
        self.tioerr = ''

    def send_feed(self, url, guid, text):
        if guid not in self.feeds[url]:
            self.client.send_message(Chats.haxorz, text)
            self.feeds[url].append(guid)

    def send_rss(self, url, feed):
        for item in feed[0].findall('item'):
            text = item.find('link').text
            if url == 'http://xkcd.com/rss.xml':
                text += ' ' + BeautifulSoup(item.find('description').text, 'html.parser').find('img').attrs['title']
            elif url == 'http://www.smbc-comics.com/rss.php':
                text += ' ' + BeautifulSoup(item.find('description').text, 'html.parser').contents[1].contents[2]
            self.send_feed(url, item.find('guid').text, text)

    def send_atom(self, url, feed):
        for item in feed.findall('entry'):
            a = item.find('link').attrib
            self.send_feed(url, item.find('id').text, a['href'])

    def checkwebsites(self):
        if hasattr(self, 'feeds'):
            for url in self.feeds:
                feed = getfeed(url)
                if feed.tag == 'rss': self.send_rss(url, feed)
                else: self.send_atom(url, feed)
        else:
            client.send_message(Chats.testing, 'WARNING: feeds not initialized @KeyboardFire')
            self.feeds = dict()

        newuotd = getuotd()
        if newuotd and self.uotd != newuotd:
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

        newkernel = getkernel()
        if newkernel and self.kernel != newkernel:
            self.kernel = newkernel
            self.client.send_message(Chats.haxorz, 'kernel '+self.kernel+' released')

    def get_reply(self, msg):
        if not hasattr(msg, 'reply_to_message') or msg.reply_to_message is None: return None
        return msg.reply_to_message

    def reply(self, msg, txt):
        print(txt)
        txt = txt.strip()
        if not txt: txt = '[reply empty]'
        if len(txt) > 4096: txt = '[reply too long]'
        self.client.send_message(msg.chat.id, txt, reply_to_message_id=msg.message_id)

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

        is_cmd = txt[:len(self.prefix)] == self.prefix
        is_ext = txt[:len(self.extprefix)] == self.extprefix
        if is_cmd or is_ext:
            # initialization
            rmsg = self.get_reply(msg)
            buf = rmsg.text if rmsg else ''
            idx = len(self.extprefix) if is_ext else len(self.prefix)

            # check for intermediate pipes
            part = ''
            parts = []
            parse = True
            while idx <= len(txt):
                if not parse:
                    part += ('' if txt[idx] in '\\|' else '\\') + txt[idx]
                    parse = True
                elif idx == len(txt) or (is_ext and txt[idx] == '|'):
                    part = connect().execute('''
                    SELECT dest || substr(:s, length(src)+1) FROM alias
                    WHERE :s = src OR :s LIKE src || ' %'
                    UNION ALL SELECT :s
                    ''', {'s': part.strip()}).fetchone()[0]
                    cmd, args = part.split(' ', 1) if ' ' in part else (part, None)
                    if not hasattr(commands, 'cmd_'+cmd):
                        self.reply(msg, 'The command {} does not exist.'.format(cmd))
                        break
                    if not perm_check(cmd, msg.from_user.id):
                        self.reply(msg, 'You do not have permission to execute the {} command.'.format(cmd))
                        break
                    parts.append((getattr(commands, 'cmd_'+cmd), args))
                    part = ''
                elif is_ext and txt[idx] == '\\': parse = False
                else: part += txt[idx]
                idx += 1
            else:
                res = ''
                for (func, args) in parts:
                    buf = func(self, msg, buf if args is None else args, buf)
                    if type(buf) == tuple:
                        res += buf[1] + '\n'
                        buf = buf[0]
                self.reply(msg, res + buf)

        elif msg.from_user.id in self.wpm:
            (start, end, n) = self.wpm[msg.from_user.id]
            n += len(msg.text) + 1
            self.wpm[msg.from_user.id] = (start, msg.date, n)

        if txt == '!!debug' and msg.from_user.id == admin:
            print(repr(vars(self)))
        elif txt == '!!updateusers' and msg.from_user.id == admin:
            count = 0
            with connect() as conn:
                for ch in self.client.send(functions.messages.GetAllChats([])).chats:
                    if isinstance(ch, types.Channel):
                        count += 1
                        conn.executemany('''
                        INSERT OR REPLACE INTO nameid (name, userid) VALUES (?, ?)
                        ''', [(u.username, u.id) for u in self.client.send(
                            functions.channels.GetParticipants(
                                self.client.peers_by_id[-1000000000000-ch.id],
                                types.ChannelParticipantsRecent(),
                                0, 0, 0
                                )
                            ).users if u.username])
                nusers = conn.execute('SELECT COUNT(*) FROM nameid').fetchone()[0]
                self.reply(msg, 'updated {} users in {} chats'.format(nusers, count))
        elif txt == '!!quota' and msg.from_user.id == admin:
            self.reply(msg, str(self.quota))
        elif txt == '!!daily' and msg.from_user.id == admin:
            self.daily()
        elif txt == '!!checkwebsites' and msg.from_user.id == admin:
            self.checkwebsites()
        elif txt == '!!initfeeds' and msg.from_user.id == admin:
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
                'http://keyboardfire.com/blog.xml',
                'https://en.wiktionary.org/w/api.php?action=featuredfeed&feed=fwotd'
                ])

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

    def callback(self, client, update):
        print(update)
        self.process_message(update)

    def daily(self):
        pass
        #text = open('messages.txt').readlines()[datetime.date.today().toordinal()-736764].strip()
        #self.client.send_message(Chats.schmett, text)
        #self.client.send_message(Chats.haxorz, text)
        #self.client.send_message(Chats.duolingo, text)

client = Client('kipfa')
bot = Bot(client)
client.add_handler(MessageHandler(bot.callback))
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
