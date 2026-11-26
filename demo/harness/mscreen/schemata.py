"""Mutant schemata via tree-sitter: rewrite a source file so every lesion site is a runtime switch (E13_ON(id)), and every function counts its entries.
instrument(src_bytes, lang, id_base, fn_base, drop=set()) -> (new_text, manifest_rows, function_rows). Lesions: operator swaps (relational, equality, +/-, &&/||, shifts) and integer constant + 1,
inside function bodies only; preprocessor lines, case labels, array sizes, enumerators, sizeof and static initialisers are never touched."""
import re
import tree_sitter_language_pack as tsp
OPS2 = {"*": "/", "/": "*", "&": "|", "|": "&"}
KIND2 = {"*": "arith2", "/": "arith2", "&": "bitwise", "|": "bitwise"}
OPS = {"<": "<=", "<=": "<", ">": ">=", ">=": ">", "==": "!=", "!=": "==", "+": "-", "-": "+", "&&": "||", "||": "&&", "<<": ">>", ">>": "<<"}
KIND = {"<": "relational", "<=": "relational", ">": "relational", ">=": "relational", "==": "equality", "!=": "equality", "+": "arithmetic", "-": "arithmetic", "&&": "logical", "||": "logical", "<<": "shift", ">>": "shift"}
MAXLEN = 3000
class C:
    NOV2 = False; COND_PARENTS = {"if_statement", "while_statement", "do_statement", "for_statement", "conditional_expression"}; UNARY = {"unary_expression"}; UPDATE = {"update_expression"}
    ON = "E13_ON(%d)"; ENTER = "E13_ENTER(%d);"
    FUNC = ("function_definition",); BIN = "binary_expression"; NUM = "number_literal"; BODY = "compound_statement"
    NOMUT_NODES = {"sizeof_expression", "enumerator", "bitfield_clause", "attribute_specifier", "static_assert_declaration"}
    NOMUT_FIELDS = {("case_statement", "value"), ("array_declarator", "size"), ("subscript_expression", "index")}  # an array index lesion is an out-of-bounds access: undefined behaviour, layout dependent
    @staticmethod
    def fname(n):
        d = n.child_by_field_name("declarator")
        while d is not None and d.type != "function_declarator" and d.child_by_field_name("declarator") is not None: d = d.child_by_field_name("declarator")
        while d is not None and d.type != "identifier":
            nd = d.child_by_field_name("declarator"); d = nd if nd is not None else (d.children[0] if d.children else None)
            if d is not None and d.type == "identifier": break
        return d.text.decode("latin-1") if d is not None and d.type == "identifier" else "?"
class CS:
    NOV2 = False; COND_PARENTS = {"if_statement", "while_statement", "do_statement", "for_statement", "conditional_expression"}; UNARY = {"prefix_unary_expression"}; UPDATE = {"prefix_unary_expression", "postfix_unary_expression"}
    ON = "E13Mut.On(%d)"; ENTER = "E13Mut.Enter(%d);"
    FUNC = ("method_declaration", "constructor_declaration"); BIN = "binary_expression"; NUM = "integer_literal"; BODY = "block"
    NOMUT_NODES = {"case_switch_label", "constant_pattern", "array_rank_specifier", "bracketed_argument_list", "attribute", "enum_member_declaration", "parameter"}
    NOMUT_FIELDS = set()
    @staticmethod
    def fname(n):
        d = n.child_by_field_name("name"); return d.text.decode("latin-1") if d is not None else "?"
