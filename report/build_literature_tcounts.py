import csv, sys
import pandas as pd
ROOT = "/home/claude/sgc-zx"
ours = {}
for fam, f in [("B1", "family_B1_counts.csv"), ("B1x", "family_B1x_counts.csv")]:
    d = pd.read_csv(f"{ROOT}/results/{f}"); d = d[d.pipeline == "P2"]
    for r in d.itertuples():
        ours[r.file.replace(".qasm", "")] = (fam, int(r.n), int(r.t_count_as_written), int(r.t_count_zx))
S = {
 "AMM2014_Tpar": ("Amy, Maslov, Mosca 2014 (Tpar)", "1303.2042v2", "Table 1", "x'T", "yes", "caption: 'using no extra ancillae'"),
 "AM2016_Tpar": ("Amy, Mosca 2016 (T-par)", "1601.07363v2", "Table II", "T-par", "yes", "KvdW 2020 Table 1 caption counts Tpar and RM results as ancilla-free"),
 "AM2016_RMmaj": ("Amy, Mosca 2016 (RM majority)", "1601.07363v2", "Table II", "majority", "yes", "KvdW 2020 Table 1 caption counts Tpar and RM results as ancilla-free"),
 "AM2016_RMrec": ("Amy, Mosca 2016 (RM recursive)", "1601.07363v2", "Table II", "recursive", "yes", "KvdW 2020 Table 1 caption counts Tpar and RM results as ancilla-free"),
 "Nam2018_L": ("Nam et al. 2018 (Light)", "1710.07345v2", "Table 4", "Our Post-Optimization (L) t", "yes", "text: optimizer adds no two-qubit interactions"),
 "Nam2018_H": ("Nam et al. 2018 (Heavy)", "1710.07345v2", "Table 4", "Our Post-Optimization (H) t", "yes", "text: optimizer adds no two-qubit interactions"),
 "TODD2018": ("Heyfron, Campbell 2018 (TODD)", "1712.01557v3", "Table I", "TODD T", "no", "uses nh Hadamard ancillas (Table I column nh)"),
 "TODDpart2018": ("Heyfron, Campbell 2018 (TODD-part)", "1712.01557v3", "Table II", "TODD-part T", "yes", "caption: 'Hadamard-bounded partitions rather than Hadamard gadgets and ancillas'"),
 "KvdW2020_PyZX": ("Kissinger, van de Wetering 2020 (PyZX)", "1903.10477v3", "Table 1", "PyZX", "yes", "text line 123: 'we target ancilla-free optimisation'"),
 "KvdW2020_PyZXTODD": ("Kissinger, van de Wetering 2020 (PyZX+TODD)", "1903.10477v3", "Table 1", "PyZX+TODD", "yes", "text line 123: 'we target ancilla-free optimisation'"),
 "AQ2024": ("Ruiz et al. 2024 (AlphaTensor-Quantum, no gadgets)", "2402.14396v2", "Table 2", "T-count without gadgets, AlphaTensor-Quantum", None, "ancilla-free only where #Qubits Compiled equals Original"),
}
# rows: circuit, key, paper_label, paper_n, paper_T_original, published_t, extra note, ancilla override (compiled qubits for AQ, nh for TODD)
R = []
def add(c, k, lab, pn, pt, t, note="", extra=None): R.append((c, k, lab, pn, pt, t, note, extra))
# --- AMM 2014 Table 1 (N, xT, x'T)
for c, lab, n, t0, t in [("mod5_4","Mod 54",5,28,16),("vbe_adder_3","VBE-Adder3",10,70,24),("csla_mux_3","CSLA-MUX3",15,70,62),
    ("rc_adder_6","RC-Adder6",14,77,63),("mod_red_21","Mod-Red21",11,119,73),("mod_mult_55","Mod-Mult55",9,49,37),
    ("barenco_tof_3","Λ3(X) – [3] (Barenco)",5,28,16),("tof_3","Λ3(X) – [24] (Nielsen-Chuang)",5,21,15),
    ("barenco_tof_4","Λ4(X) – [3] (Barenco)",7,56,28),("tof_4","Λ4(X) – [24] (Nielsen-Chuang)",7,35,23),
    ("barenco_tof_5","Λ5(X) – [3] (Barenco)",9,84,40),("tof_5","Λ5(X) – [24] (Nielsen-Chuang)",9,49,31),
    ("barenco_tof_10","Λ10(X) – [3] (Barenco)",19,224,100),("tof_10","Λ10(X) – [24] (Nielsen-Chuang)",19,119,71),
    ("gf2_pow_4_mult","GF(2^4)-Mult",12,112,68),("gf2_pow_5_mult","GF(2^5)-Mult",15,175,111),("gf2_pow_6_mult","GF(2^6)-Mult",18,252,150)]:
    add(c, "AMM2014_Tpar", lab, n, t0, t, "Nam et al. Table 4 footnote a reports the t-par output circuit for CSLA-MUX3 as incorrect" if c=="csla_mux_3" else "")
