""" OCRAutoModerator Utility functions
@authors:
---
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""

import logging
import traceback
from io import BytesIO
from praw.models import Subreddit, Redditor
import requests
from PIL import Image
from OCRAutoModerator.config import developers

logger = logging.getLogger(__name__)

allowed_video_formats = ['.gif', 'gifv', '.mp4']


# noinspection PyBroadException
def fetch_media(img_url):
    """ Fetches submission media """
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


def is_video_or_gif(submission=None, url=None):
    if submission is None and url is None:
        raise Exception('You must provide at least one non-None parameter!')
    elif submission is not None and url is not None:
        raise Exception('Submission and URL parameters cannot both be supplied')

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


def strip_sub_name(sub_name):
    """ Strips r/ from subreddit names """
    if 'r/' in sub_name:
        sub_name = sub_name.replace('/r/', '').replace('r/', '')
    return sub_name


def log_and_reply(msg, response, log_msg=None):
    """ Replies to a message/comment and logs. Separate text options for both """
    logger.info(response if log_msg is None else log_msg)
    return msg.reply(response)
