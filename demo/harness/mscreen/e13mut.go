package gore

// Mutant-screen runtime for gore (our own code; same contract as E13Mut.cs and e13_screen.c).
//   E13_MUT=<id>      the active lesion (unset: none, the zero-lesion build)
//   E13_REF=<file>    clean per-tic digest of the same engine: the run ends at the first mismatching tic
//   E13_VERDICT=<f>   "div <row> <mask>" at the first mismatch, "end <rows>" when the demo ends
//   E13_NODIGEST=1    do not write the digest file (screen runs)
//   E13_PROFILE=<f>   "F fid count first_tic" per function entered, "S id count" per lesion site executed
// Every lesion in the instrumented source is a call to one of the e13* helpers below (no ternary in Go): the operands are evaluated once,
// in the original order, and only the selected operation runs.

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

type e13Int interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 | ~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 | ~uintptr
}
type e13Num interface {
	e13Int | ~float32 | ~float64
}
type e13Ord interface {
	e13Num | ~string
}

const e13Max = 1 << 17

var e13Id = e13EnvInt("E13_MUT")
var e13NoDigest = os.Getenv("E13_NODIGEST") != ""
var e13Counts [e13Max]uint32
var e13First [e13Max]int32
var e13Site [e13Max]uint32
var e13RefRows [][19]uint64
var e13HaveRef bool
var e13Rows int
var e13Init bool

func e13EnvInt(name string) int {
	v, err := strconv.Atoi(os.Getenv(name))
	if err != nil {
		return -1
	}
	return v
}

// e13On counts one execution of a lesion site and says whether this lesion is the active one.
func e13On(id int) bool { e13Site[id]++; return e13Id == id }

// e13Enter counts one entry of a function.
func e13Enter(fid int) {
	e13Counts[fid]++
	if e13First[fid] == 0 {
		e13First[fid] = int32(e13Rows) + 1
	}
}

func e13Lt[T e13Ord](id int, l, r T) bool {
	if e13On(id) {
		return l <= r
	}
	return l < r
}
func e13Le[T e13Ord](id int, l, r T) bool {
	if e13On(id) {
		return l < r
	}
	return l <= r
}
func e13Gt[T e13Ord](id int, l, r T) bool {
	if e13On(id) {
		return l >= r
	}
	return l > r
}
func e13Ge[T e13Ord](id int, l, r T) bool {
	if e13On(id) {
		return l > r
	}
	return l >= r
}
func e13Eq[T comparable](id int, l, r T) bool {
	if e13On(id) {
		return l != r
	}
	return l == r
}
func e13Ne[T comparable](id int, l, r T) bool {
	if e13On(id) {
		return l == r
	}
	return l != r
}
func e13Add[T e13Num](id int, l, r T) T {
	if e13On(id) {
		return l - r
	}
	return l + r
}
func e13Sub[T e13Num](id int, l, r T) T {
	if e13On(id) {
		return l + r
	}
	return l - r
}
func e13Mul[T e13Num](id int, l, r T) T {
	if e13On(id) {
		return l / r // integer division by zero panics, as in the original program; a crash outcome
	}
	return l * r
}
func e13Div[T e13Num](id int, l, r T) T {
	if e13On(id) {
		return l * r
	}
	return l / r
}
func e13And[T e13Int](id int, l, r T) T {
	if e13On(id) {
		return l | r
	}
	return l & r
}
func e13Or[T e13Int](id int, l, r T) T {
	if e13On(id) {
		return l & r
	}
	return l | r
}
func e13Shl[T, S e13Int](id int, l T, r S) T {
	if e13On(id) {
		return l >> r
	}
	return l << r
}
func e13Shr[T, S e13Int](id int, l T, r S) T {
	if e13On(id) {
		return l << r
	}
	return l >> r
}

// e13K: a numeric constant replaced by another value (old = the original).
func e13K[T e13Num](id int, nw, old T) T {
	if e13On(id) {
		return nw
	}
	return old
}

// e13Inc / e13Dec: x++ and x-- as x = e13Inc(id, x); the active lesion swaps them.
func e13Inc[T e13Num](id int, v T) T {
	if e13On(id) {
		return v - 1
	}
	return v + 1
}
func e13Dec[T e13Num](id int, v T) T {
	if e13On(id) {
		return v + 1
	}
	return v - 1
}

func e13Parse(s string) uint64 {
	if strings.HasPrefix(s, "-") {
		v, _ := strconv.ParseInt(s, 10, 64)
		return uint64(v)
	}
	v, _ := strconv.ParseUint(s, 10, 64)
	return v
}

func e13Setup() {
	e13Init = true
	if rf := os.Getenv("E13_REF"); rf != "" {
		f, err := os.Open(rf)
		if err == nil {
			defer f.Close()
			sc := bufio.NewScanner(f)
			for sc.Scan() {
				p := strings.Fields(sc.Text())
				if len(p) != 19 {
					continue
				}
				var row [19]uint64
				for i, x := range p {
					row[i] = e13Parse(x)
				}
				e13RefRows = append(e13RefRows, row)
			}
			e13HaveRef = true
		}
	}
}

// e13U widens any integer to the 64-bit pattern of its decimal text (signed values sign-extended), as the reference file stores them.
func e13U[T e13Int](v T) uint64 {
	var z T
	if z-1 < z { // signed
		return uint64(int64(v))
	}
	return uint64(v)
}

var e13Cols = [...]int{1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18}

// e13Check is called once per tic with the 19 digest values (the same line the digest file gets); it ends the run at the first mismatch with the reference.
func e13Check(val [19]uint64) {
	if !e13Init {
		e13Setup()
	}
	if e13HaveRef && e13Rows < len(e13RefRows) {
		rr := e13RefRows[e13Rows]
		var mask int64
		for _, c := range e13Cols {
			if c == 7 && int32(rr[8]) <= 0 {
				continue
			}
			if val[c] != rr[c] {
				mask |= 1 << uint(c)
			}
		}
		if mask != 0 {
			if v := os.Getenv("E13_VERDICT"); v != "" {
				os.WriteFile(v, []byte(fmt.Sprintf("div %d %d\n", e13Rows, mask)), 0644)
			}
			os.Exit(0)
		}
	}
	e13Rows++
}

// e13Finish writes the profile and the verdict and ends the process (gore itself never exits after the timedemo line).
func e13Finish() {
	if !e13Init {
		e13Setup()
	}
	if pf := os.Getenv("E13_PROFILE"); pf != "" {
		if f, err := os.Create(pf); err == nil {
			w := bufio.NewWriter(f)
			for i := range e13Counts {
				if e13Counts[i] != 0 {
					fmt.Fprintf(w, "F %d %d %d\n", i, e13Counts[i], e13First[i]-1)
				}
			}
			for i := range e13Site {
				if e13Site[i] != 0 {
					fmt.Fprintf(w, "S %d %d\n", i, e13Site[i])
				}
			}
			w.Flush()
			f.Close()
		}
	}
	if v := os.Getenv("E13_VERDICT"); v != "" {
		if _, err := os.Stat(v); err != nil {
			os.WriteFile(v, []byte(fmt.Sprintf("end %d\n", e13Rows)), 0644)
		}
	}
	E13Close()
	os.Exit(0)
}