# --- AM 2016 Table II (n, original, T-par, majority, recursive)
am = [("grover_5","Grover5",9,140,52,52,52),("mod5_4","Mod 54",5,28,16,16,16),("vbe_adder_3","VBE-Adder3",10,70,24,24,24),
  ("csla_mux_3","CSLA-MUX3",15,70,62,62,58),("rc_adder_6","RC-Adder6",14,77,63,47,47),("mod_red_21","Mod-Red21",11,119,73,73,73),
  ("mod_mult_55","Mod-Mult55",9,49,37,35,35),("hwb6","HWB6",7,105,71,75,75),("hwb8","HWB8",12,5887,3551,3531,3531),
  ("gf2_pow_4_mult","GF(2^4)-Mult",12,112,68,68,68),("gf2_pow_5_mult","GF(2^5)-Mult",15,175,111,111,101),
  ("gf2_pow_6_mult","GF(2^6)-Mult",18,252,150,150,144),("ham15-low","Hamming15 (low)",17,161,97,97,97),
  ("ham15-med","Hamming15 (med)",17,574,230,230,230),("qft_4","QFT4",5,69,67,67,67),
  ("barenco_tof_3","Λ3(X) – [43] (Barenco)",5,28,16,16,16),("tof_3","Λ3(X) – [24] (Nielsen-Chuang)",5,21,15,15,15),
  ("barenco_tof_4","Λ4(X) – [43] (Barenco)",7,56,28,28,28),("tof_4","Λ4(X) – [24] (Nielsen-Chuang)",7,35,23,23,23),
  ("barenco_tof_5","Λ5(X) – [43] (Barenco)",9,84,40,40,40),("tof_5","Λ5(X) – [24] (Nielsen-Chuang)",9,49,31,31,31),
  ("barenco_tof_10","Λ10(X) – [43] (Barenco)",19,224,100,100,100),("tof_10","Λ10(X) – [24] (Nielsen-Chuang)",19,119,71,71,71)]
for c, lab, n, t0, a, b, d in am:
    nt = "HWB6 majority 75 exceeds T-par 71 although the text says majority never exceeds T-par; KvdW Table 1 lists Tpar 75 for hwb6" if c=="hwb6" else ""
    if c=="grover_5": nt = "paper footnote 3: 4 Grover iterations with a fixed 5-bit oracle; original T 140 differs from our 336"
    add(c,"AM2016_Tpar",lab,n,t0,a,nt); add(c,"AM2016_RMmaj",lab,n,t0,b,nt); add(c,"AM2016_RMrec",lab,n,t0,d,nt)
# --- Nam 2018 Table 4 (pre-opt t, L t, H t or None)
for c, lab, t0, L, H in [("mod5_4","Mod 54",28,16,None),("vbe_adder_3","VBE-Adder3",70,24,None),("csla_mux_3","CSLA-MUX3",70,64,64),
  ("rc_adder_6","RC-Adder6",77,47,47),("mod_red_21","Mod-Red21",119,73,73),("mod_mult_55","Mod-Mult55",49,35,None),
  ("barenco_tof_3","Toff-Barenco3",28,16,16),("tof_3","Toff-NC3",21,15,None),("barenco_tof_4","Toff-Barenco4",56,28,28),
  ("tof_4","Toff-NC4",35,23,None),("barenco_tof_5","Toff-Barenco5",84,40,40),("tof_5","Toff-NC5",49,31,None),
  ("barenco_tof_10","Toff-Barenco10",224,100,100),("tof_10","Toff-NC10",119,71,None),
  ("gf2_pow_4_mult","GF(2^4)-Mult",112,68,None),("gf2_pow_5_mult","GF(2^5)-Mult",175,115,None),("gf2_pow_6_mult","GF(2^6)-Mult",252,150,None)]:
    add(c,"Nam2018_L",lab,None,t0,L)
    if H is not None: add(c,"Nam2018_H",lab,None,t0,H)
