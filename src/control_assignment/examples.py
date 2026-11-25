"""Ready-made inputs for the GUI (and handy for the report's sample runs)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphExample:
    name: str
    nodes: str
    branches: tuple[tuple[str, str, str], ...]
    input_node: str
    output_node: str


GRAPH_EXAMPLES: tuple[GraphExample, ...] = (
    GraphExample(
        name="Example 1: 2 forward paths, 6 loops, 8 non-touching groups",
        nodes="R, x1, x2, x3, x4, x5, C",
        branches=(
            ("R", "x1", "1"),
            ("x1", "x2", "2"),
            ("x2", "x3", "3"),
            ("x3", "x4", "4"),
            ("x4", "x5", "5"),
            ("x5", "C", "1"),
            ("x2", "x4", "6"),
            ("x2", "x1", "-1"),
            ("x3", "x2", "-0.5"),
            ("x4", "x3", "-0.2"),
            ("x5", "x4", "-0.1"),
            ("x5", "x5", "-0.3"),
        ),
        input_node="R",
        output_node="C",
    ),
    GraphExample(
        name="Example 2: 4 forward paths, 8 loops, mixed touching loops",
        nodes="R, a, b, c, d, C",
        branches=(
            ("R", "a", "1"),
            ("a", "b", "5"),
            ("b", "c", "2"),
            ("c", "d", "4"),
            ("d", "C", "1"),
            ("a", "c", "3"),
            ("b", "d", "-2"),
            ("c", "b", "-1"),
            ("d", "c", "-3"),
            ("d", "a", "-0.5"),
            ("b", "b", "-4"),
        ),
        input_node="R",
        output_node="C",
    ),
    GraphExample(
        name="Example 3: 2 parallel paths, each untouched by one loop",
        nodes="R, a, b, c, d, e, C",
        branches=(
            ("R", "a", "1"),
            ("a", "b", "2"),
            ("b", "c", "3"),
            ("c", "C", "1"),
            ("a", "d", "4"),
            ("d", "e", "5"),
            ("e", "C", "2"),
            ("c", "b", "-0.5"),
            ("e", "d", "-0.2"),
        ),
        input_node="R",
        output_node="C",
    ),
)

ROUTH_EXAMPLES: tuple[tuple[str, str], ...] = (
    ("Given example (unstable)", "s^5 + s^4 + 10s^3 + 72s^2 + 152s + 240 = 0"),
    ("Stable: (s+1)(s+2)(s+3)", "s^3 + 6s^2 + 11s + 6 = 0"),
    ("Stable: (s+1)(s+2)(s+3)(s+4)", "s^4 + 10s^3 + 35s^2 + 50s + 24 = 0"),
    ("Unstable (2 RHP poles)", "s^4 + 2s^3 + 3s^2 + 4s + 5 = 0"),
    ("Unstable (cubic, 2 RHP poles)", "s^3 + 2s^2 + 3s + 10 = 0"),
)
