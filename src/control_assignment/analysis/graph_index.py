"""Small lookup structures shared by graph traversal algorithms."""

from control_assignment.models.signal_graph import Branch, SignalFlowGraph


def build_outgoing_branch_index(
    graph: SignalFlowGraph,
) -> dict[str, tuple[Branch, ...]]:
    """Group each node's outgoing branches while preserving their input order."""
    branches_by_source: dict[str, list[Branch]] = {
        node.node_id: [] for node in graph.nodes
    }

    for branch in graph.branches:
        branches_by_source[branch.source_node_id].append(branch)

    return {
        node_id: tuple(branches) for node_id, branches in branches_by_source.items()
    }
