"""Turn the text a user types into a validated ``SignalFlowGraph``."""

import re
from collections.abc import Iterable
from fractions import Fraction

from control_assignment.models.signal_graph import Branch, Node, SignalFlowGraph

BranchRow = tuple[str, str, str]  # (source node, target node, gain text)


class InputError(ValueError):
    """Raised when the graph description is incomplete or invalid."""


def parse_node_names(text: str) -> tuple[str, ...]:
    """Split ``"R, x1 x2; C"`` into node IDs; commas, semicolons and spaces work."""
    return tuple(name for name in re.split(r"[,;\s]+", text.strip()) if name)


def parse_gain(text: str) -> float:
    """Read a numerical gain; decimals, fractions (``1/3``) and ``1e-2`` are accepted."""
    try:
        return float(Fraction(text.strip()))
    except (ValueError, ZeroDivisionError) as error:
        raise InputError(f"'{text.strip()}' is not a valid numerical gain.") from error


def build_graph(
    node_names: Iterable[str],
    branch_rows: Iterable[BranchRow],
    input_node_id: str,
    output_node_id: str,
) -> SignalFlowGraph:
    """Validate rows from the branch table and create the graph.

    Completely blank rows are ignored. Branch IDs are generated as b1, b2, ...
    """
    names = tuple(node_names)
    if not names:
        raise InputError("Enter at least one node.")

    branches: list[Branch] = []
    for row_number, (source, target, gain_text) in enumerate(branch_rows, start=1):
        source, target, gain_text = source.strip(), target.strip(), gain_text.strip()
        if not (source or target or gain_text):
            continue
        if not (source and target and gain_text):
            raise InputError(f"Branch row {row_number} is incomplete.")
        try:
            branches.append(
                Branch(f"b{len(branches) + 1}", source, target, parse_gain(gain_text))
            )
        except InputError as error:
            raise InputError(f"Branch row {row_number}: {error}") from error
        except ValueError as error:
            raise InputError(f"Branch row {row_number}: {error}") from error

    try:
        return SignalFlowGraph(
            nodes=tuple(Node(name) for name in names),
            branches=tuple(branches),
            input_node_id=input_node_id.strip(),
            output_node_id=output_node_id.strip(),
        )
    except ValueError as error:
        raise InputError(str(error)) from error
