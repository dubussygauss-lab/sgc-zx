# Summary for the judges

Team Learned ZX Rewriting. Report title: "A pass selector keeps ZX rewriting only where it lowers the cost of a circuit on Quantinuum H2". Quantinuum Singapore Grand Challenge, submission 1. Built on 9 October 2026 from `report/report_v5.md` and aligned with its Section 1.

`[F]` marks a statement copied from the report or from the `value/` outputs. `[O]` marks a judgement. The script `check_summary_numbers.py` finds every number of this page in `report/report_v5.md` or in `value/`.

## User and decision

`[O]` The user runs Clifford+T subroutines on Quantinuum H2 under a fixed HQC budget. The same team will later price these subroutines in T gates on a fault-tolerant Helios. The decision is made per circuit. Should the circuit go through PyZX teleport_reduce (pipeline P2) before pytket's Quantinuum pass at level 2 (pipeline P0)? `[F]` The delivered tool is the pass selector PSEL in `pipelines/pass_select.py`. It decides per circuit whether to run PyZX teleport_reduce before pytket's Quantinuum pass. It compiles each circuit with P0 and with P2 and keeps the compiled circuit with the lower HQC. `[O]` The ledger explains the choice in HQC and in magic states.

## HQC saved on H2

`[F]` PSEL cannot cost more HQC than P0 on a circuit where P0 passes the exactness check. This holds by construction because P0 is always one of its two candidates. It is not a measured result. PSEL picks P2 on 14 of the 15 checked B1 circuits. HQC is computed with the organisers' formula `estimate_cost` from the gate counts of the compiled circuit (report Section 1.2). At 1000 shots it costs 14,772.4 HQC against 15,516.0 for P0 on the 15 checked B1 circuits. The saving is 743.6 HQC or 4.79 %. It comes from the ZX stage P2. P2 alone costs 14,772.8 HQC there and PSEL matches it within 0.4 HQC. The median per-circuit saving is 3.94 %. On the 180 Trotter circuits of family A PSEL picks P2 on 57 and saves 46.0 HQC or 0.28 %. It never raises the ZZ gate count against P0 on any of the 223 circuits.

`[F]` P2 is cheaper than P0 on 14 of the 15 B1 circuits. hwb8 alone accounts for 84.5 % of the PSEL saving on B1 and serves no sourced quantum algorithm. Without hwb8 the PSEL saving on B1 is 115.0 HQC. On family A P2 alone would cost 1,030.4 HQC or 6.27 % more than P0. PSEL keeps P0 on 123 of these 180 circuits and on all 60 XXZ circuits. PSEL's own contribution is to avoid this P2 loss while it keeps the B1 gain. On family A it saves 1,076.4 HQC against always running P2.

`[O]` The median of 3.94 % is the better guide for a single circuit. A user with a Trotter circuit runs PSEL and does not need to decide in advance whether the ZX stage pays.

## Magic states saved

`[F]` On a surface-code machine each T gate consumes one magic state (Litinski, arXiv:1808.02892). Against the written input circuits the ZX stage removes 2,862 of 7,048 T gates on B1. That is 40.6 % of the written T-count. On the 8 count-only B1x circuits it removes 798 of 1,652 or 48.3 %. On the 20 synthesised B2 Haar circuits it removes 862 of 42,396 or 2.0 %. Our T-count after ZX equals the best ancilla-free value in the six papers of report Section 3.4 on 14 of 22 comparable B1 and B1x circuits and is above it on the other 8 (report Table C2).

## Certified fraction

`[F]` The exactness-barrier certificate (Kam et al., arXiv:2608.22801) gives a per-instance floor on the T-count of every semantics-exact rewrite. It covers 24 circuits, all with n at most 5. On the 20 B2 circuits at n = 2 and 3 the floor is 41,414 against 41,534 T gates after ZX. The certified-incompressible fraction is 0.997. On the four B1 circuits at n = 5 the floor is 47 against 106 and the fraction is 0.443. The fraction 0.997 does not hold for B1.

