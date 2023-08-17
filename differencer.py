"""
Made by RepostSentinel developer, refactored by nickofolas
@authors:
https://github.com/korbendallas-reddit/RepostSentinel
---
https://github.com/nickofolas/
https://www.reddit.com/user/nickofolas

cv2_comparison off stackoverflow, modified by theimperious1
"""
from PIL import Image


def diff_hash(image):
    """Generates a difference hash from an image"""
    img = image.convert("L")
    img = img.resize((8, 8), Image.ANTIALIAS)
    prev_px = img.getpixel((0, 7))
    hash_diff = 0
    for row in range(0, 8, 2):
        for col in range(8):
            hash_diff <<= 1
            pixel = img.getpixel((col, row))
            hash_diff |= 1 * (pixel >= prev_px)
            prev_px = pixel
        row += 1
        for col in range(7, -1, -1):
            hash_diff <<= 1
            pixel = img.getpixel((col, row))
            hash_diff |= 1 * (pixel >= prev_px)
            prev_px = pixel
    img.close()
    return hash_diff
