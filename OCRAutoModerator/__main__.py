"""
OCRAutoModerator Reddit bot to act as AutoModerator for text in images/videos/gifs, and potentially objects in them too.
"""
import argparse
import asyncio
import logging

from OCRAutoModerator.bot import BotClient, logger

client = BotClient()

logging_level_mapping = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
    'notset': logging.NOTSET
}

formatting = "[%(asctime)s] [%(levelname)s:%(name)s] %(message)s"
# noinspection PyArgumentList
logging.basicConfig(
    format=formatting,
    level=logging.INFO,
    handlers=[logging.FileHandler('ocrautomoderator.log'),
              logging.StreamHandler()])

parser = argparse.ArgumentParser(
    description='Provides tools to interact with and run the bot')
parser.add_argument('-r', '--run', action='store_true', help='Runs the bot')
parser.add_argument('-l', '--level', nargs='?', choices=['info', 'debug', 'warning', 'error', 'notset', 'critical'],
                    help='Sets the logging level to use when running the bot')

args = parser.parse_args()

if args.level:
    logger.setLevel(logging_level_mapping[args.level])
    logger.info(f"Set logging level to {logging_level_mapping[args.level]}")

if args.run:
    asyncio.run(client.load_data())
    client.run()
