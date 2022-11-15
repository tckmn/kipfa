from collections import Counter
from datetime import *
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
import anduptime
import data   # for langs (translate & co.)
import parse  # for eval, exteval

# steno keyboard generator
import sys
sys.path.append('./tools/steno-keyboard-generator')
import keyboard

# puzzle
import puzzle
def puzlevel():
    return connect().execute('SELECT COUNT(*) FROM puzhist').fetchone()[0] + 1
def puzdesc():
    level = puzlevel()
    return 'Level {}: {}'.format(level, getattr(puzzle, 'desc'+str(level)))
def puzhist():
    return [usernamify(x[0])
            for x in connect().execute('''
            SELECT userid FROM puzhist ORDER BY level ASC
            ''').fetchall()]

# translation
def translate(text, sl, tl):
    resp = json.loads(requests.post('https://api.cognitive.microsofttranslator.com/translate', params={
            'api-version': '3.0',
            'to': tl,
            **({'from': sl} if sl else {})
        }, data=json.dumps([{'text': text.strip()}]), headers={
            'Ocp-Apim-Subscription-Key': open('data/key').read().strip(),
            'Ocp-Apim-Subscription-Region': 'canadacentral',
            'Content-Type': 'application/json'
        }).text)
    print('translate: ' + repr(resp))
    resp = resp[0] if type(resp) is list else resp
    return (resp['translations'][0]['text'], sl or resp['detectedLanguage']['language'])

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
        'never' if row[2] == INF else 'in ' + str(timedelta(seconds=row[2])))
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
        return 'This is @tckmn\'s bot. Type {}commands for a list of commands. Source code: https://github.com/tckmn/kipfa'.format(self.prefix)
    else:
        if args == 'arslan':
            return cmd_arslan(0,0,0,0)
        elif args == 'COMMAND':
            return 'Fuck you'
        elif 'cmd_'+args in globals():
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
    Changes the prefix used to run a bot command. See also: {prefix}extprefix
    '''
    if args:
        self.prefix = args
        return 'Prefix updated.'
    else:
        return 'Please specify a prefix to set.'

def cmd_extprefix(self, msg, args, stdin):
    '''
    Changes the prefix used to run a bot command with extended parsing. See
    also: {prefix}prefix
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
    if not args: return 'Please specify a command name.'
    if args == 'ALL' or 'cmd_'+args in globals():
        return perm_fmt(args) or 'No rules set.'
    else: return 'Unknown command {}.'.format(args)

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

def expand(s, r='[a-z]*'):
    return ' '.join([os.popen("grep '^{}{}$' /usr/share/dict/words | shuf -n1".format(ch, r)).read().strip() for ch in s])
def cmd_expand(self, msg, args, stdin):
    '''
    Randomly expands an acronym, e.g. {prefix}expand mfw => mole fluently
    whimpers.
    '''
    args = ''.join(c for c in args.lower() if 'a' <= c <= 'z')
    if not args:
        return 'Please give at least one letter.'
    elif len(args) > 10:
        return 'Maximum of 10 letters allowed.'
    else:
        prefix = ''
        if len(args) > 2 and args[:2] == 'wt':
            prefix = 'what the '
            args = args[2:]
        elif len(args) > 2 and args[:2] == 'om':
            prefix = 'oh my '
            args = args[2:]
        elif len(args) == 4 and args[:3] == 'rof':
            gerund = expand(args[-1], '[a-z]*ing')
            if gerund: return 'rolling on the floor ' + gerund
        return ' '.join((prefix + ' meaningfulness what '.join(expand(s) for s in args.split('mfw'))).split())

# def cmd_bash(self, msg, args, stdin):
#     '''
#     Gives the highest voted out of 50 random bash.org quotes.
#     '''
#     resp = get('http://bash.org/?random1')
#     if resp is None: return '[timeout]'
#     quote = max(BeautifulSoup(resp, features='html.parser').find_all('p', class_='quote'), key=lambda x: int(x.font.text)).next_sibling.text
#     return cf(quote)

def cmd_uptime(self, msg, args, stdin):
    '''
    Tells how long the bot and Andy have been running since their last restarts.
    '''
    return ('kipfa: ' + anduptime.fmt(time.time() - self.starttime) + '\n\n' +
            'tckmn: ' + anduptime.compute(self.lastonline, self.lastwokeup))

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
    See the current puzzle by using this command; you can make one guess per
    hour with {prefix}puzzle [guess]. The puzzles won't require any in-depth
    domain-specific knowledge (but use of the internet is encouraged and
    sometimes required). See also: {prefix}puzhist, {prefix}leaderboard
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
    return withmd(cf('\n'.join('{:<{}} {}'.format(a, maxlen, b) for a, b in data)))

