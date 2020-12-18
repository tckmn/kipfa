import random
import os


fulldir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


schema = '''
CREATE TABLE IF NOT EXISTS nameid (
    name        TEXT UNIQUE NOT NULL,
    userid      INTEGER UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS perm (
    rule        TEXT NOT NULL,
    cmd         TEXT NOT NULL,
    userid      INTEGER NOT NULL,
    duration    REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS puztime (
    userid      INTEGER UNIQUE NOT NULL,
    nextguess   REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS puzhist (
    level       INTEGER PRIMARY KEY,
    userid      INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS shocks (
    name        TEXT UNIQUE NOT NULL,
    num         INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS alias (
    src         TEXT UNIQUE NOT NULL,
    dest        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feeds (
    url         TEXT NOT NULL,
    chat        INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ttt (
    gameid      INTEGER PRIMARY KEY,
    p1          INTEGER NOT NULL,
    p2          INTEGER NOT NULL,
    turn        INTEGER NOT NULL,
    board       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dailies (
    dailyid     INTEGER PRIMARY KEY,
    hour        INTEGER NOT NULL,
    minute      INTEGER NOT NULL,
    message     TEXT NOT NULL
);
'''

saveattrs = [
    'extprefix', 'lastwokeup', 'prefix', 'quota', 'seguess', 'soguess',
    'tgguess', 'tioerr', 'wpm'
]


usernames = {
    'beat-1+5': 'Matthew',
    'The Arsenal': 'Arslan',
    '\\"blund:\\"\\"': 'Dhilan',
    '\\"ishan*tro': 'Daniel',
    'point_only)': 'Ishan',
    'sans': 'Riley',
    "alcohol'": 'Sebastian'
}

def init_tgguess():
    with open('data/db.json') as f:
        active = False
        things = []
        username = None
        for line in f:
            if active:
                if line[:13] == '    "name": "': break
                if line[:15] == '      "from": "': username = line[15:-3]
                if line[:25] == '      "forwarded_from": "': username += '/' + line[25:-3]
                if line[:15] == '      "text": "' \
                        and len(line[15:-2]) > 5 \
                        and line[15:-2].count(' ') > 1:
                    things.append((line[15:-2].replace('\\"', '"').replace('\\n', '\n'), username))
            else:
                if line == '    "name": "0x4r514n",\n': active = True
        dups = set()
        seen = set()
        for (text, username) in things:
            if text in seen:
                dups.add(text)
            else:
                seen.add(text)
        return [(t,u) for (t,u) in things if t not in dups]