# --- TODD Table I (n, pre T, TODD T, nh) and TODD-part Table II (n, pre T, T)
todd = [("mod5_4","Mod 54",5,28,16,6),("csla_mux_3","CSLA-MUX3",16,70,52,17),("gf2_pow_4_mult","GF(2^4)-mult",12,112,54,7),
  ("gf2_pow_5_mult","GF(2^5)-mult",15,175,87,9),("gf2_pow_6_mult","GF(2^6)-mult",18,252,126,11),("grover_5","Grover5",9,52,44,23),
  ("ham15-low","Hamming15 (low)",17,161,75,34),("ham15-med","Hamming15 (med)",17,574,162,85),("hwb6","HWB6",7,105,51,24),
  ("mod_mult_55","Mod-Mult55",9,49,17,10),("mod_red_21","Mod-Red21",11,119,55,17),("qft_4","QFT4",5,69,55,39),
  ("rc_adder_6","RC-Adder6",14,77,37,21),("tof_3","NC Toff4 (Table I label)",5,21,13,2),("tof_4","NC Toff5 (Table I label)",7,35,19,4),
  ("tof_5","NC Toff6 (Table I label)",9,49,25,6),("tof_10","NC Toff10",19,119,55,16),("barenco_tof_3","Barenco Toff4 (Table I label)",5,28,14,3),
  ("barenco_tof_4","Barenco Toff5 (Table I label)",7,56,24,7),("barenco_tof_5","Barenco Toff6 (Table I label)",9,84,34,11),
  ("barenco_tof_10","Barenco Toff10",19,224,84,31),("vbe_adder_3","VBE-Adder3",10,70,20,4)]
for c, lab, n, t0, t, nh in todd:
    nt = f"nh = {nh} Hadamard ancillas"
    if "Table I label" in lab: nt += "; matched by (n, Pre-Opt T) because Table I and Table II label the same circuit differently"
    add(c,"TODD2018",lab,n,t0,t,nt,nh)
tp = [("mod5_4","Mod 54",5,28,18),("csla_mux_3","CSLA-MUX3",16,70,62),("gf2_pow_4_mult","GF(2^4)-mult",12,112,56),
  ("gf2_pow_5_mult","GF(2^5)-mult",15,175,90),("gf2_pow_6_mult","GF(2^6)-mult",18,252,132),("grover_5","Grover5",9,52,52),
  ("ham15-low","Hamming15 (low)",17,161,113),("ham15-med","Hamming15 (med)",17,574,322),("hwb6","HWB6",7,105,82),
  ("hwb8","HWB8",12,5887,4187),("mod_mult_55","Mod-Mult55",9,49,28),("mod_red_21","Mod-Red21",11,119,85),("qft_4","QFT4",5,69,67),
  ("rc_adder_6","RC-Adder6",14,77,59),("tof_3","NC Toff3",5,21,15),("tof_4","NC Toff4",7,35,23),("tof_5","NC Toff5",9,49,31),
  ("tof_10","NC Toff10",19,119,71),("barenco_tof_3","Barenco Toff3",5,28,22),("barenco_tof_4","Barenco Toff4",7,56,38),
  ("barenco_tof_5","Barenco Toff5",9,84,54),("barenco_tof_10","Barenco Toff10",19,224,134),("vbe_adder_3","VBE-Adder3",10,70,36)]
