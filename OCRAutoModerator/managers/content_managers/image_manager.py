""" OCRAutoModerator Image Manager & functions
@authors:
---
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""

import logging
from OCRAutoModerator.data_types import ActionableItem

logger = logging.getLogger(__name__)


class ImageManager:

    def __init__(self, reddit, image_reader):
        self.reddit = reddit
        self.ir = image_reader

    def check_image(self, url, media, config):
        merged_result = self.ir.read_all_methods(url, media)
        to_be_removed, to_be_reported = [], []
        auto_remove = False

        for result in merged_result:
            for rule_set in config:
                action_type = rule_set['type'].strip()
                action = rule_set['action'].strip()

                if (action_type != 'any' and action_type != 'image') or action == 'nothing':
                    continue

                rule = rule_set['rule']
                action_reason = rule_set['action_reason']
                priority = rule_set['priority']

                for item in rule:
                    if item.lower() in result[0].lower().strip():
                        if not auto_remove and action == 'remove':
                            auto_remove = True
                        if action == 'remove':
                            to_be_removed.append(ActionableItem(item, action, action_reason, priority))
                        elif action == 'report':
                            to_be_reported.append(ActionableItem(item, action, action_reason, priority))

        return sorted(to_be_removed, key=lambda actionable: actionable.priority), \
            sorted(to_be_reported, key=lambda actionable: actionable.priority)
