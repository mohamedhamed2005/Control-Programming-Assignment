from control_assignment.analysis.mason import calculate_mason_gain
from control_assignment.analysis.routh import build_routh_table, verify_with_poles
from control_assignment.examples import GRAPH_EXAMPLES, ROUTH_EXAMPLES
from control_assignment.parsing.graph_input import build_graph, parse_node_names
from control_assignment.parsing.polynomial import parse_characteristic_equation
from control_assignment.reporting.formatting import polynomial_text
from control_assignment.reporting.mason_report import build_mason_report
from control_assignment.reporting.routh_report import build_routh_report


def test_mason_report_has_every_required_section():
    example = GRAPH_EXAMPLES[2]
    graph = build_graph(parse_node_names(example.nodes), example.branches, example.input_node, example.output_node)
    text = build_mason_report(graph, calculate_mason_gain(graph))
    for needle in ("M1 = 1 × 2 × 3 × 1 = 6", "L1 = 3 × (-0.5) = -1.5", "L1·L2 = (-1.5) × (-1) = 1.5",
                   "Δ = 5", "Δ1 = 2", "Δ2 = 2.5", "M2Δ2 = 40 × 2.5 = 100", "= 112/5"):
        assert needle in text, needle


def test_routh_report_has_table_steps_and_verification():
    coefficients = parse_characteristic_equation(ROUTH_EXAMPLES[0][1])
    result = build_routh_table(coefficients)
    text = build_routh_report(result, verify_with_poles(result))
    for needle in ("(1 × 10 - 1 × 72) / 1", "s^0 |", "sign changes", "UNSTABLE", "AGREES"):
        assert needle in text, needle


def test_polynomial_text_round_trips():
    original = "s^5 + s^4 + 10s^3 + 72s^2 + 152s + 240"
    assert polynomial_text(parse_characteristic_equation(original)) == original
