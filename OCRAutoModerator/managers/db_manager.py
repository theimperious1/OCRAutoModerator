""" OCRAutoModerator database functions
@authors:
---
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""
from typing import Union

import aiosqlite
from praw.models import Submission
from OCRAutoModerator.config.config import db_path


async def insert_submission(submission: Submission, media_hash: Union[int, list] = None) -> bool:
    if hasattr(submission, 'author') and submission.author.name is not None:
        username = submission.author.name
    else:
        username = 'AUTHOR_WAS_DELETED'
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO viewed_submissions (id, subreddit, title, author, url_overridden_by_dest) VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
            (submission.id, submission.subreddit.display_name, submission.title, username,
             submission.url_overridden_by_dest if hasattr(submission, 'url_overridden_by_dest') else None))
        await db.commit()
        return True


async def get_viewed_submissions() -> set:
    async with aiosqlite.connect(db_path) as db:
        rows = await db.execute("SELECT * FROM viewed_submissions")
        async with rows as cursor:
            results = await cursor.fetchall()
            res = set()
            for result in results:
                res.add(result[0])
            return res
