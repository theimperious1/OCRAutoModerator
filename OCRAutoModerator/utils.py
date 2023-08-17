""" OCRAutoModerator Utility functions
@authors:
---
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""

import logging
import traceback
from io import BytesIO
from praw.models import Subreddit, Redditor, Submission
import requests
from OCRAutoModerator.data_types import MatchSets
from PIL import Image
from OCRAutoModerator.config.config import developers
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

allowed_video_formats = ['.gif', 'gifv', '.mp4']


# noinspection PyBroadException
def fetch_media(img_url: str):
    """ Fetches submission media """

    if img_url is None:
        return False

    if 'm.imgur.com' in img_url:
        img_url = img_url.replace('m.imgur.com', 'i.imgur.com')

    if not any(a in img_url for a in ('.jpg', '.png', '.jpeg')):
        return False
    try:
        with requests.get(img_url) as resp:
            try:
                return Image.open(BytesIO(resp.content))
            except:
                traceback.print_exc()
                logger.debug(f'Encountered exception when opening image in fetch_media: {img_url}')
                return False
    except:
        traceback.print_exc()
        logger.debug(f'Encountered exception when requesting image in fetch_media: {img_url}')
        return False


def is_video_or_gif(submission: Submission = None, url: str = None):
    if submission is None and url is None:
        raise TypeError('You must provide at least one non-None parameter!')
    elif submission is not None and url is not None:
        raise ValueError('Submission and URL parameters cannot both be supplied')

    if submission is not None:
        is_video = submission.is_video if hasattr(submission, 'is_video') else False
        url_overridden = submission.url_overridden_by_dest if hasattr(submission, 'url_overridden_by_dest') else ''

        if is_video or ('youtu.be' in url_overridden or 'youtu.be' in submission.url):
            return True
    for file_format in allowed_video_formats:
        if submission.url.endswith(file_format) if submission is not None else url.endswith(file_format):
            return True
    return False


async def is_user_mod(subreddit: Subreddit, author: Redditor):
    """ Checks if user is a moderator of a subreddit we are """
    if author in developers:
        return True
    for moderator in subreddit.moderator():
        if author == moderator.name:
            return True
    return False


def strip_sub_name(sub_name: str):
    """ Strips r/ from subreddit names """
    if 'r/' in sub_name:
        sub_name = sub_name.replace('/r/', '').replace('r/', '')
    return sub_name


def log_and_reply(msg, response: str, log_msg=None):
    """ Replies to a message/comment and logs. Separate text options for both """
    logger.info(response if log_msg is None else log_msg)
    return msg.reply(response)


def replace_placeholders(submission: Submission, submission_type: str, text: str, rule_set: dict,
                         match_sets: MatchSets):
    if '{{author}}' in text:
        text = text.replace('{{author}}', submission.author.name if hasattr(submission.author, 'name') else '[DELETED]')

    if '{{subreddit}}' in text:
        text = text.replace('{{subreddit}}', submission.subreddit.display_name)

    if '{{author_flair_text}}' in text:
        text = text.replace('{{author_flair_text}}',
                            submission.author_flair_text if submission.author_flair_text is not None else 'No Flair')

    if '{{author_flair_css_class}}' in text:
        text = text.replace('{{author_flair_css_class}}',
                            submission.author_flair_css_class if submission.author_flair_css_class is not None else 'No Flair')

    if '{{author_flair_template_id}}' in text:
        text = text.replace('{{author_flair_template_id}}',
                            submission.author_flair_template_id if submission.author_flair_template_id is not None else 'No Flair')

    if '{{permalink}}' in text:
        text = text.replace('{{permalink}}', submission.permalink)

    if '{{kind}}' in text:
        text = text.replace('{{kind}}', submission_type)

    if '{{title}}' in text:
        text = text.replace('{{title}}', submission.title)

    if '{{domain}}' in text and hasattr(submission, 'url_overridden_by_dest'):
        link = submission.url_overridden_by_dest
        # noinspection PyBroadException
        try:
            domain = urlparse(link)
        except:
            return
        text = text.replace('{{domain}}', domain.netloc)

    if '{{url}}' in text:
        text = text.replace('{{url}}', f'https://reddit.com{submission.permalink}')

    if '{{rule_descriptor}}' in text and 'rule_descriptor' in rule_set:
        text = text.replace('{{rule_descriptor}}', rule_set['rule_descriptor'])

    if '{{debug}}' in text:
        text = text.replace('{{debug}}', f'{str(match_sets)}')

    if '{{total_matches}}' in text:
        text = text.replace('{{total_matches}}', str(len(match_sets)))

    return text


def get_time_difference(timestamp: int, time: int, time_type: str) -> int:
    # DOES NOT WORK
    if time_type == 'minutes':
        return timestamp - (time * 60)
    elif time_type == 'hours':
        return timestamp - (time * (60 * 60))
    elif time_type == 'days':
        return timestamp - (time * ((60 * 60) * 24))
    elif time_type == 'weeks':
        return timestamp - (time * (((60 * 60) * 24) * 7))
    elif time_type == 'months':
        return timestamp - (time * ((((60 * 60) * 24) * 7) * 4))
    elif time_type == 'years':
        return timestamp - (time * (((((60 * 60) * 24) * 7) * 4) * 12))

    return -1
