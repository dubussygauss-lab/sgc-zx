# Application mapping of the B1 and B1x benchmark circuits

Every statement carries a tag. `[F]` means the statement was checked against the cited source on 2026-10-08 (arXiv abstract page, arXiv full text or benchmark web page fetched that day). `[O]` means an editorial judgement or an inference from circuit names. Quotations are copied from the fetched pages.

## Summary

| Application area | Our circuits | Citation |
|---|---|---|
| Integer factoring (Shor) | vbe_adder_3, rc_adder_6, csla_mux_3, mod_mult_55, mod_red_21, qft_4 | VBE 1996 [arXiv:quant-ph/9511018](https://arxiv.org/abs/quant-ph/9511018), Markov and Saeedi 2012 [arXiv:1202.6614](https://arxiv.org/abs/1202.6614), Nam et al. 2018 [arXiv:1710.07345](https://arxiv.org/abs/1710.07345), Coppersmith 2002 [arXiv:quant-ph/0201067](https://arxiv.org/abs/quant-ph/0201067) `[F]` |
| Elliptic-curve discrete log over GF(2^m) | gf2^4_mult, gf2^5_mult, gf2^6_mult | Cheung, Maslov, Mathew, Pradhan [arXiv:0710.1093](https://arxiv.org/abs/0710.1093) `[F]` |
| Unstructured search (Grover) | grover_5, mod5_4, tof_n and barenco_tof_n as oracle and diffusion parts | Grover 1996 [arXiv:quant-ph/9605043](https://arxiv.org/abs/quant-ph/9605043), Figgatt et al. 2017 [arXiv:1703.10535](https://arxiv.org/abs/1703.10535), [mod5 benchmark page](https://reversiblebenchmarks.github.io/mod5.html) `[F]` for sources, `[O]` for the tof_n placement |
| Arithmetic for chemistry and simulation oracles | vbe_adder_3, rc_adder_6, csla_mux_3 | Häner, Roetteler, Svore [arXiv:1805.12445](https://arxiv.org/abs/1805.12445), Sanders et al. [arXiv:1807.03206](https://arxiv.org/abs/1807.03206) `[F]` for sources, `[O]` for the circuit placement |
| Classical reversible logic with no sourced quantum-algorithm role | hwb6, hwb8, ham15-low, ham15-med | [hwb benchmark page](https://reversiblebenchmarks.github.io/hwbs.html), [ham15 benchmark page](https://reversiblebenchmarks.github.io/ham15.html) `[F]` |

## Provenance of the benchmark set

- `[F]` Amy, Maslov, Mosca, "Polynomial-time T-depth optimization of Clifford+T circuits via matroid partitioning", DOI 10.1109/TCAD.2014.2341953, [arXiv:1303.2042](https://arxiv.org/abs/1303.2042). Section 7 says the authors "optimize[d] various quantum circuits, specifically arithmetic and reversible ones, from the literature" and notes that "most arithmetic circuits are dominated by Toffoli gates." Its table holds Λ_k(X) (Barenco and Nielsen-Chuang versions), Mod 5_4, VBE-Adder_3, CSLA-MUX_3, RC-Adder_6, Mod-Red_21, Mod-Mult_55 and GF(2^m)-Mult.
- `[F]` Nam, Ross, Su, Childs, Maslov, "Automated optimization of large quantum circuits with continuous parameters", DOI 10.1038/s41534-018-0072-4, [arXiv:1710.07345](https://arxiv.org/abs/1710.07345). The full text says it used "a set of benchmark circuits from Ref. [19], consisting of various arithmetic circuits (including a family of Galois field multipliers)" and "implementations of multiple-control Toffoli gates." Ref. [19] is Amy, Maslov, Mosca. It also states that "The names of the algorithms are taken verbatim from Ref. [19]."
- `[F]` Neither of these two papers contains hwb6, hwb8, ham15, grover_5 or qft_4 according to the fetched full texts. The provenance stated in the task brief is therefore incomplete for these five circuits.
- `[F]` All circuits of B1 and B1x appear in Table II of Amy and Mosca, "T-count optimization and Reed-Muller codes", [arXiv:1601.07363](https://arxiv.org/abs/1601.07363). The rows include Grover5, Mod 54, VBE-Adder3, CSLA-MUX3, RC-Adder6, Mod-Red21, Mod-Mult55, HWB6, HWB8, GF(2^4..6)-Mult, Hamming15 (low), Hamming15 (med), QFT4 and Λ3(X), Λ4(X), Λ5(X), Λ10(X). Each Λ_n(X) has a Barenco row [43] and a Nielsen-Chuang row [24].
- `[F]` Amy and Mosca state that the circuits were "drawn from the literature and the Reversible Logic Benchmarks page [33]", which is Maslov's page now at [reversiblebenchmarks.github.io](https://reversiblebenchmarks.github.io/).
- `[F]` None of the three papers above names RevLib. They cite the Maslov benchmarks page. The [RevLib site](https://www.revlib.org/) describes itself as an online resource of benchmarks for reversible and quantum circuit design. The Wille et al. 2008 citation itself was not fetched and stays Unverifiable.
- `[F]` Our files come from the Quantinuum pyzx fork at `third_party/pyzx-fork/circuits/qasm/` as recorded in `bench/build_family_B1.py`.
- `[O]` The fork names tof_n and barenco_tof_n match the Nielsen-Chuang and Barenco rows of Λ_n(X). Nam et al. name these families "Toff-NC" and "Toff-Barenco". The match is inferred from naming and was not checked gate by gate.

## Why T-count matters for fault-tolerant resource estimates

- `[F]` Amy, Maslov, Mosca call the T gate "typically the most costly gate in fault-tolerant models, e.g., those based on the Steane or surface codes" ([arXiv:1303.2042](https://arxiv.org/abs/1303.2042)).
- `[F]` Nam et al. cite estimates that a fault-tolerant T gate is "46 [32] to 350 [33] times more expensive" than a local fault-tolerant CNOT ([arXiv:1710.07345](https://arxiv.org/abs/1710.07345)).
- `[F]` Gidney reduces the T-count of an n-bit adder "from 8n + O(1) to 4n + O(1)" ([arXiv:1709.06648](https://arxiv.org/abs/1709.06648)).
- `[F]` Gidney and Ekerå give a factoring cost of 0.3 n^3 + 0.0005 n^3 lg n Toffolis ([arXiv:1905.09749](https://arxiv.org/abs/1905.09749)). Recomputed for n = 2048 this is 2.62 × 10^9 Toffolis with 6189 logical qubits from 3n + 0.002 n lg n.

## Circuit groups

### Toffoli chains: tof_3, tof_4, tof_5, tof_10, barenco_tof_3, barenco_tof_4, barenco_tof_5, barenco_tof_10

- `[F]` These circuits implement the multiple-control Toffoli Λ_k(X). Amy, Maslov, Mosca use "the Barenco et al. implementation using k-2 ancillae with arbitrary initial states" and "the Nielsen-Chuang implementation using k-2 ancillae initialized in the state |0⟩" ([arXiv:1303.2042](https://arxiv.org/abs/1303.2042)).
- `[F]` Barenco et al. describe generalized Deutsch-Toffoli gates and state that "These gates play a central role in many proposed constructions of quantum computational networks" ([arXiv:quant-ph/9503016](https://arxiv.org/abs/quant-ph/9503016)).
- `[F]` Figgatt et al. report "the first implementation of a Toffoli-4 gate, which is used along with Toffoli-3 gates to construct the algorithms" of 3-qubit Grover search ([arXiv:1703.10535](https://arxiv.org/abs/1703.10535)).
- `[O]` Every Toffoli costs T gates in a Clifford+T compilation. A multi-controlled Toffoli therefore sets the non-Clifford budget of oracles and diffusion steps.

### Adders: vbe_adder_3, rc_adder_6, csla_mux_3

- `[F]` vbe_adder_3 is cited to Vedral, Barenco, Ekert in Amy, Maslov, Mosca. That paper constructs "quantum networks effecting basic arithmetic operations: from addition to modular exponentiation." It calls modular exponentiation "the most difficult (time and space consuming) part of Shor's quantum factorising algorithm" ([arXiv:quant-ph/9511018](https://arxiv.org/abs/quant-ph/9511018), PRA 54, 147).
- `[F]` rc_adder_6 is cited to Cuccaro, Draper, Kutin, Moulton. Their abstract presents "a new linear-depth ripple-carry quantum addition circuit" that "uses only a single ancillary qubit" ([arXiv:quant-ph/0410184](https://arxiv.org/abs/quant-ph/0410184)).
- `[F]` csla_mux_3 is cited to Van Meter and Itoh, "Fast quantum modular exponentiation" ([arXiv:quant-ph/0408006](https://arxiv.org/abs/quant-ph/0408006), PRA 71, 052320). Their abstract concerns modular exponentiation and states that addition is "limited to O(n) time" on a neighbor-only architecture "when non-neighbor architectures can reach O(log n)".
- `[O]` CSLA reads as carry-select adder. The Van Meter and Itoh abstract does not use this term.
- `[F]` Nam et al. state that "Adders are a basic component of Shor's quantum algorithm for integer factoring" and that "Shor's integer factoring algorithm is dominated by the cost of modular exponentiation" ([arXiv:1710.07345](https://arxiv.org/abs/1710.07345)).
- `[F]` Häner, Roetteler, Svore write that "Many quantum algorithms make use of oracles which evaluate classical functions on a superposition of inputs" ([arXiv:1805.12445](https://arxiv.org/abs/1805.12445)).
- `[F]` Sanders et al. write that the standard approach to black-box state preparation "requires the quantum computer to do arithmetic, which is a key contributor to the complexity." They call state preparation "a crucial subroutine in many approaches to simulating physics on a quantum computer" ([arXiv:1807.03206](https://arxiv.org/abs/1807.03206)).

### Modular arithmetic: mod5_4, mod_mult_55, mod_red_21

- `[F]` mod5_4 is cited to Maslov's benchmarks page in Amy, Maslov, Mosca without a description. The page for the 4-input function mod5 states "Its output is 1 if and only if the binary number represented by its input is divisible by 5" and labels it a Grover oracle ([mod5 page](https://reversiblebenchmarks.github.io/mod5.html)).
- `[O]` The identification of mod5_4 with this 4-input mod5 function rests on the name and the input count. The page does not use the name mod5_4.
- `[O]` mod5_4 is a divisibility test used as a search oracle. It is not modular arithmetic of the Shor type despite its group name.
- `[F]` mod_mult_55 and mod_red_21 are cited to Markov and Saeedi in Amy, Maslov, Mosca. Their abstract says the circuits "arise as components of modular exponentiation in Shor's quantum number-factoring algorithm" ([arXiv:1202.6614](https://arxiv.org/abs/1202.6614)).
- `[F]` The Markov and Saeedi abstract does not use the term "modular reduction". What mod_red_21 computes beyond its name is Unverifiable from the fetched sources.
- `[F]` Beauregard gives a Shor circuit with "2n+3 qubits and O(n^3 lg(n)) elementary quantum gates" and lists "modular arithmetics" as a keyword ([arXiv:quant-ph/0205095](https://arxiv.org/abs/quant-ph/0205095)).

### GF(2^m) multipliers: gf2^4_mult, gf2^5_mult, gf2^6_mult

- `[F]` These multiply two elements of the binary field GF(2^m). Amy, Maslov, Mosca cite them to Maslov, Mathew, Cheung, Pradhan on an O(m^2)-depth algorithm for the elliptic-curve discrete logarithm over GF(2^m).
- `[F]` arXiv:0710.1093 (v1 and v2) is titled "On the Design and Optimization of a Quantum Polynomial-Time Attack on Elliptic Curve Cryptography" with authors in the order Cheung, Maslov, Mathew, Pradhan. Its abstract describes "constructing an efficient circuit for multiplying elements of binary finite fields" inside an algorithm that "solves the discrete logarithm problem for points on elliptic curves over" GF(2^m) ([arXiv:0710.1093](https://arxiv.org/abs/0710.1093)).
- `[F]` The title and author order differ from the reference in the task brief. Whether arXiv:0710.1093 is the exact work cited by Amy, Maslov, Mosca is Unverifiable from the fetched pages.
- `[F]` Roetteler, Naehrig, Svore, Lauter estimate resources for discrete logarithms "on elliptic curves over prime fields" ([arXiv:1706.06752](https://arxiv.org/abs/1706.06752)). Their abstract does not mention binary fields. It supports the importance of field arithmetic for elliptic-curve attacks but does not cover GF(2^m) multipliers.

### Hidden weighted bit: hwb6, hwb8

- `[F]` The benchmark page defines the function as follows. "Its output equals its input shifted left on the number of positions equal to the number of ones in the input pattern." It adds that the function "is known to have an exponential size BDD for any variable ordering" ([hwb page](https://reversiblebenchmarks.github.io/hwbs.html)).
- `[F]` Bryant's 1991 paper "On the Complexity of VLSI Implementations and Graph Representations of Boolean Functions with Application to Integer Multiplication" exists in the [CMU repository](https://kilthub.cmu.edu/articles/journal_contribution/On_the_Complexity_of_VLSI_Implementations_and_Graph_Representations_of_Boolean_Functions_with_Application_to_Integer_Multiplication/6624854). The page carries no abstract. The attribution of the hidden weighted bit function to this paper is Unverifiable from fetched text.
- `[F]` Bollig, Löbbing, Sauerhoff, Wegener study "the complexity of the hidden weighted bit function for various BDD models" (RAIRO ITA 33, 103, 1999, [numdam](https://numdam.org/item/ITA_1999__33_2_103_0/)).
- `[O]` No source found places hwb inside a quantum algorithm. Its value for us is as a reversible-logic stress test with many Toffolis.

### Grover search: grover_5

- `[F]` Amy and Mosca cite Grover5 to Grover's 1996 paper. A footnote states "Grover's search is performed with 4 iterations using the oracle f(x) = ¬x1 ∧ ¬x2 ∧ x3 ∧ x4 ∧ ¬x5" ([arXiv:1601.07363](https://arxiv.org/abs/1601.07363)).
- `[F]` Grover's algorithm finds a marked item "in only O(sqrt(N)) steps" ([arXiv:quant-ph/9605043](https://arxiv.org/abs/quant-ph/9605043)).
- `[F]` Figgatt et al. build 3-qubit Grover oracles with Toffoli-3 and Toffoli-4 gates ([arXiv:1703.10535](https://arxiv.org/abs/1703.10535)).

### Quantum Fourier transform: qft_4

- `[F]` Amy and Mosca cite QFT4 to Nielsen and Chuang ([arXiv:1601.07363](https://arxiv.org/abs/1601.07363)).
- `[F]` Coppersmith defines "an approximate version of the Fourier transform on 2^L elements" that "may find application to the problem of factoring integers with a quantum computer" ([arXiv:quant-ph/0201067](https://arxiv.org/abs/quant-ph/0201067)).
- `[F]` Kitaev gives "a polynomial quantum Fourier transform algorithm for an arbitrary finite Abelian group" and "a procedure for measuring an eigenvalue of a unitary operator" ([arXiv:quant-ph/9511026](https://arxiv.org/abs/quant-ph/9511026)).
- `[F]` Shor's abstract covers factoring and discrete logarithms but does not mention the Fourier transform ([arXiv:quant-ph/9508027](https://arxiv.org/abs/quant-ph/9508027)). The abstract of Cleve, Ekert, Macchiavello, Mosca relates quantum algorithms to "quantum phase estimation" without naming the QFT ([arXiv:quant-ph/9708016](https://arxiv.org/abs/quant-ph/9708016)).
- `[F]` qft_4 is the only B1 file whose source contains s, sdg, t and tdg gates directly (`bench/build_family_B1.py`, docstring).
- `[O]` The exact QFT needs rotations finer than T. A 4-qubit Clifford+T version is therefore an approximation or a truncated form. This was not checked against the file.

### Hamming code: ham15-low, ham15-med

- `[F]` The benchmark page states "Function ham15 is the size 15 Hamming optimal coding function" and credits the reversible specification to Patel and Markov ([ham15 page](https://reversiblebenchmarks.github.io/ham15.html)).
- `[F]` The page lists three realizations with quantum costs 1827, 453 and 206. It does not use the labels low, med or high.
- `[O]` The fork names low and med correspond to the Amy and Mosca rows Hamming15 (low) and Hamming15 (med). Their mapping to the three page realizations was not checked.
- `[O]` No source found places ham15 inside a quantum algorithm. It is a classical encoding function and not a quantum error-correcting code circuit.

## Claims that could not be sourced

- `[F]` hwb, ham15, grover_5 and qft_4 are not in Amy, Maslov, Mosca 2014 or Nam et al. 2018. Their stated provenance was corrected to Amy and Mosca 2016.
- `[F]` Roetteler et al. 2017 covers prime fields only. It does not support a GF(2^m) claim.
- `[F]` The GF(2^m) reference as written in the brief (Maslov, Mathew, Cheung, Pradhan) does not match the arXiv:0710.1093 title and author order.
- `[F]` The RevLib origin (Wille et al. 2008) is not stated in any fetched benchmark paper. The citation was not fetched.
- `[F]` Bryant 1991 as the origin of the hidden weighted bit function: the paper exists but no fetched text confirms the function is defined there.
- `[F]` The function computed by mod_red_21 is not described in any fetched abstract.
- `[F]` No fetched abstract states that the QFT is a subroutine of Shor's algorithm. Coppersmith and Kitaev were used instead.
- `[F]` No fetched source links ham15 or hwb to a quantum algorithm.
- `[F]` No fetched chemistry paper (Su et al. [arXiv:2105.12767](https://arxiv.org/abs/2105.12767) was checked) names adders explicitly in its abstract. The chemistry row rests on Sanders et al. and Häner et al.
