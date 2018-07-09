from collections import Counter
import datetime
import json
import os
import random
import re
import select
import subprocess
import time

# pocketsphinx
import speech_recognition as sr

# network
from bs4 import BeautifulSoup
import requests
import urllib
import zlib

from util import *

# steno keyboard generator
import sys
sys.path.append('./tools/steno-keyboard-generator')
import keyboard

# puzzle
import puzzle
def puzlevel():
    return connect().execute('SELECT COUNT(*) FROM puzhist').fetchone()[0] + 1
def puzdesc():
    puzlevel = puzlevel()
    return 'Level {}: {}'.format(puzlevel, getattr(puzzle, 'desc'+str(puzlevel)))
def puzhist():
    return [usernamify(x[0])
            for x in connect().execute('''
            SELECT userid FROM puzhist ORDER BY level ASC
            ''').fetchall()]

# translation
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
    return (''.join(x[0] for x in resp[0]), resp[2])

# permissions
def perm_add(rule, cmd, userid, duration):
    with connect() as conn:
        vals = {'rule': rule, 'cmd': cmd, 'userid': userid, 'duration': duration}
        # clean up expired permissions
        conn.execute('DELETE FROM perm WHERE duration <= ?', (time.time(),))
        msg = conn.execute('''
        SELECT CASE
            WHEN duration < :duration THEN 'Rule successfully lengthened.'
            WHEN :duration < duration THEN 'Rule successfully shortened.'
            ELSE 'Rule already exists.'
        END FROM perm
        WHERE rule = :rule AND cmd = :cmd AND userid = :userid
        ''', vals).fetchone()
        if msg:
            conn.execute('''
            UPDATE perm SET duration = :duration
            WHERE rule = :rule AND cmd = :cmd AND userid = :userid
            ''', vals)
            return msg[0]
        elif duration > 0:
            conn.execute('''
            INSERT INTO perm (rule, cmd, userid, duration)
            VALUES (:rule, :cmd, :userid, :duration)
            ''', vals)
            return 'Rule successfully added.'
        else: return 'Rule does not exist.'

def perm_fmt(cmd):
    return '\n'.join('{} {} (expires {})'.format(
        row[0], usernamify(row[1]),
        'never' if row[2] == INF else 'in ' + str(datetime.timedelta(seconds=row[2])))
        for row in connect().execute('''
        SELECT rule, userid, duration - (julianday('now')-2440587.5)*86400.0
        FROM perm
        WHERE cmd = ? AND (julianday('now')-2440587.5)*86400.0 < duration
        ''', (cmd,)).fetchall())

# commands start here

def cmd_help(self, msg, args, stdin):
    '''
    help helps helpfully, a helper helping helpees.
    '''
    if not args:
        return 'This is @KeyboardFire\'s bot. Type {}commands for a list of commands. Source code: https://github.com/KeyboardFire/kipfa'.format(self.prefix)
    else:
        if 'cmd_'+args in globals():
            return ' '.join(globals()['cmd_'+args].__doc__.format(prefix=self.prefix).split())
        else:
            return 'Unknown command. Type {0}help for general information or {0}help COMMAND for help with a specific command.'.format(self.prefix)

def cmd_commands(self, msg, args, stdin):
    '''
    Lists all of the bot's commands.
    '''
    return ', '.join(sorted(s[4:] for s in globals() if s[:4] == 'cmd_'))

def cmd_prefix(self, msg, args, stdin):
    '''
    Changes the prefix used to run a bot command.
    '''
    if args:
        self.prefix = args
        return 'Prefix updated.'
    else:
        return 'Please specify a prefix to set.'

def cmd_extprefix(self, msg, args, stdin):
    '''
    Changes the prefix used to run a bot command with extended parsing.
    '''
    if args:
        self.extprefix = args
        return 'Prefix updated.'
    else:
        return 'Please specify a prefix to set.'

def cmd_getperm(self, msg, args, stdin):
    '''
    Displays the current permissions (whitelist and blacklist) for a given
    command.
    '''
    if 'cmd_'+args in globals():
        return perm_fmt(args) or 'No rules set.'
    elif args:
        return 'Unknown command {}.'.format(args)
    else:
        return 'Please specify a command name.'

def cmd_js(self, msg, args, stdin):
    '''
    Executes (sandboxed) JavaScript code and returns the value of the last
    expression.
    '''
    return os.popen("""node -e 'var Sandbox = require("./node_modules/sandbox"), s = new Sandbox(); s.options.timeout = 2000; s.run("{}", function(x) {{ console.log(x.result == "TimeoutError" ? "2 second timeout reached." : x.result); }});'""".format(args.replace('\\', '\\\\').replace("'", "'\\''").replace('"', '\\"').replace('\n', '\\n'))).read()

