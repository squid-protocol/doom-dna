"""DOOM-E12 blind audit sample (registered: 40 randomly drawn emitted pairs per translation, rung and name-key verdict hidden).
Draws from the E3c list at N=250 (loc>=6 universe), seed 12; writes results/e12/audit/<program>_pairs.md (for raters) and <program>_key.csv (answer key, not shown to raters).
Note: function bodies necessarily contain the functions' own names; only the rung and the name-key verdict are hidden."""
import sys, json, sqlite3, csv, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import e12_ladder as L
REPOS = Path("/srv/storage_16tb/projects/doom-e7-work/repos"); OUT = L.OUT / "audit"; OUT.mkdir(exist_ok=True)
def starts(prog):
    c = sqlite3.connect(f"file:{L.SC / prog}/{prog}_galaxy_master.db?mode=ro", uri=True)
    q = "select f.path, fd.func_name, fd.start_line, fd.loc from function_data fd join file_data f on f.id = fd.file_id"
    try: rows = c.execute(q).fetchall()
    except Exception: rows = c.execute("select file_path, func_name, start_line, loc from function_data fd join file_data f on f.id=fd.file_id").fetchall()
    d = {}
    for p, n, s, l in rows: d.setdefault((p, n), (s, l))
    return d
def body(prog, path, name, idx):
    s_l = idx.get((path, name))
    if not s_l: return "(source location not found)"
    f = REPOS / prog / path
    try: lines = f.read_text(errors="replace").splitlines()
    except Exception: return "(source file not readable)"
    s, l = s_l; return "\n".join(lines[max(s - 1, 0): s - 1 + min(int(l), 80)])
for prog in ["gore", "doom-scheme", "dartdoom", "mochadoom"]:
    lj = L.OUT / f"lists_{prog}.json"
    if not lj.exists(): print("missing", prog); continue
    tp, _, _ = L.tables(prog, "P"); tl, _, _ = L.tables("linuxdoom", "P"); idx_p, idx_l = starts(prog), starts("linuxdoom")
    lst = [(a, b) for a, b, _ in json.load(open(lj))["E3c"] if tp.loc[a] >= L.MIN_LOC and tl.loc[b] >= L.MIN_LOC][:250]
    rng = random.Random(12); pick = rng.sample(lst, min(40, len(lst))); key = []
    md = [f"# Blind audit sample: {prog} against linuxdoom\n\nFor each pair, judge whether function A (port) is a translation or close port of function B (linuxdoom): **same / similar-derived / different / cannot tell**. Judge from the code and what it does; ignore anything else you may infer.\n"]
    for k, (a, b) in enumerate(pick, 1):
        flip = rng.random() < 0.5; A = (tp, a, idx_p, prog); B = (tl, b, idx_l, "linuxdoom")
        md.append(f"\n## Pair {k}\n\n**Function X** ({'C' if flip else prog})\n```\n{body(*( (B[3], str(B[0].path[B[1]]), str(B[0].name[B[1]]), B[2]) if flip else (A[3], str(A[0].path[A[1]]), str(A[0].name[A[1]]), A[2]) ))}\n```\n**Function Y** ({prog if flip else 'C'})\n```\n{body(*( (A[3], str(A[0].path[A[1]]), str(A[0].name[A[1]]), A[2]) if flip else (B[3], str(B[0].path[B[1]]), str(B[0].name[B[1]]), B[2]) ))}\n```\n")
        nk = (L.N.name_key(str(tp.name[a])), L.N.name_key(str(tl.name[b]))); key.append(dict(pair=k, port_row=a, ref_row=b, x_is_linuxdoom=flip, port_name=str(tp.name[a]), ref_name=str(tl.name[b]), name_key_true=bool(nk[0] and nk[0] == nk[1] and nk[0] not in L.STOP)))
    (OUT / f"{prog}_pairs.md").write_text("\n".join(md)); csv.DictWriter(f_ := open(OUT / f"{prog}_key.csv", "w", newline=""), fieldnames=list(key[0])).writeheader(); csv.DictWriter(f_, fieldnames=list(key[0])).writerows(key); f_.close(); print(prog, len(pick))