sites = [
['stackoverflow.com', 17389056],
['serverfault.com', 271501],
['superuser.com', 400037],
['meta.stackexchange.com', 89176],
['webapps.stackexchange.com', 26562],
['gaming.stackexchange.com', 85495],
['webmasters.stackexchange.com', 31404],
['cooking.stackexchange.com', 20810],
['gamedev.stackexchange.com', 44941],
['photo.stackexchange.com', 22019],
['stats.stackexchange.com', 136328],
['math.stackexchange.com', 1072578],
['diy.stackexchange.com', 43500],
['gis.stackexchange.com', 108335],
['tex.stackexchange.com', 172661],
['askubuntu.com', 316948],
['money.stackexchange.com', 24563],
['english.stackexchange.com', 105246],
['stackapps.com', 2446],
['ux.stackexchange.com', 27212],
['unix.stackexchange.com', 157880],
['wordpress.stackexchange.com', 93593],
['cstheory.stackexchange.com', 9934],
['apple.stackexchange.com', 95173],
['rpg.stackexchange.com', 32729],
['bicycles.stackexchange.com', 12836],
['softwareengineering.stackexchange.com', 52665],
['electronics.stackexchange.com', 115558],
['android.stackexchange.com', 49731],
['boardgames.stackexchange.com', 10279],
['physics.stackexchange.com', 134981],
['homebrew.stackexchange.com', 5529],
['security.stackexchange.com', 51753],
['writing.stackexchange.com', 8192],
['video.stackexchange.com', 6164],
['graphicdesign.stackexchange.com', 27222],
['dba.stackexchange.com', 72787],
['scifi.stackexchange.com', 53207],
['codereview.stackexchange.com', 58588],
['codegolf.stackexchange.com', 10441],
['quant.stackexchange.com', 12146],
['pm.stackexchange.com', 4843],
['skeptics.stackexchange.com', 9144],
['fitness.stackexchange.com', 8132],
['drupal.stackexchange.com', 79597],
['mechanics.stackexchange.com', 19257],
['parenting.stackexchange.com', 5677],
['sharepoint.stackexchange.com', 86260],
['music.stackexchange.com', 15626],
['sqa.stackexchange.com', 8707],
['judaism.stackexchange.com', 28331],
['german.stackexchange.com', 11844],
['japanese.stackexchange.com', 18253],
['philosophy.stackexchange.com', 12131],
['gardening.stackexchange.com', 11120],
['travel.stackexchange.com', 35069],
['crypto.stackexchange.com', 18420],
['dsp.stackexchange.com', 16572],
['french.stackexchange.com', 8488],
['christianity.stackexchange.com', 11014],
['bitcoin.stackexchange.com', 22018],
['linguistics.stackexchange.com', 6896],
['hermeneutics.stackexchange.com', 6465],
['history.stackexchange.com', 10111],
['bricks.stackexchange.com', 2803],
['spanish.stackexchange.com', 6291],
['scicomp.stackexchange.com', 7594],
['movies.stackexchange.com', 17320],
['chinese.stackexchange.com', 6745],
['biology.stackexchange.com', 21658],
['poker.stackexchange.com', 1604],
['mathematica.stackexchange.com', 59308],
['psychology.stackexchange.com', 5812],
['outdoors.stackexchange.com', 4816],
['martialarts.stackexchange.com', 1536],
['sports.stackexchange.com', 4628],
['academia.stackexchange.com', 27334],
['cs.stackexchange.com', 29682],
['workplace.stackexchange.com', 22067],
['windowsphone.stackexchange.com', 3460],
['chemistry.stackexchange.com', 28635],
['chess.stackexchange.com', 4778],
['raspberrypi.stackexchange.com', 25319],
['russian.stackexchange.com', 3552],
['islam.stackexchange.com', 9813],
['salesforce.stackexchange.com', 86785],
['patents.stackexchange.com', 3579],
['genealogy.stackexchange.com', 2760],
['robotics.stackexchange.com', 4392],
['expressionengine.stackexchange.com', 12044],
['politics.stackexchange.com', 8005],
['anime.stackexchange.com', 10158],
['magento.stackexchange.com', 86047],
['ell.stackexchange.com', 60835],
['sustainability.stackexchange.com', 1450],
['tridion.stackexchange.com', 6349],
['reverseengineering.stackexchange.com', 5666],
['networkengineering.stackexchange.com', 11791],
['opendata.stackexchange.com', 4585],
['freelancing.stackexchange.com', 1637],
['blender.stackexchange.com', 49640],
['mathoverflow.net', 100882],
['space.stackexchange.com', 9988],
['sound.stackexchange.com', 8640],
['astronomy.stackexchange.com', 7081],
['tor.stackexchange.com', 4774],
['pets.stackexchange.com', 5672],
['ham.stackexchange.com', 2555],
['italian.stackexchange.com', 2556],
['pt.stackoverflow.com', 122852],
['aviation.stackexchange.com', 14893],
['ebooks.stackexchange.com', 1250],
['alcohol.stackexchange.com', 936],
['softwarerecs.stackexchange.com', 17049],
['arduino.stackexchange.com', 16922],
['expatriates.stackexchange.com', 4981],
['matheducators.stackexchange.com', 2364],
['earthscience.stackexchange.com', 4501],
['joomla.stackexchange.com', 5668],
['datascience.stackexchange.com', 14577],
['puzzling.stackexchange.com', 16140],
['craftcms.stackexchange.com', 10603],
['buddhism.stackexchange.com', 5636],
['hinduism.stackexchange.com', 9798],
['communitybuilding.stackexchange.com', 497],
['worldbuilding.stackexchange.com', 20608],
['ja.stackoverflow.com', 18246],
['emacs.stackexchange.com', 15491],
['hsm.stackexchange.com', 2289],
['economics.stackexchange.com', 7441],
['lifehacks.stackexchange.com', 2391],
['engineering.stackexchange.com', 7282],
['coffee.stackexchange.com', 1060],
['vi.stackexchange.com', 6823],
['musicfans.stackexchange.com', 2357],
['woodworking.stackexchange.com', 2503],
['civicrm.stackexchange.com', 9721],
['medicalsciences.stackexchange.com', 5501],
['ru.stackoverflow.com', 259289],
['rus.stackexchange.com', 15877],
['mythology.stackexchange.com', 1437],
['law.stackexchange.com', 11848],
['opensource.stackexchange.com', 2370],
['elementaryos.stackexchange.com', 5859],
['portuguese.stackexchange.com', 1592],
['computergraphics.stackexchange.com', 2248],
['hardwarerecs.stackexchange.com', 2627],
['es.stackoverflow.com', 85340],
['3dprinting.stackexchange.com', 2140],
['ethereum.stackexchange.com', 24834],
['latin.stackexchange.com', 2729],
['languagelearning.stackexchange.com', 845],
['retrocomputing.stackexchange.com', 2058],
['crafts.stackexchange.com', 1160],
['korean.stackexchange.com', 1039],
['monero.stackexchange.com', 3218],
['ai.stackexchange.com', 3291],
['esperanto.stackexchange.com', 1213],
['sitecore.stackexchange.com', 6322],
['iot.stackexchange.com', 1220],
['literature.stackexchange.com', 2590],
['vegetarianism.stackexchange.com', 509],
['ukrainian.stackexchange.com', 1722],
['devops.stackexchange.com', 2409],
['bioinformatics.stackexchange.com', 1891],
['cseducators.stackexchange.com', 662],
['interpersonal.stackexchange.com', 3012],
['augur.stackexchange.com', 339],
['iota.stackexchange.com', 832],
['stellar.stackexchange.com', 878],
['conlang.stackexchange.com', 237],
['quantumcomputing.stackexchange.com', 1214],
['eosio.stackexchange.com', 1680],
['tezos.stackexchange.com', 362]
]

