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
import data
import commands
import puzzle
import admin
from util import *

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
            CREATE TABLE IF NOT EXISTS feeds (
                url     TEXT UNIQUE NOT NULL,
                chat    INTEGER NOT NULL
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

    def checkwebsites(self):
        if hasattr(self, 'feeds'):
            for feed in self.feeds: feed.go(self.client)
        else:
            client.send_message(Chats.testing, 'WARNING: feeds not initialized @KeyboardFire')
            self.feeds = []

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
