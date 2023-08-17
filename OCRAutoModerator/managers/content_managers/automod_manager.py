import logging
from typing import Union
from OCRAutoModerator.data_types import ActionData, ActionableItem, MatchSets
from praw.models import Submission

# Set up logging
logger = logging.getLogger(__name__)


class AutoModManager:

    def __init__(self, reddit):
        self.reddit = reddit

    async def check_against_rules(self, submission: Submission, identified_text_list: list, config: list) -> MatchSets:
        remove, report, spam, approve = [], [], [], []
        for item in identified_text_list:
            for rule_set in config:
                actionable_results = await self.check_against_rule(submission, item, rule_set)

                if not actionable_results:
                    continue

                [
                    remove.append(actionable_result) for actionable_result in actionable_results
                    if actionable_result.action_data.action == 'remove'
                ]
                # This is some interesting formatting. I kinda like it!
                [
                    report.append(actionable_result) for actionable_result in actionable_results
                    if actionable_result.action_data.action == 'report'
                ]

                [
                    spam.append(actionable_result) for actionable_result in actionable_results
                    if actionable_result.action_data.action == 'spam'
                ]

                [
                    approve.append(actionable_result) for actionable_result in actionable_results
                    if actionable_result.action_data.action == 'approve'
                ]

        return MatchSets(sorted(remove, key=lambda actionable: actionable.action_data.priority),
                         sorted(spam, key=lambda actionable: actionable.action_data.priority),
                         sorted(approve, key=lambda actionable: actionable.action_data.priority),
                         sorted(report, key=lambda actionable: actionable.action_data.priority))

    async def check_against_rule(self, submission: Submission, identified_text, rule_set: dict) -> Union[list, None]:
        if not hasattr(submission, 'author') or submission.author is None:
            # Submission is deleted or author is otherwise inaccessible
            return

        actionable_results = []
        action_type = rule_set['type'].strip()
        action = rule_set['action'].strip()

        if (action_type != 'any' and action_type != 'image') or action == 'nothing':
            return

        rule = rule_set['rule']
        action_reason = rule_set['action_reason']
        priority = rule_set['priority']

        if 'is_locked' in rule_set:
            if not submission.locked and rule_set['is_locked']:
                return
            elif submission.locked and not rule_set['is_locked']:
                return

        if 'is_original_content' in rule_set:
            if not submission.is_original_content and rule_set['is_original_content']:
                return
            elif submission.is_original_content and not rule_set['is_original_content']:
                return

        if 'is_self' in rule_set:
            if not submission.is_self and rule_set['is_self']:
                return
            elif submission.is_self and not rule_set['is_self']:
                return

        if 'is_nsfw' in rule_set:
            if not submission.over_18 and rule_set['is_nsfw']:
                return
            elif submission.over_18 and not rule_set['is_nsfw']:
                return

        if 'flair_text' in rule_set:
            if not hasattr(submission, 'link_flair_text'):
                return

            if submission.link_flair_text is None or submission.link_flair_text != rule_set['flair_text']:
                return

        if 'flair_css_class' in rule_set:
            if not hasattr(submission, 'link_flair_css_class'):
                return

            if submission.link_flair_css_class is None or \
                    submission.link_flair_css_class != rule_set['flair_css_class']:
                pass
            return

        if 'flair_template_id' in rule_set:
            if not hasattr(submission, 'link_flair_template_id'):
                return

            if submission.link_flair_template_id is None or \
                    submission.link_flair_template_id != rule_set['flair_template_id']:
                return

        if 'has_comments' in rule_set:
            if not self.check_operator_conditional(submission, 'num_comments', rule_set['has_comments']):
                return

        if 'author' in rule_set:
            author = rule_set['author']
            if 'post_karma' in author:
                if not self.check_operator_conditional(submission, 'link_karma', author['post_karma']):
                    return

            if 'comment_karma' in author:
                if not self.check_operator_conditional(submission, 'comment_karma', author['comment_karma']):
                    return

            if 'account_age' in author:
                if not self.check_operator_conditional(submission, 'account_age', author['account_age']):
                    return

            if 'has_followers' in author:
                if not self.check_operator_conditional(submission, 'has_followers', author['has_followers']):
                    return

            if 'has_trophies' in author:
                if not self.check_operator_conditional(submission, 'has_trophies', author['has_trophies']):
                    return

            if 'has_submissions' in author:
                if not self.check_operator_conditional(submission, 'submissions', author['has_submissions']):
                    return

            if 'has_comments' in author:
                if not self.check_operator_conditional(submission, 'comments', author['has_comments']):
                    return

            if 'has_verified_email' in author:
                if author['has_verified_email'] and not submission.author.has_verified_email:
                    return
                if not author['has_verified_email'] and submission.author.has_verified_email:
                    return

            if 'is_mod' in author:
                if author['is_mod'] and not submission.author.is_mod:
                    return
                if not author['is_mod'] and submission.author.is_mod:
                    return

            if 'is_gold' in author:
                if author['is_gold'] and not submission.author.is_gold:
                    return
                if not author['is_gold'] and submission.author.is_gold:
                    return

            if 'is_suspended' in author:
                if author['is_suspended'] and not submission.author.is_suspended:
                    return
                if not author['is_suspended'] and submission.author.is_suspended:
                    return

            if hasattr(submission.author, 'subreddit'):
                # TODO: Finish this
                if 'is_nsfw' in author:
                    if author['is_nsfw'] and not submission.author.subreddit['over_18']:
                        return
                    if not author['is_nsfw'] and submission.author.subreddit['over_18']:
                        return

                if 'mod_notes' in author:
                    # TODO: Add "create_mod_note"
                    if not await self.check_conditional(submission, author, 'mod_notes'):
                        return

                if 'description_contains' in author:
                    if not await self.check_conditional(submission, author, 'description_contains'):
                        return

                if 'links' in author:
                    links = author['links']
                    # satisfy_any_threshold = author['links']['satisfy_any_threshold'] \
                    #     if 'satisfy_any_threshold' in author['links'] else False
                    satisfy_any_threshold = True
                    met_conditions = []
                    user_submissions = list(self.reddit.info(f't3_{user_submission.id}' for user_submission in submission.author.submissions.new(limit=125)))
                    for user_submission in user_submissions:
                        if hasattr(user_submission, 'url_overridden_by_dest'):
                            if user_submission.url_overridden_by_dest in links:
                                met_conditions.append(ActionableItem(
                                    ActionData(user_submission.url_overridden_by_dest, action, action_reason, priority),
                                    submission,
                                    rule_set))

                    met_condition_len = len(met_conditions)
                    if (satisfy_any_threshold and met_condition_len > 0) or (
                            not satisfy_any_threshold and met_condition_len == len(links)):
                        [actionable_results.append(item) for item in met_conditions]

                    if met_condition_len == 0:
                        return
                    return actionable_results

        for item in rule:
            if (type(identified_text) is list and item.lower() in identified_text[0].lower().strip()) \
                    or (type(identified_text) is str and item.lower() in identified_text.lower().strip()):
                actionable_results.append(
                    ActionableItem(ActionData(item, action, action_reason, priority), submission, rule_set))

        return actionable_results

    @staticmethod
    def check_operator_conditional(submission: Submission, conditional_type: str, conditional: list) -> bool:
        # TODO: Does getattr work with praws lazy loading? These may always be None. Verify.
        # Should getattr be awaited since submission.author is an API call? Would that even work?
        attribute_value = len(submission.author.trophies()) \
            if conditional_type == 'has_trophies' else getattr(submission.author, conditional_type)

        if conditional_type == 'comments':
            comments = []
            [comments.append(comment) for comment in submission.author.comments.new(limit=125)]
            attribute_value = len(comments)

        if conditional[0] == '>=' and attribute_value <= conditional[1]:
            return False
        elif conditional[0] == '<=' and attribute_value >= conditional[1]:
            return False
        elif conditional[0] == '>' and attribute_value < conditional[1]:
            return False
        elif conditional[0] == '<' and attribute_value > conditional[1]:
            return False

        return True

    @staticmethod
    def check_operator_conditional_time(submission: Submission, conditional_type: str, conditional: tuple) -> bool:
        attribute_value = getattr(submission.author, conditional_type)
        if conditional[0] == '>=' and attribute_value <= conditional[1]:
            return False
        elif conditional[0] == '<=' and attribute_value >= conditional[1]:
            return False
        elif conditional[0] == '>' and attribute_value < conditional[1]:
            return False
        elif conditional[0] == '<' and attribute_value > conditional[1]:
            return False

    @staticmethod
    async def check_conditional(submission: Submission, author: dict, conditional_key: str) -> bool:
        contained_requirement = False
        contains = author[conditional_key]['contains']
        mod_notes = submission.author.notes.subreddits(submission.subreddit.display_name)
        if type(contains) is str:
            for mod_note in mod_notes:
                if mod_note.note is None:
                    continue

                if contains in mod_note.note:
                    contained_requirement = True

        else:
            satisfy_any_threshold = author[conditional_key]['satisfy_any_threshold'] \
                if 'satisfy_any_threshold' in author[conditional_key] else True
            for condition in contains:
                for mod_note in mod_notes:
                    if mod_note.note is None:
                        continue

                    if satisfy_any_threshold and condition in mod_note.note:
                        contained_requirement = True
                        break
                    elif not satisfy_any_threshold and condition not in mod_note:
                        break

        if not contained_requirement:
            return False

        return True
