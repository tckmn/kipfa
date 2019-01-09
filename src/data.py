import random


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
'''


usernames = {
    'beat-1+5': 'Matthew',
    'The Arsenal': 'Arslan',
    '\\"blund:\\"\\"': 'Dhilan',
    '\\"ishan*tro': 'Daniel',
    'point_only)': 'Ishan',
    'sans': 'John',
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


langs = {
'az': 'Azerbaijan',
'ml': 'Malayalam',
'sq': 'Albanian',
'mt': 'Maltese',
'am': 'Amharic',
'mk': 'Macedonian',
'en': 'English',
'mi': 'Maori',
'ar': 'Arabic',
'mr': 'Marathi',
'hy': 'Armenian',
'mhr': 'Mari',
'af': 'Afrikaans',
'mn': 'Mongolian',
'eu': 'Basque',
'de': 'German',
'ba': 'Bashkir',
'ne': 'Nepali',
'be': 'Belarusian',
'no': 'Norwegian',
'bn': 'Bengali',
'pa': 'Punjabi',
'my': 'Burmese',
'pap': 'Papiamento',
'bg': 'Bulgarian',
'fa': 'Persian',
'bs': 'Bosnian',
'pl': 'Polish',
'cy': 'Welsh',
'pt': 'Portuguese',
'hu': 'Hungarian',
'ro': 'Romanian',
'vi': 'Vietnamese',
'ru': 'Russian',
'ht': 'Haitian (Creole)',
'ceb': 'Cebuano',
'gl': 'Galician',
'sr': 'Serbian',
'nl': 'Dutch',
'si': 'Sinhala',
'mrj': 'Hill Mari',
'sk': 'Slovakian',
'el': 'Greek',
'sl': 'Slovenian',
'ka': 'Georgian',
'sw': 'Swahili',
'gu': 'Gujarati',
'su': 'Sundanese',
'da': 'Danish',
'tg': 'Tajik',
'he': 'Hebrew',
'th': 'Thai',
'yi': 'Yiddish',
'tl': 'Tagalog',
'id': 'Indonesian',
'ta': 'Tamil',
'ga': 'Irish',
'tt': 'Tatar',
'it': 'Italian',
'te': 'Telugu',
'is': 'Icelandic',
'tr': 'Turkish',
'es': 'Spanish',
'udm': 'Udmurt',
'kk': 'Kazakh',
'uz': 'Uzbek',
'kn': 'Kannada',
'uk': 'Ukrainian',
'ca': 'Catalan',
'ur': 'Urdu',
'ky': 'Kyrgyz',
'fi': 'Finnish',
'zh': 'Chinese',
'fr': 'French',
'ko': 'Korean',
'hi': 'Hindi',
'xh': 'Xhosa',
'hr': 'Croatian',
'km': 'Khmer',
'cs': 'Czech',
'lo': 'Laotian',
'sv': 'Swedish',
'la': 'Latin',
'gd': 'Scottish',
'lv': 'Latvian',
'et': 'Estonian',
'lt': 'Lithuanian',
'eo': 'Esperanto',
'lb': 'Luxembourgish',
'jv': 'Javanese',
'mg': 'Malagasy',
'ja': 'Japanese',
'ms': 'Malay'
}


triggers = [

    (r'(?i)\bwhere (are|r) (you|u|y\'?all)\b|\bwhere (you|u|y\'?all) at\b',
     0.5,
     lambda _: 'NUMBERS NIGHT CLUB'),

    (r'(?i)mountain|\brock|cluster',
     0.3,
     lambda _: (random.choice([
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
     0.1,
     lambda _: 'lol no generics')

]


xsIn = ['_R_F', 'J\\_<', '_H_T', 'G\\_<', '_B_L', '|\\|\\', 'r\\`', '<R>', 'g_<', '<F>', 'd_<', 'b_<', '_?\\', 'z\\', 'z`', 'X\\', 'x\\', '_x', '_X', '_w', 'v\\', '_v', 'U\\', 't`', '_t', '_T', 's\\', 's`', 'r\\', 'r`', '_r', 'R\\', '_R', '_q', 'p\\', '_o', 'O\\', '_O', 'n`', '_n', 'N\\', '_N', '_m', 'M\\', '_M', 'l\\', 'l`', '_l', 'L\\', '_L', '_k', 'K\\', 'j\\', '_j', 'J\\', 'I\\', 'h\\', '_h', 'H\\', '_H', 'G\\', '_G', '_F', '_e', 'd`', '_d', '_c', 'B\\', '_B', '_a', '_A', '3\\', '_0', '@\\', '?\\', '!\\', ':\\', '-\\', '_+', '_\\', '_}', '_"', '_/', '_-', '_>', '_=', '_~', '_^', '|\\', '||', '>\\', '=\\', '<\\', 'Z', 'z', 'y', 'Y', 'X', 'x', 'w', 'W', 'v', 'V', 'u', 'U', 'T', 't', 's', 'S', 'r', 'R', 'q', 'Q', 'p', 'P', 'O', 'o', 'N', 'n', 'm', 'M', 'l', 'L', 'k', 'K', 'j', 'J', 'i', 'I', 'h', 'H', 'g', 'G', 'f', 'F', 'E', 'e', '@', 'D', 'd', 'C', 'c', 'B', 'b', '{', 'a', 'A', '9', '8', '7', '6', '5', '4', '3', '2', '1', '%', '&', '}', '"', '\'', '.', '?', '!', ':', '|', '=', '~', '^', '`']
ipaOut = ['᷈', 'ʄ', '᷄', 'ʛ', '᷅', 'ǁ', 'ɻ', '↗', 'ɠ', '↘', 'ɗ', 'ɓ', 'ˤ', 'ʑ', 'ʐ', 'ħ', 'ɧ', '̽', '̆', 'ʷ', 'ʋ', '̬', 'ᵿ', 'ʈ', '̤', '̋', 'ɕ', 'ʂ', 'ɹ', 'ɽ', '̝', 'ʀ', '̌', '̙', 'ɸ', '̞', 'ʘ', '̹', 'ɳ', 'ⁿ', 'ɴ', '̼', '̻', 'ɰ', '̄', 'ɺ', 'ɭ', 'ˡ', 'ʟ', '̀', '̰', 'ɮ', 'ʝ', 'ʲ', 'ɟ', 'ᵻ', 'ɦ', 'ʰ', 'ʜ', '́', 'ɢ', 'ˠ', '̂', '̴', 'ɖ', '̪', '̜', 'ʙ', '̏', '̺', '̘', 'ɞ', '̥', 'ɘ', 'ʕ', 'ǃ', 'ˑ', '‿', '̟', '̂', '̚', '̈', '̌', '̠', 'ʼ', '̩', '̃', '̯', 'ǀ', '‖', 'ʡ', 'ǂ', 'ʢ', 'ʒ', 'z', 'y', 'ʏ', 'χ', 'x', 'w', 'ʍ', 'v', 'ʌ', 'u', 'ʊ', 'θ', 't', 's', 'ʃ', 'r', 'ʁ', 'q', 'ɒ', 'p', 'ʋ', 'ɔ', 'o', 'ŋ', 'n', 'm', 'ɯ', 'l', 'ʎ', 'k', 'ɬ', 'j', 'ɲ', 'i', 'ɪ', 'h', 'ɥ', 'ɡ', 'ɣ', 'f', 'ɱ', 'ɛ', 'e', 'ə', 'ð', 'd', 'ç', 'c', 'β', 'b', 'æ', 'a', 'ɑ', 'œ', 'ɵ', 'ɤ', 'ɐ', 'ɫ', 'ɾ', 'ɜ', 'ø', 'ɨ', 'ˌ', 'ɶ', 'ʉ', 'ˈ', 'ʲ', '.', 'ʔ', 'ꜜ', 'ː', '|', '̩', '̃', 'ꜛ', '˞']
