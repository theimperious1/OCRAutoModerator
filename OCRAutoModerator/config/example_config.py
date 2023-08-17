""" OCRAutoModerator configuration file
@authors:
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""

__all__ = [
    'db_name', 'db_path', 'reddit_id', 'reddit_secret', 'reddit_pass',
    'reddit_agent', 'reddit_name', 'developers', 'bot_name', 'default_wiki',
    'wiki_permissions_error', 'join_success', 'test_wiki', 'acceptable_languages_easyocr',
    'acceptable_languages_pytesseract', 'universal_lang_codes', 'language_map_easyocr_to_pytes',
    'language_map_pytes_to_easyocr', 'default_comment', 'test_mode'
]

# Bot related options
db_name = 'database.db'  # database name
db_path = f'/home/theimperious1/PycharmProjects/OCRAutoModerator/OCRAutoModerator/database/{db_name}'
bot_name = 'OCRAutoModerator'
developers = ['theimperious1']  # Bot Main Developer
test_mode = True

# Reddit API related options
reddit_id = ''  # client id of the bot application
reddit_secret = ''  # client secret of the bot application
reddit_pass = ''  # password of the redditor the bot is run out of
reddit_agent = 'script:OCRAutoModerator:v2.0.0 (by u/theimperious1)'  # the script's user agent
reddit_name = 'OCRAutoModerator'  # username of the bot account


# Default removal comment
default_comment = 'Sorry, your submission appears to violate our rules and has been removed.'

# Wiki config
default_wiki = '''
# You can add as many rules as you like, but all rules must contain type, rule, action, action_reason, and priority.
# Rules must be formatted as shown below. rules: ["example1", "example2", "etc"]
# Valid actions are remove, report, and nothing.
# Action reason is left as mod notes on removals. It does nothing for reports.
# Priority is required to be unique. Rules will be sorted by priority, and actioned by priority.
# If one rule triggers for a removal, the rest will be ignored.
# If both a removal and report rule are both triggered, removal will take priority. 
# Rule items can be a word, sentence, phrase, whatever. Any text is valid.
# If using backslashes e.g \\, make sure to escape it by adding an extra. \\\\.
---
# The lower the priority, the more important the rule is. 1 = highest.
type: image
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE"]
action: remove
action_reason: "Action reason 1"
comment: |
    "Hi {{author}}, thanks for your submission to /r/{{subreddit}}!
     Unfortunately it appears your submission violates our rules and as such, it has been removed.
     
     If you feel this was in error, [feel free to contact the moderators.](https://www.reddit.com/message/compose?to=/r/{{subreddit}})"
priority: 1
---
# With priority two, if both this and the above rule triggered, the above rule would take priority.
# This rule only works on videos, and will remove content.
type: video
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE", "OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE TWO"]
action: remove
action_reason: "Action reason 2"
priority: 2
---
# This rule works on images/videos/gifs (any) content. It would report.
type: any
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE"]
action: report
action_reason: "Action reason 3"
priority: 3
---
# This rule only works on gifs, and would report.
type: gif
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE"]
action: report
action_reason: "Action reason 4"
priority: 4
---
# This rule works on any content, and does nothing because of the action being "nothing".
type: any
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE"]
action: nothing
action_reason: "Action reason 5"
priority: 5
---
# This rule works on any content, does nothing because of the action being "nothing", and uses the Arabic language.
# Supported languages (p.s use the language code, not the name. i.e "en" not "english"):
# https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html
# https://www.jaided.ai/easyocr/
type: any
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE"]
action: nothing
action_reason: "Action reason 5"
priority: 5
lang: ar
---
'''

wiki_permissions_error = '''
Hey, it seems you forgot to give me the correct permissions. I'm unable to create my wiki config :(  
Please give me "Manage Posts & Comments & Manage Wiki Pages" permissions, then DM me like shown below.  
  
https://www.reddit.com/message/compose/?to=OCRAutoModerator&subject=reset&message=YourSubName
'''

join_success = '''
Hey! It seems like I've got integrated into your subreddit just fine :)  
  
https://www.reddit.com/r/{0}/wiki/edit/ocr_auto_moderator  
  
Make sure to configure my settings and then DM me as shown below to confirm your configuration changes!  
  
https://www.reddit.com/message/compose/?to=OCRAutoModerator&subject=update&message=YourSubName  
  
If you have any problems or questions, feel free to reach out to my creator, /u/theimperious1.
'''

test_wiki = '''
# You can add as many rules as you like, but all rules must contain type, rule, action, action_reason, and priority.
# Rules must be formatted as shown below. rules: ["example1", "example2", "etc"]
# Valid actions are remove, report, and nothing.
# Action reason is left as mod notes on removals. It does nothing for reports.
# Priority is required to be unique. Rules will be sorted by priority, and actioned by priority.
# If one rule triggers for a removal, the rest will be ignored.
# If both a removal and report rule are both triggered, removal will take priority. 
# Rule items can be a word, sentence, phrase, whatever. Any text is valid.
# If using backslashes e.g \\, make sure to escape it by adding an extra. \\\\.
---
# The lower the priority, the more important the rule is. 1 = highest.
type: image
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE"]
action: remove
action_reason: "Bad kitty!"
priority: 1
---
# With priority two, if both this and the above rule triggered, the above rule would take priority.
# This rule only works on videos, and will remove content.
type: video
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE", "OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE TWO"]
action: remove
action_reason: "I am not a cat!"
priority: 2
---
# This rule works on images/videos/gifs (any) content. It would report.
type: any
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE"]
action: report
action_reason: "Meow"
priority: 3
---
# This rule only works on gifs, and would report.
type: gif
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE"]
action: report
action_reason: "I am most definitely NOT a cat!"
priority: 4
---
# This rule works on any content, and does nothing because of the action being "nothing".
type: any
rule: ["OCR AUTOMODERATOR TEST WORD, PHRASE, SENTENCE, ETC EXAMPLE ONE"]
action: nothing
action_reason: "Can you tell that I like cats yet? Yes? Okay. Good. Beep Boop!"
priority: 5
---
'''

acceptable_languages_easyocr = {
    "ab",
    "abq",
    "ady",
    "af",
    "am",
    "amh",
    "ang",
    "ar",
    "as",
    "ava",
    "az",
    "be",
    "bg",
    "bh",
    "bho",
    "bn",
    "bs",
    "ch_pin",
    "ch_sim",
    "ch_tra",
    "che",
    "cs",
    "cy",
    "da",
    "dar",
    "de",
    "en",
    "es",
    "et",
    "fafr",
    "ga",
    "ge",
    "gom",
    "gre",
    "he",
    "hi",
    "hr",
    "hu",
    "id",
    "inh",
    "is",
    "it",
    "ja",
    "kas",
    "kbd",
    "kn",
    "ko",
    "ku",
    "la",
    "lbe",
    "lez",
    "lt",
    "lv",
    "mah",
    "mai",
    "mi",
    "ml",
    "mn",
    "mr",
    "ms",
    "mt",
    "my",
    "ne",
    "new",
    "nl",
    "no",
    "oc",
    "or",
    "pb",
    "pi",
    "pl",
    "ps",
    "pt",
    "ro",
    "rs_cyrillic",
    "rs_latin",
    "ru",
    "sck",
    "sh",
    "sk",
    "sl",
    "sq",
    "sv",
    "sw",
    "ta",
    "tab",
    "te",
    "th",
    "ti",
    "tjk",
    "tl",
    "tr",
    "ug",
    "uk",
    "ur",
    "uz",
    "vi"
}

acceptable_languages_pytesseract = {
    "afr",
    "amh",
    "ara",
    "asm",
    "aze",
    "aze_cyrl",
    "bel",
    "ben",
    "bod",
    "bos",
    "bre",
    "bul",
    "cat",
    "ceb",
    "ces",
    "chi_sim",
    "chi_tra",
    "chr_cos",
    "cym",
    "dan",
    "deu",
    "dzo",
    "ell",
    "eng",
    "enm",
    "epo",
    "equ",
    "est",
    "eus",
    "fao",
    "fas",
    "fil",
    "fin",
    "fra",
    "frk",
    "frm",
    "fry",
    "gla",
    "gle",
    "glg",
    "grc",
    "guj",
    "hat",
    "heb",
    "hin",
    "hrv",
    "hun",
    "hye",
    "iku",
    "ind",
    "isl",
    "ita",
    "ita_old",
    "jav",
    "jpn",
    "kan",
    "kat",
    "kat_old",
    "kaz",
    "khm",
    "kir",
    "kmr",
    "kor",
    "kor_vert",
    "lao",
    "lat",
    "lav",
    "lit",
    "ltz",
    "mal",
    "mar",
    "mkd",
    "mlt",
    "mon",
    "mri",
    "msa",
    "mya",
    "nep",
    "nld",
    "nor",
    "oci",
    "ori",
    "osd",
    "pan",
    "pol",
    "por",
    "pus",
    "que",
    "ron",
    "rus",
    "san",
    "sin",
    "slk",
    "slv",
    "snd",
    "spa",
    "spa_old",
    "sqi",
    "srp",
    "srp_latn",
    "sun",
    "swa",
    "swe",
    "syr",
    "tam",
    "tat",
    "tel",
    "tgk",
    "tha",
    "tir",
    "ton",
    "tur",
    "uig",
    "ukr",
    "urd",
    "uzb",
    "uzb_cyrl",
    "vie",
    "yid",
    "yor"
}

universal_lang_codes = [
    "ga",
    "ady",
    "id",
    "nl",
    "oc",
    "mt",
    "fafr",
    "is",
    "ava",
    "ti",
    "ar",
    "ms",
    "ro",
    "ja",
    "en",
    "ab",
    "bs",
    "tl",
    "ur",
    "no",
    "cy",
    "ps",
    "rs_cyrillic",
    "hr",
    "tr",
    "am",
    "lv",
    "sk",
    "af",
    "mn",
    "kbd",
    "mah",
    "cs",
    "as",
    "sv",
    "or",
    "mr",
    "pl",
    "che",
    "tab",
    "kn",
    "sh",
    "az",
    "lt",
    "ta",
    "bn",
    "ch_tra",
    "ku",
    "ru",
    "uk",
    "mai",
    "abq",
    "sck",
    "pb",
    "bh",
    "ko",
    "la",
    "ch_sim",
    "gre",
    "hu",
    "pt",
    "mi",
    "my",
    "pi",
    "sq",
    "hi",
    "sl",
    "bg",
    "ne",
    "th",
    "lbe",
    "dar",
    "gom",
    "it",
    "sw",
    "he",
    "be",
    "ml",
    "da",
    "uz",
    "new",
    "es",
    "tjk",
    "vi",
    "te",
    "kas",
    "rs_latin",
    "ang",
    "de",
    "et",
    "ug",
    "bho",
    "ch_pin",
    "lez",
    "ge",
    "inh"
]

language_map_easyocr_to_pytes = {
    'ar': 'ara',
    'af': 'afr',
    'as': 'asm',
    'az': 'aze',
    'be': 'bel',
    'bg': 'bul',
    'bn': 'ben',
    'bs': 'bos',
    'cs': 'ces',
    'cy': 'cym',
    'da': 'dan',
    'de': 'deu',
    'en': 'eng',
    'es': 'spa',
    'et': 'est',
    'fa': 'fas',
    'ga': 'gle',
    'hi': 'hin',
    'hr': 'hrv',
    'id': 'ind',
    'is': 'isl',
    'it': 'ita',
    'ja': 'jpn',
    'kn': 'kan',
    'ko': 'kor',
    'la': 'lat',
    'lt': 'lit',
    'lv': 'lav',
    'mi': 'mri',
    'mn': 'mon',
    'mr': 'mar',
    'ms': 'msa',
    'mt': 'mlt',
    'ne': 'nep',
    'nl': 'nld',
    'no': 'nor',
    'oc': 'oci',
    'pl': 'pol',
    'pt': 'por',
    'ro': 'ron',
    'ru': 'rus',
    'rs_cyrillic': 'srp',
    'rc_latin': 'srp_latn',
    'sk': 'slk',
    'sl': 'slv',
    'sq': 'sqi',
    'sv': 'swe',
    'sw': 'swa',
    'ta': 'tam',
    'te': 'tel',
    'th': 'tha',
    'tjk': 'tgk',
    'tr': 'tur',
    'ug': 'uig',
    'uk': 'ukr',
    'ur': 'urd',
    'uz': 'uzb',
    'vi': 'vie'
}

language_map_pytes_to_easyocr = {
    "ara": "ar",
    "afr": "af",
    "asm": "as",
    "aze": "az",
    "bel": "be",
    "bul": "bg",
    "ben": "bn",
    "bos": "bs",
    "ces": "cs",
    "cym": "cy",
    "dan": "da",
    "deu": "de",
    "eng": "en",
    "spa": "es",
    "est": "et",
    "fas": "fa",
    "gle": "ga",
    "hin": "hi",
    "hrv": "hr",
    "ind": "id",
    "isl": "is",
    "ita": "it",
    "jpn": "ja",
    "kan": "kn",
    "kor": "ko",
    "lat": "la",
    "lit": "lt",
    "lav": "lv",
    "mri": "mi",
    "mon": "mn",
    "mar": "mr",
    "msa": "ms",
    "mlt": "mt",
    "nep": "ne",
    "nld": "nl",
    "nor": "no",
    "oci": "oc",
    "pol": "pl",
    "por": "pt",
    "ron": "ro",
    "rus": "ru",
    "srp": "rs_cyrillic",
    "srp_latn": "rc_latin",
    "slk": "sk",
    "slv": "sl",
    "sqi": "sq",
    "swe": "sv",
    "swa": "sw",
    "tam": "ta",
    "tel": "te",
    "tha": "th",
    "tgk": "tjk",
    "tur": "tr",
    "uig": "ug",
    "ukr": "uk",
    "urd": "ur",
    "uzb": "uz",
    "vie": "vi"
}
