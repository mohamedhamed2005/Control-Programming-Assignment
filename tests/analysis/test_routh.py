from fractions import Fraction

import numpy as np
import pytest

from control_assignment.analysis.routh import (
    RouthSpecialCaseError,
    build_routh_table,
    verify_with_poles,
)
from control_assignment.examples import ROUTH_EXAMPLES
from control_assignment.parsing.polynomial import parse_characteristic_equation


def table_for(text: str):
    return build_routh_table(parse_characteristic_equation(text))


def test_assignment_example_table_and_count():
    result = table_for("s^5 + s^4 + 10s^3 + 72s^2 + 152s + 240 = 0")
    first = [float(v) for v in result.first_column]
    assert first == pytest.approx([1, 1, -62, 4376 / 62, 122.82266910420475, 240])
    assert result.sign_changes == 2
    assert not result.is_stable


def test_stable_cubic():
    result = table_for("s^3 + 6s^2 + 11s + 6")
    assert [float(v) for v in result.first_column] == [1, 6, 10, 6]
    assert result.is_stable


def test_table_shape_and_labels():
    result = table_for("s^4 + 2s^3 + 3s^2 + 4s + 5")
    assert len(result.rows) == 5
    assert result.row_powers == (4, 3, 2, 1, 0)
    assert all(len(row) == 3 for row in result.rows)


def test_every_example_agrees_with_numerical_poles():
    for _, text in ROUTH_EXAMPLES:
        result = table_for(text)
        assert verify_with_poles(result).agrees


def test_random_same_sign_polynomials_agree_with_roots():
    rng = np.random.default_rng(7)
    checked = 0
    for _ in range(300):
        degree = int(rng.integers(2, 8))
        coefficients = tuple(Fraction(int(c)) for c in rng.integers(1, 30, degree + 1))
        try:
            result = build_routh_table(coefficients)
        except RouthSpecialCaseError:
            continue
        verification = verify_with_poles(result)
        if verification.near_axis_poles:
            continue
        assert verification.agrees
        checked += 1
    assert checked > 100


def test_zero_first_column_entry_is_rejected():
    # s^4 + s^3 + s^2 + s + 1 gives a zero in the s^2... row (a special case).
    with pytest.raises(RouthSpecialCaseError):
        table_for("s^4 + s^3 + s^2 + s + 1")


def test_steps_show_the_formula_inputs():
    result = table_for("s^3 + 6s^2 + 11s + 6")
    step = result.steps[0]
    assert (step.pivot_lead, step.upper_next, step.upper_lead, step.pivot_next) == (6, 11, 1, 6)
    assert step.value == 10
