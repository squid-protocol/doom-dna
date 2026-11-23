"""Adapter: add the columns the predictor/analysis expect to spike_truth.csv (a schema gap between the spike builder and the predictor).
Adds recipient_program (chocolate-spike-<donor>-<tier>), donor_func_id (the donor function's func_id in truth/functions.csv, matched by
name and path) and recipient_func_name (the renamed name). No predictor is run. Idempotent."""
import sys
import pandas as pd

S9 = "/srv/storage_16tb/projects/doom-e7-work/e9/results/spike"
T9 = "/srv/storage_16tb/projects/doom-e7-work/e9/results/truth"
st = pd.read_csv(f"{S9}/spike_truth.csv", dtype=str)
fn = pd.read_csv(f"{T9}/functions.csv", dtype=str, usecols=["program", "func_id", "name", "path"])
st["recipient_program"] = "chocolate-spike-" + st.donor + "-" + st.tier
st["recipient_func_name"] = st.renamed_func
look = {}
for p, i, n, pa in zip(fn.program, fn.func_id, fn.name, fn.path):
    look.setdefault((p, n, pa), i)  # first definition wins for #if variants of the same name in one file
ids, miss = [], 0
for d, n, f in zip(st.donor, st.orig_func, st.donor_file):
    v = look.get((d, n, f))
    if v is None:
        miss += 1
    ids.append(v if v is not None else "")
st["donor_func_id"] = ids
st.to_csv(f"{S9}/spike_truth.csv", index=False)
print(f"spike_truth rows {len(st)}; donor_func_id unmatched {miss}")
