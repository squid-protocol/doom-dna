# DOOM-E9 spike-in recipe (fixed before any computation)

**Tools pinned:** `clang-format 18.1.8` from `doom-e7-work/e9/venv` (`--style=LLVM` with the configuration stored as `manifest/e9_clang_format.yaml`), Python 3 with a fixed seed `20261122`; `ctags` for definitions.

**Donors (absent from the recipient and from every other corpus program):**
* **Large module (about 150 eligible functions):** from `curl` at its E7 pin: the files of `lib/` taken in alphabetical order until at least 150 eligible functions (loc at least 6) are reached.
* **Small module (about 50 eligible functions):** from `libuv` at its E7 pin: the files of `src/unix/` taken in alphabetical order until at least 50 eligible functions are reached.
`curl` and `libuv` are therefore **donor sources and are not negative controls**.

**Recipient:** a scratch copy (outside the repository) of `chocolate-doom` at its E7 pin with the scope pruning of E7; the donor files are added under a new directory `spike/`.

**Tiers (cumulative where stated):** (a) verbatim; (b) functions renamed at 50% and at 100% of definitions, with every call site updated (word-boundary replacement of each renamed function in the donor files); (c) 100% renamed + comments stripped + `clang-format` as pinned; (d) light refactor on top of (c): reorder function definitions within each file and wrap single-call helpers... (specific local rewrites listed by the builder before use and committed); (e) partial module: a deterministic 30% subset of the functions (with their call sites left valid).

**Renaming scheme:** each function name `f` becomes `s9_<8 hex chars of sha1(seed + f)>`, preserving nothing of the original token; macros and struct members are untouched.

**Truth:** the exact mapping from original to renamed function is written by the builder, so recall is exact by construction.
