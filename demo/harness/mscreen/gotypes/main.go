// e13types: type facts for the Go mutant-screen instrumenter (our own code, uses only the standard library).
// Usage: e13types <package dir> <file.go>   -> JSON on stdout, keyed by byte offsets of <file.go> (the same bytes tree-sitter sees).
//   lits:  offset of an integer literal -> its final type (after context conversion; untyped -> default type)
//   bins:  offset of a binary operator  -> {l, r, t: operand and result types, c: constant expression}
//   incs:  offset of an x++/x-- statement -> type of x
//   unsafe_sdl: offsets of simple statements whose deletion would leave a local variable declared and not used
package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
	"os"
	"path/filepath"
	"strings"
)

// ty is a type as the instrumenter needs it: its name in package scope and its kind (basic name, or ptr/iface/struct/array/slice/map/func/chan/other)
type ty struct {
	N string `json:"n"`
	K string `json:"k"`
}
type bin struct {
	L ty   `json:"l"`
	R ty   `json:"r"`
	T ty   `json:"t"`
	C bool `json:"c"`
}

func main() {
	dir, target := os.Args[1], os.Args[2]
	fset := token.NewFileSet()
	ents, _ := os.ReadDir(dir)
	var files []*ast.File
	var tfile *ast.File
	for _, e := range ents {
		n := e.Name()
		if e.IsDir() || !strings.HasSuffix(n, ".go") || strings.HasSuffix(n, "_test.go") {
			continue
		}
		f, err := parser.ParseFile(fset, filepath.Join(dir, n), nil, parser.SkipObjectResolution)
		if err != nil {
			fmt.Fprintln(os.Stderr, "parse:", err)
			os.Exit(1)
		}
		files = append(files, f)
		if n == target {
			tfile = f
		}
	}
	info := &types.Info{Types: map[ast.Expr]types.TypeAndValue{}, Uses: map[*ast.Ident]types.Object{}, Defs: map[*ast.Ident]types.Object{}}
	nerr := 0
	conf := types.Config{Importer: importer.ForCompiler(fset, "source", nil), Error: func(err error) {
		nerr++
		if nerr < 10 {
			fmt.Fprintln(os.Stderr, "type error:", err)
		}
	}}
	pkg, _ := conf.Check("gore", fset, files, info)
	q := func(p *types.Package) string {
		if p == pkg {
			return ""
		}
		return p.Name()
	}
	ts := func(t types.Type) ty {
		if t == nil {
			return ty{}
		}
		if b, ok := t.(*types.Basic); ok && b.Info()&types.IsUntyped != 0 && b.Kind() != types.UntypedNil {
			t = types.Default(t)
		}
		k := "other"
		switch u := t.Underlying().(type) {
		case *types.Basic:
			k = u.Name()
			if u.Kind() == types.UntypedNil {
				k = "nil"
			}
		case *types.Pointer:
			k = "ptr"
		case *types.Interface:
			k = "iface"
		case *types.Struct:
			k = "struct"
		case *types.Array:
			k = "array"
		case *types.Slice:
			k = "slice"
		case *types.Map:
			k = "map"
		case *types.Signature:
			k = "func"
		case *types.Chan:
			k = "chan"
		}
		return ty{types.TypeString(t, q), k}
	}
	off := func(p token.Pos) int { return fset.Position(p).Offset }
	untyped := func(t types.Type) bool {
		b, ok := t.(*types.Basic)
		return ok && b.Info()&types.IsUntyped != 0 && b.Kind() != types.UntypedNil
	}
	// eff: the type an expression really has. go/types leaves the inner parts of an untyped constant expression untyped (8 * (1 << FRACBITS) records int for the shift);
	// they take the type of the nearest enclosing constant expression that was converted.
	eff := func(path []ast.Node) types.Type {
		x := path[len(path)-1].(ast.Expr)
		t := info.Types[x].Type
		if !untyped(t) {
			return t
		}
		for i := len(path) - 2; i >= 0; i-- {
			e, ok := path[i].(ast.Expr)
			if !ok {
				break
			}
			tv := info.Types[e]
			if tv.Value == nil {
				break
			}
			if !untyped(tv.Type) {
				return tv.Type
			}
		}
		return t
	}
	out := struct {
		Lits   map[int]ty `json:"lits"`
		Bins   map[int]bin    `json:"bins"`
		Incs   map[int]ty `json:"incs"`
		Unsafe []int          `json:"unsafe_sdl"`
		Errors int            `json:"type_errors"`
	}{map[int]ty{}, map[int]bin{}, map[int]ty{}, []int{}, nerr}

	// reads of every local variable: object -> list of positions of ident uses that count as a use for the compiler
	type span struct{ a, b token.Pos }
	reads := map[types.Object][]token.Pos{}
	for _, d := range tfile.Decls {
		fd, ok := d.(*ast.FuncDecl)
		if !ok || fd.Body == nil {
			continue
		}
		body := fd.Body
		isLocal := func(o types.Object) bool {
			v, ok := o.(*types.Var)
			return ok && !v.IsField() && v.Pos() > body.Lbrace && v.Pos() < body.Rbrace
		}
		var stack []ast.Node
		ast.Inspect(body, func(n ast.Node) bool {
			if n == nil {
				stack = stack[:len(stack)-1]
				return true
			}
			stack = append(stack, n)
			switch x := n.(type) {
			case *ast.BasicLit:
				if x.Kind == token.INT {
					out.Lits[off(x.Pos())] = ts(eff(stack))
				}
			case *ast.BinaryExpr:
				tv := info.Types[x]
				_ = tv
				out.Bins[off(x.OpPos)] = bin{ts(eff(append(append([]ast.Node{}, stack...), x.X))), ts(eff(append(append([]ast.Node{}, stack...), x.Y))), ts(eff(stack)), tv.Value != nil}
			case *ast.IncDecStmt:
				out.Incs[off(x.Pos())] = ts(info.Types[x.X].Type)
			case *ast.Ident:
				if o := info.Uses[x]; o != nil && isLocal(o) {
					writeOnly := false
					if len(stack) >= 2 {
						if as, ok := stack[len(stack)-2].(*ast.AssignStmt); ok && (as.Tok == token.ASSIGN || as.Tok == token.DEFINE) {
							for _, l := range as.Lhs {
								if l == ast.Expr(x) {
									writeOnly = true
								}
							}
						}
					}
					if !writeOnly {
						reads[o] = append(reads[o], x.Pos())
					}
				}
			}
			return true
		})
		// candidates: simple statements
		ast.Inspect(body, func(n ast.Node) bool {
			var lo, hi token.Pos
			switch s := n.(type) {
			case *ast.ExprStmt:
				lo, hi = s.Pos(), s.End()
			case *ast.AssignStmt:
				if s.Tok == token.DEFINE {
					return true
				}
				lo, hi = s.Pos(), s.End()
			case *ast.IncDecStmt:
				lo, hi = s.Pos(), s.End()
			default:
				return true
			}
			unsafe := false
			for o, rs := range reads {
				if !isLocal(o) {
					continue
				}
				in, outside := 0, 0
				for _, p := range rs {
					if p >= lo && p < hi {
						in++
					} else {
						outside++
					}
				}
				if in > 0 && outside == 0 {
					unsafe = true
					break
				}
			}
			if unsafe {
				out.Unsafe = append(out.Unsafe, off(lo))
			}
			return true
		})
		for o := range reads { // reads are per function: reset
			delete(reads, o)
		}
	}
	json.NewEncoder(os.Stdout).Encode(out)
}
