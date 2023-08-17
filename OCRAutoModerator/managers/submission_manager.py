import traceback
from OCRAutoModerator.data_types import ActionableItem, MatchSets
from OCRAutoModerator.utils import replace_placeholders
from OCRAutoModerator.managers.content_managers.automod_manager import AutoModManager
from OCRAutoModerator.managers.content_managers.media_manager import MediaManager
from praw.models import Submission, Comment
import logging
from OCRAutoModerator.config.config import default_comment

logger = logging.getLogger(__name__)


# noinspection PyBroadException
class SubmissionManager:

    def __init__(self, reddit, image_reader):
        self.reddit = reddit
        self.auto_mod_manager = AutoModManager(reddit)
        self.media_manager = MediaManager(self.reddit, self.auto_mod_manager, image_reader)

    async def do_submission(self, submission: Submission, match_sets: MatchSets) -> None:
        remove = len(match_sets.remove) > 0
        report = len(match_sets.report) > 0
        spam = len(match_sets.spam) > 0
        approve = len(match_sets.approve) > 0
        if not remove and not report and not spam and not approve:
            return

        if remove or spam:
            try:
                await self.remove(match_sets, spam=spam)
            except:
                logger.info(
                    f'\nERROR: Submission {submission.id} on /r/{submission.subreddit.display_name} was NOT removed '
                    f'and triggered {len(match_sets.remove)} matches.')
                traceback.print_exc()
            finally:
                return

        if approve:
            await self.approve()

        if report:
            await self.report(match_sets)

    async def check_multi_media(self, submission: Submission, media: set, config: list) -> set:
        return await self.media_manager.check_multi_media(submission, media, config)

    async def check_image(self, submission: Submission, media, config: list) -> MatchSets:
        return await self.media_manager.check_image(submission, media, config)

    async def check_video(self, submission: Submission, config: list) -> list:
        return await self.media_manager.check_video(submission, config)

    async def check_text(self, submission: Submission, config: list) -> list:
        return await self.media_manager.check_text(submission, config)

    async def report(self, match_sets: MatchSets) -> None:
        actionable: ActionableItem = match_sets.report[0]
        submission = actionable.submission
        if 'report_reason' in actionable.rule_set:
            report_reason = actionable.rule_set['report_reason']
            # TODO: Supply submission_type instead of placeholder "Image"
            report_reason = replace_placeholders(
                submission, 'Image', report_reason, actionable.rule_set, match_sets.report)
            await submission.report(report_reason)
        else:
            await submission.report(
                f'This content appears to violate the rules. It matched {len(match_sets.report)} times.')
        # TODO: Add comment_remove to wiki manager and allow mods to have bot comment removed comments

        await self.apply_extras(match_sets)
        logger.info(
            f'Submission {submission.id} on /r/{submission.subreddit.display_name} triggered {len(match_sets.report)} matches.')

    async def remove(self, match_sets: MatchSets, spam: bool) -> None:
        submission = match_sets.remove[0].submission
        rule_set = match_sets.remove[0].rule_set
        comment = rule_set['comment'].replace('\n', '  \n\n') if 'comment' in rule_set else default_comment
        comment = replace_placeholders(submission, 'Image', comment, rule_set, match_sets)

        submission.mod.remove(mod_note=rule_set['action_reason'], spam=spam)
        reply = submission.reply(body=comment)
        await self.apply_extras(match_sets, reply)
        logger.info(
            f'\nSubmission {submission.id} on /r/{submission.subreddit.display_name} was removed and triggered {len(match_sets.remove)} matches.')

    @staticmethod
    async def apply_extras(match_sets: MatchSets, comment: Comment = None) -> None:
        for match_set in match_sets:
            if len(match_set) < 1:
                continue

            rule_set = match_set[0].rule_set
            submission = match_set[0].submission

            if comment and 'comment_stickied' in rule_set and rule_set['comment_stickied'] == 'yes':
                comment.mod.distinguish(how=rule_set['comment_stickied'])

            if comment and 'comment_locked' in rule_set and rule_set['comment_locked']:
                comment.mod.lock()

            if 'set_flair' in rule_set:
                if not submission.link_flair_text:
                    submission.mod.flair(flair_template_id=rule_set['set_flair'])
                elif 'override_flair' in rule_set and rule_set['override_flair']:
                    submission.mod.flair(flair_template_id=rule_set['set_flair'])

            if 'set_locked' in rule_set:
                if not submission.locked and rule_set['set_locked']:
                    submission.mod.lock()
                elif submission.locked and not rule_set['set_locked']:
                    submission.mod.unlock()

            if 'set_nsfw' in rule_set and rule_set['set_nsfw'] and not submission.over_18:
                submission.mod.nsfw()

            if 'set_spoiler' in rule_set and rule_set['set_spoiler'] and not submission.spoiler:
                if rule_set['set_spoiler'] and not submission.spoiler:
                    submission.mod.spoiler()
                elif not rule_set['set_spoiler'] and submission.spoiler:
                    submission.mod.unspoiler()

            if 'set_contest_mode' in rule_set:
                if rule_set['set_contest_mode'] and not submission.contest_mode:
                    submission.mod.contest_mode(state=True)
                elif not rule_set['set_contest_mode'] and submission.contest_mode:
                    submission.mod.contest_mode(state=False)

            if 'set_original_content' in rule_set:
                if rule_set['set_original_content'] and not submission.is_original_content:
                    submission.mod.set_original_content()
                elif not rule_set['set_original_content'] and submission.is_original_content:
                    submission.mod.unset_original_content()

            if 'set_suggested_sort' in rule_set and submission.suggested_sort != rule_set['set_suggested_sort'].lower():
                submission.mod.suggested_sort(sort=rule_set['set_suggested_sort'])

            if 'ignore_reports' in rule_set:
                if rule_set['ignore_reports']:
                    submission.mod.ignore_reports()
                else:
                    submission.mod.unignore_reports()

    async def approve(self) -> None:
        pass

    async def comment(self) -> None:
        pass
