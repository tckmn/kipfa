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
