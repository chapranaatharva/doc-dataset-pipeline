import os
import json
import sqlite3
import hashlib
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from extractor import extract_text
from processor import clean_and_chunk
import io
import csv

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    db = sqlite3.connect('datasets.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS datasets (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                source     TEXT NOT NULL,
                chunks     TEXT NOT NULL,
                hash       TEXT,
                word_count INTEGER DEFAULT 0,
                char_count INTEGER DEFAULT 0,
                created    TEXT DEFAULT (datetime('now'))
            )
        ''')
        try:
            db.execute('ALTER TABLE datasets ADD COLUMN hash TEXT')
        except:
            pass
        db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compute_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

def check_duplicate(text_hash: str):
    with get_db() as db:
        row = db.execute('SELECT id, name FROM datasets WHERE hash = ?', (text_hash,)).fetchone()
    return dict(row) if row else None

def compute_totals(chunks: list) -> dict:
    total_words = sum(c['meta']['word_count'] for c in chunks)
    total_chars = sum(c['meta']['char_count'] for c in chunks)
    return {'word_count': total_words, 'char_count': total_chars}

def save_dataset(name, source, chunks, text_hash):
    totals = compute_totals(chunks)
    with get_db() as db:
        cursor = db.execute(
            'INSERT INTO datasets (name, source, chunks, hash, word_count, char_count) VALUES (?, ?, ?, ?, ?, ?)',
            (name, source, json.dumps(chunks), text_hash,
             totals['word_count'], totals['char_count'])
        )
        db.commit()
        return cursor.lastrowid


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/ingest', methods=['POST'])
def ingest():
    """
    Accepts:
      - multipart with one OR multiple files (batch upload)
      - JSON body with {"url": "..."}
      - JSON body with {"text": "...", "name": "..."}
    Optional param: chunk_size (int, default 300)
    """
    chunk_size = int(request.form.get('chunk_size', 300) or
                     (request.get_json() or {}).get('chunk_size', 300))

    # ── Batch file upload ──
    if 'file' in request.files:
        files = request.files.getlist('file')
        results = []

        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                results.append({'name': file.filename, 'error': 'Invalid or unsupported file'})
                continue

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            source_type = filename.rsplit('.', 1)[1].lower()

            try:
                raw_text = extract_text(filepath, source_type)
            except Exception as e:
                results.append({'name': filename, 'error': str(e)})
                continue

            if not raw_text.strip():
                results.append({'name': filename, 'error': 'No text extracted'})
                continue

            text_hash = compute_hash(raw_text)
            duplicate = check_duplicate(text_hash)
            if duplicate:
                results.append({
                    'name': filename,
                    'duplicate': True,
                    'existing_id': duplicate['id'],
                    'existing_name': duplicate['name']
                })
                continue

            chunks    = clean_and_chunk(raw_text, chunk_size)
            dataset_id = save_dataset(filename, source_type, chunks, text_hash)
            results.append({
                'id':           dataset_id,
                'name':         filename,
                'total_chunks': len(chunks),
                'preview':      chunks[:3]
            })

        return jsonify(results), 201

    # ── URL or plain text ──
    elif request.is_json:
        data = request.get_json()
        if 'url' in data:
            source_type = 'url'
            doc_name    = data['url']
            try:
                raw_text = extract_text(data['url'], 'url')
            except Exception as e:
                return jsonify({'error': str(e)}), 422
        elif 'text' in data:
            source_type = 'text'
            doc_name    = data.get('name', 'pasted-text')
            raw_text    = data['text']
        else:
            return jsonify({'error': 'Provide file, url, or text'}), 400

        if not raw_text.strip():
            return jsonify({'error': 'Could not extract text from source'}), 422

        text_hash = compute_hash(raw_text)
        duplicate = check_duplicate(text_hash)
        if duplicate:
            return jsonify({
                'duplicate':     True,
                'existing_id':   duplicate['id'],
                'existing_name': duplicate['name']
            }), 409

        chunks     = clean_and_chunk(raw_text, chunk_size)
        dataset_id = save_dataset(doc_name, source_type, chunks, text_hash)

        return jsonify({
            'id':           dataset_id,
            'name':         doc_name,
            'total_chunks': len(chunks),
            'preview':      chunks[:3]
        }), 201

    else:
        return jsonify({'error': 'No input provided'}), 400


@app.route('/api/datasets', methods=['GET'])
def list_datasets():
    search = request.args.get('q', '').strip()
    with get_db() as db:
        if search:
            rows = db.execute(
                'SELECT id, name, source, created, word_count, char_count, json_array_length(chunks) as chunk_count '
                'FROM datasets WHERE name LIKE ? ORDER BY id DESC',
                (f'%{search}%',)
            ).fetchall()
        else:
            rows = db.execute(
                'SELECT id, name, source, created, word_count, char_count, json_array_length(chunks) as chunk_count '
                'FROM datasets ORDER BY id DESC'
            ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/datasets/<int:dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    with get_db() as db:
        row = db.execute('SELECT * FROM datasets WHERE id = ?', (dataset_id,)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    d = dict(row)
    d['chunks'] = json.loads(d['chunks'])
    return jsonify(d)


@app.route('/api/datasets/<int:dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    with get_db() as db:
        db.execute('DELETE FROM datasets WHERE id = ?', (dataset_id,))
        db.commit()
    return jsonify({'deleted': dataset_id})


@app.route('/api/export/<int:dataset_id>/<fmt>')
def export(dataset_id, fmt):
    with get_db() as db:
        row = db.execute('SELECT * FROM datasets WHERE id = ?', (dataset_id,)).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404

    chunks = json.loads(row['chunks'])
    # Strip meta from export — only prompt/completion
    clean_chunks = [{'prompt': c['prompt'], 'completion': c['completion']} for c in chunks]
    name = row['name'].replace(' ', '_')

    if fmt == 'jsonl':
        output = '\n'.join(json.dumps(c) for c in clean_chunks)
        return send_file(io.BytesIO(output.encode()), mimetype='application/jsonlines',
                         as_attachment=True, download_name=f'{name}.jsonl')
    elif fmt == 'json':
        output = json.dumps(clean_chunks, indent=2)
        return send_file(io.BytesIO(output.encode()), mimetype='application/json',
                         as_attachment=True, download_name=f'{name}.json')
    elif fmt == 'csv':
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=['prompt', 'completion'])
        writer.writeheader()
        writer.writerows(clean_chunks)
        return send_file(io.BytesIO(buf.getvalue().encode()), mimetype='text/csv',
                         as_attachment=True, download_name=f'{name}.csv')
    else:
        return jsonify({'error': 'Use jsonl, json, or csv'}), 400


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True)