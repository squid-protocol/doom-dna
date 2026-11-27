"""Go back end of the mutant-schemata instrumenter (registers 'go' into schemata.LANGS; schemata.py itself is not edited).
Use:  import schemata, schemata_go; schemata_go.configure(facts, select);  schemata.instrument(src, "go", id_base, fn_base, drop)  -> same 6-tuple as for C and C#.

Same 15 lesion kinds and ids as the C and C# builds (ids < 10000 original kinds: relational, equality, arithmetic, logical, shift, constant (+1); ids >= 10000: sdl, negate,
const_zero, const_dec, const_toggle, arith2, bitwise, not, incdec). The traversal, row format and id scheme are schemata.Engine's; only the emission is Go specific, because Go has
no ternary, no ++ as an expression, no implicit conversions and rejects unused variables:
  * every lesion is a call to a generic helper in e13mut.go (operands evaluated once, in order, only the chosen operation runs): relational/equality/arithmetic/bitwise/shift
    swaps are e13Lt/e13Eq/e13Add/e13Mul/e13And/e13Shl[...](id, L, R), constants e13K[T](id, new, old), x++ is x = e13Inc[T](id, x) (or an if/else for impure operands);
  * && / || use the lazy form (e13On(id) && (A || B) || e13Id != id && (A && B));
  * condition negation is ((C) != e13On(id)); deleting a logical not is ((X) == e13On(id)); statement deletion is { if !e13On(id) { stmt } };
  * explicit type arguments come from go/types (gotypes/main.go: the 'facts' JSON), so untyped constants keep the type their context gives them;
  * integer constants whose new value does not fit the type, and statement deletions that would leave a local variable 'declared and not used', are pre-dropped
    (the row carries pre_drop = 'range' | 'unused'); the compile loop in build_go.py drops what the Go compiler still rejects;
  * every schema is bracketed by /*S<id>*/ ... /*E<id>*/ so compile errors can be attributed to the innermost lesion;
  * never touched: array lengths, index and slice index expressions (out of range = a panic, not a role), case values, keyed-element keys, const declarations, unsafe.Sizeof, string and
    rune literals, the lesion helpers' own arguments; shift lesions are kept (kind 'shift', build dependent) but the E15 primary analysis excludes them.
"""
import re
import schemata

OPS = schemata.OPS; KIND = schemata.KIND; OPS2 = schemata.OPS2; KIND2 = schemata.KIND2; MAXLEN = schemata.MAXLEN
INTS = {"int", "int8", "int16", "int32", "int64", "uint", "uint8", "uint16", "uint32", "uint64", "uintptr"}
FLOATS = {"float32", "float64"}
BITS = {"int": 64, "int8": 8, "int16": 16, "int32": 32, "int64": 64, "uint": 64, "uint8": 8, "uint16": 16, "uint32": 32, "uint64": 64, "uintptr": 64}
CMP = {"<": "Lt", "<=": "Le", ">": "Gt", ">=": "Ge", "==": "Eq", "!=": "Ne"}
ARITH = {"+": "Add", "-": "Sub", "*": "Mul", "/": "Div", "&": "And", "|": "Or", "<<": "Shl", ">>": "Shr"}
STMTS = {"expression_statement", "assignment_statement", "inc_statement", "dec_statement"}
LEAVES = {"interpreted_string_literal", "raw_string_literal", "rune_literal", "comment", "float_literal", "imaginary_literal", "ERROR"}

class GO:
    NOV2 = False; COND_PARENTS = {"if_statement"}; UNARY = {"unary_expression"}; UPDATE = {"inc_statement", "dec_statement"}
    ON = "e13On(%d)"; ENTER = "e13Enter(%d);"
    FUNC = ("function_declaration",); BIN = "binary_expression"; NUM = "int_literal"; BODY = "block"
    NOMUT_NODES = {"const_declaration", "type_declaration", "import_declaration"}
    NOMUT_FIELDS = {("array_type", "length"), ("index_expression", "index"), ("slice_expression", "start"), ("slice_expression", "end"), ("slice_expression", "capacity"),
                    ("expression_case", "value"), ("keyed_element", "key"), ("type_case", "type")}
    @staticmethod
    def fname(n):
        d = n.child_by_field_name("name"); return d.text.decode("latin-1") if d is not None else "?"
schemata.LANGS["go"] = GO

