""" OCRAutoModerator Video Manager & functions
@authors:
---
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""

import logging
from typing import Union
from PIL import Image
import os
import traceback
import urllib.request
from OCRAutoModerator.data_types import VideoData, GifData
from enum import IntEnum
import cv2
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from OCRAutoModerator.youtube_downloader import download_yt_video
from praw.models import Submission
from OCRAutoModerator.data_types import MatchSets

logger = logging.getLogger(__name__)

# Paths
VIDEO_PATH = 'videos/'
TMP_PATH = 'tmp/{}'


# Media type enum
class MediaTypes(IntEnum):
    VIDEO = 1
    GIF = 2
    YOUTUBE_VIDEO = 3


INFO_TEMPLATE = 'User | Date | Time Frame | Post | Karma | Status | Similarity\n:---|:---|:---|:---|:---|:---|:---|:---\n{0}'
ROW_TEMPLATE = '/u/\N{ZWSP}{0} | {1} | {2} | [{3}](https://redd.it/{4}) | {5} | {6} | {7}%\n'


def setup_urllib():
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0')
    ]
    urllib.request.install_opener(opener)


# TODO: Refactor MediaManager and clean it up to new standards before open sourcing.

class MediaManager:

    def __init__(self, reddit, auto_mod_manager, image_reader):
        self.reddit = reddit
        self.auto_mod_manager = auto_mod_manager
        self.ir = image_reader
        setup_urllib()

    async def check_image(self, submission: Submission, media, config: list) -> MatchSets:
        required_langs = set()
        for rule_set in config:
            if rule_set['lang_easyocr'] not in required_langs and rule_set['lang_pytes'] not in required_langs:
                required_langs.add((rule_set['lang_easyocr'], rule_set['lang_pytes']))

        merged_result = []
        for lang_tuple in required_langs:
            merged_result.extend(
                self.ir.read_all_methods(submission.url, media, lang_easyocr=lang_tuple[0], lang_pytes=lang_tuple[1]))

        return await self.auto_mod_manager.check_against_rules(submission, merged_result, config)

    async def check_video(self, submission: Submission, config: list) -> list:
        media_data = self.process_media(submission)
        required_langs = set()
        for rule_set in config:
            if rule_set['lang_easyocr'] not in required_langs and rule_set['lang_pytes'] not in required_langs:
                required_langs.add((rule_set['lang_easyocr'], rule_set['lang_pytes']))

        match_sets = []
        for fp in media_data:
            merged_result = []

            for lang_tuple in required_langs:
                merged_result.extend(self.ir.read_all_methods(fp, lang_easyocr=lang_tuple[0], lang_pytes=lang_tuple[1]))
                match_sets.append(await self.auto_mod_manager.check_against_rules(submission, merged_result, config))

        return match_sets

    async def check_multi_media(self, submission: Submission, media: set, config: list) -> set:
        logger.info('WARNING: MULTI MEDIA UNHANDLED. IMPLEMENTATION UNFINISHED')
        return set()

        results = set()
        for item in media:
            if item['e'] == 'Image':
                results.add(await self.check_image(submission, item, config))
            elif item['e'] == 'Video':
                results.add(await self.check_video(submission, item))
            else:
                logger.info(f"New Content-Type found in 'check_multi_media': {item['e']}")
            results.add(await self.auto_mod_manager.check_against_rules(submission, item, config))

        return results

    async def check_text(self, submission: Submission, config: list) -> list:
        match_sets_body = await self.auto_mod_manager.check_against_rules(submission, [submission.selftext], config)
        # match_sets_title = await self.auto_mod_manager.check_against_rules(submission, submission.title, config)

        return match_sets_body

    @staticmethod
    def process_media(submission: Submission) -> set:
        """ Process video and store video data in memory & db """
        fp = None
        try:
            media_type, url = get_media_type(submission)
            fp = download_media(submission, url, media_type)

            media_data = get_gif_data(fp) if media_type == MediaTypes.GIF else get_video_data(fp)
            logger.info(
                f'MEDIA_DATA_DEBUG_INFO:{media_type}-{media_data.fps}-{media_data.duration}-{media_data.frame_count}')
            images = get_gif_frames(media_data) \
                if media_type == MediaTypes.GIF else get_video_frames(media_data)
            return images
        except Exception:
            traceback.print_exc()
        finally:
            if fp is not None:
                try:
                    os.remove(fp)
                except FileNotFoundError:
                    logger.info('Failed to remove video, file not found!')
                except PermissionError:
                    logger.info(
                        f'The process cannot access the file because it is being used by another process: {fp}')
        return set()


# TODO: secure_media['reddit_video'] has 'is_gif', we should probably start using it.
def get_media_type(submission: Submission) -> tuple:
    url_overridden = submission.url_overridden_by_dest \
        if hasattr(submission, 'url_overridden_by_dest') else submission.url
    secure_media = get_secure_media(submission)

    if 'youtu.be' in url_overridden or 'youtube' in url_overridden:
        return MediaTypes.YOUTUBE_VIDEO, url_overridden
    elif '.gifv' in submission.url:
        logging.info('Success! GIFV switched to MP4 :)')
        return MediaTypes.VIDEO, submission.url.replace('.gifv', '.mp4')
    elif '.gif' in submission.url:
        if 'imgur.com' in submission.url:
            logging.info('Switched Imgur GIF to MP4 :)')
            return MediaTypes.VIDEO, submission.url.replace('.gif', '.mp4')
        else:
            logging.info('Processing real GIF :)')
            return MediaTypes.GIF, submission.url
    elif secure_media is not None:
        if 'fallback_url' in secure_media:
            url = secure_media['fallback_url']
            logging.info('Processing fallback_url in @get_media_type')
            return (MediaTypes.GIF, url) if '.gif' in url else (MediaTypes.VIDEO, url)
        elif 'reddit_video' in secure_media:
            url = secure_media['reddit_video']['fallback_url']
            logging.info('Processing reddit_video in @get_media_type')
            return (MediaTypes.GIF, url) if '.gif' in url else (MediaTypes.VIDEO, url)

    return MediaTypes.VIDEO, submission.url


def download_media(submission: Submission, url: str, media_type: int) -> str:
    """ Get video name, download it, then shorten to 60 seconds """
    video_name = filter_video_name(url)
    fp = get_file_path(video_name)
    if media_type != MediaTypes.YOUTUBE_VIDEO:
        urllib.request.urlretrieve(url, fp)
        # TODO: Maybe check that the videos are longer than 60s before doing sub_clip
        if media_type != MediaTypes.GIF:
            return get_sub_clip(video_name, fp)
    else:
        success = download_yt_video(submission, url, file_name=video_name)
        if success:
            fp = get_sub_clip(video_name, fp)
        elif not success:
            raise ConnectionError('Failed to download YouTube video')

    return fp


def get_video_frames(media_data: VideoData) -> set:
    """ Write video frames to tmp dir, incrementing by fps for 1 frame per second """
    frame = 0
    count = 0
    frames = set()
    vid_cap = media_data.cap
    fps = media_data.fps
    while vid_cap.isOpened():
        success, image = vid_cap.read()

        if success:
            video = os.path.join(TMP_PATH.format(f'frame{count}.jpg'))
            frames.add(video)
            cv2.imwrite(video, image)

            frame += fps
            vid_cap.set(1, frame)
            count += 1
            if count == 59:
                vid_cap.release()
                break
        else:
            vid_cap.release()

    return frames


def get_gif_frames(media_data: GifData) -> set:
    gif = media_data.gif
    gif.seek(0)

    current_frame = 0
    count = 0
    frames = set()
    while True:
        try:
            gif.seek(current_frame)
            output = TMP_PATH.format(f'frame{current_frame}.png')
            gif.save(output)
            frames.add(output)
            current_frame += media_data.fps
            count += 1
            if count == 59:
                gif.close()
                return frames
        except EOFError:
            gif.close()
            return frames


def get_video_data(fp: str) -> VideoData:
    """ Get's relevant data for a video """
    cap = cv2.VideoCapture(fp)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)  # TODO: THIS MAY NOT BE ACCURATE, getting 45 seconds on 2 min 9 sec long vids.
    duration = frame_count / fps
    return VideoData(cap, duration, frame_count, fps)


