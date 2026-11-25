"""Find individual loops and groups of mutually non-touching loops."""

from dataclasses import dataclass
from math import prod

from control_assignment.analysis.graph_index import build_outgoing_branch_index
from control_assignment.models.signal_graph import Branch, SignalFlowGraph


@dataclass(frozen=True, slots=True)
class Loop:
    """A closed sequence of branches that does not repeat an internal node."""

    branches: tuple[Branch, ...]

    @property
    def gain(self) -> float:
        """Return the loop gain: the product of its branch gains."""
        return prod((branch.gain for branch in self.branches), start=1.0)

    @property
    def node_ids(self) -> tuple[str, ...]:
        """Return the nodes visited by the loop, in traversal order."""
        return tuple(branch.source_node_id for branch in self.branches)


def find_loops(graph: SignalFlowGraph) -> tuple[Loop, ...]:
    """Return each simple directed loop once, including self-loops.

    A loop's starting node is chosen as its earliest node in ``graph.nodes``.
    This canonical start prevents the same loop from being reported once for
    every possible rotation of its branch sequence.
    """
    loops: list[Loop] = []
    outgoing_branches = build_outgoing_branch_index(graph)
    node_order = {node.node_id: index for index, node in enumerate(graph.nodes)}

    def visit(
        start_node_id: str,
        start_order: int,
        node_id: str,
        path_branches: list[Branch],
        visited_node_ids: set[str],
    ) -> None:
        for branch in outgoing_branches[node_id]:
            next_node_id = branch.target_node_id

            if next_node_id == start_node_id:
                # Returning to the starting node closes one loop.
                loops.append(Loop((*path_branches, branch)))
                continue

            # A simple loop cannot visit a node twice. Requiring the next
            # node to follow the start in graph order also prevents rotated
            # copies of this same loop from being found later.
            if (
                next_node_id in visited_node_ids
                or node_order[next_node_id] < start_order
            ):
                continue

            path_branches.append(branch)
            visited_node_ids.add(next_node_id)
            visit(
                start_node_id,
                start_order,
                next_node_id,
                path_branches,
                visited_node_ids,
            )
            visited_node_ids.remove(next_node_id)
            path_branches.pop()

    for start_node in graph.nodes:
        start_node_id = start_node.node_id
        visit(
            start_node_id,
            node_order[start_node_id],
            start_node_id,
            [],
            {start_node_id},
        )

    return tuple(loops)


def find_non_touching_loop_combinations(
    loops: tuple[Loop, ...],
) -> tuple[tuple[Loop, ...], ...]:
    """Return every combination of two or more loops with disjoint nodes."""
    combinations: list[tuple[Loop, ...]] = []

    def choose_loops(
        next_index: int,
        selected_loops: list[Loop],
        occupied_node_ids: set[str],
    ) -> None:
        for index in range(next_index, len(loops)):
            loop = loops[index]
            loop_node_ids = set(loop.node_ids)

            # Two loops touch if they share any node, so they cannot appear
            # together in a non-touching combination.
            if not occupied_node_ids.isdisjoint(loop_node_ids):
                continue

            selected_loops.append(loop)
            occupied_node_ids.update(loop_node_ids)

            if len(selected_loops) >= 2:
                combinations.append(tuple(selected_loops))

            # Increasing the next index builds each combination once and
            # keeps the result order consistent with the input loop order.
            choose_loops(index + 1, selected_loops, occupied_node_ids)

            occupied_node_ids.difference_update(loop_node_ids)
            selected_loops.pop()

    choose_loops(0, [], set())
    # Mason's determinant groups the products by pair, triple, and higher order.
    combinations.sort(key=len)
    return tuple(combinations)
