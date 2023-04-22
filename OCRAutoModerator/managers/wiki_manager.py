""" OCRAutoModerator Wiki Manager & functions
@authors:
---
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""

import logging
import re
from collections import namedtuple
import yaml
from praw.models import Subreddit
from OCRAutoModerator.config import default_wiki, bot_name, join_success, wiki_permissions_error, developers
from OCRAutoModerator.utils import is_user_mod
from OCRAutoModerator.utils import log_and_reply

logger = logging.getLogger(__name__)

RuleDefinition = namedtuple('RuleDefinition', 'yaml values')
# valid options for changing how a field value is searched for a match
_match_regexes = {
    "full-exact": u"^%s$",
    "full-text": r"^\W*%s\W*$",
    "includes": u"%s",
    "includes-word": r"(?:^|\W|\b)%s(?:$|\W|\b)",
    "starts-with": u"^%s",
    "ends-with": u"%s$",
}

# full list of modifiers that can be applied to a match
_match_modifiers = set(_match_regexes.keys()) | {
    "case-sensitive",
    "regex",
}


# noinspection PyBroadException
class WikiParser:

    def __init__(self, reddit, wiki_configs):
        self.reddit = reddit
        self.wiki_configs = wiki_configs

    async def on_subreddit_join(self, msg) -> None:
        sub_name = msg.subreddit.display_name
        sub = self.reddit.subreddit(sub_name)
        try:
            if not await self.check_wiki_exists(sub):
                self.wiki_configs[sub_name.lower()] = await self.create_wiki(sub)
                self.reddit.subreddit(sub_name).message(
                    f'{bot_name} has been setup correctly!', join_success.format(sub_name))
                logger.info(f'Created Wiki Config for /r/{sub_name}')
        except:
            logger.info(f'Failed to create Wiki Config for /r/{sub_name}')
            self.reddit.subreddit(sub_name).message(f'Permissions issue with {bot_name}', wiki_permissions_error)

    async def on_wiki_update_request(self, msg) -> None:
        sub_name = msg.body.replace('r/', '').replace('/', '').lower()
        try:
            subreddit = self.reddit.subreddit(sub_name)
            if await is_user_mod(subreddit, msg.author):
                if msg.subject == 'update':
                    try:
                        self.wiki_configs[sub_name.lower()] = await self.load_wiki_config(subreddit)
                        log_and_reply(msg, f'Wiki revision was successful! Changes have been applied to /r/{sub_name}.')
                    except Exception as e:
                        msg.reply(
                            body=f"Sorry, seems like theres an error with your configuration. Here's the error: {e}")
                        logger.info(f'Wiki Update failed on /r/{sub_name}')
                elif msg.subject == 'reset':
                    try:
                        if not await self.check_wiki_exists(sub_name):
                            self.wiki_configs[sub_name.lower()] = await self.create_wiki(sub_name)
                            self.reddit.subreddit(sub_name).message(
                                f'{bot_name} has been setup correctly!', join_success.format(sub_name))
                            logger.info(f'Created Wiki Config for /r/{sub_name}')
                        else:
                            self.wiki_configs[sub_name.lower()] = await self.reset(subreddit)
                            msg.reply(body=f'Wiki was reset successful! Changes have been applied to /r/{sub_name}.')
                            logger.info(f'Wiki Reset complete on /r/{sub_name}')

                    except Exception as e:
                        msg.reply(
                            body=f"Sorry, seems like theres an error with your configuration. Here's the error: {e}")
                        logger.info(f'Wiki Reset failed on /r/{sub_name}')
            else:
                msg.reply(
                    f"Sorry, seems like you're not a moderator of that subreddit. If this is in error, contact /u/{developers[0]}.")
                logger.info(f"/u/{msg.author} tried to update config on sub they're not a moderator of. /r/{sub_name}")
        except Exception as e:
            logger.info(e)
            logger.info(
                f'/u/{msg.author} tried to update the configuration of a subreddit that does not exist: {sub_name}')

    @staticmethod
    def parse(config: str) -> list:
        rule_defs = []
        yaml_sections = [section.strip('\r\n')
                         for section in re.split('^---', config, flags=re.MULTILINE)]
        for section_num, section in enumerate(yaml_sections, 1):
            try:
                parsed = yaml.safe_load(section)

            except Exception as e:
                raise ValueError(
                    'YAML parsing error in section %s: %s' % (section_num, e))

            # only keep the section if the parsed result is a dict (otherwise
            # it's generally just a comment)
            if isinstance(parsed, dict):
                rule_defs.append(parsed)

        return rule_defs

    @staticmethod
    def validate_config(config) -> bool:
        priorities = []
        for section in config:
            if 'type' not in section:
                raise ValueError("'type' parameter is missing")
            elif 'rule' not in section:
                raise ValueError("'rule' parameter is missing")
            elif 'action' not in section:
                raise ValueError("'action' parameter is missing")
            elif 'action_reason' not in section:
                raise ValueError("'action_reason' parameter is missing")
            elif 'priority' not in section:
                raise ValueError("'priority' parameter is missing")

            if type(section['type']) is not str:
                raise TypeError("'type' parameter is not a string/text e.g \"any\"")
            elif type(section['rule']) is not list:
                raise TypeError("'rule' parameter is a list e.g [\"example\", \"example\"]")
            elif type(section['action']) is not str:
                raise TypeError("'action' parameter is not a string/text e.g \"report\"")
            elif type(section['action_reason']) is not str:
                raise TypeError("'action_reason' parameter is not a string/text e.g \"No Profanity\"")
            elif type(section['priority']) is not int:
                raise TypeError("'priority' parameter is not a number e.g 1")

            priority = section['priority']
            if priority < 1 or priority > 2000:
                raise ValueError("'priority' cannot be lower than 1 or higher than 2000")

            if len(section['rule']) > 2000:
                raise ValueError("'rule' cannot contain more than 2000 items")

            for item in section['rule']:
                if type(item) is not str:
                    raise TypeError(
                        "An item in the rule list is not a string/text. It should look like [\"example1\", \"example2\"]")

                if len(item) > 1000:
                    raise ValueError("Items in 'rule' cannot be longer than 1000 characters")

            priorities.append(section['priority'])

        duplicates = [priority for priority in priorities if priorities.count(priority) > 1]
        if len(duplicates) > 0:
            raise ValueError("More than one rule has the same priority as another. Priority must be unique.")

        return True

    @staticmethod
    async def check_wiki_exists(subreddit: Subreddit) -> bool:
        """ Check if wiki exists in specified subreddit """
        if f'{subreddit.display_name}/ocr_auto_moderator' in subreddit.wiki:
            return True
        return False

    async def create_wiki(self, subreddit: Subreddit):
        """ Creates a wiki with the specified data """
        subreddit.wiki.create('ocr_auto_moderator', default_wiki,
                              'OCR AutoModerator added it\'s YAML configuration')
        return self.parse(default_wiki)

    async def load_wiki_config(self, subreddit: Subreddit):
        """ Checks if the wiki exists and loads new YAML from it if so, validating it in the process and returning
        the result. Otherwise, creates a new one with defaults."""
        if await self.check_wiki_exists(subreddit):
            config = self.parse(subreddit.wiki['ocr_auto_moderator'].content_md)
            if self.validate_config(config):
                return config
            # validation_response = self.validate_config(config)
            # if validation_response == True:
            #     return config
            # else:
            #     return STATUS_ERROR, validation_response
        else:
            return await self.create_wiki(subreddit)

    async def reset(self, subreddit: Subreddit):
        """ Resets the wiki config to default if it exists """
        if await self.check_wiki_exists(subreddit):
            subreddit.wiki['ocr_auto_moderator'].edit(default_wiki,
                                                      'OCR AutoModerator\'s wiki config was reset as requested')
        return self.parse(default_wiki)