def cmd_steno(self, msg, args, stdin):
    '''
    Displays the given chord on a steno keyboard.
    '''
    if not args:
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

def cmd_expand(self, msg, args, stdin):
    '''
    Randomly expands an acronym, e.g. {prefix}expand mfw => mole fluently
    whimpers.
    '''
    args = args.lower().replace(' ', '').replace('\n', '')
    if args == 'mfw':
        return 'meaningfulness what'
    elif any(not ('a' <= ch <= 'z') for ch in args):
        return 'Letters only please.'
    elif len(args) > 10:
        return 'Maximum of 10 letters allowed.'
    else:
        return ' '.join([os.popen("grep '^{}[a-z]*$' /usr/share/dict/words | shuf -n1".format(ch)).read().strip() for ch in args])

def cmd_bash(self, msg, args, stdin):
    '''
    Gives the highest voted out of 50 random bash.org quotes.
    '''
    quote = max(BeautifulSoup(requests.get('http://bash.org/?random1').text, 'html.parser').find_all('p', class_='quote'), key=lambda x: int(x.font.text)).next_sibling.text
    return '```\n{}\n```'.format(quote)

def cmd_uptime(self, msg, args, stdin):
    '''
    Tells how long the bot has been running since its last restart.
    '''
    return str(datetime.timedelta(seconds=int(time.time() - self.starttime)))

def cmd_frink(self, msg, args, stdin):
    '''
    Executes Frink code (https://frinklang.org/).
    '''
    if not args: return 'Please provide Frink code to run.'
    self.frink.stdin.write(args.replace('\n', ' ').encode('utf-8') + b'\n')
    self.frink.stdin.flush()
    r = self.frink.stdout.readline()
    ans = b''
    while True:
        line = self.frink.stdout.readline()
        if line == r: break
        ans += line
    return ans.decode('utf-8')

def cmd_transcribe(self, msg, args, stdin):
    '''
    Transcribes voice messages into text (very poorly) with PocketSphinx.
    '''
    rmsg = self.get_reply(msg)
    if rmsg is None or not hasattr(rmsg, 'voice'):
        return 'Please reply to a voice message.'
    voice = rmsg.voice
    if voice.mime_type != 'audio/ogg':
        return 'Please reply to a voice message.'
    if voice.file_size > 1024 * 200:
        return 'Message too big.'
    fname = self.client.download_media(rmsg)
    os.system('ffmpeg -i {} out.wav'.format(fname))
    os.remove(fname)
    with sr.AudioFile('out.wav') as source:
        audio = self.recog.record(source)
    os.remove('out.wav')
    try:
        return self.recog.recognize_sphinx(audio) or '(lambs)'
    except sr.UnknownValueError:
        return '(error)'

def cmd_puzzle(self, msg, args, stdin):
    '''
    Puzzles! See the current puzzle by using this command; you can make one
    guess per hour with {prefix}puzzle [guess]. The puzzles won't require
    any in-depth domain-specific knowledge (but use of the internet is
    encouraged and sometimes required). See also: {prefix}puzhist,
    {prefix}leaderboard.
    '''
    if not args: return puzdesc()
    with connect() as conn:
        if conn.execute('''
                SELECT nextguess > (julianday('now')-2440587.5)*86400.0
                FROM puztime
                WHERE userid = ?
                UNION ALL SELECT 0
                ''', (msg.from_user.id,)).fetchone()[0]:
            return 'Max one guess per person per hour.'
        if getattr(puzzle, 'guess'+str(puzlevel()))(args):
            conn.execute('''
            INSERT INTO puzhist (userid) VALUES (?);
            ''', (msg.from_user.id,))
            return 'Correct! ' + puzdesc()
        else:
            conn.execute('''
            INSERT OR REPLACE INTO puztime
            VALUES (?, (julianday('now')-2440587.5)*86400.0 + 60*60);
            ''', (msg.from_user.id,))
            return "Sorry, that's incorrect."

def cmd_puzhist(self, msg, args, stdin):
    '''
    Returns the list of people in order who have solved the puzzles from
    the {prefix}puzzle command so far.
    '''
    return 'Puzzles solved so far by: ' + ', '.join(puzhist())

def cmd_leaderboard(self, msg, args, stdin):
    '''
    Generates a sorted leaderboard of how many puzzles from the
    {prefix}puzzle command each person has solved.
    '''
    data = sorted(Counter(puzhist()).items(), key=lambda x: -x[1])
    maxlen = max(len(x[0]) for x in data)
    return '```\n'+'\n'.join('{:<{}} {}'.format(a, maxlen, b) for a, b in data)+'\n```'

def cmd_translate(self, msg, args, stdin):
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

