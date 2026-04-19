from lean2manim.layout import ForceLayout


def test_deterministic_same_seed():
    fl1 = ForceLayout("abc123")
    fl2 = ForceLayout("abc123")
    nodes = ["g0", "g1", "g2"]
    edges = [("g0", "g1"), ("g1", "g2")]
    p1 = fl1.run(nodes, edges)
    p2 = fl2.run(nodes, edges)
    for nid in nodes:
        assert abs(p1[nid][0] - p2[nid][0]) < 1e-9
        assert abs(p1[nid][1] - p2[nid][1]) < 1e-9


def test_different_seed_different_layout():
    fl1 = ForceLayout("aaaa0000")
    fl2 = ForceLayout("bbbb1111")
    nodes = ["g0", "g1"]
    p1 = fl1.run(nodes, [])
    p2 = fl2.run(nodes, [])
    # At least one coordinate must differ (different seeds → different random start)
    assert any(abs(p1[n][i] - p2[n][i]) > 0.01 for n in nodes for i in range(2))


def test_empty_layout():
    fl = ForceLayout("seed")
    assert fl.run([], []) == {}


def test_single_node():
    fl = ForceLayout("seed")
    result = fl.run(["g0"], [])
    assert "g0" in result


def test_layout_returns_all_nodes():
    fl = ForceLayout("test123")
    nodes = ["a", "b", "c", "d"]
    result = fl.run(nodes, [("a", "b"), ("b", "c")])
    assert set(result.keys()) == set(nodes)


def test_fixed_nodes_do_not_move():
    fl = ForceLayout("fixtest")
    nodes = ["g0", "g1"]
    fixed = {"g0": (10.0, 10.0)}
    result = fl.run(nodes, [], fixed=fixed)
    assert abs(result["g0"][0] - 10.0) < 1e-9
    assert abs(result["g0"][1] - 10.0) < 1e-9
