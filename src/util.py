# database
import sqlite3
def connect(): return sqlite3.connect('kipfa.db')

# convert between userid and @username
def usernamify(userid):
    return (connect().execute('''
            SELECT "@" || name FROM nameid WHERE userid = ?
            ''', (userid,)).fetchone() or [str(userid)])[0]
def user2id(name):
    if name and name[0] == '@': name = name[1:]
    uid = connect().execute('SELECT userid FROM nameid WHERE name = ?', (name,)).fetchone()
    if uid: return uid[0]

# permissions
PERM_W = 'WHITELIST'
PERM_B = 'BLACKLIST'
INF = float('inf')

# chats
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
    zendo    = -1001168099998

# network
import requests
import kipfa
def get(url, headers={}):
    try:
        return requests.get(url, timeout=3, headers=headers).text
    except requests.exceptions.Timeout:
        kipfa.client.send_message(Chats.testing, 'request timed out: ' + url)
        return None

# markdown
import re
def cf(s):
    return '```' + s.strip().replace('```', '`\u200b`\u200b`') + '```'
withmd = lambda x: (x, {'parse_mode': 'markdown'})

forcetuple = lambda x: x if type(x) is tuple else (x, {})

# latex
import os
import subprocess
def latex(l, d):
    os.mkdir(d)
    with open(d+'/a.tex', 'w') as f:
        f.write('''
        \\documentclass{standalone}
        \\usepackage{amsmath}
        \\usepackage{amsfonts}
        \\usepackage{mathtools}
        \\usepackage{eufrak}
        \\usepackage{txfonts}
        \\usepackage{xcolor}
        \\usepackage{cancel}
        \\begin{document}
        $X$
        \\end{document}
        '''.replace('X', l))
    subprocess.run(['timeout', '-s9', '3',
        'bash', '-c',
        'cd {};'.format(d) +
        'openout_any=p openin_any=p shell_escape=f pdflatex a.tex </dev/null;' +
        'convert -density 200 -background white -alpha remove -bordercolor White -border 5x5 a.pdf a.png'
        ])

import time
def mnow(msg):
    realnow = time.time()
    return msg.date if abs(msg.date - realnow) > 1 else realnow
