"""
Database Schemas for Islamski Centar u Lugu app

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

# Members who pay monthly fees
class Member(BaseModel):
    full_name: str = Field(..., description="Ime i prezime člana")
    phone: Optional[str] = Field(None, description="Telefon")
    email: Optional[str] = Field(None, description="Email")
    active: bool = Field(True, description="Da li je član aktivan")

# Individual payment record
class Payment(BaseModel):
    member_id: str = Field(..., description="ID člana (referenca)")
    year: int = Field(..., ge=2000, le=2100, description="Godina uplate")
    month: int = Field(..., ge=1, le=12, description="Mesec (1-12)")
    amount: float = Field(..., ge=0, description="Iznos")
    currency: Literal["EUR", "RSD"] = Field("EUR", description="Valuta")
    note: Optional[str] = Field(None, description="Napomena")
    paid_at: Optional[datetime] = Field(None, description="Datum uplate")

# Donations not tied to monthly fee
class Donation(BaseModel):
    name: str = Field(..., description="Naziv donacije/Donator")
    amount: float = Field(..., ge=0, description="Iznos")
    currency: Literal["EUR", "RSD"] = Field("EUR", description="Valuta")
    purpose: Optional[str] = Field(None, description="Svrha")
    donated_at: Optional[datetime] = Field(None, description="Datum donacije")

# Utility response models (optional)
class MemberWithTotals(BaseModel):
    id: str
    full_name: str
    totals_by_month: List[float]
    total: float
