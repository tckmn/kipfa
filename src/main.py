#!/usr/bin/python3

import time
from threading import Thread
from pyrogram import Client, MessageHandler
import kipfa
from util import *

kipfa.client = Client('kipfa')
bot = kipfa.Bot(kipfa.client)
kipfa.client.add_handler(MessageHandler(bot.callback))
kipfa.client.start()
kipfa.client.send_message(Chats.testing, 'bot started')

tick = 0
while True:
    tick += 1
    try:
        time.sleep(1)
        lt = time.localtime()
        if lt.tm_hour == 22 and lt.tm_min == 50:
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
