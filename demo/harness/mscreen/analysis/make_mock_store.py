"""Dry-run helper: copy a screen store's structure (lesions, functions, coverage tables) into a mock store whose OUTCOMES are synthetic (planted role groups by a hash of the function name), so the whole
analysis can be exercised on the real shape of the data without reading any real lesion outcome. Usage: python make_mock_store.py <src.sqlite> <dst.sqlite> [seed]"""
import sqlite3, sys, zlib
import numpy as np
src, dst = sys.argv[1], sys.argv[2]; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
a = sqlite3.connect(f"file:{src}?mode=ro", uri=True); b = sqlite3.connect(dst); a.backup(b); a.close()
b.execute("delete from results"); rng = np.random.default_rng(seed); demos = sorted(r[0] for r in b.execute("select distinct demo from sitereach")); di = {d: i for i, d in enumerate(demos)}
K = 12; cent = rng.beta(0.4, 0.5, size=(K, len(demos))); lesions = {r[0]: (r[1], r[2]) for r in b.execute("select id, fn, fid from lesions")}; rows = []
for les, d in b.execute("select lesion, demo from sitereach"):
    if les not in lesions: continue
    fn, fid = lesions[les]; g = zlib.crc32(fn.encode()) % K; hot = zlib.crc32(("h" + fn).encode()) % 40 == 0; dead = zlib.crc32(("i" + fn).encode()) % 4 == 0
    p = 0.97 if hot else (0.0 if dead else float(np.clip(cent[g][di[d]] + 0.15 * np.sin(zlib.crc32((fn + d).encode()) % 100), 0, 1)))
    killed = rng.random() < p; mask = (sum(1 << c for c in ([4, 5] if g % 3 == 0 else ([15, 16] if g % 3 == 1 else [17]))) | 4) if killed else None
    rows.append((les, d, "killed" if killed else "same", int(np.exp(rng.normal(3 + 0.2 * (g % 5), 0.5))) if killed else None, mask, 0, 1))
b.executemany("insert or replace into results values(?,?,?,?,?,?,?)", rows); b.commit(); print(dst, len(rows), "synthetic results")
