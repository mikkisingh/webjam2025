#!/usr/bin/env python3
"""
MediCheck CMS Data Pipeline — CLI entry point.

Usage:
  cd backend
  python3 -m pipeline.run_pipeline                     # sync all sources
  python3 -m pipeline.run_pipeline --source pfs        # only Medicare PFS
  python3 -m pipeline.run_pipeline --source hcpcs      # only HCPCS Level II
  python3 -m pipeline.run_pipeline --source icd10      # only ICD-10-PCS
  python3 -m pipeline.run_pipeline --source utilization # only utilization stats
  python3 -m pipeline.run_pipeline --source utilization --limit 100  # first 100 codes
  python3 -m pipeline.run_pipeline --force             # ignore idempotency checks
"""

import argparse
import sys
import os

# Ensure backend/ is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base, engine, SessionLocal
from pipeline import sync_pfs, sync_hcpcs, sync_icd10, sync_utilization, sync_all


def main():
    parser = argparse.ArgumentParser(
        description="MediCheck CMS Data Pipeline — download, parse, and store CMS medical data"
    )
    parser.add_argument(
        "--source",
        choices=["pfs", "hcpcs", "icd10", "utilization", "all"],
        default="all",
        help="Which data source to sync (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-sync even if data appears current",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of codes to process (utilization only)",
    )
    args = parser.parse_args()

    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if args.source == "all":
            sync_all(db, force=args.force)
        elif args.source == "pfs":
            sync_pfs(db, force=args.force)
        elif args.source == "hcpcs":
            sync_hcpcs(db, force=args.force)
        elif args.source == "icd10":
            sync_icd10(db, force=args.force)
        elif args.source == "utilization":
            sync_utilization(db, force=args.force, limit=args.limit)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Progress so far has been committed.")
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
