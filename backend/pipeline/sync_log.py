"""Helpers for reading/writing the data_sync_log table."""

from datetime import datetime, timedelta
from models import DataSyncLog


def get_last_sync(db, source_name: str):
    """Return the most recent sync log entry for a source, or None."""
    return (
        db.query(DataSyncLog)
        .filter_by(source_name=source_name)
        .order_by(DataSyncLog.started_at.desc())
        .first()
    )


def is_sync_current(db, source_name: str, max_age_days: int = 30) -> bool:
    """True if the last successful sync is within max_age_days."""
    last = get_last_sync(db, source_name)
    if not last or last.status != "completed":
        return False
    if not last.completed_at:
        return False
    return (datetime.utcnow() - last.completed_at) < timedelta(days=max_age_days)


def is_hash_current(db, source_name: str, file_hash: str) -> bool:
    """True if the last successful sync used the same file hash."""
    last = get_last_sync(db, source_name)
    return (
        last is not None
        and last.status == "completed"
        and last.source_hash == file_hash
    )


def start_sync(db, source_name: str, source_url: str = None) -> DataSyncLog:
    """Create a new sync log entry with status 'running'."""
    entry = DataSyncLog(
        source_name=source_name,
        source_url=source_url,
        started_at=datetime.utcnow(),
        status="running",
    )
    db.add(entry)
    db.commit()
    return entry


def complete_sync(db, entry: DataSyncLog, records_processed: int,
                  records_inserted: int = 0, records_updated: int = 0,
                  source_hash: str = None):
    """Mark a sync as completed."""
    entry.completed_at = datetime.utcnow()
    entry.status = "completed"
    entry.records_processed = records_processed
    entry.records_inserted = records_inserted
    entry.records_updated = records_updated
    if source_hash:
        entry.source_hash = source_hash
    db.commit()


def fail_sync(db, entry: DataSyncLog, error_message: str):
    """Mark a sync as failed."""
    entry.completed_at = datetime.utcnow()
    entry.status = "failed"
    entry.error_message = error_message
    db.commit()
