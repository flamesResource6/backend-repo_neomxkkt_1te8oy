import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Database helpers
from database import db, create_document, get_documents

# Schemas
from schemas import Member, Payment, Donation

app = FastAPI(title="IC Lug Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "service": "backend"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response

# ————— Business Endpoints —————

# Create a member
@app.post("/members")
def create_member(member: Member):
    member_id = create_document("member", member)
    return {"id": member_id}

# List members
@app.get("/members")
def list_members():
    members = get_documents("member")
    # Normalize id
    for m in members:
        m["id"] = str(m.pop("_id", ""))
    return members

# Add a payment
@app.post("/payments")
def add_payment(payment: Payment):
    # Basic value normalization
    if payment.paid_at is None:
        payment.paid_at = datetime.utcnow()
    pay_id = create_document("payment", payment)
    return {"id": pay_id}

# List payments
@app.get("/payments")
def list_payments(member_id: Optional[str] = None, year: Optional[int] = None):
    filt = {}
    if member_id:
        filt["member_id"] = member_id
    if year:
        filt["year"] = year
    payments = get_documents("payment", filt)
    for p in payments:
        p["id"] = str(p.pop("_id", ""))
    return payments

# Donations
@app.post("/donations")
def add_donation(donation: Donation):
    if donation.donated_at is None:
        donation.donated_at = datetime.utcnow()
    don_id = create_document("donation", donation)
    return {"id": don_id}

@app.get("/donations")
def list_donations():
    docs = get_documents("donation")
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
    return docs

# Aggregate: Matrix for a given year like the provided Google Sheet
@app.get("/stats/matrix")
def stats_matrix(year: int):
    """
    Returns: list of rows like
    {
      full_name: "Hamza Konicanin",
      months: [10, 0, 0, ..., 0],
      total: 10,
    }
    """
    members = get_documents("member")
    pay = get_documents("payment", {"year": year})

    # Index payments by member and month
    by_key = {}
    for p in pay:
        mid = p.get("member_id")
        mth = int(p.get("month"))
        amt = float(p.get("amount", 0))
        key = (mid, mth)
        by_key[key] = by_key.get(key, 0) + amt

    rows = []
    for m in members:
        mid = str(m.get("_id"))
        months = [0.0]*12
        for i in range(1, 13):
            months[i-1] = float(by_key.get((mid, i), 0))
        total = round(sum(months), 2)
        rows.append({
            "id": mid,
            "full_name": m.get("full_name"),
            "months": months,
            "total": total,
        })

    # Sort by name
    rows.sort(key=lambda r: (r["full_name"] or ""))
    return rows

# Simple yearly totals for dashboard
@app.get("/stats/summary")
def stats_summary(year: int):
    members_count = len(get_documents("member"))
    pay = get_documents("payment", {"year": year})
    total_year = sum(float(p.get("amount", 0)) for p in pay)
    donations_total = sum(float(d.get("amount", 0)) for d in get_documents("donation"))
    return {
        "members": members_count,
        "payments_year": round(total_year, 2),
        "donations_total": round(donations_total, 2)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
