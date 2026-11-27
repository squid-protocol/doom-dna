"""DoomGraph v0 shared definitions: paths, tier weights, schema DDL for the two database files, small helpers.
Registered spec: preregistration/E18_DOOMGRAPH.md (section 'v2' governs) and doomgraph/SCHEMA.md."""
import hashlib, json, re, subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORK = Path("/srv/storage_16tb/projects/doom-e7-work")
OUTDIR = WORK / "doomgraph"
STATIC_DB = OUTDIR / "doomgraph_static.sqlite"
BEHAV_DB = OUTDIR / "doomgraph_behaviour.sqlite"
SCAN_ROOT = WORK / "scans" / "704cb35f0"
GENE_VIEW = WORK / "gene-view"
WT = Path("/srv/storage_16tb/projects/doom-dna-worktrees")
SCHEMA_VERSION = "1"
GROUP_VERSION = "g1"
MIN_LOC_SCAN = 3     # the E12 table (fid space) keeps functions of >= 3 lines
MIN_LOC_EDGE = 6     # the E12 universe (edges are used only when both ends have >= 6 lines)
ANCHOR = "linuxdoom"
SWAP_ANCHOR = "chocolate-doom"
REF_ENGINES = ("linuxdoom", "chocolate-doom", "doomgeneric", "prboom-plus", "woof")
CONTROL_PORTS = ("lua", "quake", "quake2", "nginx", "curl", "leveldb", "libuv")   # unrelated programs: instances kept, never grouped
TIERS = ("F0", "F1c", "S", "ext1", "ext2", "ext3")                              # strongest first (E18 v2)
TIER_W = {"F0": 100, "F1c": 80, "S": 60, "ext1": 40, "ext2": 30, "ext3": 20}
NAME_W = 25          # name-agree channel: a separate evidence channel (weight between ext2 and ext3)
ARB_W = {"exact": 90, "near": 70, "derived": 35}   # text arbiter: confirmation weight only (never creates membership alone)
MIN_JOIN = 15        # minimum score for an instance to join a group (frozen with the build)
ARB_BONUS = 10       # text-arbiter confirmation adds this to a supported candidate
MAX_CAND_ROWS = 5
HOP2_FACTOR = 0.5    # a 2-hop chain weighs half of the weaker of its two edges
CONFLICT_MARGIN = 0.8
TEXT_LIMIT = 200     # ingest allowlist: no text column may exceed this

PREFIX = re.compile(r"^(EV_|P_|A_|T_|PIT_|PTR_)")   # verbatim from demo/harness/mscreen/diagnosis/prep.py
GENERIC = {"add", "remove", "get", "set", "update", "run", "start", "stop", "init", "clear", "reset", "check", "free", "alloc"}   # same file

def strip_name(n):
    return PREFIX.sub("", n or "")

