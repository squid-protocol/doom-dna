"""E15 graphs: G1 static call graph (scanner database), G2 state-table dispatch edges, G3 = G1 union G2, all restricted to the screened functions (induced subgraph)."""
import re, sys
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "difflocalize"))
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); CAP = 6
def norm(s): return s.lower().replace("_", "")
class Graph:
    """nodes = screened functions (fid -> normalised name); dist[i, j] in hops on G3 (7 = disconnected beyond the cap or unreachable)"""
    def __init__(self, fids, names, edges):
        self.fids = list(fids); self.names = [norm(n) for n in names]; node = {}
        for i, n in enumerate(self.names): node.setdefault(n, []).append(i)
        self.node = node; keys = list(node); ki = {k: i for i, k in enumerate(keys)}; rows, cols = [], []
        for a, b in edges:
            if a in ki and b in ki and a != b: rows += [ki[a], ki[b]]; cols += [ki[b], ki[a]]
        A = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(keys), len(keys))); A.data[:] = 1
        self.deg_node = np.asarray(A.sum(1)).ravel(); SP = shortest_path(A, unweighted=True, directed=False); SP[~np.isfinite(SP)] = CAP + 1; SP = np.minimum(SP, CAP + 1)
        idx = np.array([ki[n] for n in self.names]); self.D = SP[np.ix_(idx, idx)]; self.deg = self.deg_node[idx]
    def sub(self, fids):
        pos = {f: i for i, f in enumerate(self.fids)}; ix = np.array([pos[f] for f in fids]); return self.D[np.ix_(ix, ix)], self.deg[ix]
def g1_edges(scan_db):
    import locate
    g = locate.CallGraph(scan_db); e = set()
    for a, bs in g.callees.items():
        for b in bs: e.add((a, b))
    return e
def g2_chocolate():
    t = (W / "build/choc-mut-base/src/src/doom/info.c").read_text(errors="replace"); actions = set(re.findall(r"\b(A_\w+)\b", t)); weapon = {a for a in actions if a in WEAPON_ACTIONS}
    e = set()
    for a in actions: e.add((norm(a), norm("P_SetPsprite" if a in weapon else "P_SetMobjState")))
    return e
WEAPON_ACTIONS = {"A_Light0", "A_Light1", "A_Light2", "A_WeaponReady", "A_Lower", "A_Raise", "A_Punch", "A_ReFire", "A_FirePistol", "A_FireShotgun", "A_FireShotgun2", "A_FireCGun", "A_FireMissile", "A_FirePlasma", "A_FireBFG", "A_Saw", "A_GunFlash", "A_BFGsound", "A_CheckReload", "A_OpenShotgun2", "A_LoadShotgun2", "A_CloseShotgun2"}
def g2_managed():
    base = W / "build/managed-doom/src/Doom/Info"; e = set()
    for fn, disp in (("DoomInfo.MobjActions.cs", "SetState"), ("DoomInfo.PlayerActions.cs", "SetPlayerSprite")):
        t = (base / fn).read_text(errors="replace")
        for m in re.finditer(r"world\.(\w+)\.(\w+)\(", t): e.add((norm(m.group(2)), norm(disp)))
    return e
