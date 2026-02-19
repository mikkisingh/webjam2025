
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, Index, UniqueConstraint
from datetime import datetime
from database import Base


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)


class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_type = Column(String)
    raw_text = Column(Text)
    structured_data = Column(Text)
    analysis_results = Column(Text)
    summary = Column(Text)
    status = Column(String, default="uploaded")
    total_amount = Column(Float)


class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True, index=True)
    cpt_code = Column(String(10), nullable=False, index=True)
    modifier = Column(String(5), default="")
    description = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False, index=True)

    # Pricing (backward-compatible fields)
    medicare_rate = Column(Float)       # = non_fac_fee
    typical_low = Column(Float)
    typical_high = Column(Float)

    # RVU breakdown from CMS PFS
    work_rvu = Column(Float)
    non_fac_pe_rvu = Column(Float)
    fac_pe_rvu = Column(Float)
    mp_rvu = Column(Float)
    total_non_fac_rvu = Column(Float)
    total_fac_rvu = Column(Float)
    non_fac_fee = Column(Float)
    fac_fee = Column(Float)
    conversion_factor = Column(Float)
    global_period = Column(String(5))

    # Source metadata
    source = Column(String(50), default="manual_seed")
    source_year = Column(Integer)

    notes = Column(Text)

    __table_args__ = (
        UniqueConstraint("cpt_code", "modifier", name="uq_procedure_code_mod"),
    )


class HcpcsCode(Base):
    __tablename__ = "hcpcs_codes"

    id = Column(Integer, primary_key=True, index=True)
    hcpcs_code = Column(String(10), unique=True, nullable=False, index=True)
    short_desc = Column(String(300))
    long_desc = Column(Text)
    add_date = Column(String(20))
    term_date = Column(String(20))
    category = Column(String(100), index=True)
    source = Column(String(50), default="nlm_hcpcs")
    source_year = Column(Integer)


class Icd10Procedure(Base):
    __tablename__ = "icd10_procedures"

    id = Column(Integer, primary_key=True, index=True)
    icd10_code = Column(String(10), unique=True, nullable=False, index=True)
    short_desc = Column(String(100))
    long_desc = Column(Text)
    order_num = Column(Integer)
    is_billable = Column(Boolean, default=True, index=True)
    source = Column(String(50), default="cms_icd10_pcs")
    source_year = Column(Integer)


class MedicareUtilization(Base):
    __tablename__ = "medicare_utilization"

    id = Column(Integer, primary_key=True, index=True)
    hcpcs_code = Column(String(10), nullable=False, index=True)
    place_of_service = Column(String(1), default="O")

    total_providers = Column(Integer)
    total_services = Column(Integer)
    total_beneficiaries = Column(Integer)
    avg_submitted_charge = Column(Float)
    avg_allowed_amount = Column(Float)
    avg_medicare_payment = Column(Float)
    p25_submitted_charge = Column(Float)
    p75_submitted_charge = Column(Float)
    p25_allowed_amount = Column(Float)
    p75_allowed_amount = Column(Float)

    source = Column(String(50), default="cms_utilization")
    source_year = Column(Integer)

    __table_args__ = (
        Index("ix_util_hcpcs_pos", "hcpcs_code", "place_of_service", unique=True),
    )


class DataSyncLog(Base):
    __tablename__ = "data_sync_log"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")
    records_processed = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    source_hash = Column(String(64), nullable=True)