LANGS = {"c": C, "csharp": CS}
class Engine:
    def __init__(self, src, lang, id_base, fn_base, drop, id2_base=10000, old_keep=None):
        self.src = src; self.cfg = LANGS[lang]; self.parser = tsp.get_parser(lang); self.tree = self.parser.parse(src); self.id = id_base; self.fn = fn_base; self.drop = drop
        self.rows = []; self.fns = []; self.cur_fn = None; self.cur_fid = None; self.id2 = id2_base; self.neg_next = False; self.old_keep = old_keep; self.line_starts = None
    def text(self, n): return self.src[n.start_byte:n.end_byte].decode("latin-1")
    def line(self, byte): return self.src.count(b"\n", 0, byte) + 1
    def splice(self, n, const, infn):
        out = []; pos = n.start_byte
        for i, c in enumerate(n.children):
            cc = const or (n.type, n.field_name_for_child(i)) in self.cfg.NOMUT_FIELDS
            self.neg_next = (n.type in self.cfg.COND_PARENTS and n.field_name_for_child(i) == "condition")
            out.append(self.src[pos:c.start_byte].decode("latin-1")); out.append(self.emit(c, cc, infn)); pos = c.end_byte
        out.append(self.src[pos:n.end_byte].decode("latin-1")); return "".join(out)
    def new_id(self, kind, old, new, node, at, edit):
        mid = self.id2; self.id2 += 1
        self.rows.append(dict(id=mid, kind=kind, op=old, new=new, fn=self.cur_fn, fid=self.cur_fid, line=self.line(at.start_byte), col=at.start_byte - self.src.rfind(b"\n", 0, at.start_byte), byte=at.start_byte, node="v2", cls="v2", edit=[edit[0], edit[1], edit[2]]))
        return mid
    def emit(self, n, const=False, infn=False):
        neg = self.neg_next; self.neg_next = False; base = self.emit_core(n, const, infn)
        if not infn or const or self.cfg.NOV2: return base
        t = n.type; cfg = self.cfg; drop = self.drop
        # statement deletion
        if t == "expression_statement" and n.parent is not None and n.parent.type != "for_statement" and len(base) < MAXLEN:
            mid = self.new_id("sdl", "stmt", "deleted", n, n, edit=(n.start_byte, n.end_byte, ";"))
            if mid not in drop: base = "{ if (!" + cfg.ON % mid + ") { " + base + " } }"
            return base
        # condition negation
        if neg and len(base) < MAXLEN and self.text(n).strip("() \t\n") not in ("true", "false", "1", "0", "TRUE", "FALSE"):   # constant conditions: negating them breaks reachability analysis
            if t == "parenthesized_expression" and len(n.children) == 3:
                inner = n.children[1]; ie = self.text(inner); mid = self.new_id("negate", "cond", "!cond", n, inner, edit=(inner.start_byte, inner.end_byte, "!(" + ie + ")"))
                if mid not in drop: ib = base[1:-1]; base = "(" + "(" + cfg.ON % mid + " ? !(" + ib + ") : (" + ib + "))" + ")"
            elif t != "parenthesized_expression":
                mid = self.new_id("negate", "cond", "!cond", n, n, edit=(n.start_byte, n.end_byte, "!(" + self.text(n) + ")"))
                if mid not in drop: base = "(" + cfg.ON % mid + " ? !(" + base + ") : (" + base + "))"
            return base
        # integer constants: 0, minus one, toggle 0/1
        if t == cfg.NUM and re.fullmatch(r"\d+", self.text(n)):
            v = int(self.text(n)); alts = []
            if 2 <= v < 100000: alts = [("const_zero", 0), ("const_dec", v - 1)]
            elif v in (0, 1): alts = [("const_toggle", 1 - v)]
            for kind, val in alts:
                mid = self.new_id(kind, str(v), str(val), n, n, edit=(n.start_byte, n.end_byte, str(val)))
                if mid not in drop: base = "(" + cfg.ON % mid + " ? (%d) : (%s))" % (val, base)
            return base
        # delete a logical not
        if t in cfg.UNARY and len(base) < MAXLEN:
            ops = [c for c in n.children if c.type == "!"]
            if ops:
                arg = self.text(n)[1:].strip(); arg_e = base[base.index("!") + 1:]
                mid = self.new_id("not", "!", "", n, n, edit=(n.start_byte, n.end_byte, arg))
                if mid not in drop: base = "(" + cfg.ON % mid + " ? (" + arg_e + ") : (" + base + "))"
            return base
        # ++ <-> --
        if t in cfg.UPDATE and len(base) < MAXLEN:
            ops = [c for c in n.children if c.type in ("++", "--")]
            if ops and "++" not in base.replace(ops[0].type, "", 1) and "--" not in base.replace(ops[0].type, "", 1):
                o = ops[0].type; o2 = "--" if o == "++" else "++"; mid = self.new_id("incdec", o, o2, n, ops[0], edit=(ops[0].start_byte, ops[0].end_byte, o2))
                if mid not in drop: base = "(" + cfg.ON % mid + " ? (" + base.replace(o, o2, 1) + ") : (" + base + "))"
            return base
        return base
    def emit_core(self, n, const=False, infn=False):
        t = n.type; cfg = self.cfg
        if t.startswith("preproc") or t == "comment" or t == "ERROR": return self.text(n)
        if t in cfg.FUNC and not infn and not n.has_error:
            name = cfg.fname(n); body = n.child_by_field_name("body")
            if body is None or body.type != cfg.BODY: return self.text(n)
            fid = self.fn; self.fn += 1; self.fns.append(dict(fid=fid, name=name, line=self.line(n.start_byte), end_line=self.line(n.end_byte), size=n.end_byte - n.start_byte)); prev = self.cur_fn; prevf = self.cur_fid; self.cur_fn = name; self.cur_fid = fid
            out = []; pos = n.start_byte
            for c in n.children:
                out.append(self.src[pos:c.start_byte].decode("latin-1"))
                if c.id == body.id:
                    inner = self.splice(c, const, True); assert inner.startswith("{"); out.append("{ " + cfg.ENTER % fid + inner[1:])
                else: out.append(self.emit(c, const, False))
                pos = c.end_byte
            out.append(self.src[pos:n.end_byte].decode("latin-1")); self.cur_fn = prev; self.cur_fid = prevf; return "".join(out)
        if t in cfg.NOMUT_NODES: const = True
        if t == "local_declaration_statement" and any(ch.type == "modifier" and ch.text == b"const" for ch in n.children): const = True
        if t == "declaration" and any(ch.type == "storage_class_specifier" and ch.text == b"static" for ch in n.children): const = True
        if infn and not const and t == cfg.BIN:
            opn = n.child_by_field_name("operator"); op = opn.text.decode()
            if op in OPS:
                left, right = n.child_by_field_name("left"), n.child_by_field_name("right")
                L, R = self.emit(left, const, infn), self.emit(right, const, infn)
                mid1 = self.src[left.end_byte:opn.start_byte].decode("latin-1"); mid2 = self.src[opn.end_byte:right.start_byte].decode("latin-1")
                orig = L + mid1 + op + mid2 + R
                if (self.old_keep is None and len(orig) < MAXLEN) or (self.old_keep is not None and opn.start_byte in self.old_keep):   # with the expansion on, the original lesion set is fixed by the original-only pass
                    mid = self.id; self.id += 1
                    self.rows.append(dict(id=mid, kind=KIND[op], op=op, new=OPS[op], fn=self.cur_fn, fid=self.cur_fid, line=self.line(opn.start_byte), col=opn.start_byte - self.src.rfind(b"\n", 0, opn.start_byte), byte=opn.start_byte, node="binary"))
                    if mid in self.drop: return orig
                    return "(" + cfg.ON % mid + " ? (%s) : (%s))" % (L + mid1 + OPS[op] + mid2 + R, orig)
                return orig
        if infn and not const and t == cfg.BIN:
            opn = n.child_by_field_name("operator"); op = opn.text.decode()
            if op in OPS2 and not cfg.NOV2:
                left, right = n.child_by_field_name("left"), n.child_by_field_name("right")
                L, R = self.emit(left, const, infn), self.emit(right, const, infn)
                mid1 = self.src[left.end_byte:opn.start_byte].decode("latin-1"); mid2 = self.src[opn.end_byte:right.start_byte].decode("latin-1"); orig = L + mid1 + op + mid2 + R
                if len(orig) < MAXLEN:
                    mid = self.new_id(KIND2[op], op, OPS2[op], n, opn, edit=(opn.start_byte, opn.end_byte, OPS2[op]))
                    if mid in self.drop: return orig
                    return "(" + cfg.ON % mid + " ? (%s) : (%s))" % (L + mid1 + OPS2[op] + mid2 + R, orig)
                return orig
        if infn and not const and t == cfg.NUM:
            s = self.text(n)
            if re.fullmatch(r"\d+", s) and 2 <= int(s) < 100000:
                mid = self.id; self.id += 1
                self.rows.append(dict(id=mid, kind="constant", op=s, new=str(int(s) + 1), fn=self.cur_fn, fid=self.cur_fid, line=self.line(n.start_byte), col=n.start_byte - self.src.rfind(b"\n", 0, n.start_byte), byte=n.start_byte, node="literal"))
                if mid in self.drop: return s
                return "(" + cfg.ON % mid + " ? (%d) : (%s))" % (int(s) + 1, s)
            return s
        if not n.children: return self.text(n)
        return self.splice(n, const, infn)
def instrument(src, lang, id_base, fn_base, drop=frozenset(), id2_base=10000, v2=True):
    keep = None
    if v2:
        e0 = Engine(src, lang, id_base, fn_base, frozenset(), id2_base); e0.cfg = type("Cfg", (e0.cfg,), {"NOV2": True}); e0.fn = fn_base; e0.emit(e0.tree.root_node); keep = {r["byte"] for r in e0.rows if r.get("cls") != "v2" and r.get("node") == "binary"}
    e = Engine(src, lang, id_base, fn_base, drop, id2_base, keep)
    e.fn = fn_base
    if not v2: e.cfg = type("Cfg", (e.cfg,), {"NOV2": True})
    text = e.emit(e.tree.root_node); return text, e.rows, e.fns, e.id, e.fn, e.id2
