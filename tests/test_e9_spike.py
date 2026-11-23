"""Synthetic fast tests for the E9 spike-in builder (no donor repositories, no scans, no predictors)."""

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "measure"))

import e9_spike as S  # noqa: E402

SRC_A = r'''#include <stdio.h>
/* helper: foo_bar calls foo */
static int foo(int x)
{
    // foo is the base
    return x + 1;
}

int foo_bar(int y)
{
    const char *s = "foo // not a comment /* nor this */";
    char c = '"';
    return foo(y) + foo(2) + (int)c + (int)s[0]; /* trailing foo */
}

void use_member(struct st *p)
{
    p->foo = 1;
    p->foo_bar = foo(3);
    q.foo = 2;
}

int prefoo(int z)
{
    return foo(z) * 2 + prefoo_count;
}

int last_fn(void)
{
    return foo_bar(1) + prefoo(2) + foo(4) + 1;
}
'''
SRC_B = '''int other(int a)
{
    return a + 1 + 2 + 3 + 4 + 5;
}

int caller_b(int a)
{
    return other(a) + 1 + 2 + 3 + 4;
}
'''


def defs_of(files):
    d = {}
    for rel, tx in files.items():
        fs = S.ctags_funcs_text(tx)
        for f in fs:
            f["span"] = f["end"] - f["line"] + 1
            f["eligible"] = int(f["span"] >= 6)
        d[rel] = fs
    return d


def test_formatter_pinned():
    assert S.CLANG_VERSION in S.check_formatter()
    assert "BasedOnStyle: LLVM" in S.CF_CONFIG.read_text()


def test_ctags_finds_definitions_not_prototypes():
    fs = S.ctags_funcs_text("int p(int);\nint q(int a)\n{\n return a;\n}\n")
    assert [f["name"] for f in fs] == ["q"]


def test_new_name_scheme_and_determinism():
    n = S.new_name("foo")
    assert re.fullmatch(r"s9_[0-9a-f]{8}", n)
    assert n == S.new_name("foo") != S.new_name("foo_bar")
    import hashlib
    assert n == "s9_" + hashlib.sha1(b"20261122foo").hexdigest()[:8]


def test_rename_definitions_calls_word_boundaries():
    m = {"foo": "s9_aaaaaaaa", "foo_bar": "s9_bbbbbbbb"}
    out = S.rename_text(SRC_A, m)
    assert "static int s9_aaaaaaaa(int x)" in out
    assert "int s9_bbbbbbbb(int y)" in out
    assert "return s9_aaaaaaaa(y) + s9_aaaaaaaa(2)" in out
    # no substring damage
    assert "prefoo" in out and "prefoo_count" in out and "s9_aaaaaaaaprefoo" not in out
    assert "s9_bbbbbbbb(1)" in out
    # strings untouched, struct members untouched
    assert '"foo // not a comment /* nor this */"' in out
    assert "p->foo = 1;" in out and "p->foo_bar = s9_aaaaaaaa(3);" in out and "q.foo = 2;" in out
    # function count unchanged and exactly one definition per new name
    fs = [f["name"] for f in S.ctags_funcs_text(out)]
    assert fs.count("s9_aaaaaaaa") == 1 and "foo" not in fs
    assert len(fs) == len(S.ctags_funcs_text(SRC_A))
    assert not S.old_name_in_code(out, "foo") and not S.old_name_in_code(out, "foo_bar")


def test_rename_plan_apply_and_determinism():
    files = {"a.c": SRC_A, "b.c": SRC_B}
    defs = defs_of(files)
    plan = S.build_rename_plan(defs)
    plan2 = S.build_rename_plan(defs_of(files))
    assert plan["keymap"] == plan2["keymap"]
    assert len(set(plan["keymap"].values())) == len(plan["keymap"])
    out1 = S.apply_rename(files, plan, set(plan["keymap"]))
    out2 = S.apply_rename(files, plan, set(plan["keymap"]))
    assert out1 == out2
    for rel, tx in out1.items():
        assert len(S.ctags_funcs_text(tx)) == len(defs[rel])


def test_duplicate_definition_names_across_files_are_file_local():
    f1 = "static int dup(int a)\n{\n return a;\n}\nint u1(void)\n{\n return dup(1);\n}\n"
    f2 = "static int dup(int a)\n{\n return a + 2;\n}\nint u2(void)\n{\n return dup(2);\n}\n"
    files = {"x/1.c": f1, "x/2.c": f2}
    defs = defs_of(files)
    plan = S.build_rename_plan(defs)
    assert "dup@x/1.c" in plan["keymap"] and "dup@x/2.c" in plan["keymap"]
    out = S.apply_rename(files, plan, set(plan["keymap"]))
    n1, n2 = plan["keymap"]["dup@x/1.c"], plan["keymap"]["dup@x/2.c"]
    assert n1 != n2
    assert n1 in out["x/1.c"] and n2 not in out["x/1.c"]
    assert n2 in out["x/2.c"] and n1 not in out["x/2.c"]


def test_subset_deterministic_half():
    keys = [f"k{i}" for i in range(10)]
    a = S.subset_keys(keys, "b50", 0.5)
    assert len(a) == 5 and a == S.subset_keys(list(reversed(keys)), "b50", 0.5)


def test_comment_stripper_keeps_strings():
    src = 'char *a = "//x /* y */ z"; /* c1 */ int b; // tail\nchar c = \'"\'; /* "q" */ char *d = "a\\"/*b*/";\n'
    out = S.strip_comments(src)
    assert '"//x /* y */ z"' in out and '"a\\"/*b*/"' in out and "'\"'" in out
    assert "c1" not in out and "tail" not in out and '"q"' not in out
    assert "int b;" in out
    # line comment continued with backslash-newline is removed whole
    assert "gone" not in S.strip_comments("int a; // x \\\ngone\nint b;\n")
    # unterminated apostrophe in a preprocessor line does not swallow code
    assert "int z" in S.strip_comments("#error don't\nint z; /* c */\n")


