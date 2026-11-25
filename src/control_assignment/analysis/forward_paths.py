"""Find all simple forward paths through a signal flow graph."""

from dataclasses import dataclass
from math import prod

from control_assignment.analysis.graph_index import build_outgoing_branch_index
from control_assignment.models.signal_graph import Branch, SignalFlowGraph


@dataclass(frozen=True, slots=True)
class ForwardPath:
    """An ordered sequence of branches from the graph input to its output."""

    branches: tuple[Branch, ...]

    @property
    def gain(self) -> float:
        """Return the path gain: the product of its branch gains."""
        return prod((branch.gain for branch in self.branches), start=1.0)


def find_forward_paths(graph: SignalFlowGraph) -> tuple[ForwardPath, ...]:
    """Return every forward path without repeating a node.

    Branch order follows the order in ``graph.branches``. Distinct parallel
    branches therefore produce distinct paths, even when their endpoints match.
    """
    paths: list[ForwardPath] = []
    outgoing_branches = build_outgoing_branch_index(graph)
    # These two objects describe the route currently being explored.
    path_branches: list[Branch] = []
    visited_node_ids = {graph.input_node_id}

    def visit(node_id: str) -> None:
        if node_id == graph.output_node_id:
            # A forward path ends at the output, so save it and stop this route.
            paths.append(ForwardPath(tuple(path_branches)))
            return

        # Depth-first search follows one possible route as far as it can before
        # returning here and trying the next outgoing branch.
        for branch in outgoing_branches[node_id]:
            next_node_id = branch.target_node_id
            # A repeated node would turn this route into a path containing a
            # loop, so skip it. Other routes may still visit this node later.
            if next_node_id in visited_node_ids:
                continue

            # Record the choice before recursing. After exploring that choice,
            # undo it (backtrack) so the next branch starts from this same node.
            path_branches.append(branch)
            visited_node_ids.add(next_node_id)
            visit(next_node_id)
            visited_node_ids.remove(next_node_id)
            path_branches.pop()

    visit(graph.input_node_id)
    return tuple(paths)
