"""Java grammar configuration for the mutant-schemata instrumenter (schemata.py is not edited: this module registers 'java' into schemata.LANGS and reuses schemata.instrument()).
Usage: import schemata_java  (after `import schemata`), then schemata.instrument(src_bytes, "java", id_base, fn_base, drop, id2_base).
Same 15 lesion kinds and id scheme as C and C#. Java specifics:
  * only `method_declaration` with a block body counts as a function (constructors, static initialisers and field initialisers are not instrumented; lambdas and anonymous classes inside a method belong to it);
  * condition parents: if / while / do / for / ternary_expression; unary `!` is unary_expression; ++/-- is update_expression;
  * integer constants are decimal_integer_literal that are plain digits (long `5L`, hex, octal and `1_000` forms are not lesioned);
  * array index expressions, array-dimension expressions, switch labels and annotations are never lesioned (index lesions are excluded in the registration);
  * the runtime class is e13.E13Mut (fully qualified so no import is needed in any instrumented file)."""
import schemata


class J:
    NOV2 = False
    COND_PARENTS = {"if_statement", "while_statement", "do_statement", "for_statement", "ternary_expression"}
    UNARY = {"unary_expression"}
    UPDATE = {"update_expression"}
    ON = "e13.E13Mut.On(%d)"
    ENTER = "e13.E13Mut.Enter(%d);"
    FUNC = ("method_declaration",)
    BIN = "binary_expression"
    NUM = "decimal_integer_literal"
    BODY = "block"
    NOMUT_NODES = {"switch_label", "dimensions_expr", "annotation", "marker_annotation", "annotation_argument_list", "element_value_pair"}
    NOMUT_FIELDS = {("array_access", "index")}

    @staticmethod
    def fname(n):
        d = n.child_by_field_name("name")
        return d.text.decode("latin-1") if d is not None else "?"


schemata.LANGS["java"] = J


# --- statement-position ++/-- --------------------------------------------------------------------------------------------------------------
# schemata.py renders an incdec lesion as the ternary `(On(id) ? (x--) : (x++))`. Java only accepts statement expressions (call, assignment, ++/--) as a statement or a
# for-update, so `(c ? x-- : x++);` does not compile. In those two positions the value is unused, so `x++` is identical to `x += 1`: the lesion becomes
# `x += (On(id) ? -1 : 1)`, which is the same byte edit (++ -> --) in effect (the classical rebuild patches the operator).
import re

_orig_emit = schemata.Engine.emit
_HEAD = re.compile(r"\(e13\.E13Mut\.On\((\d+)\) \? ")


def _balanced(s, i):
    """index just after the parenthesis group that opens at s[i]"""
    depth = 0
    while i < len(s):
        ch = s[i]
        if ch in "\"'":
            q = ch; i += 1
            while i < len(s) and s[i] != q: i += 2 if s[i] == "\\" else 1
        elif ch == "(": depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0: return i + 1
        i += 1
    raise ValueError("unbalanced")


def _split_tern(out):
    """`(e13.E13Mut.On(id) ? (S) : (O))` -> (id, S, O) or None"""
    m = _HEAD.match(out)
    if not m: return None
    i = m.end(); j = _balanced(out, i)
    if out[j:j + 3] != " : ": return None
    k = _balanced(out, j + 3)
    if k != len(out) - 1 or out[k] != ")": return None
    return m.group(1), out[i + 1:j - 1], out[j + 4:k - 1]


def _stmt_position(n):
    p = n.parent
    if p is None:
        return False
    if p.type == "expression_statement":
        return True
    if p.type == "for_statement":
        for i, c in enumerate(p.children):
            if c.id == n.id:
                return p.field_name_for_child(i) == "update"
    return False


def _emit(self, n, const=False, infn=False):
    out = _orig_emit(self, n, const, infn)
    if n.type == "update_expression" and isinstance(self.cfg, type) and issubclass(self.cfg, J) and infn and not const and out.startswith("(e13.E13Mut.On(") and _stmt_position(n):
        m = _split_tern(out)
        if m:
            mid, swapped, orig = m
            op = "++" if orig.count("++") == 1 and "--" not in orig else "--"
            operand = orig.replace(op, "", 1).strip()
            d_orig, d_new = ("1", "-1") if op == "++" else ("-1", "1")
            return "%s += (e13.E13Mut.On(%s) ? %s : %s)" % (operand, mid, d_new, d_orig)
    return out


schemata.Engine.emit = _emit
