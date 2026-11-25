"""Immutable data structures for a numerical signal flow graph."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class Node:
    """A graph node identified by a short, user-visible name.

    The ID is used by branches and by the graph's input/output references, so
    it must contain at least one non-whitespace character.
    """

    node_id: str

    def __post_init__(self) -> None:
        # Blank IDs could not be used to identify this node in the graph.
        if not self.node_id.strip():
            raise ValueError("A node ID cannot be empty.")


@dataclass(frozen=True, slots=True)
class Branch:
    """A directed branch with a numerical gain.

    Branch IDs distinguish individual edges. Two branches may connect the
    same pair of nodes as long as they have different IDs; their gains remain
    separate terms in later path and loop calculations.
    """

    branch_id: str
    source_node_id: str
    target_node_id: str
    gain: float

    def __post_init__(self) -> None:
        # IDs and endpoints are references used when the full graph is checked.
        if not self.branch_id.strip():
            raise ValueError("A branch ID cannot be empty.")
        if not self.source_node_id.strip():
            raise ValueError("A branch's source node ID cannot be empty.")
        if not self.target_node_id.strip():
            raise ValueError("A branch's target node ID cannot be empty.")
        # NaN and infinity would make path and loop gain products unusable.
        if not isfinite(self.gain):
            raise ValueError("A branch gain must be a finite number.")


@dataclass(frozen=True, slots=True)
class SignalFlowGraph:
    """A directed graph and the nodes used as its input and output.

    The graph stores ordered tuples so the input is predictable and cannot be
    changed after validation. The input and output IDs define the endpoints
    for forward-path analysis.
    """

    nodes: tuple[Node, ...]
    branches: tuple[Branch, ...]
    input_node_id: str
    output_node_id: str

    def __post_init__(self) -> None:
        # Node IDs must be unambiguous when a branch refers to an endpoint.
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Node IDs must be unique.")

        # Branch IDs identify edges, while endpoint pairs do not have to be
        # unique. This allows distinct parallel branches with different gains.
        branch_ids = [branch.branch_id for branch in self.branches]
        if len(branch_ids) != len(set(branch_ids)):
            raise ValueError("Branch IDs must be unique.")

        # Both selected endpoints must refer to nodes that this graph contains.
        known_node_ids = set(node_ids)

        for node_id, role in (
            (self.input_node_id, "input"),
            (self.output_node_id, "output"),
        ):
            if node_id not in known_node_ids:
                raise ValueError(f"The {role} node '{node_id}' is not in the graph.")

        # Check all branch endpoints here so analysis code can trust its input
        # instead of handling dangling references during traversal.
        for branch in self.branches:
            for node_id in (branch.source_node_id, branch.target_node_id):
                if node_id not in known_node_ids:
                    raise ValueError(
                        f"Branch '{branch.branch_id}' refers to "
                        f"unknown node '{node_id}'."
                    )
