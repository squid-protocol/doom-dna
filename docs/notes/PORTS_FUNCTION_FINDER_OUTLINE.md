# Outline: what the ports taught us, as an interactive function finder (2026-11-25)

**Idea.** Replace "one big claim" with a lookup: pick a function from `linuxdoom`, see what each port did with it and **which route found it**. The page itself demonstrates the E12 result.

## What the page shows for a function and a port
* The matched function in that port (or "no reliable match"), with its **evidence tier**: exact clone / fingerprint twin / graph seed / extension (reach only, lower confidence).
* The port's **gate status** (coherent or not) so a user knows whether extension pairs can be trusted at all.
* Where truth exists: text-similarity band (same-language) or name-key agreement (translations), shown as a check, never as the matcher.
* Unrelated programs (lua, nginx, curl, ...) in a "controls" row: what the method says there, so the user can see it say little or nothing.

## Port groups and what each teaches
1. **Close same-language ports** (doomgeneric, sdl-doom, doom-ascii, puredoom, mood): fingerprints find most functions with high precision; extension adds little.
2. **Evolved C/C++ ports** (crispy, woof, prboom-plus, eternity, odamex, srb2, edge-classic, doomretro, dsda): fewer twins as divergence grows; the truth gets thin; the gate rejects the three most diverged. Show honestly as "few reliable matches".
3. **Translations with surviving call-graph shape** (gore/Go, doom-scheme, dartdoom): fingerprints find nothing; seeds do; extension reaches further at lower precision.
4. **Java** (mochadoom): fingerprints work, the graph does not.
5. **C# and Kotlin** (managed-doom, kocoa-doom): no route works; present as an open problem, not as "kept nothing".
6. **Controls:** extension fills its quota anyway; the gate and the tier labels are what keep the page honest.
7. **Horizontal transfers** (E9, E9p): pairs between ports that do not go through `linuxdoom`; take the numbers and cutoff choice from the claims register, not from memory.

## Data needed (not all of it exists yet)
* **Exists:** E12 per-program lists for E3c, G2 and S (`results/e12/lists_*.json`), tables, audit ratings; `article/data.json` (famous functions, families, fates, horizontal transfers).
* **Must be exported:** fingerprint twin lists (F0, F1c) per port, which E12 scored but did not save; tier labels; gate status; per-pair text-similarity band. Estimated size a few MB for about 25 programs.

## What to do with the existing material
* **Call-graph subsystem map (now merged):** keep as a *methods* artifact (move its home to the methods paper; link from the finder). It shows how subsystems were discovered; it is not evidence that translations kept architecture.
* **"Compare the wiring" chart (hand taxonomy):** keep as a descriptive view with its chance floor; remove any wording that presents it as a third independent line of evidence.
* **"Follow a function", "Explore all 54":** become the first versions of the finder's search and detail panels; "Names lie" and "The blind test" stay as the framing sections.
* **Two overreaching sentences** ("Structural DNA survives cross-language translation"; "Java, Kotlin and C# kept none") should change: E12 shows Java matches by fingerprints, and C# is unresolved.
