"""Build manifest/name_stoplist.txt (Amendment 1 §D3): name keys present in at least 1% of non-DOOM repositories
of the GitGalaxy population corpus. Run once, before any E7 scan. Read-only on the corpus database."""

import collections
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e7_names import name_key  # noqa: E402

DB = "/srv/storage_16tb/projects/gitgalaxy-population-analyses/data/master_db_v2.9.0.db"
SKIP = ("doom", "quake", "chocolate", "prboom", "zdoom", "linuxdoom", "wolf3d")  # corpus repos that are DOOM-family
MIN_SHARE = 0.01


def main(out):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    per_repo = collections.defaultdict(set)
    q = ("select f.repo_name, fn.func_name from function_data fn join file_data f on f.id = fn.file_id "
         "where fn.func_name is not null")
    for repo, name in con.execute(q):
        if any(s in repo.lower() for s in SKIP):
            continue
        k = name_key(name)
        if k:
            per_repo[repo].add(k)
    n = len(per_repo)
    df = collections.Counter(k for s in per_repo.values() for k in s)
    stop = sorted(k for k, c in df.items() if c / n >= MIN_SHARE)
    Path(out).write_text(
        f"# name stoplist: keys present in >= {MIN_SHARE:.0%} of {n} non-DOOM repositories of master_db_v2.9.0\n"
        + "\n".join(stop) + "\n")
    print(n, "repos;", len(stop), "stop keys")


if __name__ == "__main__":
    main(sys.argv[1])
