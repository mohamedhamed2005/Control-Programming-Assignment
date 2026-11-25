"""Parse a characteristic equation such as ``s^5 + s^4 + 10s^3 + 72s^2 + 152s + 240 = 0``."""

import re
from fractions import Fraction

_TERM_SPLIT = re.compile(r"[+-]?[^+-]+")
_TERM = re.compile(r"^([+-]?)(\d+\.?\d*|\.\d+)?\*?(?:(s)(?:\^(\d+))?)?$")


class PolynomialError(ValueError):
    """Raised when the characteristic equation cannot be used."""


def parse_characteristic_equation(text: str) -> tuple[Fraction, ...]:
    """Return the coefficients, highest power of s first.

    Two input styles are accepted:

    * an equation in ``s`` (``^`` or ``**`` for powers, optional ``* ``, optional ``= 0``);
    * a plain list of coefficients separated by commas or spaces, highest power first.

    The assignment guarantees every power from s^0 to s^n is present with the
    same sign, so anything else is rejected with an explanatory message.
    """
    cleaned = text.replace("\u2212", "-").replace("**", "^").strip()
    if not cleaned:
        raise PolynomialError("Enter a characteristic equation.")

    if "s" not in cleaned.lower():
        coefficients = _parse_coefficient_list(cleaned)
    else:
        coefficients = _parse_equation(cleaned.lower())

    _validate(coefficients)
    return coefficients


def _parse_coefficient_list(text: str) -> tuple[Fraction, ...]:
    parts = [part for part in re.split(r"[,\s;]+", text) if part]
    try:
        return tuple(Fraction(part) for part in parts)
    except (ValueError, ZeroDivisionError) as error:
        raise PolynomialError(f"Cannot read the coefficient list: {error}") from error


def _parse_equation(text: str) -> tuple[Fraction, ...]:
    if "=" in text:
        left, _, right = text.partition("=")
        if right.replace(" ", "") not in {"0", "0.0", ""}:
            raise PolynomialError("The right-hand side of the equation must be 0.")
        text = left

    compact = text.replace(" ", "")
    if not compact:
        raise PolynomialError("The left-hand side of the equation is empty.")

    by_power: dict[int, Fraction] = {}
    for term in _TERM_SPLIT.findall(compact):
        match = _TERM.match(term)
        if match is None:
            raise PolynomialError(f"Cannot understand the term '{term}'.")
        sign, number, variable, power_text = match.groups()
        if number is None and variable is None:
            raise PolynomialError(f"Cannot understand the term '{term}'.")

        coefficient = Fraction(number) if number is not None else Fraction(1)
        if sign == "-":
            coefficient = -coefficient
        power = (int(power_text) if power_text is not None else 1) if variable else 0

        if power in by_power:
            raise PolynomialError(f"The power s^{power} appears more than once.")
        by_power[power] = coefficient

    degree = max(by_power)
    missing = [power for power in range(degree + 1) if power not in by_power]
    if missing:
        names = ", ".join(f"s^{power}" for power in reversed(missing))
        raise PolynomialError(f"Missing coefficient(s): {names}.")
    return tuple(by_power[power] for power in range(degree, -1, -1))


def _validate(coefficients: tuple[Fraction, ...]) -> None:
    if len(coefficients) < 2:
        raise PolynomialError("The equation must have degree 1 or higher.")
    if any(coefficient == 0 for coefficient in coefficients):
        raise PolynomialError(
            "Every coefficient from s^0 to s^n must be non-zero "
            "(a missing power is a case outside this assignment)."
        )
    if len({coefficient > 0 for coefficient in coefficients}) != 1:
        raise PolynomialError("All coefficients must have the same sign.")
