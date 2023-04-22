""" OCRAutoModerator configuration file
@authors:
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""

__all__ = [
    'db_name', 'db_path', 'reddit_id', 'reddit_secret', 'reddit_pass',
    'reddit_agent', 'reddit_name', 'developers', 'bot_name', 'default_wiki',
    'wiki_permissions_error', 'join_success', 'test_wiki'
]

# Bot related options
db_name = 'database.db'  # database name
db_path = f'/path/to/database/{db_name}'  # path to database
bot_name = 'OCRAutoModerator'  # name of the bot (used in logging)
developers = ['theimperious1']  # bot developers

# Reddit API related options
reddit_id = ''  # client id of the bot application
reddit_secret = ''  # client secret of the bot application
reddit_pass = ''  # password of the redditor the bot is run out of
reddit_agent = 'script:OCRAutoModerator:v1.1.1 (by u/theimperious1)'  # the script's user agent
reddit_name = ''  # username of the bot account

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
