"""Write the step-by-step Part 1 report: paths, loops, Delta, and Mason's formula."""

from collections import defaultdict
from fractions import Fraction

from control_assignment.analysis.mason import DeltaCalculation, MasonGainResult
from control_assignment.analysis.loops import Loop, find_non_touching_loop_combinations
from control_assignment.models.signal_graph import SignalFlowGraph
from control_assignment.reporting.formatting import fmt, fmt_paren, product_text


def _heading(lines: list[str], title: str) -> None:
    lines.extend(["", title, "=" * len(title)])


def _loop_route(loop: Loop) -> str:
    return " → ".join((*loop.node_ids, loop.node_ids[0]))


def _delta_lines(name: str, calc: DeltaCalculation) -> list[str]:
    """Show every sum, the symbolic formula, the substitution, and the value."""
    by_order: dict[int, list] = defaultdict(list)
    for term in calc.terms:
        if term.loop_numbers:
            by_order[len(term.loop_numbers)].append(term)

    if not by_order:
        return [f"{name} = 1   (no loops contribute)", f"{name} = {fmt(calc.value)}"]

    lines: list[str] = []
    symbolic = "1"
    substituted = "1"
    for order in sorted(by_order):
        terms = by_order[order]
        label = f"S{order}"
        meaning = (
            "sum of all loop gains"
            if order == 1
            else f"sum of products of {order} non-touching loops"
        )
        symbols = " + ".join("·".join(f"L{n}" for n in t.loop_numbers) for t in terms)
        numbers = " + ".join(fmt_paren(t.product) for t in terms)
        total = sum(t.product for t in terms)
        lines.append(f"{label} ({meaning})")
        lines.append(f"   = {symbols}")
        lines.append(f"   = {numbers}")
        lines.append(f"   = {fmt(total)}")
        operator = "-" if order % 2 == 1 else "+"
        symbolic += f" {operator} {label}"
        substituted += f" {operator} ({fmt(total)})"
    lines.append(f"{name} = {symbolic}")
    lines.append(f"{name} = {substituted}")
    lines.append(f"{name} = {fmt(calc.value)}")
    return lines


def build_mason_report(graph: SignalFlowGraph, result: MasonGainResult) -> str:
    """Return the whole Part 1 report as plain text."""
    lines: list[str] = []
    loop_number = {loop: number for number, loop in enumerate(result.loops, start=1)}

    _heading(lines, "1. Signal flow graph")
    lines.append("Nodes: " + ", ".join(node.node_id for node in graph.nodes))
    lines.append(f"Input node: {graph.input_node_id}    Output node: {graph.output_node_id}")
    lines.append("Branches (source → target, gain):")
    for branch in graph.branches:
        lines.append(
            f"  {branch.branch_id}: {branch.source_node_id} → "
            f"{branch.target_node_id}, gain = {fmt(branch.gain)}"
        )

    _heading(lines, "2. Forward paths")
    lines.append("Mi = product of the branch gains along forward path i.")
    if not result.forward_paths:
        lines.append("There is no forward path from the input to the output.")
    for number, path in enumerate(result.forward_paths, start=1):
        route = " → ".join(
            (graph.input_node_id, *(b.target_node_id for b in path.branches))
        )
        gains = [b.gain for b in path.branches]
        if len(gains) == 1:
            product = f"M{number} = {fmt(path.gain)}"
        else:
            product = f"M{number} = {product_text(gains)} = {fmt(path.gain)}"
        lines.append(f"Path {number}: {route}")
        lines.append(f"   {product}")

    _heading(lines, "3. Individual loops")
    lines.append("Li = product of the branch gains around loop i.")
    if not result.loops:
        lines.append("The graph has no loops.")
    for number, loop in enumerate(result.loops, start=1):
        gains = [b.gain for b in loop.branches]
        if len(gains) == 1:
            product = f"L{number} = {fmt(loop.gain)}"
        else:
            product = f"L{number} = {product_text(gains)} = {fmt(loop.gain)}"
        lines.append(f"Loop {number}: {_loop_route(loop)}")
        lines.append(f"   {product}")

    _heading(lines, "4. Non-touching loop combinations")
    lines.append("Loops that share no node are non-touching.")
    combos = find_non_touching_loop_combinations(result.loops)
    if not combos:
        lines.append("No combination of mutually non-touching loops exists.")
    by_size: dict[int, list[tuple[Loop, ...]]] = defaultdict(list)
    for combo in combos:
        by_size[len(combo)].append(combo)
    for size in sorted(by_size):
        lines.append(f"{size} mutually non-touching loops:")
        for combo in by_size[size]:
            names = "·".join(f"L{loop_number[loop]}" for loop in combo)
            gains = [loop.gain for loop in combo]
            value = 1.0
            for gain in gains:
                value *= gain
            lines.append(f"   {names} = {product_text(gains)} = {fmt(value)}")

    _heading(lines, "5. Graph determinant Δ")
    lines.append("Δ = 1 - Σ(loop gains) + Σ(2 non-touching loops) - Σ(3 non-touching loops) + ...")
    lines.extend(_delta_lines("Δ", result.delta))

    _heading(lines, "6. Path cofactors Δi (loops touching path i are excluded)")
    all_numbers = set(loop_number.values())
    for index, cofactor in enumerate(result.path_cofactors, start=1):
        kept = {t.loop_numbers[0] for t in cofactor.delta_i.terms if len(t.loop_numbers) == 1}
        touching = sorted(all_numbers - kept)
        lines.append(f"Path {index}:")
        lines.append(
            "   loops touching it (removed): "
            + (", ".join(f"L{n}" for n in touching) if touching else "none")
        )
        lines.append(
            "   loops kept: " + (", ".join(f"L{n}" for n in sorted(kept)) if kept else "none")
        )
        lines.extend("   " + text for text in _delta_lines(f"Δ{index}", cofactor.delta_i))

    _heading(lines, "7. Mason's gain formula")
    lines.append("T = (M1Δ1 + M2Δ2 + ... + MmΔm) / Δ")
    terms: list[str] = []
    for index, cofactor in enumerate(result.path_cofactors, start=1):
        m, d = cofactor.path.gain, cofactor.delta_i.value
        lines.append(
            f"M{index}Δ{index} = {fmt_paren(m)} × {fmt_paren(d)} = {fmt(cofactor.numerator_term)}"
        )
        terms.append(fmt_paren(cofactor.numerator_term))
    numerator = result.numerator
    if terms:
        lines.append(f"Numerator = {' + '.join(terms)} = {fmt(numerator)}")
    else:
        lines.append(f"Numerator = 0   (no forward paths)")
    delta = result.delta.value
    gain = result.gain
    lines.append(f"T = {fmt_paren(numerator)} / {fmt_paren(delta)} = {fmt(gain)}")

    exact = Fraction(numerator).limit_denominator(10**6) / Fraction(delta).limit_denominator(10**6)
    if abs(float(exact) - gain) <= 1e-9 * max(1.0, abs(gain)):
        compact = str(exact.numerator) if exact.denominator == 1 else f"{exact.numerator}/{exact.denominator}"
        lines.append("")
        lines.append(f"Simplified transfer function: {graph.output_node_id}/{graph.input_node_id} = {compact}")
        if exact.denominator != 1:
            lines.append(f"                              ≈ {fmt(gain)}")
    else:
        lines.append("")
        lines.append(f"Transfer function: {graph.output_node_id}/{graph.input_node_id} = {fmt(gain)}")
    return "\n".join(lines) + "\n"
