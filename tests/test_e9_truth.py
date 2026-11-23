"""Synthetic tests of the DOOM-E9 truth builder (measure/e9_truth.py). No predictor, no real corpus data."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e9_truth", ROOT / "measure" / "e9_truth.py")
assert spec is not None and spec.loader is not None
T = importlib.util.module_from_spec(spec)
sys.modules["e9_truth"] = T
spec.loader.exec_module(T)

TOY_C = """#include <stdio.h>

static int add(int a,
               int b)
{
    return a + b;
}

int main(void) { printf("hi"); return 0; }

struct s { int x; };

void
long_one(void)
{
    int i;
    for (i = 0; i < 3; i++)
        puts("x");
}
"""

BODY = """int %s(int a, int b)
{
    int total = 0;
    /* a comment */
    for (int i = 0; i < a; i++) {
        total += table[i] * b;   // inline comment
        if (total > LIMIT) {
            log_message("overflow %%d", total);
            break;
        }
    }
    return total;
}
"""


def test_ctags_boundaries_on_toy_c(tmp_path):
    (tmp_path / "toy.c").write_text(TOY_C)
    got = {name: (s, e) for path, name, s, e in T.ctags_dir(tmp_path)}
    assert got["add"] == (3, 7)  # multi-line signature starts at the name line, ends at the closing brace
    assert got["main"] == (9, 9)
    assert got["long_one"] == (14, 19)
    assert "s" not in got  # the struct is not a function
    assert [n for _, n, _, _ in T.ctags_dir(tmp_path)] == ["add", "main", "long_one"]  # ordered by start line


def test_load_functions_eligibility_and_tokens(tmp_path):
    (tmp_path / "toy.c").write_text(TOY_C)
    fs = {f.name: f for f in T.load_functions(tmp_path)}
    assert fs["add"].loc == 5 and fs["add"].toks is None  # loc < 6: not eligible
    assert fs["long_one"].loc == 6 and fs["long_one"].toks
    assert fs["long_one"].toks[0] == "@"  # the own name (first token) is masked
    allf = {f.name: f for f in T.load_functions(tmp_path, all_tokens=True)}
    assert allf["add"].toks is not None


def test_shingles_and_jaccard():
    a = T.tokenize_body(BODY % "alpha", "a.c", "alpha")
    b = T.tokenize_body(BODY % "beta", "b.c", "beta")
    assert a == b  # name masked, comments stripped
    assert T.body_hash(a) == T.body_hash(b)
    sa, sb = T.shingle_array(a), T.shingle_array(b)
    assert T.jaccard(sa, sb) == 1.0
    other = T.shingle_array(T.tokenize_body("void q(void){ while(1) { sleep(2); } }", "c.c", "q"))
    assert T.jaccard(sa, other) < 0.1
    assert T.jaccard(sa, np.zeros(0, np.uint64)) == 0.0
    c = list(a)
    c[10] = "CHANGED"
    assert 0.5 < T.jaccard(sa, T.shingle_array(c)) < 1.0
    # a body shorter than 4 tokens is one shingle
    assert len(T.shingle_array(["a", "b"])) == 1


def test_identifier_normalisation_renamed_variant():
    orig = BODY % "alpha"
    renamed = (BODY % "gamma").replace("total", "sum").replace("table", "tbl").replace("LIMIT", "MAXV")
    renamed = renamed.replace("log_message", "emit")
    p_a = T.shingle_array(T.tokenize_body(orig, "a.c", "alpha"))
    p_b = T.shingle_array(T.tokenize_body(renamed, "b.c", "gamma"))
    i_a = T.shingle_array(T.idnorm_tokens(orig, "a.c"))
    i_b = T.shingle_array(T.idnorm_tokens(renamed, "b.c"))
    assert T.jaccard(p_a, p_b) < 0.6  # the plain text no longer agrees
    assert T.jaccard(i_a, i_b) == 1.0  # the identifier-normalised variant does
    toks = T.idnorm_tokens('int f(void) { return g("hello world", 42); }', "a.c")
    assert "ID" in toks and '"hello world"' in toks and "42" in toks and "int" in toks and "return" in toks
    assert "f" not in toks and "g" not in toks


def test_lsh_recall_on_synthetic_near_copies():
    r = T.synthetic_lsh_recall(n_base=400, seed=11)
    assert r["j06_07"]["n"] > 100 and r["j07_09"]["n"] > 100 and r["j09_up"]["n"] > 50
    assert r["j06_07"]["miss_rate"] <= 0.03  # theory: 1.2% at exactly 0.6
    assert r["j07_09"]["miss_rate"] <= 0.005
    assert r["j09_up"]["miss_rate"] == 0.0
    # the banding keeps unrelated sets apart: random functions produce almost no candidate pairs
    rng = np.random.default_rng(3)
    sh = [T.shingle_array([f"w{k}" for k in rng.integers(0, 5000, 80)]) for _ in range(300)]
    lo, hi, big = T.lsh_pairs(T.signatures(sh))
    assert len(lo) <= 5 and big == 0


def test_vertical_mask_logic():
    names = ["linuxdoom", "boomX", "chocolate-doom", "crispy-doom", "other"]
    programs = {
        "linuxdoom": dict(clade="own"), "boomX": dict(clade="boom-mbf"), "chocolate-doom": dict(clade="chocolate"),
        "crispy-doom": dict(clade="chocolate"), "other": dict(clade="own"),
    }  # fmt: skip
    anc = {p: T.ancestors_of(p, programs) for p in names}
    assert anc["linuxdoom"] == [] and anc["crispy-doom"] == ["linuxdoom", "chocolate-doom"]
    assert anc["boomX"][:1] == ["linuxdoom"] and "boom-2.02" in anc["boomX"] and "winmbf" in anc["boomX"]
    # (prog, func) pairs: crispy f3 ~ linuxdoom f0 at 0.95; crispy f4 ~ chocolate f9 at 0.7; other f1 ~ crispy f2 at 0.99
    v = T.vertical_from_pairs(anc, [3, 3, 4], [3, 4, 1], [0, 2, 3], [0, 9, 2], [0.95, 0.7, 0.99], names)
    assert v[("crispy-doom", 3)] == ("linuxdoom", 0.95)
    assert v[("crispy-doom", 4)] == ("chocolate-doom", 0.7)
    assert ("linuxdoom", 0) not in v and ("chocolate-doom", 9) not in v  # ancestors are not vertical themselves
    assert ("other", 1) not in v and ("crispy-doom", 2) not in v  # not an ancestor relation
    below = T.vertical_from_pairs(anc, [3], [3], [0], [0], [0.59], names)
    assert below == {}


PROGRAMS = {
    "a": dict(language_group="c_family", clade="own"), "b": dict(language_group="c_family", clade="own"),
    "c1": dict(language_group="c_family", clade="chocolate"), "c2": dict(language_group="c_family", clade="chocolate"),
    "z": dict(language_group="c_family", clade="zdoom"), "r": dict(language_group="cross_language", clade="own"),
}  # fmt: skip


def test_eligibility_rules():
    shared = {frozenset(("a", "z"))}
    f = lambda x, y: T.pair_ineligible_reason(x, y, PROGRAMS, shared)  # noqa: E731
    assert f("a", "b") == ""  # two 'own' programs are different clades
    assert f("c1", "c2") == "co-clade"
    assert f("a", "c1") == ""
    assert f("a", "z") == "shared-commit"
    assert f("a", "r") == "cross-language"
    assert f("c1", "r") == "cross-language"
    assert T.stratum_of(".c", ".h") == "c-c" and T.stratum_of(".c", ".cpp") == "c-cpp"
    assert T.stratum_of(".cc", ".hpp") == "cpp-cpp" and T.stratum_of(".c", ".py") == "c-other"


LIBS = [dict(library="zlib", directory_pattern="zlib"), dict(library="lua", directory_pattern="lua|blua"),
        dict(library="libpng", directory_pattern="libpng*"), dict(library="opl", directory_pattern="opl")]  # fmt: skip
T3 = [
    dict(module="textscreen", donor="don", borrower="b1", borrower_path="source/textscreen", type="port-to-port (cross-clade)", evidence=""),
    dict(module="textscreen", donor="don", borrower="b2", borrower_path="libs/textscreen", type="port-to-port (cross-clade)", evidence=""),
    dict(module="textscreen", donor="don", borrower="cc", borrower_path="textscreen", type="co-clade (vertical)", evidence=""),
    dict(module="opl", donor="don", borrower="b1", borrower_path="opl", type="port-to-port or co-clade per clade table", evidence=""),
]  # fmt: skip


def test_classification_rules():
    R = T.Rules(LIBS, T3)
    ann = R.annotate
    # directed port-to-port, either argument order
    c = R.classify("b1", ann("b1", "source/textscreen/x.c"), "don", ann("don", "textscreen/x.c"))
    assert c["pair_class"] == "port-to-port" and c["donor"] == "don" and c["recipient"] == "b1"
    assert c["module"] == "textscreen" and c["module_cluster"] == "source/textscreen"
    c = R.classify("don", ann("don", "textscreen/x.c"), "x", ann("x", "src/y.c"))
    assert c["pair_class"] == "coincidence" and c["donor"] == ""
    # co-borrowing: both borrowers of the same module from the same donor
    c = R.classify("b1", ann("b1", "source/textscreen/x.c"), "b2", ann("b2", "libs/textscreen/x.c"))
    assert c["pair_class"] == "co-borrowing" and c["donor"] == "don" and c["recipient"] == "b1+b2"
    assert T.event_id(c["donor"], c["recipient"], c["module_cluster"]) == "don|b1+b2|textscreen"
    # a co-clade T3 borrower is not eligible
    c = R.classify("b1", ann("b1", "source/textscreen/x.c"), "cc", ann("cc", "textscreen/x.c"))
    assert c["pair_class"] == "co-clade"
    # but the donor of a module that also has co-clade rows is NOT marked co-clade
    c = R.classify("b1", ann("b1", "source/textscreen/x.c"), "don", ann("don", "textscreen/y.c"))
    assert c["pair_class"] == "port-to-port"
    # external library by directory pattern (case-insensitive, globs, alternatives), either side
    assert R.external_lib("third/ZLIB/inflate.c") == "zlib" and R.external_lib("a/blua/x.c") == "lua"
    assert R.external_lib("a/libpng-1.6/x.c") == "libpng" and R.external_lib("a/zlibrary.c") == ""
    assert R.external_lib("zlib_notes/x.c") == ""  # the file name itself is not a directory
    c = R.classify("p", ann("p", "src/zlib/x.c"), "q", ann("q", "lib/y.c"))
    assert c["pair_class"] == "external-library" and c["module"] == "zlib"
    # T3 takes precedence over the external-library list (opl is in both)
    c = R.classify("b1", ann("b1", "opl/z.c"), "don", ann("don", "opl/z.c"))
    assert c["pair_class"] == "port-to-port" and c["module"] == "opl"
    c = R.classify("x", ann("x", "opl/z.c"), "y", ann("y", "opl/z.c"))
    assert c["pair_class"] == "external-library"
    c = R.classify("p", ann("p", "src/a.c"), "q", ann("q", "src/b.c"))
    assert c["pair_class"] == "coincidence" and c["module_cluster"] == "src|src"
    # lineage collapse
    assert T.lineage_of("crispy-doom", "inter-doom") == "chocolate-family|chocolate-family"
    assert T.lineage_of("nugget-doom", "eternity") == "eternity|woof-family"


def test_left_censoring_rule():
    day = 86400
    root = 1_000_000_000
    assert T.censor_reason(root + 3 * day, root, 1, 100) == "root-14d"
    assert T.censor_reason(root + 14 * day, root, 1, 100) == "root-14d"
    assert T.censor_reason(root + 15 * day, root, 10, 100) == ""
    assert T.censor_reason(root + 400 * day, root, 51, 100) == "squash-import"
    assert T.censor_reason(root + 400 * day, root, 50, 100) == ""  # more than 50%, not 50%


def test_dedup_representatives():
    hashes = ["h1", "h2", "h1", "", "h2", "h3", "h1"]
    elig = [True, True, True, False, True, True, True]
    rep = T.dedup_reps(hashes, elig)
    assert rep.tolist() == [0, 1, 0, -1, 1, 5, 0]
    assert rep[3] == -1


def test_build_events_and_family_collapse():
    def p(a, b, fa, fb, j, ji, cls, donor, rec, cl, mod):
        return dict(prog_a=a, prog_b=b, func_a=fa, func_b=fb, jaccard=j, jaccard_idnorm=ji, pair_class=cls,
                    eligible_primary=1, donor=donor, recipient=rec, module_cluster=cl, module=mod,
                    event_id=T.event_id(donor, rec, cl))  # fmt: skip
    pairs = [p("don", "b1", 1, 1, 0.95, 0.95, "port-to-port", "don", "b1", "d", "m"),
             p("don", "b1", 2, 2, 1.0, 1.0, "port-to-port", "don", "b1", "d", "m"),
             p("don", "b1", 3, 3, 0.7, 0.95, "port-to-port", "don", "b1", "d", "m")]  # fmt: skip
    t1 = T.build_events(pairs, "t1")
    assert len(t1) == 1 and t1[0]["n_functions"] == 2 and t1[0]["n_pairs"] == 2
    assert T.build_events(pairs, "j06")[0]["n_functions"] == 3
    assert T.build_events(pairs, "idnorm")[0]["n_functions"] == 3


def _git(cwd, *args, date=None):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")  # fmt: skip
    if date:
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    return subprocess.run(["git", "-C", str(cwd), *args], env=env, capture_output=True, text=True, check=True).stdout


def _fn(name, k, extra=""):
    return (f"int {name}(int a, int b)\n{{\n    int t = {k};\n    for (int i = 0; i < a; i++) {{\n"
            f"        t += table_{name}[i] * b + {k};\n        if (t > limit_{k}) {{\n            report(t);\n"
            f"        }}\n    }}\n{extra}    return t;\n}}\n\n")  # fmt: skip


def test_t2_first_appearance_on_synthetic_history(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    foo, bar = _fn("foo", 7), _fn("bar", 11)
    (repo / "a.c").write_text(foo)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "root", date="2010-01-01T12:00:00+0000")
    # filler commits so the later introduction is not a squash import
    for i in range(3):
        (repo / f"f{i}.txt").write_text("x" * (i + 1))
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", f"f{i}", date=f"2012-0{i + 1}-01T12:00:00+0000")
    (repo / "a.c").write_text(foo + bar)  # bar introduced here
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "add bar", date="2015-05-05T12:00:00+0000")
    (repo / "a.c").write_text(foo + _fn("bar", 11, extra="    t++;\n"))  # small edit to bar
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "edit bar", date="2016-06-06T12:00:00+0000")
    _git(repo, "mv", "a.c", "b.c")  # rename the file
    _git(repo, "commit", "-qm", "rename", date="2017-07-07T12:00:00+0000")
    sha = _git(repo, "rev-parse", "HEAD").strip()
    root_ct = T.first_parent_root(repo, sha)
    assert root_ct == 1262347200
    final = T.load_functions(repo)
    by = {f.name: f for f in final}
    tasks = dict(program="synthetic", gd=str(repo), sha=sha, path="b.c", cpp_h=False, root_ct=root_ct,
                 targets=[(i, T.shingle_array(by[n].toks), by[n].loc) for i, n in enumerate(["foo", "bar"])])  # fmt: skip
    rows = {r["func_id"]: r for r in T.t2_for_file(tasks)}
    foo_row, bar_row = rows[0], rows[1]
    assert foo_row["first_date_committer"].startswith("2010-01-01") and foo_row["censored"] == 1
    assert foo_row["reason"] == "root-14d"
    assert bar_row["first_date_committer"].startswith("2015-05-05")  # the post-copy edit and the rename do not move it
    assert bar_row["censored"] == 0 and bar_row["reason"] == ""
    assert bar_row["first_commit"] == _git(repo, "log", "--format=%H", "--grep=add bar").strip()
    # file_versions follows the rename
    vs = T.file_versions(repo, sha, "b.c")
    assert [v["path"] for v in vs] == ["b.c", "a.c", "a.c", "a.c"]  # path AT each commit, newest first
    # a squash import (commit adding most of the repository's files) is censored
    big = tmp_path / "big"
    big.mkdir()
    _git(big, "init", "-q", "-b", "main")
    (big / "keep.txt").write_text("k")
    _git(big, "add", "-A")
    _git(big, "commit", "-qm", "first", date="2010-01-01T12:00:00+0000")
    for i in range(6):
        (big / f"m{i}.c").write_text(_fn(f"fn{i}", i))
    _git(big, "add", "-A")
    _git(big, "commit", "-qm", "import", date="2014-01-01T12:00:00+0000")
    sha2 = _git(big, "rev-parse", "HEAD").strip()
    f0 = {f.name: f for f in T.load_functions(big)}["fn0"]
    t = dict(program="big", gd=str(big), sha=sha2, path="m0.c", cpp_h=False, root_ct=T.first_parent_root(big, sha2),
             targets=[(0, T.shingle_array(f0.toks), f0.loc)])  # fmt: skip
    r = T.t2_for_file(t)[0]
    assert r["censored"] == 1 and r["reason"] == "squash-import"


@pytest.mark.skipif(not (T.WORK / "repos" / "chocolate-doom").is_dir(), reason="corpus not available")
def test_reproduction_of_the_e7_arbiter_shares():
    r = T.reproduce_arbiter()
    assert abs(r["share_exact_near"] - 0.43) <= 0.03
    assert abs(r["share_exact_near_derived"] - 0.66) <= 0.03
