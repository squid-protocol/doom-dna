"""Mutant schemata via tree-sitter: rewrite a source file so every lesion site is a runtime switch (E13_ON(id)), and every function counts its entries.
instrument(src_bytes, lang, id_base, fn_base, drop=set()) -> (new_text, manifest_rows, function_rows). Lesions: operator swaps (relational, equality, +/-, &&/||, shifts) and integer constant + 1,
inside function bodies only; preprocessor lines, case labels, array sizes, enumerators, sizeof and static initialisers are never touched."""
import re
import tree_sitter_language_pack as tsp
OPS = {"<": "<=", "<=": "<", ">": ">=", ">=": ">", "==": "!=", "!=": "==", "+": "-", "-": "+", "&&": "||", "||": "&&", "<<": ">>", ">>": "<<"}
KIND = {"<": "relational", "<=": "relational", ">": "relational", ">=": "relational", "==": "equality", "!=": "equality", "+": "arithmetic", "-": "arithmetic", "&&": "logical", "||": "logical", "<<": "shift", ">>": "shift"}
MAXLEN = 3000
class C:
    FUNC = "function_definition"; BIN = "binary_expression"; NUM = "number_literal"; BODY = "compound_statement"
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
LANGS = {"c": C}
class Engine:
    def __init__(self, src, lang, id_base, fn_base, drop):
        self.src = src; self.cfg = LANGS[lang]; self.parser = tsp.get_parser(lang); self.tree = self.parser.parse(src); self.id = id_base; self.fn = fn_base; self.drop = drop
        self.rows = []; self.fns = []; self.cur_fn = None; self.line_starts = None
    def text(self, n): return self.src[n.start_byte:n.end_byte].decode("latin-1")
    def line(self, byte): return self.src.count(b"\n", 0, byte) + 1
    def splice(self, n, const, infn):
        out = []; pos = n.start_byte
        for i, c in enumerate(n.children):
            cc = const or (n.type, n.field_name_for_child(i)) in self.cfg.NOMUT_FIELDS
            out.append(self.src[pos:c.start_byte].decode("latin-1")); out.append(self.emit(c, cc, infn)); pos = c.end_byte
        out.append(self.src[pos:n.end_byte].decode("latin-1")); return "".join(out)
    def emit(self, n, const=False, infn=False):
        t = n.type; cfg = self.cfg
        if t.startswith("preproc") or t == "comment" or t == "ERROR": return self.text(n)
        if t == cfg.FUNC and not infn and not n.has_error:
            name = cfg.fname(n); body = n.child_by_field_name("body")
            if body is None or body.type != cfg.BODY: return self.text(n)
            fid = self.fn; self.fn += 1; self.fns.append(dict(fid=fid, name=name, line=self.line(n.start_byte), end_line=self.line(n.end_byte), size=n.end_byte - n.start_byte)); prev = self.cur_fn; self.cur_fn = name
            out = []; pos = n.start_byte
            for c in n.children:
                out.append(self.src[pos:c.start_byte].decode("latin-1"))
                if c.id == body.id:
                    inner = self.splice(c, const, True); assert inner.startswith("{"); out.append("{ E13_ENTER(%d);" % fid + inner[1:])
                else: out.append(self.emit(c, const, False))
                pos = c.end_byte
            out.append(self.src[pos:n.end_byte].decode("latin-1")); self.cur_fn = prev; return "".join(out)
        if t in cfg.NOMUT_NODES: const = True
        if t == "declaration" and any(ch.type == "storage_class_specifier" and ch.text == b"static" for ch in n.children): const = True
        if infn and not const and t == cfg.BIN:
            opn = n.child_by_field_name("operator"); op = opn.text.decode()
            if op in OPS:
                left, right = n.child_by_field_name("left"), n.child_by_field_name("right")
                L, R = self.emit(left, const, infn), self.emit(right, const, infn)
                mid1 = self.src[left.end_byte:opn.start_byte].decode("latin-1"); mid2 = self.src[opn.end_byte:right.start_byte].decode("latin-1")
                orig = L + mid1 + op + mid2 + R
                if len(orig) < MAXLEN:
                    mid = self.id; self.id += 1
                    self.rows.append(dict(id=mid, kind=KIND[op], op=op, new=OPS[op], fn=self.cur_fn, line=self.line(opn.start_byte), col=opn.start_byte - self.src.rfind(b"\n", 0, opn.start_byte), byte=opn.start_byte, node="binary"))
                    if mid in self.drop: return orig
                    return "(E13_ON(%d) ? (%s) : (%s))" % (mid, L + mid1 + OPS[op] + mid2 + R, orig)
                return orig
        if infn and not const and t == cfg.NUM:
            s = self.text(n)
            if re.fullmatch(r"\d+", s) and 2 <= int(s) < 100000:
                mid = self.id; self.id += 1
                self.rows.append(dict(id=mid, kind="constant", op=s, new=str(int(s) + 1), fn=self.cur_fn, line=self.line(n.start_byte), col=n.start_byte - self.src.rfind(b"\n", 0, n.start_byte), byte=n.start_byte, node="literal"))
                if mid in self.drop: return s
                return "(E13_ON(%d) ? (%d) : (%s))" % (mid, int(s) + 1, s)
            return s
        if not n.children: return self.text(n)
        return self.splice(n, const, infn)
def instrument(src, lang, id_base, fn_base, drop=frozenset()):
    e = Engine(src, lang, id_base, fn_base, drop); e.fn = fn_base
    text = e.emit(e.tree.root_node); return text, e.rows, e.fns, e.id, e.fn
