"""Tests for the name-blind arbiter (measure/e7_arbiter.py)."""

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "measure"))

import e7_arbiter as A  # noqa: E402
from e7_names import name_key  # noqa: E402

BASE = """
void P_MoveThing(mobj_t *mo, int dx, int dy)
{
    int i;
    /* comment that must not count */
    for (i = 0; i < mo->count; i++) {
        if (mo->flags[i] & MF_SOLID) {
            mo->x += dx * FRACUNIT;
            mo->y += dy * FRACUNIT;
        } else {
            mo->momx = mo->momx / 2;
            mo->momy = mo->momy / 2;
        }
        P_CheckPosition(mo, mo->x, mo->y);
    }
    mo->floorz = mo->subsector->sector->floorheight;
}
"""


def fn(src, name):
    return A.Func("x.c", name, 1, A.tokenize_body(src, "x.c", name))


def test_renamed_edited_found_name_blind():
    ref = [fn(BASE, "P_MoveThing")]
    edited = BASE.replace("P_MoveThing", "Actor_Shift").replace("mo->momx / 2", "mo->momx / 4").replace(
        "int i;", "int i; int unused;")
    port = [fn("int other(int a) { return a * a + 3; }\n\n\n", "other"), fn(edited, "Actor_Shift")]
    r = A.match(ref, port)[0]
    assert r["verdict"] in ("near", "derived")
    assert r["j"] == 1
    # same-name-only logic (lineage.py) has no candidate: the names differ
    assert name_key("P_MoveThing") != name_key("Actor_Shift")
    rows = A.run_port(ref, port)
    assert rows[0]["name_survives"] == 0 and rows[0]["verdict"] != "gone"


def test_unrelated_is_gone():
    other = """
    static int checksum(const unsigned char *buf, size_t n)
    {
        unsigned h = 5381;
        while (n--) { h = ((h << 5) + h) ^ *buf++; }
        return (int)(h & 0x7fffffff);
    }
    """
    assert A.match([fn(BASE, "P_MoveThing")], [fn(other, "checksum")])[0]["verdict"] == "gone"


def test_identical_different_name_is_exact():
    renamed = BASE.replace("P_MoveThing", "Totally_Different")
    r = A.match([fn(BASE, "P_MoveThing")], [fn("int z(void){return 0;}", "z"), fn(renamed, "Totally_Different")])[0]
    assert r["verdict"] == "exact" and r["sim"] == 1.0 and r["j"] == 1


def test_summary_shares():
    ref = [fn(BASE, "P_MoveThing")]
    rows = A.run_port(ref, [fn(BASE, "P_MoveThing")])
    s = A.summarise("p", rows)
    assert s["exact"] == 1 and s["share_exact_near"] == 1.0 and s["name_survivors"] == 1


def test_eligible_set_matches_sfs_filter():
    db = A.scan_db(Path("/srv/storage_16tb/projects/doom-e7-work"), "704cb35f0", "linuxdoom")
    if db is None:
        pytest.skip("linuxdoom scan not present")
    scan = A.load_scan_data(db)
    expect = [i for i in range(scan.n_functions) if scan.loc[i] >= 6 and scan.func_name[i] != "__global_context__"]
    assert int(A.eligible_mask(scan).sum()) == len(expect) > 0
    funcs = A.build_funcs(scan, Path("/srv/storage_16tb/projects/doom-e7-work/repos/linuxdoom"), db,
                          list(A.np.flatnonzero(A.eligible_mask(scan))))
    assert len(funcs) == len(expect)
