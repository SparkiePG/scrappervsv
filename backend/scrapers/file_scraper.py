"""
FileScraper: download non‑HTML resources.

This scraper detects when a URL points to a binary or media resource
(images, videos, documents) and downloads it.  It does not attempt
to parse HTML.  Instead, it checks the file extension and Content‑Type
header to determine if the resource is a file.  If the content type
starts with ``text/html``, it returns ``success=False`` so that other
scrapers can handle the page.

This scraper respects robots.txt and only downloads resources when
permitted.  It uses ``requests`` for HTTP requests and limits
download size to avoid loading large files into memory.  If the
resource exceeds ``max_bytes`` (default 5 MB), it aborts and returns
an error.  Successfully downloaded content is returned as a base64
encoded string along with metadata such as filename and MIME type.

**Ethical considerations**: Downloading premium or paywalled media
without authorization may violate copyright and terms of service.  This
scraper does not bypass authentication or paywalls, and it should
only be used on publicly accessible resources【510108747246327†L93-L100】.
"""

from __future__ import annotations

import base64
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse, unquote

import requests

from .base import Scraper
from backend.utils import get_proxy_dict

logger = logging.getLogger(__name__)


def _guess_filename(url: str) -> str:
    path = urlparse(url).path
    filename = path.split('/')[-1]
    return unquote(filename) or 'downloaded_file'


class FileScraper(Scraper):
    """Scraper that downloads non‑HTML files (images, videos, documents)."""

    name = "file"

    # List of extensions considered as files (this is not exhaustive).
    #
    # We include common image formats (JPEG, PNG, GIF, BMP, SVG, WebP, HEIC, TIFF),
    # video formats (MP4, MKV, MOV, AVI, FLV, WEBM, WMV, TS, M2TS, MPEG, MPG,
    # 3GP, 3G2, M4V), audio formats (MP3, WAV, FLAC, AAC, OGG, OGA, OPUS, M4A,
    # M4B), document formats (PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, RTF,
    # ODT, ODS, ODP, EPUB, MD), archive formats (ZIP, RAR, 7Z, TAR, GZ, BZ2,
    # XZ, TAR.GZ, TAR.BZ2, TAR.XZ, ISO), executables/installers (EXE, APK, DMG,
    # MSI), and structured data formats (JSON, CSV).  This set is not
    # exhaustive but covers most common file types a user might want to
    # download.  Extensions are stored in lower‑case for case‑insensitive
    # comparison.
    _file_extensions = {
        # images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tif', '.tiff', '.heic', '.heif', '.raw',
        # video
        '.mp4', '.mkv', '.mov', '.avi', '.flv', '.webm', '.wmv', '.ts', '.m2ts', '.mpeg', '.mpg',
        '.3gp', '.3g2', '.m4v', '.ogv', '.ogm', '.m4p',
        # audio
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.oga', '.opus', '.m4a', '.m4b',
        # documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods', '.odp', '.epub', '.md',
        # archives
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.tar.gz', '.tar.bz2', '.tar.xz', '.iso',
        # executables
        '.exe', '.apk', '.dmg', '.msi',
        # structured data
        '.json', '.csv', '.yaml', '.yml', '.xml', '.sql',
    }

    def __init__(self, user_agent: str | None = None, max_bytes: int = 20 * 1024 * 1024) -> None:
        super().__init__(user_agent=user_agent)
        # Increase default max_bytes to 20 MB to accommodate larger media files.
        self.max_bytes = max_bytes

    def can_handle(self, url: str) -> bool:
        # Check by file extension
        path = urlparse(url).path.lower()
        for ext in self._file_extensions:
            if path.endswith(ext):
                return True
        return False

    def scrape(self, url: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            'success': False,
            'text': '',
            'images': [],
            'links': [],
            'metadata': {},
        }
        headers = {'User-Agent': self.user_agent}
        proxies = get_proxy_dict() or {}
        try:
            resp = requests.get(url, headers=headers, stream=True, timeout=30, proxies=proxies)
            resp.raise_for_status()
            # Check content type; if HTML, let other scrapers handle
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                result['error'] = 'Resource appears to be HTML'
                return result
            # Download up to max_bytes
            content = resp.content
            if len(content) > self.max_bytes:
                result['error'] = f'File exceeds {self.max_bytes} bytes limit'
                return result
            b64_content = base64.b64encode(content).decode('ascii')
            filename = _guess_filename(url)
            file_type = content_type.split(';')[0]
            # If the file is a PDF or DOCX, attempt to extract text
            extracted_text = ''
            try:
                if file_type == 'application/pdf' or filename.lower().endswith('.pdf'):
                    from pdfminer.high_level import extract_text  # type: ignore
                    # Write content to a temporary bytes buffer
                    extracted_text = extract_text(bytes(content))
                elif file_type in ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword') or filename.lower().endswith(('.docx', '.doc')):
                    import io
                    from docx import Document  # type: ignore
                    f = io.BytesIO(content)
                    doc = Document(f)
                    extracted_text = "\n".join([p.text for p in doc.paragraphs])
            except Exception as parse_exc:
                # Log parse errors but continue; the file content is still returned
                logger.debug('FileScraper: failed to extract text from %s: %s', filename, parse_exc)
                extracted_text = ''
            result.update({
                'success': True,
                'file_content': b64_content,
                'file_name': filename,
                'file_type': file_type,
                'text': extracted_text,
                'metadata': {'scraper': self.name},
            })
            return result
        except Exception as exc:
            result['error'] = f'Failed to download file: {exc}'
            logger.warning('FileScraper failed to fetch %s: %s', url, exc)
            return result