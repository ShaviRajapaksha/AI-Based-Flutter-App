import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import Session
from datetime import date
from db import Base, engine, get_db
from models import FinancialEntry
from categorizer import guess_type
from ocr import extract_text
from parser import parse_ocr_text

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize DB
Base.metadata.create_all(bind=engine)

def to_dict(entry: FinancialEntry):
    return {
        "id": entry.id,
        "entry_type": entry.entry_type,
        "category": entry.category,
        "amount": entry.amount,
        "currency": entry.currency,
        "vendor": entry.vendor,
        "reference": entry.reference,
        "notes": entry.notes,
        "entry_date": entry.entry_date.isoformat(),
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        "source": entry.source,
        "raw_text": entry.raw_text,
    }

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/categories")
def categories():
    return {
        "entry_types": ["SAVINGS", "EXPENSES", "INVESTMENTS", "DEBT"],
        "suggested_categories": [
            "Groceries", "Transport", "Utilities", "Rent", "Dining", "Medical",
            "Education", "Entertainment", "Salary", "Interest", "Stocks", "Loans",
        ],
    }

@app.post("/api/ocr/upload")
def ocr_upload():
    if "file" not in request.files:
        return {"error": "No file provided"}, 400
    f = request.files["file"]
    path = os.path.join(UPLOAD_DIR, f.filename)
    f.save(path)

    raw_text = extract_text(path)
    parsed = parse_ocr_text(raw_text)
    # guess type
    gtype = guess_type(parsed.get("vendor"), parsed.get("raw_text"), None)
    parsed["entry_type"] = gtype
    parsed["source"] = "ocr"

    return parsed

@app.get("/api/entries")
def list_entries():
    db: Session = next(get_db())
    q = db.query(FinancialEntry)

    entry_type = request.args.get("entry_type")
    if entry_type:
        q = q.filter(FinancialEntry.entry_type == entry_type)

    # date range
    start = request.args.get("start")
    end = request.args.get("end")
    if start:
        q = q.filter(FinancialEntry.entry_date >= start)
    if end:
        q = q.filter(FinancialEntry.entry_date <= end)

    items = [to_dict(e) for e in q.order_by(FinancialEntry.entry_date.desc()).all()]
    return {"items": items}

@app.post("/api/entries")
def create_entry():
    db: Session = next(get_db())
    data = request.get_json()
    try:
        entry = FinancialEntry(
            entry_type=data["entry_type"],
            category=data.get("category"),
            amount=float(data["amount"]),
            currency=data.get("currency", "LKR"),
            vendor=data.get("vendor"),
            reference=data.get("reference"),
            notes=data.get("notes"),
            entry_date=date.fromisoformat(data["entry_date"]),
            source=data.get("source", "manual"),
            raw_text=data.get("raw_text"),
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return to_dict(entry), 201
    except Exception as e:
        db.rollback()
        return {"error": str(e)}, 400

@app.get("/api/entries/<int:entry_id>")
def get_entry(entry_id):
    db: Session = next(get_db())
    entry = db.get(FinancialEntry, entry_id)
    if not entry:
        return {"error": "Not found"}, 404
    return to_dict(entry)

@app.put("/api/entries/<int:entry_id>")
def update_entry(entry_id):
    db: Session = next(get_db())
    entry = db.get(FinancialEntry, entry_id)
    if not entry:
        return {"error": "Not found"}, 404
    data = request.get_json()
    try:
        for field in ["entry_type", "category", "currency", "vendor", "reference", "notes", "raw_text", "source"]:
            if field in data:
                setattr(entry, field, data[field])
        if "amount" in data:
            entry.amount = float(data["amount"]) if data["amount"] is not None else None
        if "entry_date" in data and data["entry_date"]:
            entry.entry_date = date.fromisoformat(data["entry_date"])
        db.commit()
        db.refresh(entry)
        return to_dict(entry)
    except Exception as e:
        db.rollback()
        return {"error": str(e)}, 400

@app.delete("/api/entries/<int:entry_id>")
def delete_entry(entry_id):
    db: Session = next(get_db())
    entry = db.get(FinancialEntry, entry_id)
    if not entry:
        return {"error": "Not found"}, 404
    db.delete(entry)
    db.commit()
    return {"status": "deleted"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)