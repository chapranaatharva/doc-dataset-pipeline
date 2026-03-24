# processor.py
# Takes raw text and returns a list of clean prompt/completion pairs
# ready for LLM fine-tuning export (JSONL format).

import re


# ── Public API ────────────────────────────────────────────────────────────────

def clean_and_chunk(raw_text: str, chunk_size: int = 300) -> list:
    """
    Steps:
      1. Clean  — remove noise (extra whitespace, special chars, page numbers)
      2. Split  — break into sentences
      3. Chunk  — group sentences into chunks of ~chunk_size words
      4. Format — wrap each chunk as {"prompt": ..., "completion": ..., "meta": {...}}

    Args:
        raw_text   : raw string from extractor
        chunk_size : target word count per chunk (default 300)

    Returns:
        list of dicts [{"prompt": str, "completion": str, "meta": {...}}, ...]
    """
    cleaned   = _clean(raw_text)
    sentences = _split_sentences(cleaned)
    chunks    = _chunk_sentences(sentences, chunk_size)
    return _format_pairs(chunks)


# ── Step 1: Clean ─────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\bPage\s+\d+\s+(of\s+\d+)?\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\'\"]', ' ', text)
    text = text.strip()
    return text


# ── Step 2: Split into sentences ──────────────────────────────────────────────

def _split_sentences(text: str) -> list:
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if len(s.split()) >= 5]


# ── Step 3: Group sentences into chunks ───────────────────────────────────────

def _chunk_sentences(sentences: list, chunk_size: int) -> list:
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        word_count = len(sentence.split())
        current_chunk.append(sentence)
        current_word_count += word_count

        if current_word_count >= chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_word_count = 0

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


# ── Step 4: Format as prompt/completion pairs with quality metadata ────────────

def _format_pairs(chunks: list) -> list:
    pairs = []
    for chunk in chunks:
        sentences = re.split(r'(?<=[.!?])\s+', chunk, maxsplit=1)
        if len(sentences) == 2:
            prompt, completion = sentences
        else:
            words = chunk.split()
            half = max(1, len(words) // 2)
            prompt     = ' '.join(words[:half])
            completion = ' '.join(words[half:])

        word_count = len(chunk.split())
        char_count = len(chunk)
        sentence_count = len(re.findall(r'[.!?]+', chunk))

        pairs.append({
            'prompt':     prompt.strip(),
            'completion': completion.strip(),
            'meta': {
                'word_count':     word_count,
                'char_count':     char_count,
                'sentence_count': max(1, sentence_count),
                'quality':        _quality_score(word_count, sentence_count)
            }
        })

    return pairs


def _quality_score(word_count: int, sentence_count: int) -> str:
    """Simple quality rating based on chunk density."""
    if word_count >= 200 and sentence_count >= 3:
        return 'high'
    elif word_count >= 80:
        return 'medium'
    else:
        return 'low'