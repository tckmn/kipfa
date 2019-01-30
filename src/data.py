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
['stackoverflow.com', 17003338],
['serverfault.com', 269544],
['superuser.com', 394092],
['meta.stackexchange.com', 88537],
['webapps.stackexchange.com', 25895],
['gaming.stackexchange.com', 85020],
['webmasters.stackexchange.com', 31257],
['cooking.stackexchange.com', 20666],
['gamedev.stackexchange.com', 44805],
['photo.stackexchange.com', 22081],
['stats.stackexchange.com', 134514],
['math.stackexchange.com', 1040358],
['diy.stackexchange.com', 42350],
['gis.stackexchange.com', 107354],
['tex.stackexchange.com', 169887],
['askubuntu.com', 313210],
['money.stackexchange.com', 24032],
['english.stackexchange.com', 104194],
['stackapps.com', 2439],
['ux.stackexchange.com', 27067],
['unix.stackexchange.com', 154888],
['wordpress.stackexchange.com', 92898],
['cstheory.stackexchange.com', 9901],
['apple.stackexchange.com', 94814],
['rpg.stackexchange.com', 31366],
['bicycles.stackexchange.com', 12653],
['softwareengineering.stackexchange.com', 52197],
['electronics.stackexchange.com', 112836],
['android.stackexchange.com', 49995],
['boardgames.stackexchange.com', 10052],
['physics.stackexchange.com', 132405],
['homebrew.stackexchange.com', 5465],
['security.stackexchange.com', 50892],
['writing.stackexchange.com', 7672],
['video.stackexchange.com', 6289],
['graphicdesign.stackexchange.com', 26884],
['dba.stackexchange.com', 72126],
['scifi.stackexchange.com', 51865],
['codereview.stackexchange.com', 57289],
['codegolf.stackexchange.com', 10285],
['quant.stackexchange.com', 12048],
['pm.stackexchange.com', 4741],
['skeptics.stackexchange.com', 9040],
['fitness.stackexchange.com', 8059],
['drupal.stackexchange.com', 79603],
['mechanics.stackexchange.com', 18773],
['parenting.stackexchange.com', 5656],
['sharepoint.stackexchange.com', 85606],
['music.stackexchange.com', 14898],
['sqa.stackexchange.com', 8514],
['judaism.stackexchange.com', 27484],
['german.stackexchange.com', 11390],
['japanese.stackexchange.com', 17707],
['philosophy.stackexchange.com', 11823],
['gardening.stackexchange.com', 10745],
['travel.stackexchange.com', 34116],
['crypto.stackexchange.com', 18107],
['dsp.stackexchange.com', 16618],
['french.stackexchange.com', 8140],
['christianity.stackexchange.com', 10775],
['bitcoin.stackexchange.com', 22105],
['linguistics.stackexchange.com', 6677],
['hermeneutics.stackexchange.com', 6157],
['history.stackexchange.com', 9816],
['bricks.stackexchange.com', 2704],
['spanish.stackexchange.com', 6085],
['scicomp.stackexchange.com', 7516],
['movies.stackexchange.com', 16948],
['chinese.stackexchange.com', 6484],
['biology.stackexchange.com', 21587],
['poker.stackexchange.com', 1574],
['mathematica.stackexchange.com', 57521],
['psychology.stackexchange.com', 5768],
['outdoors.stackexchange.com', 4711],
['martialarts.stackexchange.com', 1506],
['sports.stackexchange.com', 4587],
['academia.stackexchange.com', 26582],
['cs.stackexchange.com', 28836],
['workplace.stackexchange.com', 21052],
['windowsphone.stackexchange.com', 3498],
['chemistry.stackexchange.com', 28569],
['chess.stackexchange.com', 4648],
['raspberrypi.stackexchange.com', 25064],
['russian.stackexchange.com', 3437],
['islam.stackexchange.com', 9712],
['salesforce.stackexchange.com', 84923],
['patents.stackexchange.com', 3506],
['genealogy.stackexchange.com', 2645],
['robotics.stackexchange.com', 4434],
['expressionengine.stackexchange.com', 12172],
['politics.stackexchange.com', 7536],
['anime.stackexchange.com', 10076],
['magento.stackexchange.com', 84280],
['ell.stackexchange.com', 58403],
['sustainability.stackexchange.com', 1426],
['tridion.stackexchange.com', 6284],
['reverseengineering.stackexchange.com', 5741],
['networkengineering.stackexchange.com', 11571],
['opendata.stackexchange.com', 4625],
['freelancing.stackexchange.com', 1621],
['blender.stackexchange.com', 47442],
['mathoverflow.net', 99188],
['space.stackexchange.com', 9415],
['sound.stackexchange.com', 8731],
['astronomy.stackexchange.com', 6834],
['tor.stackexchange.com', 5150],
['pets.stackexchange.com', 5515],
['ham.stackexchange.com', 2426],
['italian.stackexchange.com', 2483],
['pt.stackoverflow.com', 118952],
['aviation.stackexchange.com', 14154],
['ebooks.stackexchange.com', 1233],
['alcohol.stackexchange.com', 923],
['softwarerecs.stackexchange.com', 16422],
['arduino.stackexchange.com', 16578],
['expatriates.stackexchange.com', 4888],
['matheducators.stackexchange.com', 2312],
['earthscience.stackexchange.com', 4388],
['joomla.stackexchange.com', 5751],
['datascience.stackexchange.com', 14188],
['puzzling.stackexchange.com', 15465],
['craftcms.stackexchange.com', 10494],
['buddhism.stackexchange.com', 5453],
['hinduism.stackexchange.com', 8946],
['communitybuilding.stackexchange.com', 495],
['worldbuilding.stackexchange.com', 19681],
['ja.stackoverflow.com', 17550],
['emacs.stackexchange.com', 15300],
['hsm.stackexchange.com', 2205],
['economics.stackexchange.com', 7490],
['lifehacks.stackexchange.com', 2317],
['engineering.stackexchange.com', 7255],
['coffee.stackexchange.com', 1033],
['vi.stackexchange.com', 6751],
['musicfans.stackexchange.com', 2281],
['woodworking.stackexchange.com', 2420],
['civicrm.stackexchange.com', 9508],
['medicalsciences.stackexchange.com', 5398],
['ru.stackoverflow.com', 248065],
['rus.stackexchange.com', 14994],
['mythology.stackexchange.com', 1390],
['law.stackexchange.com', 11419],
['opensource.stackexchange.com', 2231],
['elementaryos.stackexchange.com', 6138],
['portuguese.stackexchange.com', 1550],
['computergraphics.stackexchange.com', 2214],
['hardwarerecs.stackexchange.com', 2559],
['es.stackoverflow.com', 78177],
['3dprinting.stackexchange.com', 1946],
['ethereum.stackexchange.com', 24400],
['latin.stackexchange.com', 2564],
['languagelearning.stackexchange.com', 818],
['retrocomputing.stackexchange.com', 1888],
['crafts.stackexchange.com', 1112],
['korean.stackexchange.com', 990],
['monero.stackexchange.com', 3276],
['ai.stackexchange.com', 2922],
['esperanto.stackexchange.com', 1176],
['sitecore.stackexchange.com', 5781],
['iot.stackexchange.com', 1139],
['literature.stackexchange.com', 2382],
['vegetarianism.stackexchange.com', 489],
['ukrainian.stackexchange.com', 1639],
['devops.stackexchange.com', 2116],
['bioinformatics.stackexchange.com', 1666],
['cseducators.stackexchange.com', 634],
['interpersonal.stackexchange.com', 2821],
['augur.stackexchange.com', 333],
['iota.stackexchange.com', 819],
['stellar.stackexchange.com', 801],
['conlang.stackexchange.com', 224],
['quantumcomputing.stackexchange.com', 973],
['eosio.stackexchange.com', 1544]
]



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


