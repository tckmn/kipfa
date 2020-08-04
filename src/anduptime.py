from datetime import *
import pytz

mytz = pytz.timezone('America/Chicago')

def now(): return datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(mytz)
def parse(x): return datetime.fromtimestamp(x, mytz)
def fellasleep(d): return not (5 < d.hour < 23)
def diff(a, b): return (a - b) / timedelta(hours=1)
def slept(a, b): return diff(b, a) > 4 and fellasleep(a)

def fmt(td): return str(timedelta(seconds=int(td.total_seconds() if type(td) is timedelta else td)))

def compute(lastonline, lastwokeup):
    if lastwokeup is None: return 'insufficient data (please wait 1 day cycle or less)'
    cur = now()
    offlinehrs = 0 if lastonline is None else diff(cur, lastonline)
    awaketime = fmt(cur - lastwokeup)
    asleeptime = 0 if lastonline is None else fmt(cur - lastonline)

    # if we've been online in the past half hour or couldn't have fallen asleep
    # when we were last online, assume we're awake
    if offlinehrs < 0.5 or not fellasleep(lastonline): return awaketime

    # otherwise, we might be asleep; return messages of varying certainty if so
    if offlinehrs < 1: return f'probably {awaketime} (but maybe down for {asleeptime})'
    elif offlinehrs < 3: return f'maybe {awaketime}? (or down for {asleeptime})'
    elif offlinehrs < 4: return f'probably down for {asleeptime} (but maybe up for {awaketime})'
    else: return f'down for {asleeptime}'
