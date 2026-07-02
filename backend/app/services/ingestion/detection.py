import hashlib
import mimetypes
from pathlib import Path

import magic


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".pptx",
    ".txt",
    ".html",
    ".htm",
    ".xml",
    ".csv",
    ".md",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".tif",
    ".dwg",
    ".dxf",
    ".zip",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_file_type(filename: str, data: bytes) -> tuple[str, str | None]:
    suffix = Path(filename).suffix.lower()
    mime = magic.from_buffer(data, mime=True) or mimetypes.guess_type(filename)[0]
    if suffix in SUPPORTED_EXTENSIONS:
        return suffix.lstrip("."), mime
    if mime:
        ext = mimetypes.guess_extension(mime) or "bin"
        return ext.lstrip("."), mime
    return "bin", mime