langs = {
  "af": "Afrikaans",
  "ar": "Arabic",
  "bg": "Bulgarian",
  "bn": "Bangla",
  "bs": "Bosnian",
  "ca": "Catalan",
  "cs": "Czech",
  "cy": "Welsh",
  "da": "Danish",
  "de": "German",
  "el": "Greek",
  "en": "English",
  "es": "Spanish",
  "et": "Estonian",
  "fa": "Persian",
  "fi": "Finnish",
  "fil": "Filipino",
  "fj": "Fijian",
  "fr": "French",
  "ga": "Irish",
  "gu": "Gujarati",
  "he": "Hebrew",
  "hi": "Hindi",
  "hr": "Croatian",
  "ht": "Haitian Creole",
  "hu": "Hungarian",
  "id": "Indonesian",
  "is": "Icelandic",
  "it": "Italian",
  "ja": "Japanese",
  "kk": "Kazakh",
  "kmr": "Kurdish (Northern)",
  "kn": "Kannada",
  "ko": "Korean",
  "ku": "Kurdish (Central)",
  "lt": "Lithuanian",
  "lv": "Latvian",
  "mg": "Malagasy",
  "mi": "Maori",
  "ml": "Malayalam",
  "mr": "Marathi",
  "ms": "Malay",
  "mt": "Maltese",
  "mww": "Hmong Daw",
  "nb": "Norwegian",
  "nl": "Dutch",
  "or": "Odia",
  "otq": "Querétaro Otomi",
  "pa": "Punjabi",
  "pl": "Polish",
  "prs": "Dari",
  "ps": "Pashto",
  "pt": "Portuguese (Brazil)",
  "pt-pt": "Portuguese (Portugal)",
  "ro": "Romanian",
  "ru": "Russian",
  "sk": "Slovak",
  "sl": "Slovenian",
  "sm": "Samoan",
  "sr-Cyrl": "Serbian (Cyrillic)",
  "sr-Latn": "Serbian (Latin)",
  "sv": "Swedish",
  "sw": "Swahili",
  "ta": "Tamil",
  "te": "Telugu",
  "th": "Thai",
  "tlh-Latn": "Klingon (Latin)",
  "tlh-Piqd": "Klingon (pIqaD)",
  "to": "Tongan",
  "tr": "Turkish",
  "ty": "Tahitian",
  "uk": "Ukrainian",
  "ur": "Urdu",
  "vi": "Vietnamese",
  "yua": "Yucatec Maya",
  "yue": "Cantonese (Traditional)",
  "zh-Hans": "Chinese Simplified",
  "zh-Hant": "Chinese Traditional"
}

langsgood = [ "af", "ar", "bg", "bn", "bs", "ca", "zh-Hans", "cs", "cy", "da", "de", "el", "es", "et", "fa", "fi", "ht", "fr", "he", "hi", "hr", "hu", "id", "is", "it", "ja", "ko", "lt", "lv", "mt", "ms", "mww", "nl", "nb", "pl", "pt", "ro", "ru", "sk", "sl", "sr-Latn", "sv", "sw", "ta", "th", "tlh-Latn", "tr", "uk", "ur", "vi" ]


