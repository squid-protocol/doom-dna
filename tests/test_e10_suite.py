import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "measure"))
import e10_suite as s  # noqa: E402
import e9_spike as e9  # noqa: E402

TOY = '''/* header comment with "quote" */
#include <stdio.h>

static const char *msg = "not /* a comment */ here; // nor this";

int add(int a, int b)
{
    int c = a + b; /* sum */
    c++;
    return c;
}

static void
noop(void)
{
    puts("x;"); // trailing
    if (msg) {
        puts(msg);
    }
}

#if FOO
int dup(int x)
{
    return x;
}
#else
int dup(int x)
{
    return x + 1;
}
#endif
'''


def nfun(t):
    return len(e9.ctags_funcs_text(t))


def test_comment_rewrite_keeps_strings():
    out, n = s.edit_comment(TOY)
    assert n == 3
    assert '"not /* a comment */ here; // nor this"' in out
    assert '"x;"' in out and "header comment" not in out and "/* sum */" not in out
    assert "/* edited */" in out and "// edited" in out
    assert nfun(out) == nfun(TOY)


def test_blank_only_in_bodies_after_semicolon():
    out, n = s.edit_blank(TOY)
    lines = out.split("\n")
    # the global declaration ends with ';' but is outside any body: no blank after it
    j = lines.index(next(l for l in lines if l.startswith("static const char *msg")))
    assert lines[j + 1] == ""  # original blank line only
    assert lines[j + 2] == "int add(int a, int b)"
    k = lines.index("    int c = a + b; /* sum */")
    assert lines[k + 1] == "" and lines[k + 2] == "    c++;" and lines[k + 3] == ""
    k = lines.index('    puts("x;"); // trailing')
    assert lines[k + 1] == ""
    assert lines[lines.index("    if (msg) {") + 1] == "        puts(msg);"  # `{` line not a semicolon line
    assert n == 4 and nfun(out) == nfun(TOY)
    # no blank inserted after '#include' or function signature lines
    assert lines[lines.index("int add(int a, int b)") + 1] == "{"


def _first_stmt(out, name_line_prefix):
    lines = out.split("\n")
    i = next(i for i, l in enumerate(lines) if l.startswith(name_line_prefix))
    while "{" not in lines[i]:
        i += 1
    return lines[i], lines[i + 1]


def test_insertions_after_open_brace():
    for fn, snip in ((s.edit_kw, "if (0) { }"), (s.edit_stmt, "(void)0;"), (s.edit_decl, "int e10_unused;")):
        out, n = fn(TOY)
        assert n == 4  # add, noop, and both #if variants of dup
        assert out.count(snip) == 4
        assert _first_stmt(out, "int add") == ("{", snip)
        assert _first_stmt(out, "noop")[1] == snip
        assert nfun(out) == nfun(TOY) == 4


def test_format_and_combos_preserve_count():
    for v in s.VARIANTS:
        out, c = s.apply_variant(v, TOY)
        assert nfun(out) == nfun(TOY), v
    out, _ = s.apply_variant("E_verbatim", TOY)
    assert out == TOY
    out, c = s.apply_variant("E_combo2", TOY)
    assert c["comments"] == 3 and c["defs_edited"] == 4 and "if (0) { }" in out
    out, _ = s.apply_variant("E_format", TOY)
    assert "\n{\n" in out and "    int c = a + b;" in out


def test_suite_table_keys():
    assert {"donors", "recipient", "clang_config", "variants", "work", "prefix"} <= set(s.SUITES["dev"])