def test_mask_same_length():
    t = 'a("x/*y*/"); /* c\nd */ b;'
    m = S.mask(t)
    assert len(m) == len(t) and m.count("\n") == t.count("\n") and "x" not in m and "c" not in m.replace("a", "")


def test_tier_c_formats_and_keeps_function_count():
    src = S.rename_text(SRC_A, {"foo": "s9_aaaaaaaa"})
    c = S.clang_format(S.strip_comments(src))
    assert "helper" not in c and "trailing" not in c and "not a comment" in c
    assert len(S.ctags_funcs_text(c)) == len(S.ctags_funcs_text(SRC_A))
    assert S.clang_format(c) == c  # idempotent under the pinned config


def test_void0_and_reorder_keep_function_count():
    c = S.clang_format(S.strip_comments(SRC_A))
    n = len(S.ctags_funcs_text(c))
    v = S.clang_format(S.insert_void0(c))
    assert v.count("(void)0;") == n
    assert len(S.ctags_funcs_text(v)) == n
    # (void)0; is the first statement of every body
    for f in S.ctags_funcs_text(v):
        lines = v.split("\n")
        i = f["line"] - 1
        while "{" not in lines[i]:
            i += 1
        assert lines[i + 1].strip() == "(void)0;"
    r = S.reorder_functions(v, "a.c")
    assert len(S.ctags_funcs_text(r)) == n
    assert sorted(f["name"] for f in S.ctags_funcs_text(r)) == sorted(f["name"] for f in S.ctags_funcs_text(v))
    assert [f["name"] for f in S.ctags_funcs_text(r)] != [f["name"] for f in S.ctags_funcs_text(v)]
    assert r == S.reorder_functions(v, "a.c")  # deterministic
    assert sorted(l for l in r.split("\n") if l.strip()) == sorted(l for l in v.split("\n") if l.strip())


def test_partial_module_subset_and_valid_calls():
    files = {"a.c": SRC_A, "b.c": SRC_B}
    new, kept = S.partial_module(files, 0.3)
    n_tot = sum(len(S.ctags_funcs_text(t)) for t in files.values())
    assert len(kept) == round(0.3 * n_tot)
    assert sum(len(S.ctags_funcs_text(t)) for t in new.values()) == len(kept)
    assert (new, kept) == S.partial_module(files, 0.3)
    # every removed function still referenced by remaining text keeps a prototype; unreferenced ones are gone
    kept_names = {n for _, n, _ in kept}
    allnames = {f["name"] for t in files.values() for f in S.ctags_funcs_text(t)}
    for rel, tx in new.items():
        m = S.mask(tx)
        used = {m[s:e] for k, s, e in S.tokens(m) if k == "id"}
        protos = set(re.findall(r"^[^\n(]*?\b(\w+)\s*\([^)]*\)\s*;", m, re.M))
        for name in (used & allnames) - kept_names:
            assert name in protos or name in {f["name"] for f in S.ctags_funcs_text(tx)}


def test_partial_module_contiguous_block():
    src = "".join(f"int f{i}(int a)\n{{\n return a + {i};\n}}\n\n" for i in range(10))
    new, kept = S.partial_module({"z.c": src}, 0.3)
    idx = sorted(int(n[1:]) for _, n, _ in kept)
    assert len(idx) == 3 and idx == list(range(idx[0], idx[0] + 3))


def test_truth_rows_and_mapping_file(tmp_path, monkeypatch):
    mod = dict(donor="curl", files=["a.c", "b.c"], texts={"a.c": SRC_A, "b.c": SRC_B}, defs=defs_of({"a.c": SRC_A, "b.c": SRC_B}))
    tiers = S.make_tiers(mod)
    rows = S.truth_rows(mod, tiers)
    n = sum(len(v) for v in mod["defs"].values())
    assert len(rows) == n * len(S.TIERS)
    by = {}
    for r in rows:
        by.setdefault(r["tier"], []).append(r)
    assert all(r["renamed_func"] == r["orig_func"] for r in by["a"])
    assert all(re.fullmatch(r"s9_[0-9a-f]{8}", r["renamed_func"]) for r in by["b100"] + by["c"] + by["d"])
    n50 = sum(r["renamed_func"] != r["orig_func"] for r in by["b50"])
    assert n50 == n // 2
    assert sum(r["kept"] for r in by["e"]) == len(tiers["e"]["kept"])
    # exact: every renamed definition exists once in its tier text, no original name left
    for tier in ("b50", "b100", "c", "d"):
        for r in by[tier]:
            names = [f["name"] for f in S.ctags_funcs_text(tiers[tier]["files"][r["donor_file"]])]
            assert names.count(r["renamed_func"]) == 1
    assert all(r["recipient_file"] == f"spike/curl/{r['donor_file']}" and r["module_size"] == "large" for r in rows)
    # csv round trip with the specified columns
    monkeypatch.setattr(S, "S9", tmp_path)
    p = S.write_truth(rows)
    got = list(csv.DictReader(open(p)))
    assert len(got) == len(rows)
    for col in ["tier", "module_size", "donor", "orig_func", "renamed_func", "donor_file", "recipient_file", "kept",
                "recipient_engine_row"]:
        assert col in got[0]


def test_program_names():
    assert S.program_name("curl", "c") == "chocolate-spike-curl-c"
    assert S.program_name("libuv", "b50") == "chocolate-spike-libuv-b50"
