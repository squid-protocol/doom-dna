package gore

// DOOM-E13 per-tic digest for gore (our own code, added to the package in a work copy).
// Line format as the other engines: gametic leveltime prndindex rndindex x y z angle health armor readyweapon ammo0..3

import (
	"fmt"
	"os"
	"runtime"
	"strings"
)

var e13file *os.File

func e13Digest() {
	if e13file == nil {
		name := os.Getenv("E13_DIGEST")
		if name == "" {
			name = "e13_digest.txt"
		}
		f, err := os.Create(name)
		if err != nil {
			return
		}
		e13file = f
	}
	p := &players[consoleplayer]
	if p.Fmo == nil {
		return
	}
	m := p.Fmo
	fmt.Fprintf(e13file, "%d %d %d 0 %d %d %d %d %d %d %d %d %d %d %d\n", gametic, leveltime, prndindex,
		int32(m.Fx), int32(m.Fy), int32(m.Fz), uint32(m.Fangle), p.Fhealth, p.Farmorpoints, int32(p.Freadyweapon),
		p.Fammo[0], p.Fammo[1], p.Fammo[2], p.Fammo[3])
}

// E13Close flushes and closes the digest file.
func E13Close() {
	if e13file != nil {
		e13file.Close()
		e13file = nil
	}
}

var e13trace *os.File
var e13traceOff bool

// e13Trace logs "gametic caller prndindex" for every gameplay-RNG call (only when the build was patched to call it and $E13_TRACE is set).
func e13Trace() {
	if e13traceOff {
		return
	}
	if e13trace == nil {
		name := os.Getenv("E13_TRACE")
		if name == "" {
			e13traceOff = true
			return
		}
		f, err := os.Create(name)
		if err != nil {
			e13traceOff = true
			return
		}
		e13trace = f
	}
	pc, _, _, _ := runtime.Caller(2)
	fn := runtime.FuncForPC(pc).Name()
	if i := strings.LastIndex(fn, "."); i >= 0 {
		fn = fn[i+1:]
	}
	fmt.Fprintf(e13trace, "%d %s %d\n", gametic, fn, prndindex)
}