def cmd_flipflop(self, msg, args, stdin):
    '''
    Translates from English to another language and back repeatedly until
    reaching a fixed point. Specify a language with e.g. {prefix}flipflop
    ja: A towel is about the most massively useful thing an interstellar
    hitchhiker can have. If no language is specified, a random one will be
    chosen.
    '''
    m = re.match(r'([a-z-]*):', args)
    hist = []
    tl = random.choice(list(langs.keys() - ['en']))
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

def cmd_flepflap(self, msg, args, stdin):
    '''
    Translates repeatedly from English to different languages and back for
    a fixed number of iterations. Specify a list of languages with e.g.
    {prefix}flepflap ja es ko: (message), or a number of iterations with
    {prefix}flepflap 3: (message). If neither a list nor a number is given,
    5 iterations will be used by default.
    '''
    args = args.replace('\n', ' ')
    m = re.match(r'([0-9a-z- ]*):', args)
    hist = []
    if m is None: m = '5'
    else:
        m = m.group(1)
        args = args[args.find(':')+1:].strip()
    tls = [tl for x in m.split() for tl in (random.sample(list(langs.keys() - ['en']), int(x)) if x.isdigit() else [x])]
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
    return (hist[-1], '\n'.join(hist[:-1]))

def cmd_soguess(self, msg, args, stdin):
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
                return 'Guess a tag!\n```' + pre.text.rstrip('\n') + '```'
        # somehow no answers matched the criteria
        return 'Something went horribly wrong'
    else:
        resp = 'The correct tags were: ' + ', '.join(self.soguess)
        self.soguess = None
        return resp

def cmd_ddg(self, msg, args, stdin):
    '''
    Returns a link to the first search result on DuckDuckGo for a given
    query.
    '''
    if not args:
        return 'Please provide a search query.'
    url = 'https://duckduckgo.com/html/?q=' + urllib.parse.quote(args)
    res = BeautifulSoup(requests.get(url).text, 'lxml').find('div', class_='web-result')
    link = urllib.parse.unquote(res.find('a').attrs['href'][15:])
    return link if link else 'No results.'

def cmd_wpm(self, msg, args, stdin):
    '''
    Calculates the WPM starting from when you run this command to the
    moment you send the last message before running the command again.
    '''
    uid = msg.from_user.id
    if uid in self.wpm:
        (start, end, n) = self.wpm[uid]
        del self.wpm[uid]
        if start == end:
            return "Please type for longer than a second."
        return '{:.3f} WPM'.format(n / ((end - start) / 60.0) / 5)
    else:
        self.wpm[uid] = (msg.date, msg.date, 0)

def cmd_Flypflap(self, msg, args, stdin):
    '''
    Flypflap
    '''
    return random.choice(['Go to the top', 'Flip-valve', 'Flytrap', 'Flapplop'])

def cmd_vim(self, msg, args, stdin):
    with open('vim.txt', 'w') as f:
        f.write(stdin)
    print(subprocess.run(['timeout', '2',
        'tools/neovim/build/bin/nvim',
        '-Z',
        '-n',
        '--headless',
        '+exe feedkeys("{}", "tx")|wq'.format(args \
                .replace('\\', '\\\\') \
                .replace('"', r'\"') \
                .replace('<esc>', r'\<esc>') if args else ''),
        '/home/llama/neollama/kipfa/vim.txt']))
    with open('vim.txt', 'r') as f:
        stdin = f.read()
    os.remove('vim.txt')
    return stdin

