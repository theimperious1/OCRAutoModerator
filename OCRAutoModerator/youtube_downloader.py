""" OCRAutoModerator YouTube functions
@authors:
---
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""

from pytube import YouTube
import logging
import traceback


# noinspection PyBroadException
def download_yt_video(submission, url, file_name, is_scan=False):
    try:
        logging.info(f'YouTube Video URL: {url}')
        YouTube(url).streams.first().download('videos/' if not is_scan else 'videos_scan/', filename=file_name,
                                              timeout=60, max_retries=2)
        return True
    except:
        logging.info(
            f"Something went wrong while downloading the YouTube video for {submission.id}"
            f" on /r/{submission.subreddit.display_name if not is_scan else submission.subreddit}")
        traceback.print_exc()
        return False
