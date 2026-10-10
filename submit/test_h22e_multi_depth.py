import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h22e_multi_depth as D


def test_cdkm_depth():
    r = {(c, k, p): (n2, d2) for c, k, p, n2, d2, _ in D.rows()}
    for k in (1, 2, 3):
        assert r[("cdkm_adder_10", k, "P0")] == (141, 122)
        assert r[("cdkm_adder_10", k, "L3")] == (118, 65)


def test_md_matches():
    D.main()
    t = open(os.path.join(D.ROOT, "results", "h22e_multi_depth.md")).read()
    assert "| cdkm_adder_10 | i1 | L3 | 118 | 65 | 111 |" in t
