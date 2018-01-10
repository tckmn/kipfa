#!/usr/bin/python3

import re
import os

from pyrogram import Client
from pyrogram.api import types

import data

def xtoi(s):
    s = s[1:]
    for (x, i) in zip(data.xsIn, data.ipaOut): s = s.replace(x, i)
    return s

class Perm:

    def __init__(self, whitelist, blacklist):
        self.whitelist = whitelist
        self.blacklist = blacklist

    def __str__(self):
        return 'whitelist: {}, blacklist: {}'.format(self.whitelist, self.blacklist)

    def check(self, id):
        return (not self.whitelist or id in self.whitelist) and (id not in self.blacklist)

class Bot:

    def __init__(self, client):
        self.client = client
        self.prefix = '!'
        self.commands = {
            'help':     (self.cmd_help,     Perm([], [])),
            'commands': (self.cmd_commands, Perm([], [])),
            'prefix':   (self.cmd_prefix,   Perm([212594557], [])),
            'getperm':  (self.cmd_getperm,  Perm([], [])),
            'js':       (self.cmd_js,       Perm([], [])),
            'restart':  (self.cmd_restart,  Perm([212594557], []))
        }

    def cmd_help(self, msg, args):
        self.reply(msg, 'For a list of commands, type {}commands.'.format(self.prefix))

    def cmd_commands(self, msg, args):
        self.reply(msg, ', '.join(self.commands.keys()))

    def cmd_prefix(self, msg, args):
        if args:
            self.prefix = args
            self.reply(msg, 'Prefix updated.')
        else:
            self.reply(msg, 'Please specify a prefix to set.')

    def cmd_getperm(self, msg, args):
        if args in self.commands:
            self.reply(msg, 'Permissions for command {}: {}.'.format(args, self.commands[args][1]))
        elif args:
            self.reply(msg, 'Unknown command {}.'.format(args))
        else:
            self.reply(msg, 'Please specify a command name.')

    def cmd_js(self, msg, args):
        self.reply(msg, os.popen("""node -e 'var Sandbox = require("./node_modules/sandbox"), s = new Sandbox(); s.options.timeout = 2000; s.run("{}", function(x) {{ console.log(x.result == "TimeoutError" ? "2 second timeout reached." : x.result); }});'""".format(args.replace('\\', '\\\\').replace("'", "'\\''").replace('"', '\\"'))).read())

    def cmd_restart(self, msg, args):
        self.reply(msg, 'restarting...')
        self.client.stop()
        os._exit(0)

    def reply(self, msg, txt):
        print(txt)
        client.send_message(msg.to_id.channel_id, txt, reply_to_msg_id=msg.id)

    def process_message(self, msg):
        txt = msg.message

        if txt[:len(self.prefix)] == self.prefix:
            cmd, *args = txt[len(self.prefix):].split(' ', 1)
            args = args[0] if len(args) else None
            if cmd in self.commands:
                (func, perms) = self.commands[cmd]
                if perms.check(msg.from_id):
                    func(msg, args)
                else:
                    self.reply(msg, 'You do not have the permission to execute that command.')

        matches = re.findall(r'\bx/[^/]*/|\bx\[[^]]*\]', txt)
        if matches:
            self.reply(msg, '\n'.join(map(xtoi, matches)))

    def callback(self, update):
        if isinstance(update, types.Update):
            for u in update.updates: self.callback(u)
        elif isinstance(update, types.UpdateNewChannelMessage):
            msg = update.message
            # print(msg.to_id.channel_id)
            if msg.to_id.channel_id in [
                        1032618176, # schmett
                        1059322065, # 0x
                        1224278565, # superbots
                    ]:
                print(msg)
                self.process_message(msg)

client = Client('meemerino')
bot = Bot(client)
client.set_update_handler(bot.callback)
client.start()
client.idle()