def cmd_translate(self, msg, args, stdin):
    '''
    Translates its argument into English by default; to translate into
    another language, use e.g. {prefix}translate es: This is Spanish. See also:
    {prefix}flipflop, {prefix}flepflap
    '''
    m = re.match(r'([a-z-]*):', args)
    tl = 'en'
    if m:
        tl = m.group(1)
        args = args[args.find(':')+1:]
    (res, sl) = translate(args, None, tl)
    return '(from {}) {}'.format(data.langs[sl], res)

# TODO document asterisk
def flipflop(hist, sl, tl):
    (res, _) = translate(hist[-1], sl, tl)
    end = False
    if res in hist: end = True
    hist += [res]
    return end
def cmd_flipflop(self, msg, args, stdin):
    '''
    Translates from English to another language and back repeatedly until
    reaching a fixed point. Specify a language with e.g. {prefix}flipflop ja:
    [message]. If no language is specified, a random one will be chosen. See
    also: {prefix}translate, {prefix}flepflap
    '''
    m = re.match(r'(\*)?([A-Za-z-]*):', args)
    hist = []
    tl = random.choice(data.langsgood)
    if m:
        tl = m.group(2)
        args = args[args.find(':')+1:].strip()
    else:
        hist += ['(chose '+data.langs[tl]+')']
    if len(args) > 100:
        return "That's too long. Try something shorter please."
    hist += [args]
    if m and m.group(1):
        if flipflop(hist, tl, 'en'): return '\n'.join(hist)
    while 1:
        if flipflop(hist, 'en', tl): break
        if flipflop(hist, tl, 'en'): break
        if sum(len(x) for x in hist) > 5000:
            hist += ['[result too long, terminated]']
            break
    return '\n'.join(hist)

def cmd_flepflap(self, msg, args, stdin):
    '''
    Translates repeatedly from English to different languages and back for
    a fixed number of iterations. Specify a list of languages with e.g.
    {prefix}flepflap ja es ko: [message], or a number of iterations with
    {prefix}flepflap 3: [message]. If neither a list nor a number is given,
    5 iterations will be used by default. See also: {prefix}translate,
    {prefix}flipflop
    '''
    args = args.replace('\n', ' ')
    m = re.match(r'([0-9A-Za-z- ]*):', args)
    hist = []
    if m is None: m = '5'
    else:
        m = m.group(1)
        args = args[args.find(':')+1:].strip()
    tls = [tl for x in m.split() for tl in (random.sample(data.langsgood, int(x)) if x.isdigit() else [x])]
    if len(tls) > 8:
        return "That's too many languages. You may provide a maximum of 8."
    if len(args) > 100:
        return "That's too long. Try something shorter please."
    hist += [args]
    for tl in tls:
        (res, sl) = translate(args, 'en', tl)
        hist += ['[{}] {}'.format(tl, res)]
        (res2, sl2) = translate(res, tl, 'en')
        hist += [res2]
        args = res2
    return (hist[-1], {'stderr': '\n'.join(hist[:-1])})

soa = 'https://api.stackexchange.com/2.2/answers?page={}&pagesize=100&order=desc&sort=activity&site=stackoverflow&filter=!-.3J6_JIMYrq&key=Oij)9kWgsRogxL0fBwKdCw(('
soq = 'https://api.stackexchange.com/2.2/questions/{}?order=desc&sort=activity&site=stackoverflow&filter=!4(YqzWIjDDMcfFBmP&key=Oij)9kWgsRogxL0fBwKdCw(('
seq = 'https://api.stackexchange.com/2.2/questions?page={}&pagesize=100&order=desc&sort=activity&site={}&filter=!bA1d_KulCdCDHu&key=Oij)9kWgsRogxL0fBwKdCw(('

