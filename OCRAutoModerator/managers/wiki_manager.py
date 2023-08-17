""" OCRAutoModerator Wiki Manager & functions
@authors:
---
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""

import logging
import re
from collections import namedtuple
from typing import Union
from enum import IntEnum
import yaml
from praw.models import Subreddit
from OCRAutoModerator.config.config import default_wiki, bot_name, join_success, wiki_permissions_error, developers, \
    acceptable_languages_easyocr, acceptable_languages_pytesseract, language_map_pytes_to_easyocr, \
    language_map_easyocr_to_pytes
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


class OperatorTypes(IntEnum):
    STANDARD = 1
    TIME = 2


# noinspection PyBroadException
class WikiParser:

    def __init__(self, reddit, wiki_configs):
        self.reddit = reddit
        self.wiki_configs = wiki_configs

    async def on_subreddit_join(self, msg) -> None:
        sub_name = msg.subreddit.display_name
        subreddit = self.reddit.subreddit(sub_name)
        try:
            if not await self.check_wiki_exists(subreddit):
                self.wiki_configs[sub_name.lower()] = await self.create_wiki(subreddit)
                self.reddit.subreddit(sub_name).message(
                    f'{bot_name} has been setup correctly!', join_success.format(sub_name))
                logger.info(f'Created Wiki Config for /r/{sub_name}')
            else:
                self.wiki_configs[sub_name.lower()] = await self.load_wiki_config(subreddit)
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
                        if not await self.check_wiki_exists(subreddit):
                            self.wiki_configs[sub_name.lower()] = await self.create_wiki(subreddit)
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
        """
        AutoModerator within OCRAutoModerator.... AutoModerator inception! If you know, you know... ;)
        Author: Reddit Inc.
        Edits: rule_defs and related code. I did not need the extra data but left the code in case I do later.
        """
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

    def validate_config(self, config: list) -> bool:
        priorities = []
        for section in config:
            if 'type' not in section:
                raise ValueError("'type' parameter is missing.")
            elif 'rule' not in section:
                raise ValueError("'rule' parameter is missing.")
            elif 'action' not in section:
                raise ValueError("'action' parameter is missing.")
            elif 'action_reason' not in section:
                raise ValueError("'action_reason' parameter is missing.")
            elif 'priority' not in section:
                raise ValueError("'priority' parameter is missing.")

            if type(section['type']) is not str:
                raise TypeError("'type' parameter is not a string/text, e.g \"any\".")
            elif type(section['rule']) is not list:
                raise TypeError("'rule' parameter is a list, e.g [\"example\", \"example\"].")
            elif type(section['action']) is not str:
                raise TypeError("'action' parameter is not a string/text, e.g \"report\".")
            elif type(section['action_reason']) is not str:
                raise TypeError("'action_reason' parameter is not a string/text, e.g \"No Profanity\".")
            elif type(section['priority']) is not int:
                raise TypeError("'priority' parameter is not a number, e.g 1.")
            elif 'flair_text' in section and type(section['flair_text']) is not str:
                raise TypeError("'flair_text' parameter is not a string/text.")
            elif 'flair_css_class' in section and type(section['flair_css_class']) is not str:
                raise TypeError("'flair_css_class' parameter is not a string/text.")
            elif 'flair_template_id' in section and type(section['flair_template_id']) is not str:
                raise TypeError(
                    "'flair_template_id' parameter is not a string/text. You can find this value on https://www.reddit.com/r/YOUR_SUBREDDIT/about/postflair, click Copy ID.")
            elif 'set_flair' in section and type(section['set_flair']) is not str:
                raise TypeError("'set_flair' parameter is not a string/text.")
            elif 'overwrite_flair' in section and type(section['overwrite_flair']) is not bool:
                raise TypeError("'overwrite_flair' parameter is not a boolean value, e.g true or false.")
            elif 'comment' in section and type(section['comment']) is not str:
                raise TypeError("'comment_locked' parameter is not a string/text.")
            elif 'comment_stickied' in section and type(section['comment_stickied']) is not bool:
                raise TypeError("'comment_stickied' parameter is not a boolean value, e.g true or false.")
            elif 'comment_locked' in section and type(section['comment_locked']) is not bool:
                raise TypeError("'comment_locked' parameter is not a boolean value, e.g true or false.")
            elif 'moderators_exempt' in section and type(section['moderators_exempt']) is not bool:
                raise TypeError("'moderators_exempt' parameter is not a boolean value, e.g true or false.")
            elif 'report_reason' in section and type(section['report_reason']) is not str:
                raise TypeError("'report_reason' parameter is not a string/text.")
            elif 'standard' in section and type(section['standard']) is not str:
                raise TypeError(
                    "'standard' parameter is not a string/text. Options for standards can be found on https://www.reddit.com/wiki/automoderator/standard-conditions/")
            elif 'set_locked' in section and type(section['set_locked']) is not bool:
                raise TypeError("'set_locked' parameter is not a boolean value, e.g true or false.")
            elif 'is_original_content' in section and type(section['is_original_content']) is not bool:
                raise TypeError("'is_original_content' parameter is not a boolean value, e.g true or false.")
            elif 'is_self' in section and type(section['is_self']) is not bool:
                raise TypeError("'is_self' parameter is not a boolean value, e.g true or false.")
            elif 'is_nsfw' in section and type(section['is_nsfw']) is not bool:
                raise TypeError("'is_nsfw' parameter is not a boolean value, e.g true or false.")
            elif 'set_sticky' in section and type(section['set_sticky']) is not bool:
                raise TypeError("'set_sticky' parameter is not a boolean value, e.g true or false.")
            elif 'set_nsfw' in section and type(section['set_nsfw']) is not bool:
                raise TypeError("'set_nsfw' parameter is not a boolean value, e.g true or false.")
            elif 'set_spoiler' in section and type(section['set_spoiler']) is not bool:
                raise TypeError("'set_spoiler' parameter is not a boolean value, e.g true or false.")
            elif 'set_contest_mode' in section and type(section['set_contest_mode']) is not bool:
                raise TypeError("'set_contest_mode' parameter is not a boolean value, e.g true or false.")
            elif 'set_original_content' in section and type(section['set_original_content']) is not bool:
                raise TypeError("'set_original_content' parameter is not a boolean value, e.g true or false.")
            elif 'set_suggested_sort' in section and type(section['set_suggested_sort']) is not str:
                raise TypeError("'set_suggested_sort' parameter is not a string/text.")
            elif 'ignore_reports' in section and type(section['ignore_reports']) is not bool:
                raise TypeError("'ignore_reports' parameter is not a boolean value, e.g true or false.")
            elif 'satisfy_any_threshold' in section and type(section['satisfy_any_threshold']) is not bool:
                raise TypeError("'satisfy_any_threshold' parameter is not a boolean value, e.g true or false.")
            elif 'has_comments' in section:
                section['has_comments'] = self.assign_operators(section['has_comments'])
            elif 'author' in section:
                if type(section['author']) is not dict:
                    raise TypeError(
                        "'author' parameter is not a dictionary/group value, please refer to https://www.reddit.com/wiki/automoderator/full-documentation/ for how to do this.")
                author = section['author']
                if 'satisfy_any_threshold' in author and type(author['satisfy_any_threshold']) is not bool:
                    raise TypeError("'satisfy_any_threshold' parameter is not a boolean value, e.g true or false.")
                elif 'has_verified_email' in author and type(author['has_verified_email']) is not bool:
                    raise TypeError("'has_verified_email' parameter is not a boolean value, e.g true or false.")
                elif 'is_mod' in author and type(author['is_mod']) is not bool:
                    raise TypeError("'is_mod' parameter is not a boolean value, e.g true or false.")
                elif 'is_gold' in author and type(author['is_gold']) is not bool:
                    raise TypeError("'is_gold' parameter is not a boolean value, e.g true or false.")
                elif 'is_suspended' in author and type(author['is_suspended']) is not bool:
                    raise TypeError("'is_suspended' parameter is not a boolean value, e.g true or false.")
                elif 'is_nsfw' in author and type(author['is_nsfw']) is not bool:
                    raise TypeError("'is_nsfw' parameter is not a boolean value, e.g true or false.")

                if 'post_karma' in author:
                    author['post_karma'] = self.assign_operators(author['post_karma'])

                if 'comment_karma' in author:
                    author['comment_karma'] = self.assign_operators(author['comment_karma'])

                if 'account_age' in author:
                    author['account_age'] = self.assign_operators(author['account_age'], OperatorTypes.TIME)
                    # TODO: Finish TIME Operator Assignments

                if 'description_contains' in author:
                    self.validate_conditionals(author['description_contains'], 'description_contains')

                if 'has_followers' in author:
                    section['author']['has_followers'] = self.assign_operators(author['has_followers'])

                if 'mod_notes' in author:
                    if type(author['mod_notes']) is not dict:
                        raise TypeError(
                            "'mod_notes' parameter is not a dictionary/group value, please refer to https://www.reddit.com/wiki/automoderator/full-documentation/ for how to do this.")

                    if 'contains' not in author['mod_notes']:
                        raise ValueError(
                            "'mod_notes' is a dictionary/group value and *must contain* a parameter called 'contains' with the value being a list or str.")

                    self.validate_conditionals(author['mod_notes']['contains'], 'contains')

                    if 'satisfy_any_threshold' in author['mod_notes'] \
                            and type(author['mod_notes']['satisfy_any_threshold']) is not bool:
                        raise TypeError("'satisfy_any_threshold' is not a boolean value, e.g true or false.")

                if 'has_trophies' in author:
                    section['author']['has_trophies'] = self.assign_operators(author['has_trophies'])

                if 'has_submissions' in author:
                    # TODO: Implement has_submissions
                    author['has_submissions'] = self.assign_operators(author['has_submissions'])

                if 'has_comments' in author:
                    # TODO: Implement has_comments
                    author['has_comments'] = self.assign_operators(author['has_comments'])

                if 'links' in author:
                    if type(author['links']) is not list and type(author['links']) is not str:
                        raise TypeError(
                            "'links' parameter is a list of strings, e.g [\"example\", \"example\"], or a string e.g \"Example\"")

                    if 'satisfy_any_threshold' in author['links'] \
                            and type(author['links']['satisfy_any_threshold']) is not bool:
                        raise TypeError("'satisfy_any_threshold' is not a boolean value, e.g true or false.")

            if section['action'] not in ('report', 'remove', 'spam', 'approve', 'nothing'):
                raise ValueError("'action' must be either 'report', 'remove', 'spam', 'approve', or 'nothing'")

            if len(section['action_reason']) > 99:
                raise ValueError(
                    "'action_reason' cannot contain more than 99 characters. This value does not change the removal comment.")

            if 'flair_text' in section and len(section['flair_text']) > 99:
                raise ValueError("'flair_text' cannot contain more than 99 characters.")

            if 'flair_css_class' in section and len(section['flair_css_class']) > 99:
                raise ValueError("'flair_css_class' cannot contain more than 99 characters.")

            if 'flair_template_id' in section and len(section['flair_template_id']) != 36:
                raise ValueError(
                    "'flair_template_id' will never be above or below 36 characters. You can find this value on https://www.reddit.com/r/YOUR_SUBREDDIT/about/postflair, click Copy ID.")

            if 'set_flair' in section and len(section['set_flair']) != 36:
                raise ValueError("'set_flair' accepts a flair_template_id which should always be 36 chars long.")

            if 'comment' in section:
                if len(section['comment']) >= 9999:
                    raise ValueError("'comment' length can be no greater than 9,999 characters.")

                section['comment'] = section['comment'].replace('\n', '  ')

            if 'comment_stickied' in section:
                section['comment_stickied'] = 'yes' if section['comment_stickied'] else 'no'

            if 'report_reason' in section and len(section['report_reason']) > 99:
                raise ValueError("'report_reason' cannot contain more than 99 characters.")

            if 'set_suggested_sort' in section and section['set_suggested_sort'].lower() \
                    not in ('best', 'top', 'new', 'controversial', 'old', 'qa'):
                raise ValueError(
                    "'set_suggested_sort' parameter must be one of 'best', 'top', 'new', 'controversial', 'old', or 'qa'")

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

            if 'language' in section:
                lang = section['language']
                if lang not in acceptable_languages_easyocr and lang not in acceptable_languages_pytesseract:
                    raise ValueError(
                        f'The language code you provided is not valid or not supported. These are the supported language codes: {set(acceptable_languages_easyocr + acceptable_languages_pytesseract)}.  \n '
                        f'Please note that OCR AutoMod uses multiple OCR libraries and by using a non english language, '
                        f'you may not be able to utilize all of them. This may result in OCR AutoMod finding less matches and or having worse accuracy.')

                if lang in language_map_easyocr_to_pytes:
                    section['lang_easyocr'] = lang
                    section['lang_pytes'] = language_map_easyocr_to_pytes[lang]
                elif lang in language_map_pytes_to_easyocr:
                    section['lang_pytes'] = lang
                    section['lang_easyocr'] = language_map_pytes_to_easyocr[lang]
                elif lang not in acceptable_languages_easyocr or lang not in acceptable_languages_pytesseract:
                    if lang not in acceptable_languages_pytesseract:
                        section['lang_pytes'] = 'INVALID'
                    elif lang not in acceptable_languages_easyocr:
                        section['lang_easyocr'] = 'INVALID'

                else:
                    section['lang_easyocr'] = 'en'
                    section['lang_pytes'] = 'eng'
            else:
                section['lang_easyocr'] = 'en'
                section['lang_pytes'] = 'eng'

        duplicates = [priority for priority in priorities if priorities.count(priority) > 1]
        if len(duplicates) > 0:
            raise ValueError("More than one rule has the same priority as another. Priority must be unique.")

        return True

    @staticmethod
    def validate_conditionals(conditional: Union[str, list], conditional_name: str) -> bool:
        conditional_type = type(conditional)
        if conditional_type is not str and conditional_type is not list:
            raise TypeError(
                "'{conditional_name}' parameter is not a string/text value or list value, e.g \"example\" or [\"example1\", \"example2\"].")
        elif conditional_type is list:
            if not all(isinstance(x, str) for x in conditional):
                raise ValueError(
                    f"'{conditional_name}' must be either a string/text or a list of strings/text. e.g abc or [\"abc\", \"defg\"]")

        return True

    @staticmethod
    def assign_operators(rule_text: str, operator_type: OperatorTypes = OperatorTypes.STANDARD) -> list:
        operator_set = rule_text.split(' ')
        if operator_type == OperatorTypes.STANDARD:
            try:
                int(operator_set[1])
            except:
                raise TypeError('The second part of your conditional is not a number. e.g "> 80".')
            if len(operator_set) != 2 or operator_set[0] not in ('>=', '<=', '>', '<'):
                raise ValueError(
                    "Conditionals must start with either '>', '>=', '<', '<=' followed by a single space and the desired number. Don't include quotes.")

            # noinspection PyTypeChecker
            operator_set[1] = int(operator_set[1])
            return operator_set

        elif operator_type == OperatorTypes.TIME:
            if len(operator_set) != 3:
                if operator_set[0] not in ('>=', '<=', '>', '<'):
                    raise ValueError(
                        "Time conditionals must start with either '>', '>=', '<', '<=' followed by a single space and the desired number. Don't include quotes.")
                elif operator_set[2] not in ('minutes', 'hours', 'days', 'weeks', 'months', 'years'):
                    raise ValueError(
                        "Time conditionals must end with either 'minutes', 'hours', 'days', 'weeks', 'months', or 'years'. ex: >= 7 hours")
                elif type(operator_set[1]) is not int:
                    raise TypeError('The second part of your time conditional is not a number. e.g "> 60 minutes".')
                else:
                    try:
                        int(operator_set[1])
                    except:
                        raise TypeError('The second part of your conditional is not a number. e.g "> 80".')

            # noinspection PyTypeChecker
            operator_set[1] = int(operator_set[1])
            return operator_set

        return []

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
