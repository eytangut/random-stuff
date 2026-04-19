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


def test_different_topology_different_layout():
    # Different graph topologies produce different layouts (meaningful determinism).
    # Linear chain vs star topology: g2 ends up in different positions.
    fl1 = ForceLayout("seed")
    fl2 = ForceLayout("seed")
    nodes = ["g0", "g1", "g2", "g3"]
    linear_edges = [("g0", "g1"), ("g1", "g2"), ("g2", "g3")]
    star_edges   = [("g0", "g1"), ("g0", "g2"), ("g0", "g3")]
    p_linear = fl1.run(nodes, linear_edges)
    p_star   = fl2.run(nodes, star_edges)
    # Same seed but different topology → different positions for at least one node
    assert any(abs(p_linear[n][i] - p_star[n][i]) > 0.1 for n in nodes for i in range(2))


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
