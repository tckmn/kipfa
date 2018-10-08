from util import *
import commands


def perm_check(cmd, userid):
    return connect().execute('''
    SELECT EXISTS(SELECT 1 FROM perm WHERE
        ((rule = :w AND (cmd = 'ALL' OR cmd = :cmd) AND userid  = :userid)) AND
        duration > (julianday('now')-2440587.5)*86400.0
    ) OR NOT EXISTS(SELECT 1 FROM perm WHERE
        ((rule = :b AND (cmd = 'ALL' OR cmd = :cmd) AND userid  = :userid) OR
         (rule = :w AND (cmd = 'ALL' OR cmd = :cmd) AND userid != :userid)) AND
        duration > (julianday('now')-2440587.5)*86400.0
    )
    ''', {'cmd': cmd, 'userid': userid, 'w': PERM_W, 'b': PERM_B}).fetchone()[0]


def parse(bot, txt, buf, msg, is_ext=False):
    idx = 0
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
            cmd, args = part.split(None, 1) if ' ' in part or '\n' in part else (part, None)
            if not hasattr(commands, 'cmd_'+cmd):
                return 'The command {} does not exist.'.format(cmd)
            if not perm_check(cmd, msg.from_user.id):
                return 'You do not have permission to execute the {} command.'.format(cmd)
            parts.append((getattr(commands, 'cmd_'+cmd), args))
            part = ''
        elif is_ext and txt[idx] == '\\': parse = False
        else: part += txt[idx]
        idx += 1

    res = ''
    for (func, args) in parts:
        buf = func(bot, msg, buf if args is None else args, buf)
        if type(buf) == tuple:
            res += buf[1] + '\n'
            buf = buf[0]
    return res + buf
