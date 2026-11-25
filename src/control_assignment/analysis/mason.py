"""Calculate Mason's graph determinant, cofactors, and gain formula."""

from dataclasses import dataclass
from math import prod

from control_assignment.analysis.forward_paths import ForwardPath, find_forward_paths
from control_assignment.analysis.loops import (
    Loop,
    find_loops,
    find_non_touching_loop_combinations,
)
from control_assignment.models.signal_graph import SignalFlowGraph


@dataclass(frozen=True, slots=True)
class DeltaTerm:
    """One signed term in a graph determinant calculation."""

    loop_numbers: tuple[int, ...]
    loop_gains: tuple[float, ...]
    sign: int

    @property
    def product(self) -> float:
        """Return the product of loop gains in this term (1 for the constant)."""
        return prod(self.loop_gains, start=1.0)

    @property
    def signed_value(self) -> float:
        """Return this term's contribution to the determinant."""
        return self.sign * self.product


@dataclass(frozen=True, slots=True)
class DeltaCalculation:
    """All terms and the final value of a graph determinant or cofactor."""

    terms: tuple[DeltaTerm, ...]

    @property
    def value(self) -> float:
        """Sum the signed constant, single-loop, and non-touching terms."""
        return sum(term.signed_value for term in self.terms)


@dataclass(frozen=True, slots=True)
class PathCofactor:
    """A forward path, its cofactor, and their product in Mason's numerator."""

    path: ForwardPath
    delta_i: DeltaCalculation

    @property
    def numerator_term(self) -> float:
        """Return the path gain multiplied by its cofactor value."""
        return self.path.gain * self.delta_i.value


@dataclass(frozen=True, slots=True)
class MasonGainResult:
    """The complete numerical quantities used in Mason's gain formula."""

    forward_paths: tuple[ForwardPath, ...]
    loops: tuple[Loop, ...]
    delta: DeltaCalculation
    path_cofactors: tuple[PathCofactor, ...]

    @property
    def numerator(self) -> float:
        """Sum all ``M_i * Delta_i`` terms in Mason's formula."""
        return sum(item.numerator_term for item in self.path_cofactors)

    @property
    def gain(self) -> float:
        """Return the transfer gain ``sum(M_i * Delta_i) / Delta``."""
        return self.numerator / self.delta.value


def calculate_delta(
    loops: tuple[Loop, ...],
    *,
    loop_numbers: tuple[int, ...] | None = None,
) -> DeltaCalculation:
    """Calculate a determinant from its loops and non-touching combinations.

    The returned terms are ordered as the constant, individual loops, then
    non-touching pairs, triples, and higher-order combinations. ``loop_numbers``
    lets a cofactor keep the original graph-wide loop labels after some loops
    have been excluded.
    """
    if loop_numbers is None:
        loop_numbers = tuple(range(1, len(loops) + 1))
    elif len(loop_numbers) != len(loops):
        raise ValueError("Each loop must have exactly one loop number.")

    if any(loop_number < 1 for loop_number in loop_numbers):
        raise ValueError("Loop numbers must be positive integers.")
    if len(set(loop_numbers)) != len(loop_numbers):
        raise ValueError("Loop numbers must be unique.")

    terms = [DeltaTerm(loop_numbers=(), loop_gains=(), sign=1)]

    # Each individual loop contributes with a minus sign.
    for loop_number, loop in zip(loop_numbers, loops, strict=True):
        terms.append(
            DeltaTerm(
                loop_numbers=(loop_number,),
                loop_gains=(loop.gain,),
                sign=-1,
            )
        )

    # Products of k mutually non-touching loops have sign (-1)^k.
    loop_numbers_by_value = dict(zip(loops, loop_numbers, strict=True))
    for combination in find_non_touching_loop_combinations(loops):
        loop_numbers = tuple(loop_numbers_by_value[loop] for loop in combination)
        loop_gains = tuple(loop.gain for loop in combination)
        sign = 1 if len(combination) % 2 == 0 else -1
        terms.append(
            DeltaTerm(
                loop_numbers=loop_numbers,
                loop_gains=loop_gains,
                sign=sign,
            )
        )

    return DeltaCalculation(terms=tuple(terms))


def calculate_mason_gain(graph: SignalFlowGraph) -> MasonGainResult:
    """Calculate Mason's formula and retain every path cofactor calculation."""
    forward_paths = find_forward_paths(graph)
    loops = find_loops(graph)
    delta = calculate_delta(loops)

    if delta.value == 0:
        raise ZeroDivisionError("Mason's formula is undefined because Delta is zero.")

    loop_nodes = tuple(set(loop.node_ids) for loop in loops)
    all_loop_numbers = tuple(range(1, len(loops) + 1))
    path_cofactors: list[PathCofactor] = []

    for path in forward_paths:
        path_node_ids = {graph.input_node_id}
        path_node_ids.update(branch.target_node_id for branch in path.branches)

        # Delta_i omits every loop that touches this forward path.
        untouched_loop_pairs = tuple(
            (loop_number, loop)
            for loop_number, loop, loop_node_ids in zip(
                all_loop_numbers, loops, loop_nodes, strict=True
            )
            if path_node_ids.isdisjoint(loop_node_ids)
        )
        path_cofactors.append(
            PathCofactor(
                path=path,
                delta_i=calculate_delta(
                    tuple(loop for _, loop in untouched_loop_pairs),
                    loop_numbers=tuple(number for number, _ in untouched_loop_pairs),
                ),
            )
        )

    return MasonGainResult(
        forward_paths=forward_paths,
        loops=loops,
        delta=delta,
        path_cofactors=tuple(path_cofactors),
    )
