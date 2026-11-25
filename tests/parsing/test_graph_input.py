import pytest

from control_assignment.parsing.graph_input import InputError, build_graph, parse_gain, parse_node_names


def test_node_names_accept_commas_and_spaces():
    assert parse_node_names("R, a  b;C") == ("R", "a", "b", "C")


def test_gain_forms():
    assert parse_gain("2") == 2
    assert parse_gain("-0.5") == -0.5
    assert parse_gain("1/4") == 0.25
    with pytest.raises(InputError):
        parse_gain("abc")


def test_build_graph_skips_blank_rows_and_numbers_branches():
    graph = build_graph(["a", "b"], [("a", "b", "2"), ("", "", ""), ("b", "a", "-1")], "a", "b")
    assert [b.branch_id for b in graph.branches] == ["b1", "b2"]


@pytest.mark.parametrize(
    "nodes,rows,source,target",
    [
        ([], [], "a", "b"),
        (["a", "b"], [("a", "", "2")], "a", "b"),
        (["a", "b"], [("a", "z", "2")], "a", "b"),
        (["a", "b"], [("a", "b", "x")], "a", "b"),
        (["a", "a"], [], "a", "a"),
        (["a", "b"], [], "a", "q"),
    ],
)
def test_invalid_graphs_raise_input_error(nodes, rows, source, target):
    with pytest.raises(InputError):
        build_graph(nodes, rows, source, target)