np = lambda *_: random.choice([
    'no problem', 'np', 'you\'re welcome', 'my pleasure'
    ]) + ' ' + random.choice([
    '', 'friend', 'buddy', 'pal'
    ])
fu = lambda *_: ':('

isprime = lambda n: f'{n} is{"" if all(n%x for x in range(2, int(n**0.5))) else " not"} prime'

triggers = [

    (r'(?i)(?<!no )thank(s| you) kipfa', 1, False, np),
    (r'(?i)(?<!no )thank', 1, True, np),
    (r'(?i)fuck you kipfa', 1, False, fu),
    (r'(?i)fuck you', 1, True, fu),

    (r'(?i)\bwhere (are|r) (you|u|y\'?all)\b|\bwhere (you|u|y\'?all) at\b',
     0.01, False,
     lambda *_: 'NUMBERS NIGHT CLUB'),

    (r'(?i)mountain|\brock|cluster',
     0.01, False,
     lambda *_: (random.choice([
         'aftershock', 'airlock', 'air lock', 'air sock', 'alarm clock',
         'antiknock', 'arawak', 'around the clock', 'atomic clock',
         'authorized stock', 'baby talk', 'bach', 'balk', 'ballcock',
         'ball cock', 'bangkok', 'bedrock', 'biological clock', 'bloc',
         'block', 'boardwalk', 'bock', 'brock', 'building block', 'calk',
         'capital stock', 'catwalk', 'caudal block', 'caulk', 'chalk',
         'chalk talk', 'chicken hawk', 'chock', 'chopping block',
         'cinder block', 'clock', 'combination lock', 'common stock',
         'control stock', 'crock', 'crosstalk', 'crosswalk', 'cuckoo clock',
         'cylinder block', 'deadlock', 'doc', 'dock', 'double talk',
         'dry dock', 'eastern hemlock', 'electric shock', 'electroshock',
         'engine block', 'en bloc', 'fish hawk', 'flintlock', 'floating dock',
         'floc', 'flock', 'french chalk', 'frock', 'gamecock', 'gawk',
         'goshawk', 'grandfather clock', 'gridlock', 'growth stock',
         'hammerlock', 'hawk', 'haycock', 'heart block', 'hemlock', 'hoc',
         'hock', 'hollyhock', 'insulin shock', 'interlock', 'iraq', 'jaywalk',
         'jock', 'johann sebastian bach', 'john hancock', 'john locke',
         'kapok', 'knock', 'lady\'s smock', 'laughingstock', 'letter stock',
         'line block', 'livestock', 'loch', 'lock', 'locke', 'manioc', 'maroc',
         'marsh hawk', 'matchlock', 'medoc', 'mental block', 'mock', 'mohawk',
         'mosquito hawk', 'nighthawk', 'nock', 'o\'clock', 'oarlock',
         'office block', 'out of wedlock', 'overstock', 'padauk', 'padlock',
         'peacock', 'penny stock', 'pigeon hawk', 'pillow block', 'pock',
         'poison hemlock', 'poppycock', 'post hoc', 'preferred stock',
         'restock', 'roadblock', 'roc', 'rock', 'rolling stock',
         'round the clock', 'sales talk', 'sauk', 'schlock', 'scotch woodcock',
         'shamrock', 'shell shock', 'sherlock', 'shock', 'sidewalk',
         'sleepwalk', 'small talk', 'smock', 'snatch block', 'sock',
         'space walk', 'sparrow hawk', 'squawk', 'stalk', 'starting block',
         'stock', 'stumbling block', 'sweet talk', 'table talk', 'take stock',
         'talk', 'time clock', 'tomahawk', 'tower block', 'treasury stock',
         'turkey cock', 'unblock', 'undock', 'unfrock', 'unlock', 'vapor lock',
         'voting stock', 'walk', 'war hawk', 'watered stock', 'water clock',
         'water hemlock', 'wedlock', 'wheel lock', 'widow\'s walk',
         'wind sock', 'wok', 'woodcock', 'writer\'s block', 'yellow dock'
         ]) + ' ' + random.choice([
         'adjuster', 'adjuster', 'adjustor', 'blockbuster', 'bluster',
         'buster', 'cluster', 'combustor', 'custard', 'duster', 'filibuster',
         'fluster', 'ghosebuster', 'ghostbuster', 'just her', 'knuckle duster',
         'lackluster', 'luster', 'lustre', 'mustard', 'muster', 'thruster',
         'trust her'
         ])).upper() + ' ' + ''.join(random.choice('˥˦˧˨˩') for _ in range(50))),

    (r'(?i)\bgo\b',
     0.01, False,
     lambda *_: 'lol no generics'),

    (r'(?i)is (\d{1,10}) prime',
     1, False,
     lambda _, res: isprime(int(res.group(1))))

]


