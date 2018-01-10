#!/usr/bin/python3

import os
import re
import sys
import time

from pyrogram import Client
from pyrogram.api import types, functions

import speech_recognition as sr

import requests

import data
sys.path.insert(0, './steno-keyboard-generator')
import keyboard

def xtoi(s):
    s = s[1:]
    for (x, i) in zip(data.xsIn, data.ipaOut): s = s.replace(x, i)
    return s

def getuotd():
    r = requests.get('https://lichess.org/training/daily')
    return r.text[r.text.find('og:title')+33:].split()[0]

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
        self.uotd = getuotd()
        self.recog = sr.Recognizer()

    def cmd_help(self, msg, args):
        self.reply(msg, 'For a list of commands, type {}commands. Source code: https://github.com/KeyboardFire/kipfa'.format(self.prefix))

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

    def checkuotd(self):
        newuotd = getuotd()
        if self.uotd != newuotd:
            self.uotd = newuotd
            client.send_message(1059322065, 'obtw new uotd')

    def reply(self, msg, txt):
        print(txt)
        client.send_message(msg.to_id.channel_id, txt, reply_to_msg_id=msg.id)

    def reply_photo(self, msg, path):
        print(path)
        client.send_photo(msg.to_id.channel_id, path#, reply_to_msg_id=msg.id)
                )

    def process_message(self, msg):
        txt = msg.message

        if hasattr(msg, 'media'):
            media = msg.media
            if isinstance(msg.media, types.MessageMediaDocument):
                doc = media.document
                if doc.mime_type == 'audio/ogg':
                    fname = '{}_{}_0.jpg'.format(doc.id, doc.access_hash)
                    client.get_file(doc.dc_id, doc.id, doc.access_hash)
                    os.system('ffmpeg -i {} out.wav'.format(fname))
                    os.remove(fname)
                    with sr.AudioFile('out.wav') as source:
                        audio = self.recog.record(source)
                    self.reply(msg, self.recog.recognize_sphinx(audio))
                    os.remove('out.wav')

        if not txt: return

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

        if re.fullmatch(r'S?T?K?P?W?H?R?A?O?\*?-?E?U?F?R?P?B?L?G?T?S?D?Z?', txt):
            m = re.search(r'[AO*\-EU]+', txt)
            dups = 'SPTR'
            keyboard.draw_keyboard_to_png(
                    [s+('-' if s in dups else '') for s in txt[:m.start()]] +
                    [s for s in m.group() if s != '-'] +
                    [('-' if s in dups else '')+s for s in txt[m.end():]],
                    'tmp.png')
            self.reply_photo(msg, 'tmp.png')

    def callback(self, update):
        if isinstance(update, types.Update):
            for u in update.updates: self.callback(u)
        elif isinstance(update, types.UpdateNewChannelMessage):
            msg = update.message
            # print(msg.to_id.channel_id)
            # if msg.to_id.channel_id in [
            #             1032618176, # schmett
            #             1059322065, # 0x
            #             1224278565, # superbots
            #         ]:
            print(msg)
            self.process_message(msg)

client = Client('meemerino')
bot = Bot(client)
client.set_update_handler(bot.callback)
client.start()

while True:
    time.sleep(5 * 60)
    bot.checkuotd()
