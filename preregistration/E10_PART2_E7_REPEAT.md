# DOOM-E10 part 2: repeat of the E7 structural arm on canonically normalised source

**Status: written 2026-11-23, before any normalised scan was read or analysed.** Exploratory-confirmatory: the hypothesis comes from the owner and was generated after E7, E8 and the E10 format audit, so this is a test of a post hoc idea, not independent confirmation of E7.

## Question
The owner's reading: the low structural detection of some ports in E7 (and the flat low curves in E8) may come partly from formatting differences between ports, not only from rewritten code. E10 development showed that reformatting, extra blank lines and edited comments defeat the plain scan (recall 0.00 to 0.53) and that a canonical normalisation before scanning restores it (0.90 to 0.94) on constructed copies. Does the same normalisation change the E7 results on the real ports?

## What is held fixed and what changes
* Fixed: the 66 programs, their E7 pins and scope rules (`manifest/RUN_PINS.json`, `scope.csv`), the engine (`704cb35f0`), sfs, the `structure` lens, the E7 twin machinery and analysis code (copied unchanged; only the work directory differs), the names arm (unchanged by definition; names are read from the same engine output).
* Changed: for every program, every C-family source file (`.c .h .cc .cpp .hpp .cxx .hh`) is normalised before the scan: comments removed, blank lines removed, `clang-format` 18.1.8 with `manifest/e10_canon_clang_format.yaml`. Programs with no C-family file reuse E7's scan.
* The "either" rule from E10 development (flag if plain or normalised certifies) is **not** used here: E7's analysis is a single-scan pipeline. The result is therefore normalised against plain, with E7's published plain numbers as the comparator.

## Predictions (stated before seeing the data; direction and rough size)
* **P1:** the number of programs with detectable structural descent (2% floor; E7: 25 of 51) does not fall and rises by at least 3.
* **P2:** for same-language C-family ports, shared structure with their declared nearest relatives rises or stays equal in most ports (at least 70% of those detectable in both).
* **P3 (expected to NOT change):** translations (`cpp-doom` from Crispy, `gore`) stay at their E7 level. Formatting cannot explain a language change. If they rise, that is a surprise to report.
* **P4 (controls):** the unrelated programs (`nginx`, `leveldb`, `curl`, `libuv`) stay below the floor; `quake` and `quake2` may rise slightly from 0.02.
* **P5:** rank agreement with the name-blind text survival (E7 Spearman 0.87) does not fall by more than 0.05.
* **P6 (honest doubt):** the net effect on the nearest-is-family rate (E7 0.62) is small (within 0.05) because most low ports are low from rewriting, not from layout. A large rise would support the owner's reading; no change would reject it for most ports.

## Reporting
Per program: E7 plain structural share versus normalised, the change, with the E7 floor and the same bootstrap rules; the headline E7 quantities side by side; a list of which ports moved by more than 0.05. Failures of any prediction are reported as such. Normalisation failures (files `clang-format` cannot parse) are counted and listed.

## Limits
* clang-format is a C-family formatter; ports in other languages are unchanged, so for them the result is identical to E7 by construction.
* Normalisation can change function boundaries in macro-heavy code; scan and function counts per program are reported before and after.
* Third-party source is not committed; only measurements and hashes.