np = lambda _: random.choice([
    'no problem', 'np', 'you\'re welcome', 'my pleasure'
    ]) + ' ' + random.choice([
    '', 'friend', 'buddy', 'pal'
    ])
fu = lambda _: ':('

triggers = [

    (r'(?i)(?<!no )thank(s| you) kipfa', 1, False, np),
    (r'(?i)(?<!no )thank', 1, True, np),
    (r'(?i)fuck you kipfa', 1, False, fu),
    (r'(?i)fuck you', 1, True, fu),

    (r'(?i)\bwhere (are|r) (you|u|y\'?all)\b|\bwhere (you|u|y\'?all) at\b',
     0.5, False,
     lambda _: 'NUMBERS NIGHT CLUB'),

    (r'(?i)mountain|\brock|cluster',
     0.3, False,
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
     0.1, False,
     lambda _: 'lol no generics')

]


xsIn = ['_R_F', 'J\\_<', '_H_T', 'G\\_<', '_B_L', '|\\|\\', 'r\\`', '<R>', 'g_<', '<F>', 'd_<', 'b_<', '_?\\', 'z\\', 'z`', 'X\\', 'x\\', '_x', '_X', '_w', 'v\\', '_v', 'U\\', 't`', '_t', '_T', 's\\', 's`', 'r\\', 'r`', '_r', 'R\\', '_R', '_q', 'p\\', '_o', 'O\\', '_O', 'n`', '_n', 'N\\', '_N', '_m', 'M\\', '_M', 'l\\', 'l`', '_l', 'L\\', '_L', '_k', 'K\\', 'j\\', '_j', 'J\\', 'I\\', 'h\\', '_h', 'H\\', '_H', 'G\\', '_G', '_F', '_e', 'd`', '_d', '_c', 'B\\', '_B', '_a', '_A', '3\\', '_0', '@\\', '?\\', '!\\', ':\\', '-\\', '_+', '_\\', '_}', '_"', '_/', '_-', '_>', '_=', '_~', '_^', '|\\', '||', '>\\', '=\\', '<\\', 'Z', 'z', 'y', 'Y', 'X', 'x', 'w', 'W', 'v', 'V', 'u', 'U', 'T', 't', 's', 'S', 'r', 'R', 'q', 'Q', 'p', 'P', 'O', 'o', 'N', 'n', 'm', 'M', 'l', 'L', 'k', 'K', 'j', 'J', 'i', 'I', 'h', 'H', 'g', 'G', 'f', 'F', 'E', 'e', '@', 'D', 'd', 'C', 'c', 'B', 'b', '{', 'a', 'A', '9', '8', '7', '6', '5', '4', '3', '2', '1', '%', '&', '}', '"', '\'', '.', '?', '!', ':', '|', '=', '~', '^', '`']
ipaOut = ['᷈', 'ʄ', '᷄', 'ʛ', '᷅', 'ǁ', 'ɻ', '↗', 'ɠ', '↘', 'ɗ', 'ɓ', 'ˤ', 'ʑ', 'ʐ', 'ħ', 'ɧ', '̽', '̆', 'ʷ', 'ʋ', '̬', 'ᵿ', 'ʈ', '̤', '̋', 'ɕ', 'ʂ', 'ɹ', 'ɽ', '̝', 'ʀ', '̌', '̙', 'ɸ', '̞', 'ʘ', '̹', 'ɳ', 'ⁿ', 'ɴ', '̼', '̻', 'ɰ', '̄', 'ɺ', 'ɭ', 'ˡ', 'ʟ', '̀', '̰', 'ɮ', 'ʝ', 'ʲ', 'ɟ', 'ᵻ', 'ɦ', 'ʰ', 'ʜ', '́', 'ɢ', 'ˠ', '̂', '̴', 'ɖ', '̪', '̜', 'ʙ', '̏', '̺', '̘', 'ɞ', '̥', 'ɘ', 'ʕ', 'ǃ', 'ˑ', '‿', '̟', '̂', '̚', '̈', '̌', '̠', 'ʼ', '̩', '̃', '̯', 'ǀ', '‖', 'ʡ', 'ǂ', 'ʢ', 'ʒ', 'z', 'y', 'ʏ', 'χ', 'x', 'w', 'ʍ', 'v', 'ʌ', 'u', 'ʊ', 'θ', 't', 's', 'ʃ', 'r', 'ʁ', 'q', 'ɒ', 'p', 'ʋ', 'ɔ', 'o', 'ŋ', 'n', 'm', 'ɯ', 'l', 'ʎ', 'k', 'ɬ', 'j', 'ɲ', 'i', 'ɪ', 'h', 'ɥ', 'ɡ', 'ɣ', 'f', 'ɱ', 'ɛ', 'e', 'ə', 'ð', 'd', 'ç', 'c', 'β', 'b', 'æ', 'a', 'ɑ', 'œ', 'ɵ', 'ɤ', 'ɐ', 'ɫ', 'ɾ', 'ɜ', 'ø', 'ɨ', 'ˌ', 'ɶ', 'ʉ', 'ˈ', 'ʲ', '.', 'ʔ', 'ꜜ', 'ː', '|', '̩', '̃', 'ꜛ', '˞']
