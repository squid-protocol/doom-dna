"""Evaluation population for the A1 ungrouped-rate gate: the simulation-scope functions of chocolate-doom, managed-doom and prboom-plus, taken from the
E15 usable lists (tests.usable over the E15 screen stores, verbatim) ONLY as instance ids.  No phenotype value is returned or stored.
Used by audit_v1.py after the groups are built; the group build never imports this module."""
import collections, os, sys
from pathlib import Path
import build_behaviour as BB
import common as C

def eval_scope_ids(static_path):
    """returns {port: {'usable': set(inst_id), 'screened': set(inst_id)}} (ids only)"""
    roles, tests = BB.import_e15()
    S = BB._real_connect(f"file:{static_path}?mode=ro", uri=True)
    out = {}
    for store, port in BB.STORES:
        dbp = BB.SCREEN / f"{store}_phenotypes.sqlite"
        P = roles.load_port(port, dbp); ph = roles.phenotype(P); us = tests.usable(ph)
        idx = collections.defaultdict(list)
        for iid, name, file, line in S.execute("select i.inst_id, i.name, i.file, i.line from instance i join port p using(port_id) where p.name=?", (port,)):
            idx[(os.path.splitext(os.path.basename(file))[0].lower(), name)].append((iid, line))
        st = BB._real_connect(f"file:{dbp}?mode=ro", uri=True); fmap = {}
        for fid, f, n, l in st.execute("select fid, file, name, line from functions"):
            c = idx.get((f.lower(), n), [])
            if len(c) > 1: c = [x for x in c if x[1] == l]
            if len(c) == 1: fmap[fid] = c[0][0]
        st.close()
        out[port] = dict(usable={fmap[int(f)] for f, u in zip(ph.fids, us) if u and int(f) in fmap}, screened={fmap[int(f)] for f in ph.fids if int(f) in fmap})
    S.close()
    return out