def sha256_file(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()

def sha1_short(s):
    return hashlib.sha1(s.encode()).hexdigest()[:16]

def git_info(path=REPO):
    def g(*a):
        return subprocess.run(["git", "-C", str(path), *a], capture_output=True, text=True).stdout.strip()
    return dict(code_commit=g("rev-parse", "HEAD"), code_branch=g("rev-parse", "--abbrev-ref", "HEAD"),
                code_dirty=str(bool(g("status", "--porcelain", "--", "doomgraph", "preregistration/E18_DOOMGRAPH.md"))))

def jdump(d):
    return json.dumps(d, separators=(",", ":"), sort_keys=True)

STATIC_DDL = """
CREATE TABLE build_manifest(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE port(port_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, language TEXT, kind TEXT NOT NULL,
  scan_path TEXT NOT NULL, scan_commit TEXT, scan_engine TEXT NOT NULL, scan_db_sha256 TEXT NOT NULL, inst_digest TEXT NOT NULL,
  n_scanned INTEGER, n_instances INTEGER, source TEXT NOT NULL, build_id TEXT NOT NULL);
CREATE TABLE instance(inst_id INTEGER PRIMARY KEY, port_id INTEGER NOT NULL REFERENCES port(port_id), fid INTEGER NOT NULL,
  instance_key TEXT NOT NULL, name TEXT NOT NULL, file TEXT NOT NULL, line INTEGER, size INTEGER, args INTEGER, complexity INTEGER,
  lang_kind TEXT, source TEXT NOT NULL, build_id TEXT NOT NULL, UNIQUE(port_id, fid));
CREATE INDEX instance_key_ix ON instance(instance_key);
CREATE INDEX instance_name_ix ON instance(port_id, name);
CREATE TABLE match_edge(edge_id INTEGER PRIMARY KEY, a_inst INTEGER NOT NULL REFERENCES instance(inst_id), b_inst INTEGER NOT NULL REFERENCES instance(inst_id),
  tier TEXT NOT NULL, score REAL, source TEXT NOT NULL, pair_file TEXT, gate_passed INTEGER, verdict TEXT, evidence_hash TEXT, build_id TEXT NOT NULL,
  CHECK(a_inst < b_inst), UNIQUE(a_inst, b_inst, tier, source));
CREATE INDEX match_edge_a ON match_edge(a_inst); CREATE INDEX match_edge_b ON match_edge(b_inst);
CREATE TABLE call_edge(edge_id INTEGER PRIMARY KEY, caller_inst INTEGER NOT NULL REFERENCES instance(inst_id), callee_inst INTEGER NOT NULL REFERENCES instance(inst_id),
  kind TEXT NOT NULL, source TEXT NOT NULL, build_id TEXT NOT NULL, UNIQUE(caller_inst, callee_inst, kind, source));
CREATE TABLE lineage_edge(edge_id INTEGER PRIMARY KEY, port TEXT NOT NULL, parent TEXT NOT NULL, parent_kind TEXT NOT NULL, basis TEXT NOT NULL,
  role TEXT, shared_struct REAL, shared_names REAL, rank_struct INTEGER, source TEXT NOT NULL, source_commit TEXT, build_id TEXT NOT NULL);
CREATE TABLE subsystem(inst_id INTEGER PRIMARY KEY REFERENCES instance(inst_id), subsystem_id INTEGER NOT NULL, basis TEXT NOT NULL, source TEXT NOT NULL, build_id TEXT NOT NULL);
CREATE TABLE ortholog_group(group_id INTEGER PRIMARY KEY, build_scope TEXT NOT NULL, anchor_inst INTEGER NOT NULL REFERENCES instance(inst_id),
  method TEXT NOT NULL, version TEXT NOT NULL, n_members INTEGER, n_ports INTEGER, build_id TEXT NOT NULL, UNIQUE(build_scope, anchor_inst));
CREATE TABLE membership(inst_id INTEGER NOT NULL REFERENCES instance(inst_id), group_id INTEGER NOT NULL REFERENCES ortholog_group(group_id),
  build_scope TEXT NOT NULL, rank INTEGER NOT NULL, role TEXT NOT NULL, confidence REAL, evidence TEXT NOT NULL, build_id TEXT NOT NULL,
  PRIMARY KEY(inst_id, group_id), CHECK(role IN ('anchor','member','split','merge','conflict')));
CREATE INDEX membership_group ON membership(group_id);
CREATE TABLE ungrouped(inst_id INTEGER NOT NULL REFERENCES instance(inst_id), build_scope TEXT NOT NULL, reason TEXT NOT NULL, build_id TEXT NOT NULL, PRIMARY KEY(inst_id, build_scope));
CREATE TABLE layer_availability(port TEXT NOT NULL, layer TEXT NOT NULL, n_instances INTEGER NOT NULL, PRIMARY KEY(port, layer));
"""

BEHAV_DDL = """
CREATE TABLE build_manifest(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE demo(demo_id TEXT PRIMARY KEY, store TEXT NOT NULL, iwad TEXT NOT NULL, family TEXT NOT NULL, demo_set TEXT NOT NULL, source TEXT NOT NULL);
CREATE TABLE demo_reach(port TEXT NOT NULL, inst_id INTEGER NOT NULL, instance_key TEXT NOT NULL, demo TEXT NOT NULL, entries INTEGER, first_tic INTEGER,
  source TEXT NOT NULL, build_id TEXT NOT NULL, PRIMARY KEY(port, inst_id, demo));
CREATE TABLE phenotype(port TEXT NOT NULL, inst_id INTEGER NOT NULL, instance_key TEXT NOT NULL, hot INTEGER NOT NULL, inert INTEGER NOT NULL, usable INTEGER NOT NULL,
  eligible INTEGER NOT NULL, nobs INTEGER NOT NULL, median_log_tic REAL, class_player REAL, class_world REAL, class_sector REAL, class_keys REAL, class_time REAL,
  e15_commit TEXT NOT NULL, demo_set_id TEXT NOT NULL, source TEXT NOT NULL, build_id TEXT NOT NULL, PRIMARY KEY(port, inst_id));
CREATE TABLE phenotype_demo(port TEXT NOT NULL, inst_id INTEGER NOT NULL, demo TEXT NOT NULL, kill_fraction REAL NOT NULL, PRIMARY KEY(port, inst_id, demo));
CREATE TABLE conformance(port TEXT NOT NULL, demo TEXT NOT NULL, variant TEXT NOT NULL, status TEXT NOT NULL, first_tic INTEGER, field TEXT, source TEXT NOT NULL, build_id TEXT NOT NULL,
  PRIMARY KEY(port, demo, variant, source));
CREATE TABLE behaviour_confirmed(a_inst INTEGER, b_inst INTEGER, d REAL, d_threshold REAL, call_profile_identical INTEGER, formula_version TEXT, build_id TEXT);
CREATE TABLE sfs_confidence(a_inst INTEGER, b_inst INTEGER, tier TEXT, score REAL, formula_version TEXT, build_id TEXT);
CREATE TABLE holdout_fold(fold_id INTEGER, task TEXT, seed INTEGER, edge_a INTEGER, edge_b INTEGER, stratum TEXT, hidden INTEGER, build_id TEXT);
CREATE TABLE layer_availability(port TEXT NOT NULL, layer TEXT NOT NULL, n_instances INTEGER NOT NULL, PRIMARY KEY(port, layer));
"""

# ---- v1 (E18 amendment A1): multi-anchor consensus
STATIC_V1_DB = OUTDIR / "doomgraph_static_v1.sqlite"
GROUP_VERSION_V1 = "g2"
V1_ANCHORS = REF_ENGINES                                    # joint anchors of the primary v1 run
V1_SWAPS = {"v1_swap:ldgw": ("linuxdoom", "doomgeneric", "woof"),          # pre-fixed anchor-swap runs (A1 gate a): the references
            "v1_swap:cpw": ("chocolate-doom", "prboom-plus", "woof")}      # without / with the two test-port-like engines
