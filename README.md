# 📄 Doc-to-Dataset Pipeline

**Convert any unstructured document into clean, LLM-ready training data.**

Upload PDFs, scrape URLs, OCR images, or paste raw text — the pipeline extracts, cleans, chunks, and exports structured prompt/completion pairs in JSONL, JSON, or CSV format, ready for fine-tuning models like GPT, Mistral, or Llama.

> 🔗 **Live Demo:** [doc-dataset-pipeline.onrender.com](https://doc-dataset-pipeline.onrender.com)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Multi-source ingestion** | PDF (PyMuPDF), URL (BeautifulSoup), Image/OCR (Tesseract), Plain text |
| **Smart chunking** | Sentence-aware splitting with configurable chunk size (50–800 words) |
| **Quality scoring** | Each chunk rated HIGH / MEDIUM / LOW based on word density and sentence count |
| **Batch upload** | Drag & drop multiple files at once for bulk processing |
| **Duplicate detection** | MD5 hashing prevents re-processing the same document |
| **Search & filter** | Instantly search across all processed datasets |
| **Multi-format export** | JSONL (LLM fine-tuning), JSON, CSV |
| **Dashboard stats** | Live totals for datasets, chunks, and words processed |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, SQLite
- **Text Extraction:** PyMuPDF, BeautifulSoup4, Tesseract OCR
- **NLP Processing:** Regex-based sentence splitting, noise removal, smart chunking
- **Frontend:** Vanilla HTML/CSS/JS — dark theme, responsive UI
- **Deployment:** Render (Gunicorn)

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/chapranaatharva/doc-dataset-pipeline.git
cd doc-dataset-pipeline

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

Open **http://localhost:5000** in your browser.

---

## ⚙️ Environment Configuration

For local development with PostgreSQL, you can create a `.env` file in the root directory:

```env
# Optional: Set this to use PostgreSQL. 
# If omitted, the app will automatically default to local SQLite.
DATABASE_URL=postgresql://user:password@localhost/dbname
```

Make sure to install `python-dotenv` if you want the `.env` file to be loaded automatically:
```bash
pip install python-dotenv
```

---

## 📊 How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  PDF / URL  │────▶│   Extract    │────▶│   Clean &   │────▶│   Export as  │
│ Image / Text│     │   Raw Text   │     │   Chunk     │     │ JSONL/JSON/CSV│
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

1. **Extract** — Pull raw text from any supported source
2. **Clean** — Remove noise (page numbers, URLs, special chars, extra whitespace)
3. **Chunk** — Split into sentence-aware segments of configurable size
4. **Format** — Each chunk → `{"prompt": "...", "completion": "..."}` pair with quality metadata
5. **Export** — Download as JSONL (industry standard for LLM fine-tuning)

---

## 📁 Project Structure

```
├── app.py              # Flask backend — routes, DB, API endpoints
├── extractor.py        # Text extraction (PDF, URL, OCR, plaintext)
├── processor.py        # NLP pipeline — clean, chunk, format, score
├── templates/
│   └── index.html      # Dashboard UI
├── render.yaml         # Render deployment config
└── requirements.txt    # Python dependencies
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ingest` | Upload file(s), URL, or text for processing |
| `GET` | `/api/datasets` | List all datasets (supports `?q=` search) |
| `GET` | `/api/datasets/:id` | Get dataset with all chunks |
| `DELETE` | `/api/datasets/:id` | Delete a dataset |
| `GET` | `/api/export/:id/:fmt` | Export as `jsonl`, `json`, or `csv` |

---

## 📝 Output Format (JSONL)

Each line in the exported `.jsonl` file:

```json
{"prompt": "First sentence of the chunk.", "completion": "Remaining sentences providing context and detail..."}
```

This is the standard format used by OpenAI, Mistral, and other providers for fine-tuning custom models.

---

## 📌 Notes

- **Render free tier** uses ephemeral storage — the SQLite database resets on redeploy. For production use, swap to PostgreSQL.
- **OCR** requires [Tesseract](https://github.com/tesseract-ocr/tesseract) installed on your OS.

---

Built by **Atharva Chaprana**
