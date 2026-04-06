from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json, os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_FILE = "database.json"

# ── JSON HELPERS ──────────────────────────────────────
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)
# ─────────────────────────────────────────────────────


# Serve frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')


# Health check
@app.route('/health', methods=['GET'])
def health_check():
    try:
        data = load_db()
        return jsonify({
            'status': 'healthy',
            'message': 'Using JSON database',
            'record_count': len(data)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Get all mappings
@app.route('/all', methods=['GET'])
def get_all():
    try:
        return jsonify(load_db())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🔍 SEARCH (UPDATED → works for both fields)
@app.route('/search', methods=['GET'])
def search():
    term = request.args.get('q', '').strip().lower()

    if not term:
        return jsonify([])

    data = load_db()

    filtered = [
        r for r in data
        if term in r["supplier_id"].lower()
        or term in r["part_number"].lower()
    ]

    return jsonify(filtered)


# ➕ ADD MAPPING
@app.route('/add', methods=['POST'])
def add_mapping():
    data = request.get_json()

    sid = data.get('supplier_id', '').strip()
    pn = data.get('part_number', '').strip()

    if not sid or not pn:
        return jsonify({'error': 'Both fields required'}), 400

    db = load_db()

    # duplicate check
    if any(r["supplier_id"] == sid and r["part_number"] == pn for r in db):
        return jsonify({'error': 'Already exists'}), 409

    db.append({
        "supplier_id": sid,
        "part_number": pn
    })

    save_db(db)

    return jsonify({'success': True}), 201


# ❌ DELETE
@app.route('/delete/<supplier_id>/<part_number>', methods=['DELETE'])
def delete_mapping(supplier_id, part_number):
    db = load_db()

    new_db = [
        r for r in db
        if not (r["supplier_id"] == supplier_id and r["part_number"] == part_number)
    ]

    if len(new_db) == len(db):
        return jsonify({'error': 'Not found'}), 404

    save_db(new_db)

    return jsonify({'success': True})


# 📊 STATS
@app.route('/stats', methods=['GET'])
def stats():
    db = load_db()

    return jsonify({
        'total_records': len(db),
        'unique_suppliers': len(set(r["supplier_id"] for r in db)),
        'database_type': 'JSON'
    })


# ── RUN ───────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 50)
    print(" PARTMAPPER (JSON MODE)")
    print("=" * 50)
    print(" Open: http://localhost:5000")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)