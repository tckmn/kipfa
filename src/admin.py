import traceback

from util import *


prefix = '>>'
userid = 212594557
username = 'tckmn'


def cmd_eval(bot, args):
    try:
        return cf(repr(eval(args)))
    except Exception as e:
        return cf(traceback.format_exc())


from pyrogram.api import types, functions
def cmd_updateusers(bot, args):
    count = 0
    with connect() as conn:
        for ch in bot.client.send(functions.messages.GetAllChats([])).chats:
            if isinstance(ch, types.Channel) and not ch.broadcast:
                count += 1
                conn.executemany('''
                INSERT OR REPLACE INTO nameid (name, userid) VALUES (?, ?)
                ''', [(u.username, u.id) for u in bot.client.send(
                    functions.channels.GetParticipants(
                        bot.client.peers_by_id[-1000000000000-ch.id],
                        types.ChannelParticipantsRecent(),
                        0, 0, 0
                        )
                    ).users if u.username])
        nusers = conn.execute('SELECT COUNT(*) FROM nameid').fetchone()[0]
        return 'updated {} users in {} chats'.format(nusers, count)


def cmd_quota(bot, args):
    return str(bot.quota)


def cmd_daily(bot, args):
    bot.daily()


def cmd_checkwebsites(bot, args):
    bot.checkwebsites()


from bs4 import BeautifulSoup
from io import StringIO
import xml.etree.ElementTree as ET
import re

class Req:
    def __init__(self, url, query, callback, rooms):
        self.url = url
        self.query = query
        self.callback = callback
        self.rooms = rooms
        self.val = self.update()
    def update(self):
        try:
            resp = get(self.url)
            return None if resp is None else self.query(resp)
        except:
            __import__('kipfa').client.send_message(Chats.testing, 'error in req '+self.url)
            return None
    def go(self):
        newval = self.update()
        if newval and self.val != newval:
            if self.val: yield self.callback(newval)
            self.val = newval
    def __repr__(self):
        return self.val

class Feed:
    def __init__(self, url, rooms):
        self.url = url
        self.rooms = rooms
        self.guids = guids(url)
    def go(self):
        if self.guids is None:
            self.guids = guids(self.url)
            return []
        feed = getfeed(self.url)
        if feed is None: return []
        if feed.tag == 'rss': return self.send_rss(feed)
        else: return self.send_atom(feed)
    def send_feed(self, guid, text):
        if guid not in self.guids:
            yield text
            self.guids.add(guid)
    def send_rss(self, feed):
        for item in feed[0].findall('item'):
            text = item.find('link').text
            if self.url == 'http://xkcd.com/rss.xml':
                try: text += ' ' + BeautifulSoup(item.find('description').text, 'html.parser').find('img').attrs['title']
                except: pass
            elif self.url == 'http://www.smbc-comics.com/rss.php':
                try: text += ' ' + BeautifulSoup(item.find('description').text, 'html.parser').contents[1].contents[2]
                except: pass
            for x in self.send_feed(item.find('guid').text, text): yield x
    def send_atom(self, feed):
        for item in feed.findall('entry'):
            a = item.find('link').attrib
            for x in self.send_feed(item.find('id').text, a['href']): yield x

def getfeed(feed):
    print('getfeed({})'.format(feed))
    text = get(feed)
    if text is None: return None
    if feed == 'http://www.archr.org/atom.xml':
        text = text.replace(' & ', ' &amp; ')

    try:
        # https://stackoverflow.com/a/33997423/1223693
        it = ET.iterparse(StringIO(text))
        for _, el in it:
            el.tag = el.tag[el.tag.find('}')+1:]
            for at in el.attrib.keys():
                if '}' in at:
                    el.attrib[at[at.find('}')+1:]] = el.attrib[at]
                    del el.attrib[at]
        return it.root
    except:
        __import__('kipfa').client.send_message(Chats.testing, 'error in feed '+feed)
        return None

def guids(url):
    feed = getfeed(url)
    if feed is None: return None
    if feed.tag == 'rss':
        return set(x.find('guid').text for x in feed[0].findall('item'))
    else:
        return set(x.find('id').text for x in feed.findall('entry'))

def cmd_initfeeds(bot, args):
    bot.feeds = [
        Req('https://lichess.org/training/daily',
            lambda text: re.search(r'"puzzle":.*?"fen":"([^"]+)', text).group(1),
            lambda val: 'obtw new uotd',
            [Chats.haxorz]),
        Req('https://www.sjsreview.com/?s=',
            lambda text: BeautifulSoup(text, 'lxml').find('h2').find('a').attrs['href'].replace(' ', '%20'),
            lambda val: val,
            [Chats.schmett]),
        Req('https://www.voanoticias.com/z/537',
            lambda text: BeautifulSoup(text, 'lxml').find('div', id='content').find('div', class_='content').find('a').attrs['href'],
            lambda val: 'https://www.voanoticias.com'+val,
            [Chats.mariposa]),
        Req('https://kernel.org/',
            lambda text: BeautifulSoup(text, 'lxml').find('td', id='latest_link').text.strip(),
            lambda val: 'kernel '+val+' released',
            [Chats.haxorz]),
        Req('https://twitter.com/billwurtz',
            lambda text: BeautifulSoup(text, 'html5lib').find('p', class_='tweet-text').text,
            lambda val: val,
            [Chats.haxorz])
    ]
    feeds = dict()
    with connect() as conn:
        for (url, chat) in conn.execute('SELECT url, chat FROM feeds').fetchall():
            if url in feeds: feeds[url].append(chat)
            else: feeds[url] = [chat]
    for (url, chats) in feeds.items(): bot.feeds.append(Feed(url, chats))
