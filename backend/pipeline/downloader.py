"""Shared utilities for downloading and extracting CMS data files."""

import os
import hashlib
import zipfile
import requests
from .config import PIPELINE_DIR, DOWNLOAD_TIMEOUT


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def compute_file_hash(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_file(url: str, dest_dir: str = None, filename: str = None) -> str:
    """Download a file from url. Returns the local file path."""
    dest_dir = dest_dir or ensure_dir(PIPELINE_DIR)
    ensure_dir(dest_dir)

    if not filename:
        filename = url.rsplit("/", 1)[-1]
    filepath = os.path.join(dest_dir, filename)

    print(f"  Downloading {url} ...")
    resp = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded * 100 // total
                print(f"\r  Downloaded {downloaded // 1024}KB / {total // 1024}KB ({pct}%)", end="", flush=True)
    print()  # newline after progress

    return filepath


def extract_zip(zip_path: str, dest_dir: str = None) -> list:
    """Extract a ZIP file. Returns list of extracted file paths."""
    dest_dir = dest_dir or os.path.dirname(zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
        extracted = [os.path.join(dest_dir, name) for name in zf.namelist()]
        print(f"  Extracted {len(extracted)} files from {os.path.basename(zip_path)}")
        return extracted


def download_and_extract(url: str, dest_dir: str = None) -> list:
    """Download a ZIP file and extract it. Returns list of extracted paths."""
    zip_path = download_file(url, dest_dir)
    extracted = extract_zip(zip_path, dest_dir)
    return extracted
