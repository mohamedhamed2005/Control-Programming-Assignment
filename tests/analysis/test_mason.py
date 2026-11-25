import random

import numpy as np
import pytest

from control_assignment.analysis.forward_paths import find_forward_paths
from control_assignment.analysis.loops import find_loops, find_non_touching_loop_combinations
from control_assignment.analysis.mason import calculate_mason_gain
from control_assignment.examples import GRAPH_EXAMPLES
from control_assignment.models.signal_graph import Branch, Node, SignalFlowGraph
from control_assignment.parsing.graph_input import build_graph, parse_node_names


def solve_directly(graph: SignalFlowGraph) -> float:
    """Reference answer: solve the node equations x = A x + b as a linear system."""
    index = {node.node_id: i for i, node in enumerate(graph.nodes)}
    matrix = np.eye(len(index))
    for branch in graph.branches:
        matrix[index[branch.target_node_id], index[branch.source_node_id]] -= branch.gain
    rhs = np.zeros(len(index))
    rhs[index[graph.input_node_id]] = 1.0
    return float(np.linalg.solve(matrix, rhs)[index[graph.output_node_id]])


def graph_from_example(example):
    return build_graph(
        parse_node_names(example.nodes), example.branches, example.input_node, example.output_node
    )


@pytest.mark.parametrize("example", GRAPH_EXAMPLES, ids=lambda e: e.name[:9])
def test_examples_match_direct_solution(example):
    graph = graph_from_example(example)
    assert calculate_mason_gain(graph).gain == pytest.approx(solve_directly(graph))


def test_example_three_hand_calculation():
    graph = graph_from_example(GRAPH_EXAMPLES[2])
    result = calculate_mason_gain(graph)
    # L1 = 3 * -0.5 = -1.5, L2 = 5 * -0.2 = -1, non-touching => Delta = 1 + 2.5 + 1.5
    assert result.delta.value == pytest.approx(5.0)
    assert [c.delta_i.value for c in result.path_cofactors] == pytest.approx([2.0, 2.5])
    assert result.numerator == pytest.approx(6 * 2.0 + 40 * 2.5)
    assert result.gain == pytest.approx(22.4)


def test_example_one_counts():
    graph = graph_from_example(GRAPH_EXAMPLES[0])
    assert len(find_forward_paths(graph)) == 2
    loops = find_loops(graph)
    assert len(loops) == 6
    combos = find_non_touching_loop_combinations(loops)
    assert sorted(len(c) for c in combos) == [2] * 7 + [3]


def test_random_graphs_agree_with_linear_solve():
    rng = random.Random(341)
    checked = 0
    for _ in range(300):
        count = rng.randint(3, 6)
        nodes = tuple(Node(f"n{i}") for i in range(count))
        branches = []
        for source in range(count):
            for target in range(count):
                if rng.random() < 0.35:
                    gain = rng.choice([-3, -2, -1, -0.5, 0.5, 1, 2, 3])
                    branches.append(Branch(f"b{len(branches)}", f"n{source}", f"n{target}", gain))
        graph = SignalFlowGraph(tuple(nodes), tuple(branches), "n0", f"n{count - 1}")
        try:
            expected = solve_directly(graph)
            result = calculate_mason_gain(graph)
        except (np.linalg.LinAlgError, ZeroDivisionError):
            continue
        if abs(result.delta.value) < 1e-9:
            continue
        assert result.gain == pytest.approx(expected, rel=1e-7, abs=1e-9)
        checked += 1
    assert checked > 100


def test_zero_delta_is_reported():
    graph = SignalFlowGraph(
        (Node("a"), Node("b")),
        (Branch("1", "a", "b", 1.0), Branch("2", "b", "a", 1.0)),
        "a",
        "b",
    )
    with pytest.raises(ZeroDivisionError):
        calculate_mason_gain(graph)
