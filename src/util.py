# database
import sqlite3
def connect(): return sqlite3.connect('kipfa.db')

# turn userid into @username
def usernamify(userid):
    return (connect().execute('''
            SELECT "@" || name FROM nameid WHERE userid = ?
            ''', (userid,)).fetchone() or [str(userid)])[0]

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

# network
import requests
import kipfa
def get(url):
    try:
        return requests.get(url, timeout=3).text
    except requests.exceptions.Timeout:
        kipfa.client.send_message(Chats.testing, 'request timed out: ' + url)
        return None