`[O]` The certificate does not say whether the B1 gap is headroom for a better rewrite or slack in the bound.

## Application map

`[F]` All B1 and B1x circuits appear in Table II of Amy and Mosca (arXiv:1601.07363). Report Table 1.3 places vbe_adder_3, mod_mult_55, mod_red_21 and qft_4 under integer factoring. gf2_pow_4_mult goes under elliptic-curve discrete log over GF(2^m). grover_5 and mod5_4 go under Grover search. hwb6, hwb8 and the two ham15 circuits have no sourced algorithm role. P2 saves 7.9 % HQC on the checked factoring circuits and 4.8 % on the checked search circuits.

`[O]` The tof and barenco_tof circuits are placed in search as oracle and diffusion parts.

## Emulator runs

`[F]` Three H2-Emulator jobs with 22 circuit rows and six H2-2E jobs ran on 8 October 2026 at 1000 shots. Twelve repeat H2-2E jobs ran vbe_adder_3 and grover_5 three more times. The 18 H2-2E jobs carry HQC estimates that sum to 5933.2 HQC. On H2-2E at 1000 shots the difference F_H(P2) minus F_H(P0) is +0.0050 on vbe_adder_3 (z = +0.55), -0.0150 on hwb6 (z = -1.21) and +0.0076 on grover_5 (z = +0.48). On the H2-Emulator the four Toffoli comparisons all lie within two sd of zero. Neither tier resolves P2 against P0 at 1000 shots. At the predicted gain a 2-sd resolution needs 1147 shots per pipeline on vbe_adder_3, 1974 on grover_5 and 20462 on hwb6. At 4000 shots per pipeline the pooled H2-2E difference is +0.0108 on vbe_adder_3 with z = +2.38 and a two-sided p of 0.017. The repeat circuits were chosen after Table E2. The Holm-adjusted p is 0.035 over the two repeated circuits and 0.052 over all three H2-2E circuits. On grover_5 it is +0.0007 with z = +0.10 and is not resolved. It lies 2.94 sd below the predicted gain of 0.0229. Nothing in the report has run on hardware.

`[O]` The emulator runs confirm execution and HQC accounting on the Quantinuum platform. vbe_adder_3 is the one circuit on which the emulator measures a fidelity gain of P2 over P0. The gain is significant before correction and after correction over the two repeated circuits. It is not significant at 0.05 after correction over all three H2-2E circuits. Elsewhere the P2 against P0 comparison rests on the ZZPhase counts and the Selene ensemble means.

## Table C2 finding

`[F]` Table C2 sets our T-count after ZX beside the smallest T-count reported in six papers and beside the certified floor. Our ZX stage matches the best published ancilla-free count on 14 of the 22 comparable circuits. On the four certified circuits the ZX stage leaves 106 T gates and the floor is 47. The best published ancilla-free counts on them sum to 105. Published optimisers therefore close 1 of the 59 gates between our count and the floor. That gate is on mod5_4. The other 58 gates are closed by neither side.

`[O]` The certificate cannot tell whether the 58 open gates are headroom or slack in the bound.

## Files in this package

| File | Content |
|---|---|
| `report.pdf`, `report.md` | Report v5 without its changelog sections, `figures/` holds its images |
| `code.zip` | `git archive` of the commit named in `MANIFEST.txt` |
| `REPRODUCE.md` | Environment, commands, tests and seeds |
| `SUMMARY.md`, `check_summary_numbers.py` | This page and the script that checks its numbers |
| `MANIFEST.txt` | Size and sha256 of every file |
| `build.sh`, `run_tests.sh`, `strip_changelog.py`, `check_pdf_tables.py`, `report.css` | Scripts that rebuild and check this package |
| `build_logs/` | Build log and test logs |
