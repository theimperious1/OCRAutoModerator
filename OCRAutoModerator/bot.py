"""
OCR AutoModerator 2023 (by theimperious1)
@authors:
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""
import asyncio
import logging
# import signal
import sys
import traceback
from OCRAutoModerator.image_reader import ImageReaderTesseract
import praw
from OCRAutoModerator.managers.wiki_manager import WikiParser
from OCRAutoModerator.config.config import *
from OCRAutoModerator.managers.db_manager import get_viewed_submissions, insert_submission
from OCRAutoModerator.managers.submission_manager import SubmissionManager
from OCRAutoModerator.utils import fetch_media, is_video_or_gif
from html import unescape

# Set up logging
logger = logging.getLogger(__name__)
formatting = "[%(asctime)s] [%(levelname)s:%(name)s] %(message)s"
logging.basicConfig(
    format=formatting,
    level=logging.INFO,
    handlers=[logging.FileHandler('ocrautomoderator.log', encoding='utf8'),
              logging.StreamHandler()])


def signal_handler(sig, frame):
    """ Signal handler for CTRL C """
    logger.info(f'{bot_name} was killed by Ctrl C. Making smooth exit...')
    sys.exit(0)


# noinspection PyBroadException
class BotClient:

    def __init__(self):
        """ Initializes variables and loads data from db """
        # signal.signal(signal.SIGINT, signal_handler)
        self.reddit = praw.Reddit(
            client_id=reddit_id,
            client_secret=reddit_secret,
            password=reddit_pass,
            user_agent=reddit_agent,
            username=reddit_name,
            check_for_async=False)

        self.wiki_configs = {}
        self.wiki_manager = WikiParser(self.reddit, self.wiki_configs)
        self.ir = ImageReaderTesseract()
        self.submission_manager = SubmissionManager(self.reddit, self.ir)
        self.viewed_submissions = None
        self.sub_list = self.reddit.redditor(reddit_name).moderated()
        logger.info(f'Successfully loaded! {bot_name} is active...')

    async def load_data(self) -> None:
        self.viewed_submissions = await get_viewed_submissions()
        for subreddit in self.sub_list:
            try:
                self.wiki_configs[subreddit.display_name.lower()] = await self.wiki_manager.load_wiki_config(subreddit)
            except:
                traceback.print_exc()
                self.wiki_configs[subreddit.display_name.lower()] = self.wiki_manager.parse(default_wiki)
                # Maybe worth mod mailing the sub? Then again, this only happens on restarts, and I would be notified instantly.
                # However... the very fact it would happen means that mod team did not send the update msg to the bot. Possibly need educating.
                # self.reddit.redditor(developers[0]).message(
                #    f'{bot_name} has an error in load_data for /r/{subreddit.display_name}', 'Please check on it.'
                # )

    def run(self) -> None:
        async def runner():
            await self.do_job()

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            return

    async def do_job(self) -> None:
        """ Runs the bot
        This function is entirely blocking, so any calls to other functions must
        be made prior to calling this. """
        while 1:
            try:
                await self.handle_dms()
                await self.do_submissions()
            except:
                traceback.print_exc()

    async def handle_dms(self) -> None:
        """ Looks for mod invites and checks for wiki updates and resets """
        for msg in self.reddit.inbox.unread(mark_read=True):
            if not msg.was_comment and (msg.body.startswith('gadzooks!') and 'invitation to moderate' in msg.subject):
                try:
                    await self.accept_invite(msg)
                except Exception as e:
                    logger.info(f'Moderator invite already accepted: continuing... {e}')

            elif not msg.was_comment and "You have been removed as a moderator from " in msg.body:
                await self.on_mod_removal(msg)

            elif msg.body is not None and msg.body.lower() \
                    in self.wiki_configs and (msg.subject.lower() == 'update' or msg.subject.lower() == 'reset'):
                await self.wiki_manager.on_wiki_update_request(msg)

            msg.mark_read()

    async def accept_invite(self, msg) -> None:
        """Accepts an invitation to a new subreddit, adds it to the database and creates a config wiki if none exists """
        msg.subreddit.mod.accept_invite()
        self.sub_list = self.reddit.redditor(reddit_name).moderated()
        await self.wiki_manager.on_subreddit_join(msg)
        logger.info(f"Accepted mod invite to r/{msg.subreddit.display_name}")

        redditor = self.reddit.redditor(developers[0])
        redditor.message(
            f'{bot_name} was added to a new subreddit!',
            f'/r/{msg.subreddit.display_name} '
        )

    async def on_mod_removal(self, msg) -> None:
        self.sub_list = self.reddit.redditor(reddit_name).moderated()
        logger.info(f"Removed from r/{msg.subreddit.display_name}")

        redditor = self.reddit.redditor(developers[0])
        redditor.message(
            f'{bot_name} was removed from a subreddit!',
            f'/r/{msg.subreddit.display_name} '
        )

    async def do_submissions(self) -> None:
        for submission in self.reddit.subreddit('mod' if not test_mode else 'Approval_Bot').new():
            subreddit = submission.subreddit
            media_url = submission.url_overridden_by_dest if hasattr(submission, 'url_overridden_by_dest') else None
            if submission.id in self.viewed_submissions:
                #  or \
                #                     (not hasattr(submission, 'url_overridden_by_dest') and not hasattr(submission, 'media_metadata'))
                continue

            elif submission.id not in self.viewed_submissions:
                await insert_submission(submission)
                self.viewed_submissions.add(submission.id)

            if submission.removed_by_category is not None:
                logger.info(f'Cancelled submission processing, submission was removed. {submission.permalink}')
                continue

            logger.info(f'Scanning {submission.id} by /u/{submission.author} on /r/{subreddit.display_name}')
            try:
                # If the content is an image
                if media := fetch_media(media_url) or hasattr(submission, 'media_metadata'):
                    if media:
                        match_sets = \
                            await self.submission_manager.check_image(
                                submission, media, self.wiki_configs[subreddit.display_name.lower()]
                            )
                    else:
                        media = set()
                        metadata = submission.media_metadata
                        # e = media type, s = the highest resolution link
                        [
                            media.add((unescape(metadata[key]['s']), metadata[key]['e']))
                            for key in metadata if metadata[key]['status'] == 'valid'
                        ]
                        match_sets = await self.submission_manager.check_multi_media(
                            submission, media, self.wiki_configs[subreddit.display_name.lower()])

                elif is_video_or_gif(submission):
                    match_sets = self.submission_manager.check_video(
                        submission, self.wiki_configs[subreddit.display_name.lower()]
                    )

                else:
                    match_sets = await self.submission_manager.check_text(
                        submission,
                        self.wiki_configs[subreddit.display_name.lower()])

                await self.submission_manager.do_submission(submission, match_sets)
                logger.info(
                    f'Scanning complete for {submission.id} by /u/{submission.author} on /r/{subreddit.display_name}')
            except:
                traceback.print_exc()


client = BotClient()
asyncio.run(client.load_data())
client.run()