def cmd_wump(self, msg, args, stdin):
    if not args:
        if self.wump: return 'A game of wump is already in progress!'
        else:
            self.wump = subprocess.Popen(['wump'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE)
            args = 'n'
    if self.wump is None:
        return 'There is no game of wump in progress (type {}wump to start one!)'.format(self.prefix)
    self.wump.stdin.write(args.encode('utf-8') + b'\n')
    self.wump.stdin.flush()
    resp = b''
    while self.wump.poll() is None and \
            select.select([self.wump.stdout], [], [], 0.1)[0]:
        resp += os.read(self.wump.stdout.fileno(), 4096)
    if self.wump.poll() is not None:
        self.wump = None
        resp += b' [terminated]'
    return resp.decode('utf-8')

def cmd_getshock(self, msg, args, stdin):
    return '\n'.join('{}: {}'.format(*x) for x in connect().execute('''
        SELECT name, num FROM shocks ORDER BY num DESC
        ''').fetchall())

def cmd_shock(self, msg, args, stdin):
    if not args:
        return 'Please specify who to shock.'
    num = re.search(r'[+-]?\d+$', args)
    if num:
        args = args[:num.start()]
        num = int(num.group())
    else:
        num = 1
    args = ' '.join(args.split()).title()
    with connect() as conn:
        conn.execute('INSERT OR IGNORE INTO shocks (name, num) VALUES (?, 0)', (args,))
        conn.execute('UPDATE shocks SET num = num + ? WHERE name = ?', (num, args))
        s = conn.execute('SELECT num FROM shocks WHERE name = ?', (args,)).fetchone()[0]
        if s == 0: conn.execute('DELETE FROM shocks WHERE name = ?', (args,))
        return '{} now has {} shock{}'.format(args, s, '' if s == 1 else 's')

def cmd_mma(self, msg, args, stdin):
    if not args:
        return 'Please provide Mathematica code to run.'
    p = subprocess.run(['timeout', '-s9', '3',
        '/home/llama/neollama/mma/scriptdir/wolframscript',
        '-c',
        'Developer`StartProtectedMode[];' + args], stdout=subprocess.PIPE)
    print(p.returncode)
    return '3 second timeout reached.' if p.returncode == -9 else \
            '```\u200b'+(p.stdout.decode('utf-8').rstrip() or '[no output]')+'```'

def cmd_bf(self, msg, args, stdin):
    if not args:
        return 'Please provide Brainfuck code to run.'
    p = subprocess.run(['./tools/brainfuck', 'tmp'],
            stdout=subprocess.PIPE,
            input=args.encode('utf-8'))
    if p.returncode == 1: return 'Compilation failed.'
    if p.returncode == 124: return '5 second timeout reached.'
    return p.stdout.decode('utf-8') or '[no output]'

def cmd_tio(self, msg, args, stdin):
    '''
    todo: documentation
    '''
    err = " (try `{}help tio` for more information)".format(self.prefix)
    if not args: return 'Basic usage: {}tio [lang] [code]'.format(self.prefix) + err
    if args == 'err': return self.tioerr
    lang, *rest = args.split(None, 1)
    rest = rest[0] if len(rest) else ''
    stdin = ''
    stderr = False
    args = []
    code, *parts = rest.split('\n###')
    for part in parts:
        name, data = part.split('\n', 1) if '\n' in part else (part, '')
        name = name.strip()
        if name == 'stdin': stdin = data
        elif name == 'stderr': stderr = True
        elif name == 'arg': args.append(data)
        else: return "Unknown section `{}`".format(name) + err
    try:
        data = requests.post('https://tio.run/cgi-bin/run/api/', zlib.compress(bytes('Vlang\u00001\u0000{}\u0000F.code.tio\u0000{}\u0000{}F.input.tio\u0000{}\u0000{}Vargs\u0000{}{}\u0000R'.format(lang, len(bytes(code, 'utf-8')), code, len(stdin), stdin, len(args), (len(args) * '\u0000{}').format(*args)), 'utf-8'), 9)[2:-4], timeout=5).text
        data = data.split(data[:16])[1:]
        if len(data) == 1: return data[0]  # error
        dout, derr = [x.strip('\n') for x in data[:2]]
        self.tioerr = derr
        haserr = re.search('\nReal time: \\d+\\.\\d+ s\nUser time: \\d+\\.\\d+ s\nSys\\. time: \\d+\\.\\d+ s\nCPU share: \\d+\\.\\d+ %\nExit code: \\d+$', data[1]).start() > 0
        return (dout+'\n--- stderr ---\n'+derr if stderr else dout+('\n[stderr output - use {}tio err to view]'.format(self.prefix) if haserr else '')) or '[no output]'
    except requests.exceptions.ConnectionError:
        return '5 second timeout reached.'

def cmd_perm(self, msg, args, stdin):
    usage = 'Usage: {}perm [command] [whitelist|blacklist|unwhitelist|unblacklist] [user] [duration] (omit duration for permanent)'.format(self.prefix)

    parts = (args or '').split(' ')
    if not (3 <= len(parts) <= 4): return usage

    (cmd, action, user, *duration) = parts
    if user and user[0] == '@': user = user[1:]
    duration = time.time() + float(duration[0]) if duration else INF

    uid = connect().execute('SELECT userid FROM nameid WHERE name = ?', (user,)).fetchone()
    if 'cmd_'+cmd not in globals() or not uid: return usage

    if   action == 'whitelist':   return perm_add(PERM_W, cmd, uid[0], duration)
    elif action == 'blacklist':   return perm_add(PERM_B, cmd, uid[0], duration)
    elif action == 'unwhitelist': return perm_add(PERM_W, cmd, uid[0], 0)
    elif action == 'unblacklist': return perm_add(PERM_B, cmd, uid[0], 0)
    return usage

def cmd_restart(self, msg, args, stdin):
    '''
    Restarts the bot.
    '''
    self.reply(msg, 'restarting...')
    os._exit(0)