xsIn = ['_R_F', 'J\\_<', '_H_T', 'G\\_<', '_B_L', '|\\|\\', 'r\\`', '<R>', 'g_<', '<F>', 'd_<', 'b_<', '_?\\', 'z\\', 'z`', 'X\\', 'x\\', '_x', '_X', '_w', 'v\\', '_v', 'U\\', 't`', '_t', '_T', 's\\', 's`', 'r\\', 'r`', '_r', 'R\\', '_R', '_q', 'p\\', '_o', 'O\\', '_O', 'n`', '_n', 'N\\', '_N', '_m', 'M\\', '_M', 'l\\', 'l`', '_l', 'L\\', '_L', '_k', 'K\\', 'j\\', '_j', 'J\\', 'I\\', 'h\\', '_h', 'H\\', '_H', 'G\\', '_G', '_F', '_e', 'd`', '_d', '_c', 'B\\', '_B', '_a', '_A', '3\\', '_0', '@\\', '?\\', '!\\', ':\\', '-\\', '_+', '_\\', '_}', '_"', '_/', '_-', '_>', '_=', '_~', '_^', '|\\', '||', '>\\', '=\\', '<\\', 'Z', 'z', 'y', 'Y', 'X', 'x', 'w', 'W', 'v', 'V', 'u', 'U', 'T', 't', 's', 'S', 'r', 'R', 'q', 'Q', 'p', 'P', 'O', 'o', 'N', 'n', 'm', 'M', 'l', 'L', 'k', 'K', 'j', 'J', 'i', 'I', 'h', 'H', 'g', 'G', 'f', 'F', 'E', 'e', '@', 'D', 'd', 'C', 'c', 'B', 'b', '{', 'a', 'A', '9', '8', '7', '6', '5', '4', '3', '2', '1', '%', '&', '}', '"', '\'', '.', '?', '!', ':', '|', '=', '~', '^', '`']
ipaOut = ['᷈', 'ʄ', '᷄', 'ʛ', '᷅', 'ǁ', 'ɻ', '↗', 'ɠ', '↘', 'ɗ', 'ɓ', 'ˤ', 'ʑ', 'ʐ', 'ħ', 'ɧ', '̽', '̆', 'ʷ', 'ʋ', '̬', 'ᵿ', 'ʈ', '̤', '̋', 'ɕ', 'ʂ', 'ɹ', 'ɽ', '̝', 'ʀ', '̌', '̙', 'ɸ', '̞', 'ʘ', '̹', 'ɳ', 'ⁿ', 'ɴ', '̼', '̻', 'ɰ', '̄', 'ɺ', 'ɭ', 'ˡ', 'ʟ', '̀', '̰', 'ɮ', 'ʝ', 'ʲ', 'ɟ', 'ᵻ', 'ɦ', 'ʰ', 'ʜ', '́', 'ɢ', 'ˠ', '̂', '̴', 'ɖ', '̪', '̜', 'ʙ', '̏', '̺', '̘', 'ɞ', '̥', 'ɘ', 'ʕ', 'ǃ', 'ˑ', '‿', '̟', '̂', '̚', '̈', '̌', '̠', 'ʼ', '̩', '̃', '̯', 'ǀ', '‖', 'ʡ', 'ǂ', 'ʢ', 'ʒ', 'z', 'y', 'ʏ', 'χ', 'x', 'w', 'ʍ', 'v', 'ʌ', 'u', 'ʊ', 'θ', 't', 's', 'ʃ', 'r', 'ʁ', 'q', 'ɒ', 'p', 'ʋ', 'ɔ', 'o', 'ŋ', 'n', 'm', 'ɯ', 'l', 'ʎ', 'k', 'ɬ', 'j', 'ɲ', 'i', 'ɪ', 'h', 'ɥ', 'ɡ', 'ɣ', 'f', 'ɱ', 'ɛ', 'e', 'ə', 'ð', 'd', 'ç', 'c', 'β', 'b', 'æ', 'a', 'ɑ', 'œ', 'ɵ', 'ɤ', 'ɐ', 'ɫ', 'ɾ', 'ɜ', 'ø', 'ɨ', 'ˌ', 'ɶ', 'ʉ', 'ˈ', 'ʲ', '.', 'ʔ', 'ꜜ', 'ː', '|', '̩', '̃', 'ꜛ', '˞']
