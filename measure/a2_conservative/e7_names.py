"""DOOM-E7 name method: name keys, survival and the shared score (Amendment 1 §D, §E).

Registered rules, in one place so the stoplist, the scan matrices and the tests use the same key.

* ``name_key``: last component of a qualified name (``::`` or ``.``), lower-cased, non-alphanumerics removed.
  Destructors, ``operator*``, empty keys and keys under 3 characters give ``None`` (not a usable name).
* ``name_key_n2`` (variant N2): additionally strips a documented DOOM subsystem prefix, only when the stem has
  at least 6 characters (as ``measure/lineage.py`` does).
* ``survival_names(q, t)``: sum over keys of ``min(n_q, n_t)`` divided by the number of eligible functions of Q.
* ``wilson_lower``: Wilson 95% lower bound, shared with the structure method (METHOD.md §5).
"""

from __future__ import annotations

import collections
import math
import re
from collections.abc import Iterable

DOOM_PREFIXES = ("p", "r", "g", "d", "i", "v", "w", "z", "m", "s", "f", "hu", "st", "am", "wi", "net", "txt", "deh")
_QUAL = re.compile(r"::|\.")
_NONALNUM = re.compile(r"[^0-9a-z]")
_N2 = re.compile(r"^(" + "|".join(DOOM_PREFIXES) + r")_(.+)$")
MIN_KEY = 3
MIN_STEM_N2 = 6


def _norm(last: str) -> str | None:
    key = _NONALNUM.sub("", last.lower())
    return key if len(key) >= MIN_KEY else None


def name_key(name: str | None) -> str | None:
    if not name:
        return None
    last = _QUAL.split(name.strip())[-1]
    if last.startswith("~") or last.lower().startswith("operator"):
        return None
    return _norm(last)


def name_key_n2(name: str | None) -> str | None:
    if not name:
        return None
    last = _QUAL.split(name.strip())[-1]
    if last.startswith("~") or last.lower().startswith("operator"):
        return None
    m = _N2.match(last.lower())
    if m:
        stem = _norm(m.group(2))
        if stem is not None and len(stem) >= MIN_STEM_N2:
            return stem
    return _norm(last)


def key_counts(names: Iterable[str | None], key=name_key, stoplist: frozenset[str] = frozenset()) -> collections.Counter:
    c: collections.Counter = collections.Counter()
    for n in names:
        k = key(n)
        if k is not None and k not in stoplist:
            c[k] += 1
    return c


def matched(q: collections.Counter, t: collections.Counter) -> int:
    small, big = (q, t) if len(q) <= len(t) else (t, q)
    return sum(min(n, big[k]) for k, n in small.items() if k in big)


def survival_names(q: collections.Counter, t: collections.Counter, q_eligible: int | None = None) -> float:
    """Share of Q's eligible functions matched one-to-one by key in T (never above 1)."""
    n = q_eligible if q_eligible is not None else sum(q.values())
    return min(1.0, matched(q, t) / n) if n else 0.0


def wilson_lower(k: float, n: int, z: float = 1.959964) -> float:
    if n <= 0:
        return 0.0
    p = min(max(k / n, 0.0), 1.0)
    d = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - half) / d)


def shared_names(q: collections.Counter, t: collections.Counter) -> float:
    """Larger of the two directions' Wilson lower bounds of survival (METHOD.md §5, applied to names)."""
    nq, nt = sum(q.values()), sum(t.values())
    m = matched(q, t)
    return max(wilson_lower(m, nq), wilson_lower(m, nt))
