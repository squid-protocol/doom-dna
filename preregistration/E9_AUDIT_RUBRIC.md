# DOOM-E9 hand-audit rubric (fixed before any rater sees a pair; 2026-11-22)

**Raters:** two independent **model raters** (a Claude subagent and Gemini), each given the same blinded packets and this rubric, with no access to either predictor's output, the Jaccard score, the program names or the truth classes. This is a weaker substitute for human raters and is reported as such.

**Sample:** 50 pairs from the T1-confirmed set (Jaccard at least 0.9, eligible, drawn at random with a fixed seed) and 50 predicted pairs that T1 did **not** confirm (drawn at random from pairs emitted by the structure or names predictor with Jaccard below 0.9), 100 in all, shuffled, with a packet id that reveals nothing.

**What the rater sees:** the two function bodies (source text with comments left in), their file extensions and line counts. Nothing else.

**Question:** do these two functions look like **the same code, copied or derived from one source**, as opposed to two independent implementations of a similar task?

**Labels (choose exactly one):**
* **COPY**: same logic and the same structure statement for statement, differing at most in names, formatting, comments or small local edits. A reader would conclude one was derived from the other or both from a common source.
* **INDEPENDENT**: same or similar purpose but different logic, structure or statement order; similarity is explained by the task.
* **TRIVIAL**: too short or too generic to tell (a one-line getter or wrapper, a bare accessor, an obvious idiom) so that copying cannot be judged.

**Scoring:** a pair counts as audited-positive if **both** raters say COPY; audited-negative if **both** say INDEPENDENT; otherwise it is **disputed** and excluded from the co-primary truth and counted. Inter-rater agreement (Cohen's kappa) is reported. TRIVIAL from either rater excludes the pair from the audit but not from T1.
