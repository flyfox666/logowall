"""Logo file validation and optimisation.

The file type is decided from the content (magic bytes), never from the
client-supplied filename or Content-Type, so a script or HTML page cannot be
stored under logos/ by naming it `logo.png`. Large raster logos are
downscaled so the wall and poster export don't download multi-MB images.
"""
import io
import re
import hashlib
from typing import Optional, Tuple

from . import config

try:
    from PIL import Image
except ImportError:  # Pillow is optional: without it logos are stored as-is
    Image = None

ALLOWED_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico')
SAFE_LOGO_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$')


class InvalidImage(ValueError):
    pass


def sniff_image(content: bytes) -> Optional[str]:
    """Return the canonical extension for a supported image, else None."""
    head = content[:64]
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if head.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    if head.startswith((b'GIF87a', b'GIF89a')):
        return '.gif'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return '.webp'
    if head[:4] == b'\x00\x00\x01\x00':
        return '.ico'
    text = content[:2048].lstrip(b'\xef\xbb\xbf \t\r\n').lower()
    if text.startswith((b'<?xml', b'<svg', b'<!--', b'<!doctype svg')) and b'<svg' in text:
        return '.svg'
    return None


def is_safe_logo_name(name: str) -> bool:
    return bool(SAFE_LOGO_NAME.match(name or '')) and name.lower().endswith(ALLOWED_EXTS)


def optimize(content: bytes, ext: str) -> bytes:
    """Downscale raster logos whose longest side exceeds LOGO_MAX_PX.

    Format (and transparency) is preserved; animated GIFs and vector/icon
    formats are left untouched. Returns the original bytes when no change
    is needed or Pillow is unavailable.
    """
    max_px = config.LOGO_MAX_PX
    if Image is None or max_px <= 0 or ext not in ('.png', '.jpg', '.webp'):
        return content
    try:
        with Image.open(io.BytesIO(content)) as im:
            if getattr(im, 'is_animated', False) or max(im.size) <= max_px:
                return content
            im.thumbnail((max_px, max_px), Image.LANCZOS)
            out = io.BytesIO()
            if ext == '.jpg':
                if im.mode not in ('RGB', 'L'):
                    im = im.convert('RGB')
                im.save(out, 'JPEG', quality=90, optimize=True)
            elif ext == '.webp':
                im.save(out, 'WEBP', quality=90)
            else:
                im.save(out, 'PNG', optimize=True)
            data = out.getvalue()
            return data if len(data) < len(content) else content
    except Exception:
        return content


def validate_raster(content: bytes, ext: str):
    """Make sure a raster image actually decodes (rejects polyglots/garbage)."""
    if Image is None or ext == '.svg':
        return
    try:
        with Image.open(io.BytesIO(content)) as im:
            im.verify()
    except Exception as e:
        raise InvalidImage(f'Corrupt or unsupported image: {e}')


def prepare_logo(content: bytes) -> Tuple[bytes, str]:
    """Validate + optimise an uploaded/downloaded logo. Returns (bytes, ext)."""
    if not content:
        raise InvalidImage('Empty file')
    ext = sniff_image(content)
    if not ext:
        raise InvalidImage('Not a supported image (png / jpg / gif / webp / svg / ico)')
    validate_raster(content, ext)
    return optimize(content, ext), ext


def content_key(content: bytes, ext: str) -> str:
    return hashlib.md5(content).hexdigest()[:12] + ext
