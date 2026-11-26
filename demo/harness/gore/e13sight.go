package gore

import (
	"fmt"
	"os"
)

var e13sight *os.File
var e13sightOff bool

// p_CheckSight wraps the original (renamed in the work copy) and logs "gametic type1 x1 y1 x2 y2 type2 result".
func p_CheckSight(t1 *mobj_t, t2 *mobj_t) boolean {
	r := p_CheckSight_orig(t1, t2)
	if e13sightOff {
		return r
	}
	if e13sight == nil {
		name := os.Getenv("E13_SIGHT")
		if name == "" {
			e13sightOff = true
			return r
		}
		f, err := os.Create(name)
		if err != nil {
			e13sightOff = true
			return r
		}
		e13sight = f
	}
	fmt.Fprintf(e13sight, "%d %d %d %d %d %d %d %d\n", gametic, int32(t1.Ftype1), int32(t1.Fx), int32(t1.Fy), int32(t2.Fx), int32(t2.Fy), int32(t2.Ftype1), int32(r))
	return r
}
