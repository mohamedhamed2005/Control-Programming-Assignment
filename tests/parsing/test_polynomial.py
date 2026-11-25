from fractions import Fraction

import pytest

from control_assignment.parsing.polynomial import PolynomialError, parse_characteristic_equation


def values(text):
    return [float(c) for c in parse_characteristic_equation(text)]


def test_assignment_example():
    assert values("s^5 + s^4 + 10s^3 + 72s^2 + 152s + 240 = 0") == [1, 1, 10, 72, 152, 240]


@pytest.mark.parametrize(
    "text",
    ["s**2 + 3*s + 2", "S^2+3S+2=0", "s^2 + 3s + 2 = 0.0", "1 3 2", "1, 3, 2"],
)
def test_equivalent_spellings(text):
    assert values(text) == [1, 3, 2]


def test_decimals_stay_exact():
    assert parse_characteristic_equation("s^2 + 0.1s + 0.2")[1] == Fraction(1, 10)


def test_all_negative_is_allowed():
    assert values("-s^2 - 3s - 2") == [-1, -3, -2]


@pytest.mark.parametrize(
    "text",
    ["", "s^3 + 2s + 1", "s^2 - 3s + 2", "s^2 + 3s + 2 = 5", "s^2 + s^2 + 1", "s^2 + ? + 1", "5"],
)
def test_bad_input_is_rejected(text):
    with pytest.raises(PolynomialError):
        parse_characteristic_equation(text)
