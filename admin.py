from util import *


prefix = '>>'
userid = 212594557


def cmd_eval(bot, args):
    return repr(eval(args))


from pyrogram.api import types, functions
def cmd_updateusers(bot, args):
    count = 0
    with connect() as conn:
        for ch in bot.client.send(functions.messages.GetAllChats([])).chats:
            if isinstance(ch, types.Channel):
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
    def __init__(self, url, query, callback):
        self.url = url
        self.query = query
        self.callback = callback
        self.val = self.update()
    def update(self):
        resp = get(self.url)
        return None if resp is None else self.query(resp)
    def go(self, client):
        newval = self.update()
        if newval and self.val != newval:
            if self.val: self.callback(client, newval)
            self.val = newval
    def __repr__(self):
        return self.val

class Feed:
    def __init__(self, url, room):
        self.url = url
        self.room = room
        self.guids = guids(url)
    def go(self, client):
        if self.guids is None:
            self.guids = guids(self.url)
            return
        feed = getfeed(self.url)
        if feed is None: return
        if feed.tag == 'rss': self.send_rss(client, feed)
        else: self.send_atom(client, feed)
    def send_feed(self, client, guid, text):
        if guid not in self.guids:
            client.send_message(self.room, text)
            self.guids.add(guid)
    def send_rss(self, client, feed):
        for item in feed[0].findall('item'):
            text = item.find('link').text
            if self.url == 'http://xkcd.com/rss.xml':
                text += ' ' + BeautifulSoup(item.find('description').text, 'html.parser').find('img').attrs['title']
            elif self.url == 'http://www.smbc-comics.com/rss.php':
                text += ' ' + BeautifulSoup(item.find('description').text, 'html.parser').contents[1].contents[2]
            self.send_feed(client, item.find('guid').text, text)
    def send_atom(self, client, feed):
        for item in feed.findall('entry'):
            a = item.find('link').attrib
            self.send_feed(client, item.find('id').text, a['href'])

def getfeed(feed):
    print('getfeed({})'.format(feed))
    text = get(feed)
    if text is None: return None
    if feed == 'http://www.archr.org/atom.xml':
        text = text.replace(' & ', ' &amp; ')

    # https://stackoverflow.com/a/33997423/1223693
    it = ET.iterparse(StringIO(text))
    for _, el in it:
        el.tag = el.tag[el.tag.find('}')+1:]
        for at in el.attrib.keys():
            if '}' in at:
                el.attrib[at[at.find('}')+1:]] = el.attrib[at]
                del el.attrib[at]

    return it.root

def guids(url):
    feed = getfeed(url)
    if feed is None: return None
    if feed.tag == 'rss':
        return set(x.find('guid').text for x in feed[0].findall('item'))
    else:
        return set(x.find('id').text for x in feed.findall('entry'))

def cmd_initfeeds(bot, args):
    bot.feeds = [
        Feed('http://xkcd.com/rss.xml', Chats.haxorz),
        Feed('http://what-if.xkcd.com/feed.atom', Chats.haxorz),
        Feed('http://www.smbc-comics.com/rss.php', Chats.haxorz),
        Feed('http://feeds.feedburner.com/PoorlyDrawnLines?format=xml', Chats.haxorz),
        Feed('http://www.commitstrip.com/en/feed/', Chats.haxorz),
        Feed('https://mathwithbaddrawings.com/feed/', Chats.haxorz),
        Feed('http://feeds.feedburner.com/InvisibleBread', Chats.haxorz),
        Feed('http://www.archr.org/atom.xml', Chats.haxorz),
        Feed('http://existentialcomics.com/rss.xml', Chats.haxorz),
        Feed('http://feeds.feedburner.com/codinghorror?format=xml', Chats.haxorz),
        Feed('http://thecodelesscode.com/rss', Chats.haxorz),
        Feed('https://lichess.org/blog.atom', Chats.haxorz),
        Feed('http://keyboardfire.com/blog.xml', Chats.haxorz),
        Feed('https://en.wiktionary.org/w/api.php?action=featuredfeed&feed=fwotd', Chats.haxorz),
        Req('https://lichess.org/training/daily',
            lambda text: re.search(r'"puzzle":.*?"fen":"([^"]+)', text).group(1),
            lambda client, val: client.send_message(Chats.haxorz, 'obtw new uotd')),
        Req('https://www.sjsreview.com/?s=',
            lambda text: BeautifulSoup(text, 'lxml').find('h2').find('a').attrs['href'].replace(' ', '%20'),
            lambda client, val: client.send_message(Chats.schmett, val)),
        Req('https://www.voanoticias.com/z/537',
            lambda text: BeautifulSoup(text, 'lxml').find('div', id='content').find('div', class_='content').find('a').attrs['href'],
            lambda client, val: client.send_message(Chats.mariposa, 'https://www.voanoticias.com'+val)),
        Req('https://kernel.org/',
            lambda text: BeautifulSoup(text, 'lxml').find('td', id='latest_link').text.strip(),
            lambda client, val: client.send_message(Chats.haxorz, 'kernel '+val+' released')),
        Req('https://twitter.com/billwurtz',
            lambda text: BeautifulSoup(text, 'html5lib').find('p', class_='tweet-text').text,
            lambda client, val: client.send_message(Chats.haxorz, val))
    ]