import pytest

from control_assignment.models.signal_graph import Branch, Node, SignalFlowGraph


def test_rejects_unknown_endpoint_and_duplicate_ids():
    nodes = (Node("a"), Node("b"))
    with pytest.raises(ValueError):
        SignalFlowGraph(nodes, (Branch("1", "a", "z", 1.0),), "a", "b")
    with pytest.raises(ValueError):
        SignalFlowGraph(nodes, (Branch("1", "a", "b", 1.0), Branch("1", "b", "a", 1.0)), "a", "b")
    with pytest.raises(ValueError):
        Branch("1", "a", "b", float("inf"))
