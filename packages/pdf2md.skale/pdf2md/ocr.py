# ocr.py within the pdf2md package

import os
from typing import Optional

# Heavy OCR dependencies will be lazily loaded in their respective classes


class OCRExtractor:
    supported_extensions = ['.pdf']

    def __init__(self, lang='deu'):
        self.lang = lang

    def extract_text(self, pdf_path):
        import pytesseract
        from pdf2image import convert_from_path

        # Convert PDF to images
        images = convert_from_path(pdf_path)

        full_text = []
        for i, image in enumerate(images):
            # Perform OCR on each image
            text = pytesseract.image_to_string(
                image,
                lang=self.lang
            )
            full_text.append(text)

        # Join all extracted text
        combined_text = "\n\n".join(full_text)

        return combined_text, len(images)


def get_ocr_extractor(lang='deu'):
    return OCRExtractor(lang)


class EasyOCRExtractor:
    supported_extensions = ['.pdf']

    def __init__(self, lang='de'):
        self.lang = lang
        self.reader = None

    def extract_text(self, pdf_path):
        import easyocr
        import numpy as np
        from pdf2image import convert_from_path

        if self.reader is None:
            self.reader = easyocr.Reader([self.lang])

        images = convert_from_path(pdf_path)
        full_text = []
        for image in images:
            result = self.reader.readtext(np.array(image), detail=0)
            full_text.append("\n".join(result))
        combined_text = "\n\n".join(full_text)
        return combined_text, len(images)


class PaddleOCRExtractor:
    supported_extensions = ['.pdf']

    def __init__(self, lang='german'):
        import platform
        self.lang = lang
        self.is_macos = platform.system() == 'Darwin'

        if self.is_macos:
            raise RuntimeError(
                "PaddleOCR is not supported on macOS. Please use one of these alternatives:\n"
                "- OCRExtractor (pytesseract based): '--parsers ocr'\n"
                "- EasyOCRExtractor (easyocr based): '--parsers easyocr'\n"
                "These alternatives provide similar functionality and work on macOS.")

        self.config_options = [
            # Fallback to MKLDNN acceleration (not available on macOS)
            {'use_angle_cls': True, 'lang': lang, 'ocr_version': 'PP-OCRv4',
             'download_model': True, 'use_gpu': False, 'enable_mkldnn': True},
            # Most basic configuration
            {'use_angle_cls': True, 'lang': lang, 'ocr_version': 'PP-OCRv4',
             'download_model': True, 'use_gpu': False}
        ]

    def extract_text(self, pdf_path):
        try:
            from pdf2image import convert_from_path

            # Initialize OCR with fallback options
            ocr = None
            for config in self.config_options:
                try:
                    ocr = PaddleOCR(**config)
                    break
                except Exception as e:
                    print(
                        f"PaddleOCR initialization attempt failed with config {config}: {str(e)}")
                    continue

            if ocr is None:
                raise RuntimeError(
                    "Failed to initialize PaddleOCR with any CPU configuration")

            images = convert_from_path(pdf_path)
            full_text = []
            for image in images:
                try:
                    result = ocr.ocr(np.array(image), cls=True)
                    if result and result[0]:
                        text = [line[1][0] for line in result[0]]
                        full_text.append("\n".join(text))
                except Exception as e:
                    print(f"OCR failed for page: {str(e)}")
                    continue

            if not full_text:
                raise Exception("No text extracted from any page")

            combined_text = "\n\n".join(full_text)
            return combined_text, len(images)
        except Exception as e:
            print(f"PaddleOCR extraction failed for {pdf_path}: {str(e)}")
            raise
