import pandas as pd, numpy as np, subprocess, io, sys, ast, re
def head(p): return pd.read_csv(io.StringIO(subprocess.check_output(["git","show","HEAD:"+p],text=True)))
TIME={"t_zx","t_tket","t_total","t_wall","t_sim","wall_s","t_check"}
def cmp(name,new,old,keys):
    old=old.copy(); new=new.copy()
    m=new.merge(old,on=keys,how="inner",suffixes=("_new","_old"))
    print(f"\n## {name}: new rows {len(new)}, committed rows {len(old)}, matched {len(m)}")
    cols=[c for c in new.columns if c not in keys and c in old.columns]
    diffs=[]
    for c in cols:
        a,b=m[c+"_new"],m[c+"_old"]
        tag="time" if (c in TIME or c.startswith("t_")) else ""
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b) and not pd.api.types.is_bool_dtype(a) and not pd.api.types.is_bool_dtype(b):
            a=a.astype(float); b=b.astype(float)
            both_nan=a.isna()&b.isna()
            d=(a-b).abs()[~both_nan]
            nanmis=int((a.isna()^b.isna()).sum())
            mx=float(d.max()) if len(d) and d.notna().any() else 0.0
            if mx>0 or nanmis: diffs.append((c,tag,f"max abs diff {mx:.3g}, rows differing {int((d>0).sum())}, NaN mismatches {nanmis}"))
        else:
            ne=int((a.astype(str)!=b.astype(str)).sum())
            if ne: diffs.append((c,tag,f"{ne} rows differ (non-numeric)"))
    if not diffs: print("all shared columns identical")
    for c,t,s in diffs: print(f"- {c}{' [timing]' if t else ''}: {s}")
r=lambda p: pd.read_csv(p)
cmp("family_A_counts.csv (tfim rows regenerated, merged)", r("results/family_A_counts.csv"), head("results/family_A_counts.csv"), ["file","pipeline"])
cmp("family_A_summary.csv", r("results/family_A_summary.csv"), head("results/family_A_summary.csv"), [c for c in ["model","n","r","disorder","pipeline"] if c in r("results/family_A_summary.csv").columns])
cmp("family_B1x_counts.csv", r("results/family_B1x_counts.csv"), head("results/family_B1x_counts.csv"), ["file","pipeline"])
cmp("family_B1x_summary.csv", r("results/family_B1x_summary.csv"), head("results/family_B1x_summary.csv"), ["file"] if "file" in r("results/family_B1x_summary.csv").columns else list(r("results/family_B1x_summary.csv").columns[:1]))
cmp("family_B1_repro_counts.csv vs committed family_B1_counts.csv (14 circuits, hwb8 excluded)", r("results/family_B1_repro_counts.csv"), head("results/family_B1_counts.csv"), ["file","pipeline"])
cmp("family_B2_counts (P0ref,P0,P3) vs committed", r(sys.argv[1]), head("results/family_B2_counts.csv"), ["file","pipeline"])
cmp("family_A_proxy_h22e.csv", r("results/family_A_proxy_h22e.csv"), head("results/family_A_proxy_h22e.csv"), ["file","pipeline"])
cmp("family_B1_proxy_h22e.csv", r("results/family_B1_proxy_h22e.csv"), head("results/family_B1_proxy_h22e.csv"), ["file","pipeline"])
rows=[ast.literal_eval(l) for l in open(sys.argv[2]) if l.startswith("{'family'")]
cmp(f"certificates (rows printed before timeout)", pd.DataFrame(rows), head("results/certificates.csv"), ["family","file"])