FACTS = {"lits": {}, "bins": {}, "incs": {}, "unsafe_sdl": set()}
SELECT = None
def configure(facts, select=None):
    """facts: the gotypes JSON (offsets as str or int keys); select: set of function names to instrument (None = every top-level function)."""
    global FACTS, SELECT
    FACTS = dict(lits={int(k): v for k, v in facts["lits"].items()}, bins={int(k): v for k, v in facts["bins"].items()}, incs={int(k): v for k, v in facts["incs"].items()}, unsafe_sdl=set(facts["unsafe_sdl"]))
    SELECT = set(select) if select is not None else None

def simulation_functions(src):
    """Names of gore's simulation functions: the translation keeps chocolate-doom's file order (p_ceilng ... p_user); the E15 screens cover p_enemy p_map p_maputl p_sight p_mobj p_user p_pspr p_inter
    p_doors p_floor p_ceilng p_spec p_switch p_plats p_lights p_telept, so the save-game block, p_setup and p_tick, the random-number generators and every init are left out."""
    import tree_sitter_language_pack as tsp
    t = tsp.get_parser("go").parse(src)
    names = [c.child_by_field_name("name").text.decode() for c in t.root_node.children if c.type == "function_declaration"]
    lo, hi = names.index("t_MoveCeiling"), names.index("p_PlayerThink")
    span = names[lo:hi + 1]
    setup = ("p_TempSaveGameFile", "p_Init")   # p_saveg .. p_setup, one contiguous block in the translation
    a = min(i for i, x in enumerate(span) if x.startswith("saveg_") or x == setup[0]); b = max(i for i, x in enumerate(span) if x == setup[1])
    tick = {"p_InitThinkers", "p_AddThinker", "p_RemoveThinker", "p_RunThinkers", "p_Ticker"}
    return [x for i, x in enumerate(span) if not (a <= i <= b) and x not in tick and x != "init"]

def fits(kind, v):
    if kind in FLOATS: return True
    if kind not in BITS: return False
    n = BITS[kind]
    return (0 <= v < (1 << n)) if kind.startswith("u") else (-(1 << (n - 1)) <= v < (1 << (n - 1)))

