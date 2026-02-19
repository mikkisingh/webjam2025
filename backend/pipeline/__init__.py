from .pfs_parser import sync_pfs_data as sync_pfs
from .hcpcs_parser import sync_hcpcs_data as sync_hcpcs
from .icd10_parser import sync_icd10_data as sync_icd10
from .utilization_parser import sync_utilization_data as sync_utilization


def sync_all(db, force=False):
    """Run all pipeline stages in order."""
    print("=== Stage 1/4: Medicare PFS RVU data ===")
    sync_pfs(db, force=force)

    print("\n=== Stage 2/4: HCPCS Level II codes ===")
    sync_hcpcs(db, force=force)

    print("\n=== Stage 3/4: ICD-10-PCS codes ===")
    sync_icd10(db, force=force)

    print("\n=== Stage 4/4: Medicare Utilization data ===")
    sync_utilization(db, force=force)

    print("\n=== Pipeline complete ===")
