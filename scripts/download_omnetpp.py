# -*- coding: utf-8 -*-
"""分段、可续传地下载 OMNeT++ 6.4.0 Windows 包，并校验 SHA256。"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

URL = ("https://ghproxy.net/https://github.com/omnetpp/omnetpp/releases/"
       "download/omnetpp-6.4.0/omnetpp-6.4.0-windows-x86_64.7z")
TOTAL = 1_209_918_370
SHA256 = "3c0957fe466332bcf441f132ac0fe102986c96699f50fee03abbcafbdc4504ab"
PARTS = 6
OUT = Path(r"D:\download\omnetpp-6.4.0")
CHUNK = 256 * 1024
RETRIES = 40


def fmt(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MB"


def download_part(i: int, start: int, end: int) -> None:
    path = OUT / f"part{i:02d}.bin"
    need = end - start + 1
    for attempt in range(1, RETRIES + 1):
        have = path.stat().st_size if path.exists() else 0
        if have >= need:
            print(f"[part{i}] done {fmt(have)}", flush=True)
            return
        if have > need:
            path.unlink()
            have = 0
        headers = {
            "Range": f"bytes={start + have}-{end}",
            "Accept-Encoding": "identity",
            "User-Agent": "Mozilla/5.0 omnetpp-course-downloader",
        }
        try:
            with requests.get(URL, headers=headers, stream=True,
                              timeout=(20, 90)) as r:
                if r.status_code != 206:
                    raise RuntimeError(f"HTTP {r.status_code}")
                cr = r.headers.get("Content-Range", "")
                if not cr.startswith(f"bytes {start + have}-"):
                    raise RuntimeError(f"bad Content-Range: {cr!r}")
                with open(path, "ab") as f:
                    for chunk in r.iter_content(CHUNK):
                        if not chunk:
                            continue
                        f.write(chunk)
                        have += len(chunk)
                        if have >= need:
                            break
                    f.flush()
                    os.fsync(f.fileno())
            if have >= need:
                print(f"[part{i}] done {fmt(have)}", flush=True)
                return
            raise RuntimeError(f"short read {have}/{need}")
        except Exception as exc:  # noqa: BLE001
            wait = min(30, 2 * attempt)
            print(f"[part{i}] attempt {attempt} failed: {exc}; retry in {wait}s",
                  flush=True)
            time.sleep(wait)
    raise RuntimeError(f"part{i} failed after {RETRIES} attempts")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("part*.bin"):
        if old.stat().st_size == 0:
            old.unlink()
    chunk = (TOTAL + PARTS - 1) // PARTS
    ranges = []
    for i in range(PARTS):
        start = i * chunk
        end = min(start + chunk - 1, TOTAL - 1)
        ranges.append((i, start, end))
    print(f"total={fmt(TOTAL)} parts={PARTS} chunk={fmt(chunk)}", flush=True)
    started = time.time()
    try:
        with ThreadPoolExecutor(max_workers=PARTS) as pool:
            futures = [pool.submit(download_part, i, s, e) for i, s, e in ranges]
            while any(not f.done() for f in futures):
                done = sum(f.stat().st_size for f in OUT.glob("part*.bin"))
                pct = 100 * done / TOTAL
                speed = done / max(1, time.time() - started)
                print(f"progress {pct:5.1f}%  {fmt(done)}  {fmt(speed)}/s",
                      flush=True)
                time.sleep(10)
            for f in futures:
                f.result()
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {exc}", flush=True)
        return 1

    sizes = [p.stat().st_size for p in sorted(OUT.glob("part*.bin"))]
    if sum(sizes) != TOTAL:
        print(f"size mismatch: {sum(sizes)} != {TOTAL}; {sizes}", flush=True)
        return 2

    final = OUT / "omnetpp-6.4.0-windows-x86_64.7z"
    print("concatenating...", flush=True)
    with open(final, "wb") as out:
        for p in sorted(OUT.glob("part*.bin")):
            with open(p, "rb") as src:
                shutil.copyfileobj(src, out, 4 * 1024 * 1024)
    print("hashing...", flush=True)
    h = hashlib.sha256()
    with open(final, "rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    print(f"sha256={h.hexdigest()}", flush=True)
    if h.hexdigest() != SHA256:
        print("HASH MISMATCH", flush=True)
        return 3
    print("DOWNLOAD_OK", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