class GoEngine(schemata.Engine):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.facts = FACTS; self.sel = SELECT; self.in_for_post = False
    def sent(self, mid, text): return "/*S%d*/%s/*E%d*/" % (mid, text, mid)
    def is_pure(self, n):
        if n.type == "identifier": return True
        if n.type == "selector_expression": return self.is_pure(n.child_by_field_name("operand"))
        if n.type == "parenthesized_expression" and len(n.children) == 3: return self.is_pure(n.children[1])
        return False
    def row(self, kind, op, new, at, byte, node, mid, **kw):
        r = dict(id=mid, kind=kind, op=op, new=new, fn=self.cur_fn, fid=self.cur_fid, line=self.line(byte), col=byte - self.src.rfind(b"\n", 0, byte), byte=byte, node=node, **kw); self.rows.append(r); return r
    def v2row(self, kind, old, new, node, at, edit, **kw):
        mid = self.new_id(kind, old, new, node, at, edit)
        if kw: self.rows[-1].update(kw)
        return mid
    # ---- traversal ----
    def splice(self, n, const, infn):
        out = []; pos = n.start_byte
        for i, c in enumerate(n.children):
            f = n.field_name_for_child(i)
            cc = const or (n.type, f) in self.cfg.NOMUT_FIELDS
            self.neg_next = (n.type == "if_statement" and f == "condition") or (n.type == "for_clause" and f == "condition") or (n.type == "for_statement" and c.type not in ("for", "for_clause", "range_clause", "block"))
            if n.type == "for_clause" and f == "update": self.in_for_post = True
            out.append(self.src[pos:c.start_byte].decode("latin-1")); out.append(self.emit(c, cc, infn)); pos = c.end_byte
            if f == "update": self.in_for_post = False
        out.append(self.src[pos:n.end_byte].decode("latin-1")); return "".join(out)
    def emit(self, n, const=False, infn=False):
        neg = self.neg_next; self.neg_next = False; t = n.type
        if t in LEAVES or (not n.children and not (infn and not const and t == "int_literal")): return self.text(n)
        if t in self.cfg.FUNC and not infn: return self.func(n)
        if not infn: return self.text(n) if t != "source_file" else self.splice(n, const, infn)
        if n.has_error: return self.text(n)
        if t in self.cfg.NOMUT_NODES: const = True
        if t == "call_expression" and self.text(n.child_by_field_name("function")) in ("unsafe.Sizeof", "unsafe.Offsetof", "unsafe.Alignof"): const = True
        if const: return self.splice(n, True, True)
        v2 = not self.cfg.NOV2
        if t == self.cfg.BIN: base = self.binary(n)
        elif t == "int_literal": base = self.literal(n)
        elif t in ("inc_statement", "dec_statement"): base = self.incdec(n, v2)
        else: base = self.splice(n, const, True)
        if not v2: return base
        # v2 wrappers, in the order of schemata.Engine.emit
        if t in STMTS and n.parent is not None and n.parent.type == "statement_list" and len(base) < MAXLEN and not self.is_panic(n):
            pre = "unused" if n.start_byte in self.facts["unsafe_sdl"] else None
            mid = self.v2row("sdl", "stmt", "deleted", n, n, edit=(n.start_byte, n.end_byte, ";"), **({"pre_drop": pre} if pre else {}))
            if mid in self.drop or pre: return base
            return self.sent(mid, "{ if !e13On(%d) { %s } }" % (mid, base))
        if neg and len(base) < MAXLEN and self.text(n).strip("() \t\n") not in ("true", "false"):
            mid = self.v2row("negate", "cond", "!cond", n, n, edit=(n.start_byte, n.end_byte, "!(" + self.text(n) + ")"))
            if mid in self.drop: return base
            return self.sent(mid, "((%s) != e13On(%d))" % (base, mid))
        if t == "int_literal" and re.fullmatch(r"\d+", self.text(n)): return self.literal_v2(n, base)
        if t in self.cfg.UNARY and len(base) < MAXLEN:
            if any(c.type == "!" for c in n.children):
                arg = self.text(n)[1:].strip(); arg_e = base[base.index("!") + 1:]
                mid = self.v2row("not", "!", "", n, n, edit=(n.start_byte, n.end_byte, arg))
                if mid in self.drop: return base
                return self.sent(mid, "((%s) == e13On(%d))" % (arg_e, mid))
        return base
    def is_panic(self, n):
        return n.type == "expression_statement" and self.text(n).startswith("panic(")
    def func(self, n):
        name = self.cfg.fname(n); body = n.child_by_field_name("body")
        if (self.sel is not None and name not in self.sel) or n.has_error or body is None or body.type != "block": return self.text(n)
        fid = self.fn; self.fn += 1; self.fns.append(dict(fid=fid, name=name, line=self.line(n.start_byte), end_line=self.line(n.end_byte), size=n.end_byte - n.start_byte))
        self.cur_fn = name; self.cur_fid = fid; out = []; pos = n.start_byte
        for c in n.children:
            out.append(self.src[pos:c.start_byte].decode("latin-1"))
            if c.id == body.id:
                inner = self.splice(c, False, True); assert inner.startswith("{"); out.append("{ " + self.cfg.ENTER % fid + inner[1:])
            else: out.append(self.text(c))
            pos = c.end_byte
        out.append(self.src[pos:n.end_byte].decode("latin-1")); self.cur_fn = None; self.cur_fid = None; return "".join(out)
    # ---- binary operators ----
    def binary(self, n):
        opn = n.child_by_field_name("operator"); op = opn.text.decode(); left, right = n.child_by_field_name("left"), n.child_by_field_name("right")
        orig_kind = op in OPS; v2 = op in OPS2 and not self.cfg.NOV2
        if not (orig_kind or v2): return self.splice(n, False, True)
        L, R = self.emit(left, False, True), self.emit(right, False, True)
        mid1 = self.src[left.end_byte:opn.start_byte].decode("latin-1"); mid2 = self.src[opn.end_byte:right.start_byte].decode("latin-1"); orig = L + mid1 + op + mid2 + R
        if len(orig) >= MAXLEN: return orig
        fx = self.facts["bins"].get(opn.start_byte)
        if fx is None: return orig
        if op in ("&&", "||"):
            if fx["l"]["k"] != "bool" or fx["r"]["k"] != "bool": return orig
            mid = self.id; self.id += 1; o2 = OPS[op]; self.row(KIND[op], op, o2, opn, opn.start_byte, "binary", mid)
            if mid in self.drop: return orig
            return self.sent(mid, "(e13On(%d) && (%s %s %s) || e13Id != %d && (%s))" % (mid, L + mid1, o2, mid2 + R, mid, orig))
        helper = self.helper(op, fx)
        if helper is None: return orig
        new = OPS[op] if orig_kind else OPS2[op]
        if orig_kind: mid = self.id; self.id += 1; self.row(KIND[op], op, new, opn, opn.start_byte, "binary", mid)
        else: mid = self.new_id(KIND2[op], op, new, n, opn, edit=(opn.start_byte, opn.end_byte, new))
        if mid in self.drop: return orig
        return self.sent(mid, "%s(%d, %s, %s)" % (helper, mid, L, R))
    def helper(self, op, fx):
        lk, rk, tk = fx["l"]["k"], fx["r"]["k"], fx["t"]["k"]
        if op in CMP:
            T = fx["l"]["n"] if lk != "nil" else fx["r"]["n"]; k = lk if lk != "nil" else rk
            if op in ("==", "!="):
                if k not in INTS | FLOATS | {"string", "bool", "ptr", "iface"} or {lk, rk} - (INTS | FLOATS | {"string", "bool", "ptr", "iface", "nil"}): return None
            elif k not in INTS | FLOATS | {"string"}: return None
            return "e13%s[%s]" % (CMP[op], T)
        if op in ("<<", ">>"):
            if lk not in INTS or rk not in INTS: return None
            return "e13%s[%s, %s]" % (ARITH[op], fx["l"]["n"], fx["r"]["n"])
        if op in ("&", "|"):
            if tk not in INTS or lk != tk or rk != tk: return None
        elif tk not in INTS | FLOATS or lk != tk or rk != tk: return None
        return "e13%s[%s]" % (ARITH[op], fx["t"]["n"])
    # ---- constants ----
    def literal(self, n):
        s = self.text(n)
        if re.fullmatch(r"\d+", s) and 2 <= int(s) < 100000:
            v = int(s); mid = self.id; self.id += 1; r = self.row("constant", s, str(v + 1), n, n.start_byte, "literal", mid); ty = self.facts["lits"].get(n.start_byte)
            if ty is None or ty["k"] not in INTS | FLOATS: r["pre_drop"] = "type"; return s
            if not fits(ty["k"], v + 1) or not fits(ty["k"], v): r["pre_drop"] = "range"; return s
            if mid in self.drop: return s
            r["T"] = ty["n"]; return self.sent(mid, "e13K[%s](%d, %d, %s)" % (ty["n"], mid, v + 1, s))
        return s
    def literal_v2(self, n, base):
        v = int(self.text(n)); alts = []; ty = self.facts["lits"].get(n.start_byte)
        if 2 <= v < 100000: alts = [("const_zero", 0), ("const_dec", v - 1)]
        elif v in (0, 1): alts = [("const_toggle", 1 - v)]
        for kind, val in alts:
            pre = None
            if ty is None or ty["k"] not in INTS | FLOATS: pre = "type"
            elif not fits(ty["k"], val) or not fits(ty["k"], v): pre = "range"
            mid = self.v2row(kind, str(v), str(val), n, n, edit=(n.start_byte, n.end_byte, str(val)), **({"pre_drop": pre} if pre else {}))
            if pre or mid in self.drop: continue
            base = self.sent(mid, "e13K[%s](%d, %d, %s)" % (ty["n"], mid, val, base))
        return base
    # ---- x++ / x-- ----
    def incdec(self, n, v2):
        operand = n.children[0]; opn = n.children[1]; o = opn.type; o2 = "--" if o == "++" else "++"
        X = self.emit(operand, False, True); mid1 = self.src[operand.end_byte:opn.start_byte].decode("latin-1"); base = X + mid1 + o
        if not v2: return base
        ty = self.facts["incs"].get(n.start_byte)
        if ty is None or ty["k"] not in INTS | FLOATS: return base
        pure = self.is_pure(operand)
        if not pure and self.in_for_post: return base
        mid = self.v2row("incdec", o, o2, n, opn, edit=(opn.start_byte, opn.end_byte, o2))
        if mid in self.drop: return base
        if pure: return self.sent(mid, "%s = e13%s[%s](%d, %s)" % (X, "Inc" if o == "++" else "Dec", ty["n"], mid, X))
        return self.sent(mid, "if e13On(%d) { %s%s } else { %s }" % (mid, X, o2, base))

_Orig = schemata.Engine
def _dispatch(src, lang, *a, **k):
    return GoEngine(src, lang, *a, **k) if lang == "go" else _Orig(src, lang, *a, **k)
class _Meta(type(_Orig)): pass
schemata.Engine = _dispatch   # instrument() builds its engines through this name
