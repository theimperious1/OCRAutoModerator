from collections import namedtuple

VideoData = namedtuple('VideoData', 'cap duration frame_count fps')
GifData = namedtuple('GifData', 'gif duration frame_count fps')
ActionData = namedtuple('ActionData', 'item action action_reason priority')
ActionData2 = namedtuple('ActionData2', 'item action action_reason priority')
MatchSets = namedtuple('MatchSets', 'remove spam approve report')
ActionableItem = namedtuple('ActionableItem', 'action_data submission rule_set')