def get_gif_data(fp: str) -> GifData:
    """ Gets GifData from a gif and then returns it with a vidcap
    total_duration will be in milliseconds
    """
    # TODO: NoneType object has no attribute 'seek'. Why? This happened multiple time.
    gif = Image.open(fp)
    gif.seek(0)
    total_duration = 0
    frame_count = 0
    while True:
        try:
            frame_duration = gif.info['duration']  # returns current frame duration in milli sec.
            total_duration += frame_duration
            frame_count += 1
            # now move to the next frame of the gif
            gif.seek(gif.tell() + 1)  # image.tell() = current frame
        except EOFError:
            fps = ((frame_count / total_duration) * 1000) if total_duration != 0 else 0
            return GifData(gif, total_duration, frame_count, round(fps))


def get_sub_clip(video_name: str, fp: str) -> str:
    new_video = f'{VIDEO_PATH}1-{video_name}'
    ffmpeg_extract_subclip(fp, 0, 59 * 1000, targetname=new_video)
    os.remove(fp)
    return new_video


def get_total_frames(clips: list, clip_length: int) -> int:
    clips_length = len(clips)

    if clips_length == 1:
        logger.info('CL1:' + str(clip_length))
        return clip_length

    elif clips_length > 1:
        frame_count = 0
        for clip in clips:
            frame_count += len(clip)
            logger.info('FCIC: ' + str(clip))

        logger.info('CL>1-2: ' + str(frame_count))
        return frame_count
    return 0


def filter_video_name(url: str) -> str:
    video_name = url[url.rindex("/") + 1:len(url)]
    if '?' in video_name:
        video_name = video_name[0: video_name.rindex('?')]

    if not any(a in video_name for a in ('.mp4', '.mov', '.m4a', '.gif', '.gifv')):
        video_name += '.mp4'

    if '.gifv' in video_name:
        video_name = video_name.replace('.gifv', '.gif')
    return video_name


def get_file_path(video_name: str) -> str:
    return VIDEO_PATH + video_name


def get_secure_media(submission: Submission) -> Union[dict, None]:
    if hasattr(submission, 'secure_media'):
        return submission.secure_media
    elif 'secure_media' in submission:
        return submission['secure_media']

    return None


def get_thumbnail_url(submission: Submission) -> str:
    thumbnail = submission.thumbnail if hasattr(submission, 'thumbnail') else None
    secure_media = get_secure_media(submission)

    if thumbnail is not None and thumbnail != 'default' and thumbnail != 'nsfw':
        return thumbnail
    elif secure_media is not None:
        if 'oembed' in secure_media:
            return secure_media['oembed']['thumbnail_url']
    return ''
