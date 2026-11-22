# `DOOM-E8`: Half-life snapshots: how name sharing and structure sharing change over a port's history, and whether a divergence date can be recovered

**Status: DRAFT, not registered. [Amendment 1](E8_AMENDMENT_1.md) (2026-11-22) reconciles two independent design reviews and supersedes the sections it names; read it with this file.** Registers when two independent design reviews are reconciled in a dated amendment and this file is committed before any E8 scan. Thresholds marked `[LOCK]` are proposals. Builds on `DOOM-E7` (draft PR #2: [protocol](https://github.com/squid-protocol/doom-dna/pull/2)); it reuses E7's engine pin, name key, stoplist, twin parameters and shared-score formula unchanged.

## 1. Why, and the owner's hypotheses

Every E7 number is taken at one commit per port: the pinned tip. This experiment looks back in time, in half-life steps, to see how each method's agreement with the source changes with a port's age. Hypotheses as the owner stated them:

* **H8.1 (names flat):** a port's name-sharing with `linuxdoom` stays roughly constant over its history.
* **H8.2 (structure rises toward the origin):** structure-sharing is highest near a port's first commit and decays with time, monotonically.
* **H8.3 (date estimation):** if the decay is regular enough, a copying date can be estimated from how far a port has diverged, so a port can be identified not only by shared code but by the **divergence between two code lines over time**.

Plausible alternatives that this design can also show: names decay too, only more slowly; decay comes in bursts, not smoothly (earlier work found rewriting comes in bursts); the "origin" of a repository is often an import date, not a copy date.

## 2. Corpus and snapshots

* **Histories:** the existing full (non-shallow) clones under `/srv/storage_16tb/projects/temporal-crucible-pool/doom-ports/<port>`, for the 44 manifest ports. Each port's head is its E7 pinned SHA (or `HEAD` where the pinned SHA is not in the clone; flagged).
* **Snapshots per port:** the last **first-parent** commit at or before each age fraction `f` of `(head date - origin date)` measured from the port's first commit, `f in {1, 1/2, 1/4, 1/8, 1/16, 1/32}`, plus the first commit itself (`f = 0`). Plan computed 2026-11-22 from the clones: `halflife/plan.csv`. **210 distinct commits** over 44 ports once duplicates (shared history, tiny repos) are merged. The plan file is committed before scanning and fixes every SHA.
* **Analysis ports (rule):** class `engine-port` with a declared parent in `declared_lineage.csv`, at least **100 first-parent commits** and a span of at least **2 years**. By the plan this gives `chocolate-doom`, `crispy-doom`, `doomretro`, `prboom-plus`, `dsda-doom`, `woof`, `nugget-doom`, `eternity`, `odamex`, `gzdoom`, `srb2`, `fastdoom`, `edge-classic`, `inter-doom`. `managed-doom` (C#) is a cross-language case, reported separately. Ports under the rule's thresholds are listed and not scored (most have under 60 commits or under 2 years: `gore`, `mochadoom`, `puredoom`, `doom-wasm`, ...).
* **Negative controls with history:** `helion`, `rust-doom` (from scratch), `freedoom` (assets). Expected: no descent at any age.
* **Scans:** each distinct commit is exported with `git archive` and scanned by the E7 engine commit `704cb35f0`; `scope.csv` pruning applies where the directories exist at that commit. Fingerprints use sfs `bcd3cb7`, spec `f5d525ed16bc91db`, as E7.

## 3. Measurements (identical rules to E7)

For each snapshot `s` of port `P` and for each reference `R`:
* **References.** `R1` = `linuxdoom` at its E7 pin (the common 1997 source, constant). `R2` = `P`'s declared parent at its E7 pinned head (constant; for `P` whose parent is `linuxdoom` this equals `R1`).
* **Survival of the reference's code in the snapshot**, per method: `surv_names(R -> s)` and `surv_struct(R -> s)` (either-direction twins), over the reference's eligible functions (loc at least 6), one-to-one, exactly as E7. This is the "half-life" quantity: the share of `linuxdoom`'s code still present at age `a`.
* **Shared** (`max` over directions of the Wilson lower bound) with the decoy certification for names and `fdr 0.01` for structure, floor 2%. A snapshot with **fewer than 100 eligible functions** is flagged underpowered and **excluded from trend tests** (listed).
* **Eligible-function duplicates.** The E7 rule had no de-duplication; E8 reports, per snapshot, the share of eligible functions in an exact-digest duplicate group, and runs the trend tests **with and without** snapshots above 25% duplicates.

## 4. Tests

**H8.1 and H8.2 (per port, trend over snapshots with at least 100 eligible functions; at least 4 such snapshots required to score a port):**
* Kendall's `tau` between age (years since first commit) and `surv_struct(R1 -> s)`; same for names. Exact p-value; ports with fewer than 4 usable snapshots are listed.
* **Summary across ports:** the median `tau` for each method and a sign test over ports (how many ports have `tau < 0` for structure; how many have `|tau|` small for names), with exact 95% intervals.
* **Predictions `[LOCK]`:**
  * `H8.1`: names: the median over ports of `surv_names(f = 1/32) - surv_names(head)` lies within ±0.10, and fewer than half of the ports have a significant (p < 0.05) trend.
  * `H8.2`: structure: median `tau` (age against survival) at most -0.6, and the share of ports with `tau < 0` at least 70%; `surv_struct(f = 1/32) - surv_struct(head)` at least +0.10 for at least 70% of the scored ports.
* **Functional form (descriptive):** fit `S(a) = S0 * exp(-lambda * a)` and a two-phase alternative per port; report `lambda` (per year) with a bootstrap interval, the rate heterogeneity across ports, and whether decay is smooth or burst-like (largest single step as a share of total loss).

**H8.3 date estimation (two parts, both descriptive with a registered decision rule):**
* **(a) Age from the head alone.** Leave one port out; take the median `lambda` of the others; from the held-out port's head survival `S_head`, estimate age `a_hat = ln(S0 / S_head) / lambda_median` (with `S0` = the median origin survival over the other ports). Compare with the true age since the first commit. Rule `[LOCK]`: **supported** if the Spearman correlation between `a_hat` and true age across scored ports is at least 0.6 and the median absolute error is at most 50% of the true age; otherwise **not supported** (reported either way, per method).
* **(b) Divergence date between a child and its parent, with exact ground truth.** For child/parent pairs whose clones share commits, the fork date is the last shared first-parent commit (`crispy-doom`/`chocolate-doom` 2013-12-09; `dsda-doom`/`prboom-plus` 2020-11-09; `nugget-doom`/`woof` 2021-08-31; `kocoa-doom`/`mochadoom` 2019-07-20; others by the same rule). Take the child and parent commit at or before each date on a **common yearly grid** around the fork (extra scans, added to the plan file before scanning), compute `shared(child@t, parent@t)` per method, and locate the change-point (largest drop, single change-point fit with a bootstrap interval). Rule `[LOCK]`: **recovered** if the estimated date is within ±1 year of the git ground truth; report per pair and per method (names vs structure).

**Controls:** `helion`, `rust-doom`, `freedoom`: `shared` with `linuxdoom` below the floor at every usable snapshot, under both methods (false attachment is any snapshot at or above the floor).

## 5. Primary endpoints and corrections

Primary: `H8.2` (structure trend) and `H8.3(a)` (date from head), each per method, Holm-corrected across these four tests. Everything else (names flatness, functional form, change-point recovery, controls) is descriptive and reported either way.

## 6. Disclosure, limits and what this cannot show

* **The first commit is not the copy date.** Several clones start at an import (`linuxdoom` 2012; `prboom-plus` 2000 from CVS; Chocolate and Crispy share their 2005 start). The estimated quantity is *age since this repository's first commit*; a copy date has ground truth only where shared git history shows a fork point (part b).
* Ports with few commits give few distinct snapshots and tiny early repositories (fewer than 100 functions) are excluded from trend tests; early snapshots may be underpowered by construction.
* Time fractions are calendar-based; a **commit-count** version (same fractions of the number of first-parent commits) is run as a sensitivity.
* Rates differ between ports and come in bursts, so a single decay constant may not exist; H8.3(a) tests exactly that.
* Four to five ground-truth fork pairs is a small validation set; intervals will be wide.
* Names and structure are both measured against `linuxdoom` as a fixed reference; a port that diverges from `linuxdoom` by following a different parent is read through `R2` as well.
* No third-party source or WAD data is committed; scans and clones stay outside the repository, hashed in the run manifest.

## 7. Order of work

1. Reviews and amendment; commit `plan.csv`, the pair list for part (b), the analysis scripts and tests.
2. Pin: engine `704cb35f0`, sfs `bcd3cb7`, snapshot SHAs; write the run manifest.
3. Export and scan every commit; fingerprint; compute survival and shared per snapshot.
4. Analysis; manifest hash committed before any figure is made.