def cmd_soguess(self, msg, args, stdin):
    '''
    Run this command once to get a code snippet from a random answer on
    Stack Overflow. Then guess the tags of the question and run it again to
    see if you were right.
    '''
    if self.soguess is None:
        data = json.loads(requests.get(soa.format(random.randint(1, 100000))).text)
        for item in sorted(data['items'], key=lambda x: -x['score']):
            pre = BeautifulSoup(item['body'], features='html.parser').find('pre')
            if pre is not None and 10 < len(pre.text) < 500:
                qdata = json.loads(requests.get(soq.format(item['question_id'])).text)
                self.soguess = qdata['items'][0]['tags']
                self.quota = qdata['quota_remaining']
                return withmd('Guess a tag!\n' + cf(pre.text))
        # somehow no answers matched the criteria
        return 'Something went horribly wrong'
    else:
        resp = 'The correct tags were: ' + ', '.join(self.soguess)
        self.soguess = None
        return resp

import html
def cmd_seguess(self, msg, args, stdin):
    '''
    Run this command once to get the title of a question from a random Stack
    Exchange site. Then guess the site and run it again to see if you were
    right.
    '''
    if self.seguess is None:
        [site, questions] = random.choice(data.sites)
        resp = json.loads(requests.get(seq.format(random.randint(1, max(1, questions//100)), site)).text)
        self.seguess = site
        return 'Guess a site!\n' + html.unescape(random.choice([x['title'] for x in resp['items'] if x['score'] >= 0]))
    else:
        resp = 'The correct site was: ' + self.seguess
        self.seguess = None
        return resp

def cmd_ddg(self, msg, args, stdin):
    '''
    Returns a link to the first search result on DuckDuckGo for a given
    query.
    '''
    if not args:
        return 'Please provide a search query.'
    # ddg doesn't like requests headers
    resp = get('https://duckduckgo.com/html/?q=' + urllib.parse.quote(args),
               headers={'User-Agent': 'curl/7.70.0'})
    if resp is None: return '[timeout]'
    try:
        href = BeautifulSoup(resp, features='html.parser').find('div', class_='web-result').find('a').attrs['href']
        return urllib.parse.parse_qs(urllib.parse.urlparse(href).query)['uddg'][0]
    except:
        return 'no results'

def cmd_wpm(self, msg, args, stdin):
    '''
    Calculates the WPM starting from when you run this command to the
    moment you send the last message before running the command again.
    '''
    uid = msg.from_user.id
    if uid in self.wpm:
        (start, end, n) = self.wpm[uid]
        del self.wpm[uid]
        if end is None:
            return "you literally didn't type anything"
        if start == end:
            return "please type for longer than that"
        return '{:.3f} WPM'.format(n / ((end - start) / 60.0) / 5)
    else:
        self.wpm[uid] = (mnow(msg), None, 0)

def cmd_Flypflap(self, msg, args, stdin):
    '''
    Flypflap
    '''
    return random.choice(['Go to the top', 'Flip-valve', 'Flytrap', 'Flapplop'])

def cmd_vim(self, msg, args, stdin):
    '''
    Places input in a file, evaluates argument as vim keystrokes, then returns
    the result.
    '''
    with open('vim.txt', 'w') as f: f.write(stdin)
    env = os.environ.copy()
    env['VIMRUNTIME'] = data.fulldir + '/tools/neovim/runtime'
    # weird hack to work around GCE oddity
    subprocess.run(['timeout', '3', 'tools/neovim/build/bin/nvim', '-Z', '-n', '--headless', '+q'], env=env)
    print(subprocess.run(['timeout', '3',
        'tools/neovim/build/bin/nvim',
        '-Z',
        '-n',
        '--headless',
        '+exe feedkeys("{}", "tx")|wq'.format(args \
                .replace('\\', '\\\\') \
                .replace('"', r'\"') \
                .replace('<esc>', r'\<esc>') if args else ''),
        data.fulldir + '/vim.txt'], env=env))
    with open('vim.txt', 'r') as f:
        stdin = f.read()
    os.remove('vim.txt')
    return stdin

def cmd_wump(self, msg, args, stdin):
    '''
    Plays the `wump` game from `bsdgames` (Hunt the Wumpus).
    '''
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
    '''
    Gets a list of people Kurt has shocked. See also: {prefix}shock
    '''
    return '\n'.join('{}: {}'.format(*x) for x in connect().execute('''
        SELECT name, num FROM shocks ORDER BY num DESC
        ''').fetchall())

def cmd_shock(self, msg, args, stdin):
    '''
    The God of Thunder, the Almighty, the omniscient Kurt Louie in his infinite
    wisdom and grace bestows upon us mere mortals the gift of his electrifying
    rage. See also: {prefix}getshock
    '''
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
    '''
    Evaluates Mathematica code.
    '''
    if not args:
        return 'Please provide Mathematica code to run.'
    p = subprocess.run(['timeout', '-s9', '3',
        '/home/atckmn/mma/scriptdir/wolframscript',
        '-c',
        'Developer`StartProtectedMode[];ToExpression["' + args.replace('\\', '\\\\').replace('"', '\\"') + '"]'], stdout=subprocess.PIPE)
    print(p.returncode)
    return withmd('3 second timeout reached.' if p.returncode == -9 else \
            cf('\u200b'+(p.stdout.decode('utf-8') or '[no output]')))

def cmd_bf(self, msg, args, stdin):
    '''
    Evaluates Brainfuck code. Input not yet supported.
    '''
    if not args:
        return 'Please provide Brainfuck code to run.'
    p = subprocess.run(['./tools/brainfuck', 'tmp'],
            stdout=subprocess.PIPE,
            input=args.encode('utf-8'))
    try:
        os.remove('tmp.c')
        os.remove('tmp.out')
    except OSError: pass
    if p.returncode == 1: return 'Compilation failed.'
    if p.returncode == 124: return '5 second timeout reached.'
    return p.stdout.decode('utf-8') or '[no output]'

def cmd_tio(self, msg, args, stdin):
    '''
    Run {prefix}tio [language] [code] to evaluate code in a given language on
    Try it online! (https://tio.run/). Specify additional sections on a
    separate line consisting of three hashes (###) followed by the section
    name, which can be any of: stdin (provide input), arg (provide any number
    of command line arguments), or stderr (specify this section to view stderr
    output in addition to stdout; you may also retroactively do this with
    {prefix}tio err).
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
        name, data = part.split(None, 1) if '\n' in part or ' ' in part else (part, '')
        name = name.strip()
        if name == 'stdin': stdin = data
        elif name == 'stderr': stderr = True
        elif name == 'arg': args.append(data)
        else: return "Unknown section `{}`".format(name) + err
    try:
        data = requests.post('https://tio.run/cgi-bin/run/api/', zlib.compress(bytes('Vlang\u00001\u0000{}\u0000F.code.tio\u0000{}\u0000{}F.input.tio\u0000{}\u0000{}Vargs\u0000{}{}\u0000R'.format(lang, len(bytes(code, 'utf-8')), code, len(bytes(stdin, 'utf-8')), stdin, len(args), (len(args) * '\u0000{}').format(*args)), 'utf-8'), 9)[2:-4], timeout=5).content.decode('utf-8')
        data = data.split(data[:16])[1:]
        if len(data) == 1: return data[0]  # error
        dout, derr = [x.strip('\n') for x in data[:2]]
        self.tioerr = derr
        haserr = re.search('\nReal time: \\d+\\.\\d+ s\nUser time: \\d+\\.\\d+ s\nSys\\. time: \\d+\\.\\d+ s\nCPU share: \\d+\\.\\d+ %\nExit code: \\d+$', data[1]).start() > 0
        return (dout+'\n--- stderr ---\n'+derr if stderr else dout+('\n[stderr output - use {}tio err to view]'.format(self.prefix) if haserr else '')) or '[no output]'
    except requests.exceptions.ConnectionError:
        return '5 second timeout reached.'

def cmd_eval(self, msg, args, stdin):
    '''
    Evaluate the argument as a kipfa command (do not include the prefix). See
    also: {prefix}exteval
    '''
    return parse.parse(self, args.lstrip('!'), '', msg, False)

def cmd_exteval(self, msg, args, stdin):
    '''
    Evaluate the argument as a kipfa command with extended parsing (do not
    include the prefix). See also: {prefix}eval
    '''
    return parse.parse(self, args.lstrip('!'), '', msg, True)

def ttt_fmt(board):
    s = ''
    for i1 in range(0, 9, 3):
        for i2 in range(0, 9, 3):
            s += ' '.join(''.join(x[i2:i2+3]) for x in board[i1:i1+3]) + '\n'
        s += '\n'
    return withmd(cf(s))

def ttt_check(board):
    for i in range(3):
        s = set(board[i::3])
        if s == {'x'}: return 'x'
        if s == {'o'}: return 'o'
        s = set(board[3*i:3*i+3])
        if s == {'x'}: return 'x'
        if s == {'o'}: return 'o'
    s = set(board[0::4])
    if s == {'x'}: return 'x'
    if s == {'o'}: return 'o'
    s = set(board[2:7:2])
    if s == {'x'}: return 'x'
    if s == {'o'}: return 'o'

def cmd_ttt(self, msg, args, stdin):
    '''
    To start a game of Ultimate Tic-Tac-Toe with someone, type {prefix}ttt
    @username. Explanation:
    https://mathwithbaddrawings.com/2013/06/16/ultimate-tic-tac-toe/
    '''
    with connect() as conn:
        game = conn.execute('''
        SELECT gameid, turn > 1, :u = p1, abs(turn), board
        FROM ttt
        WHERE (p1 = :u OR p2 = :u) AND turn != 0''', {'u': msg.from_user.id}).fetchone()
        if game:
            if game[1] != game[2]: return "It's not your turn!"
            match = re.match(r'([1-9])\s*([1-9])$', args)
            if not match: return 'Move format is two digits 1–9 to select first from the large and then the small board.'
            i1, i2 = int(match.group(1)), int(match.group(2))
            if game[3] != 10 and game[3] != i1: return 'You have to move in large board {}.'.format(game[3])
            board = list(map(list, game[4].split()))
            if board[i1-1][i2-1] != '·': return "Someone's already moved there."
            board[i1-1][i2-1] = 'x' if game[2] else 'o'
            check = ttt_check(board[i1-1])
            if check: board[i1-1] = [check]*9
            newturn = 10 if (ttt_check(board[i2-1]) or '·' not in board[i2-1]) else i2
            won = ttt_check(list(map(ttt_check, board)))
            if won: newturn = 0
            conn.execute('UPDATE ttt SET turn = ?, board = ? WHERE gameid = ?',
                    (newturn * (-1 if game[2] else 1), ' '.join(map(''.join, board)), game[0]))
            return won.upper() + ' wins!' if won else ttt_fmt(board)
        else:
            uid = user2id(args)
            if not uid: return 'To start a game with someone, use !ttt @username.'
            p1, p2 = random.sample([msg.from_user.id, uid], 2)
            conn.execute('INSERT INTO ttt (p1, p2, turn, board) VALUES (?, ?, ?, ?)',
                    (p1, p2, 10, ' '.join(['·'*9]*9)))
            return ('You go' if p1 == msg.from_user.id else args + ' goes') + ' first!'

def cmd_feed(self, msg, args, stdin):
    '''
    Manages Atom or RSS feeds that are posted in a room. Usage: {prefix}feed
    [add|del] [url]. See also: {prefix}getfeed
    '''
    usage = 'Usage: {}feed [add|del] [url]'.format(self.prefix)
    parts = (args or '').split()
    if len(parts) != 2: return usage
    (cmd, url) = parts
    with connect() as conn:
        if cmd == 'add':
            conn.execute('INSERT INTO feeds (url, chat) VALUES (?, ?)', (url, msg.chat.id))
        elif cmd == 'del':
            conn.execute('DELETE FROM feeds WHERE url = ? AND chat = ?', (url, msg.chat.id))
        else: return usage
    return 'Feed will be {} on next {}initfeeds.'.format(
            'added' if cmd == 'add' else 'deleted',
            __import__('admin').prefix)

def cmd_getfeed(self, msg, args, stdin):
    '''
    Gets a list of feeds that are being posted in a room. See also:
    {prefix}feed
    '''
    with connect() as conn:
        return 'Feeds in this room: ' + (', '.join(x[0] for x in conn.execute('SELECT url FROM feeds WHERE chat = ?', (msg.chat.id,)).fetchall()) or '[none]')

def cmd_arslan(self, msg, args, stdin):
    '''
    We are infinitely honored to be graced with these holy messages from the
    Lord himself, the almighty being known to man as Alex Arslan.
    '''
    f = lambda s: re.sub('[^a-z]', '', s.lower())
    arses = open('data/arslan.txt').read().split('\n=====\n')
    return random.choice([ars for ars in arses if f(args) in f(ars)] or arses if args else arses)

def cmd_choose(self, msg, args, stdin):
    '''
    Chooses a random item from a comma-separated list.
    '''
    if not args or ',' not in args:
        return 'Please provide a comma-separated list of items to choose from.'
    return random.choice(args.split(',')).strip()

def cmd_tgguess(self, msg, args, stdin):
    if self.tgguess is not None:
        ret = self.tgguess
        self.tgguess = None
        return ret.replace('/', ', forwarded from ')
    if not hasattr(self, 'tgarr'): self.tgarr = data.init_tgguess()
    (username, text) = random.choice(self.tgarr)
    self.tgguess = username
    return text

def cmd_oeis(self, msg, args, stdin):
    if not args: return 'Please provide a sequence to search.'
    resp = json.loads(requests.get('https://oeis.org/search', params={'fmt':'json', 'q': args}).text)
    if resp['count'] == 0: return 'No results found.'
    res = resp['results'][0]
    q = ', '.join(map(str.strip, args.split(',')))
    return withmd('[A{0:06}](http://oeis.org/A{0:06}) {1} -- {2}'.format(
        res['number'],
        res['name'],
        res['data'].replace(',', ', ').replace(q, '**'+q+'**')))

from difflib import get_close_matches
wordlist = [x[:-1] for x in open('/usr/share/dict/words').readlines()]
def cmd_quote(self, msg, args, stdin):
    args = args or 'its a quote from lord palmerston about schlewswig holstein'
    return re.sub(r"[a-zA-Z']+", lambda m: (get_close_matches(m.group(0), random.sample(wordlist, 50000), 1)+[m.group(0)])[0], args)


def cmd_buffalo(self, msg, args, stdin):
    fname = 'data/buffalo/' + random.choice(os.listdir('data/buffalo'))
    self.reply_photo(msg, fname)


def cmd_alias(self, msg, args, stdin):
    '''
    Creates a synonym for a given kipfa command. Usage: {prefix}alias
    [synonym]=[target command].
    '''
    if not args or '=' not in args:
        return 'Usage: {}alias [src]=[dest]'.format(self.prefix)
    src, dest = args.split('=', 1)
    if src in [s[4:] for s in globals() if s[:4] == 'cmd_']:
        return 'You cannot alias a builtin command.'
    with connect() as conn:
        conn.execute('INSERT OR REPLACE INTO alias (src, dest) VALUES (?, ?)', (src, dest))
        return 'Command successfully aliased.'

def cmd_unalias(self, msg, args, stdin):
    if not args:
        return 'Usage: {}unalias src'.format(self.prefix)
    with connect() as conn:
        rows = conn.execute('DELETE FROM alias WHERE src = ?', (args,)).rowcount
        return 'Deleted {} rows.'.format(rows)

def cmd_perm(self, msg, args, stdin):
    '''
    Manages permissions for a given kipfa command. Usage: {prefix}perm
    [command] [whitelist|blacklist] [user] [duration]. If a duration is not
    specified, it is taken to be permanent. Use "unwhitelist" or "unblacklist"
    to remove a permission directive.
    '''

    usage = 'Usage: {}perm [command] [whitelist|blacklist|unwhitelist|unblacklist] [user] [duration] (omit duration for permanent)'.format(self.prefix)

    parts = (args or '').split(' ')
    if not (3 <= len(parts) <= 4): return usage

    (cmd, action, user, *duration) = parts
    duration = time.time() + float(duration[0]) if duration else INF

    uid = user2id(user)
    if not (cmd == 'ALL' or 'cmd_'+cmd in globals()) or not uid: return usage

    if   action == 'whitelist':   return perm_add(PERM_W, cmd, uid, duration)
    elif action == 'blacklist':   return perm_add(PERM_B, cmd, uid, duration)
    elif action == 'unwhitelist': return perm_add(PERM_W, cmd, uid, 0)
    elif action == 'unblacklist': return perm_add(PERM_B, cmd, uid, 0)
    return usage

def cmd_restart(self, msg, args, stdin):
    '''
    Restarts the bot.
    '''
    self.reply(msg, 'restarting...')
    os._exit(0)

# weights:
# (0) completely innocuous commands
# (1) large output / otherwise annoying
# (2) semi-heavy commands (cpu use, etc)
# (3) heavy commands (network, etc)

names, *info = map(str.split, '''
command     weight
Flypflap    0
alias       0
arslan      1
bf          2
choose      0
commands    0
ddg         3
eval        0
expand      0
exteval     0
extprefix   0
feed        0
flepflap    3
flipflop    3
frink       2
getfeed     0
getperm     0
getshock    0
help        0
js          2
leaderboard 0
mma         2
oeis        3
perm        0
prefix      0
puzhist     1
puzzle      1
quote       2
restart     0
seguess     3
shock       0
soguess     3
steno       2
tgguess     2
tio         3
transcribe  2
translate   3
ttt         1
unalias     0
uptime      0
vim         2
wpm         0
wump        1
'''.strip().split('\n'))

info = dict([cmd, dict(zip(names[1:], props))] for cmd, *props in info)
rate_penalty = [1, 2, 4, 6]
rate_threshold = 50
