""" OCRAutoModerator OCR functions
@authors:
---
https://github.com/theimperious1
https://www.reddit.com/user/theimperious1
"""

import logging
from pytesseract import pytesseract
import easyocr

# from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)
pytesseract.tesseract_cmd = r'/usr/bin/tesseract'


class ImageReaderTesseract:

    def __init__(self):
        # self.paddleocr = PaddleOCR(use_angle_cls=True, lang='en')
        self.easyocr = easyocr.Reader(['en'])

    def read_all_methods(self, fp, media=None) -> list[tuple]:
        # TODO: Get rid of duplicates from videos having dozens of identical frames for memes
        pytes_result = self.read_image_pytesseract(fp if not media else media)
        # paddle_result = await self.read_image_paddleocr(fp)
        easyocr_result = self.read_image_easyocr(fp)

        # merged_result = paddle_result + easyocr_result
        easyocr_result.append((pytes_result, 'No Data'))
        return easyocr_result

    @staticmethod
    def read_image_pytesseract(fp) -> str:
        """
        This method is pretty fast, but slower than easyocr. 10 seconds for 60 560kb frames.
        Made by Google and pretty good, but performs badly on small or large text in some cases.

        https://openbase.com/python/pytesseract
        """
        return pytesseract.image_to_string(fp)

    def read_image_paddleocr(self, fp) -> list:
        """
        This method is notably slow. 33 seconds for 60 560kb frames.
        Probably best if skipped on videos.

        https://openbase.com/python/paddleocr
        :param fp: File name or link
        :param lang: Language code to use. e.g en for english or es for spanish.
        :return: List of tuples. e.g ('Meow', 0.943947975492). Trigger, Certainty.
        """

        result = self.paddleocr.ocr(fp)
        results = []
        for idx in range(len(result)):
            res = result[idx]
            for line in res:
                results.append(line[1])

        return results

    def read_image_easyocr(self, fp) -> list:
        """
        This method is very fast. 5 seconds for 60 560kb frames.
        Good at small text and big text. Can find watermarks, copyright, onlyfans links, etc.

        https://openbase.com/python/easyocr
        :param fp:
        :param lang: List of language codes to use. e.g ['ch_sim', 'en]
        :return: List of tuples. e.g ('Meow', 0.943947975492). Trigger, Certainty.
        """
        result = self.easyocr.readtext(fp)
        results = []
        for tupl in result:
            results.append((tupl[1], tupl[2]))

        return results
