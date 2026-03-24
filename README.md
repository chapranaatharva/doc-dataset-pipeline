# Document-to-Dataset Pipeline

A Flask web app that ingests unstructured documents and transforms them into clean, structured datasets ready for LLM fine-tuning.

**Live Demo:** [your-app.onrender.com](https://your-app.onrender.com)

---

## What it does

Takes any messy document → outputs LLM-ready JSONL training data.

| Input | How |
|-------|-----|
| PDF | PyMuPDF text extraction |
| URL | BeautifulSoup web scraping |
| Image | Tesseract OCR |
| Plain text | Direct ingestion |

Each document is cleaned, chunked into ~N-word segments, and formatted as `{"prompt": ..., "completion": ...}` pairs — the standard format for fine-tuning OpenAI, Mistral, and Llama models.

---

## Features

- **Multi-file batch upload** — drag and drop multiple files at once
- **Adjustable chunk size** — slider from 100 to 600 words per chunk
- **Duplicate detection** — MD5 hash check prevents re-processing the same content
- **Quality scoring** — each chunk rated high / medium / low based on density
- **Search & filter** — real-time search across all datasets
- **Word & character counts** — total words and characters processed per dataset
- **Export formats** — JSONL, CSV, JSON
- **Preview modal** — inspect chunks before exporting
- **REST API** — all functionality accessible via clean endpoints

---

## Project structure

```
pipeline/
├── app.py              # Flask app — routes, DB, API endpoints
├── extractor.py        # Text extraction (PDF / URL / image / text)
├── processor.py        # Cleaning, chunking, quality scoring
├── requirements.txt    # Python dependencies
├── render.yaml         # Render deployment config
└── templates/
    └── index.html      # Dashboard UI
```

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install Tesseract (for image/OCR support)
# Ubuntu:  sudo apt install tesseract-ocr
# Mac:     brew install tesseract
# Windows: https://github.com/UB-Mannheim/tesseract/wiki

# Run
python app.py
```

Open `http://localhost:5000`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ingest` | Ingest file(s), URL, or text |
| GET | `/api/datasets` | List all datasets (supports `?q=search`) |
| GET | `/api/datasets/<id>` | Get dataset with all chunks |
| DELETE | `/api/datasets/<id>` | Delete a dataset |
| GET | `/api/export/<id>/<fmt>` | Export as `jsonl` / `csv` / `json` |

### Ingest examples

```bash
# Single file
curl -X POST -F "file=@document.pdf" -F "chunk_size=300" \
  http://localhost:5000/api/ingest

# Multiple files
curl -X POST -F "file=@doc1.pdf" -F "file=@doc2.pdf" \
  http://localhost:5000/api/ingest

# URL
curl -X POST -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "chunk_size": 200}' \
  http://localhost:5000/api/ingest

# Plain text
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "Your text here", "name": "my-doc"}' \
  http://localhost:5000/api/ingest
```

---

## Output format (JSONL)

```json
{"prompt": "First sentence of the chunk.", "completion": "Rest of the chunk text here..."}
{"prompt": "Next chunk first sentence.", "completion": "Rest of second chunk..."}
```

Each line is a self-contained training example. Feed directly into any fine-tuning script.

---

## Tech stack

Python · Flask · SQLite · PyMuPDF · BeautifulSoup · Tesseract · Gunicorn · Render