for c, lab, n, t0, t in tp: add(c,"TODDpart2018",lab,n,t0,t)
# --- KvdW 2020 Table 1 (n, T, PyZX, PyZX+TODD)
kv = [("barenco_tof_3","barenco-tof3",5,28,16,16),("mod5_4","mod54",5,28,8,7),("tof_3","tof3",5,21,15,15),
  ("barenco_tof_4","barenco-tof4",7,56,28,28),("hwb6","hwb6",7,105,75,72),("tof_4","tof4",7,35,23,23),
  ("barenco_tof_5","barenco-tof5",9,84,40,40),("mod_mult_55","mod-mult-55",9,49,35,20),("tof_5","tof5",9,49,31,31),
  ("vbe_adder_3","vbe-adder3",10,70,24,24),("mod_red_21","mod-red-21",11,119,73,73),("gf2_pow_4_mult","gf(2^4)-mult",12,112,68,52),
  ("hwb8","hwb8",12,5887,3517,3501),("rc_adder_6","rc-adder6",14,77,47,47),("csla_mux_3","csla-mux3",15,70,62,45),
  ("gf2_pow_5_mult","gf(2^5)-mult",15,175,115,86),("ham15-low","ham15-low",17,161,97,97),("ham15-med","ham15-med",17,574,212,212),
  ("gf2_pow_6_mult","gf(2^6)-mult",18,252,150,122),("barenco_tof_10","barenco-tof10",19,224,100,100),("tof_10","tof10",19,119,71,71)]
for c, lab, n, t0, a, b in kv:
    add(c,"KvdW2020_PyZX",lab,n,t0,a); add(c,"KvdW2020_PyZXTODD",lab,n,t0,b)
# --- AlphaTensor-Quantum Table 2 (original qubits, compiled qubits or None for split, T without gadgets)
aq = [("barenco_tof_3","Barenco Toff3",5,8,13),("barenco_tof_4","Barenco Toff4",7,14,23),("barenco_tof_5","Barenco Toff5",9,20,33),
  ("barenco_tof_10","Barenco Toff10",19,50,83),("csla_mux_3","CSLA-MUX3",15,21,39),("gf2_pow_4_mult","GF(2^4)-mult",12,12,39),
  ("gf2_pow_5_mult","GF(2^5)-mult",15,15,59),("gf2_pow_6_mult","GF(2^6)-mult",18,18,77),("grover_5","Grover5",9,None,152),
  ("ham15-low","Hamming15 (low)",17,42,73),("ham15-med","Hamming15 (med)",17,None,156),("hwb6","HWB6",7,27,51),
  ("mod_mult_55","Mod-Mult55",9,11,17),("mod_red_21","Mod-Red21",11,28,51),("mod5_4","Mod 54",5,5,7),("qft_4","QFT4",5,43,53),
  ("rc_adder_6","RC-Adder6",14,24,37),("tof_3","NC Toff3",5,7,13),("tof_4","NC Toff4",7,11,19),("tof_5","NC Toff5",9,15,25),
  ("tof_10","NC Toff10",19,35,55),("vbe_adder_3","VBE-Adder3",10,14,19)]
for c, lab, n, comp, t in aq:
    nt = "split into sub-circuits (★), compiled qubit count not given" if comp is None else f"compiled qubits {comp} (Hadamard gadgetization)"
    if c == "grover_5": nt += "; circuit taken from Amy's set whose Grover5 has original T 140 in arXiv:1601.07363 Table II"
    add(c,"AQ2024",lab,n,None,t,nt,comp)
cols = ["circuit","family","n","t_written","t_zx_P2","source_key","source","arxiv","table","column","paper_label","paper_n",
        "paper_t_original","published_t","ancilla_free","same_circuit","read_from_fetched_text","reported_error","note"]
w = csv.writer(open(sys.argv[1], "w", newline="")); w.writerow(cols)
for c, k, lab, pn, pt, t, note, extra in R:
    fam, n, tw, tz = ours[c]
    src, ax, tab, col, af, afnote = S[k]
    if k == "AQ2024":
        af = "unknown" if extra is None else ("yes" if extra == n else "no")
    same = "yes"
    if (pn is not None and pn != n) or (pt is not None and pt != tw): same = "no"
    if c == "grover_5": same = "no"
    if k == "AQ2024" and c == "grover_5": same = "no"
    notes = "; ".join(x for x in [afnote if k != "AQ2024" else "", note] if x)
    if pn is not None and pn != n: notes += f"; paper n {pn} differs from our n {n}"
    if pt is not None and pt != tw: notes += f"; paper original T {pt} differs from our T {tw}"
    w.writerow([c, fam, n, tw, tz, k, src, ax, tab, col, lab, "" if pn is None else pn, "" if pt is None else pt, t, af, same, "yes", "yes" if (k == "AMM2014_Tpar" and c == "csla_mux_3") else "no", notes])
print(len(R), "rows;", "circuits covered:", len({r[0] for r in R}), "of", len(ours), sorted(set(ours) - {r[0] for r in R}))
