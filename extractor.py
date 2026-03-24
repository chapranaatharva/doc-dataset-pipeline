# extractor.py
# Pulls raw text out of any supported source.
#
# Supported source_type values:
#   'pdf'   → PyMuPDF          (pip install pymupdf)
#   'url'   → requests + BS4   (pip install requests beautifulsoup4)
#   'png'   → Tesseract OCR    (pip install pillow pytesseract)
#   'jpg'   → same as png
#   'jpeg'  → same as png
#   'txt'   → plain read
#   'text'  → plain string pass-through (already extracted)


def extract_text(source: str, source_type: str) -> str:
    """
    Args:
        source      : file path, URL string, or raw text
        source_type : one of pdf / url / png / jpg / jpeg / txt / text
    Returns:
        raw extracted text as a single string
    """
    source_type = source_type.lower()

    if source_type == 'pdf':
        return _from_pdf(source)
    elif source_type == 'url':
        return _from_url(source)
    elif source_type in ('png', 'jpg', 'jpeg'):
        return _from_image(source)
    elif source_type in ('txt', 'text'):
        # If it looks like a file path, read it; otherwise treat as raw text
        if len(source) < 300 and source.endswith('.txt'):
            return _from_txt(source)
        return source
    else:
        raise ValueError(f"Unsupported source type: {source_type}")


# ── PDF ───────────────────────────────────────────────────────────────────────

def _from_pdf(filepath: str) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("Run: pip install pymupdf")

    doc = fitz.open(filepath)
    pages = [page.get_text() for page in doc]
    return '\n'.join(pages)


# ── URL ───────────────────────────────────────────────────────────────────────

def _from_url(url: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("Run: pip install requests beautifulsoup4")

    headers = {'User-Agent': 'Mozilla/5.0 (compatible; DocPipeline/1.0)'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Strip boilerplate
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
        tag.decompose()

    # Prefer <article> or <main> if the page has them
    main = soup.find('article') or soup.find('main') or soup.body
    return main.get_text(separator='\n', strip=True) if main else soup.get_text(separator='\n', strip=True)


# ── Image / OCR ───────────────────────────────────────────────────────────────

def _from_image(filepath: str) -> str:
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        raise ImportError("Run: pip install pillow pytesseract  (also install tesseract-ocr on your OS)")

    img = Image.open(filepath)
    return pytesseract.image_to_string(img)


# ── Plain text file ───────────────────────────────────────────────────────────

def _from_txt(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()
