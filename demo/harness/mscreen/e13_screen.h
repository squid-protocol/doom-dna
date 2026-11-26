/* mutant-screen runtime (our code): a lesion is active when E13_MUT equals its id; per-function entry counters feed the dynamic profile */
extern int e13_mut_id;
extern unsigned e13_fcount[];
extern int e13_first[];
extern int gametic;
#define E13_ON(id) (e13_mut_id == (id))
static inline int e13_enter(int fid) { e13_fcount[fid]++; if (!e13_first[fid]) e13_first[fid] = gametic + 1; return 0; }
#define E13_ENTER(fid) int e13_e_##fid __attribute__((unused)) = e13_enter(fid)
