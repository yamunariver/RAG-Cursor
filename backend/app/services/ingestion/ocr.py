from io import BytesIO

from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract


def ocr_image(data: bytes) -> str:
    image = Image.open(BytesIO(data))
    return pytesseract.image_to_string(image)


def ocr_pdf(data: bytes) -> tuple[str, int]:
    pages = convert_from_bytes(data)
    texts = [pytesseract.image_to_string(page) for page in pages]
    return "\n\n".join(texts), len(pages)
