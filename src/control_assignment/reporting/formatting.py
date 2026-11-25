"""Number and expression formatting shared by the text reports."""

from collections.abc import Iterable
from fractions import Fraction


def fmt(value: float | Fraction, digits: int = 10) -> str:
    """Format a number compactly: 12.0 -> '12', 0.1 + 0.2 -> '0.3'."""
    number = float(value)
    if abs(number) < 1e-12:
        number = 0.0
    text = f"{number:.{digits}g}"
    return "0" if text == "-0" else text


def fmt_paren(value: float | Fraction) -> str:
    """Like ``fmt`` but wraps negative numbers in parentheses for substitutions."""
    text = fmt(value)
    return f"({text})" if text.startswith("-") else text


def product_text(values: Iterable[float | Fraction]) -> str:
    """Return ``2 × (-3) × 4`` for the given factors."""
    return " × ".join(fmt_paren(value) for value in values)


def polynomial_text(coefficients: Iterable[Fraction]) -> str:
    """Return ``s^5 + s^4 + 10s^3 + ... + 240`` (highest power first)."""
    values = tuple(coefficients)
    degree = len(values) - 1
    pieces: list[str] = []
    for index, coefficient in enumerate(values):
        power = degree - index
        magnitude = abs(coefficient)
        number = "" if (magnitude == 1 and power > 0) else fmt(magnitude)
        if power == 0:
            body = number
        elif power == 1:
            body = f"{number}s"
        else:
            body = f"{number}s^{power}"
        if index == 0:
            pieces.append(body if coefficient > 0 else f"-{body}")
        else:
            pieces.append(f"{'+' if coefficient > 0 else '-'} {body}")
    return " ".join(pieces)


def complex_text(value: complex, digits: int = 6) -> str:
    """Format a pole as ``-1.5 + 2j`` with a tidy sign."""
    real = 0.0 if abs(value.real) < 1e-12 else value.real
    imag = 0.0 if abs(value.imag) < 1e-12 else value.imag
    if imag == 0:
        return f"{real:.{digits}g}"
    sign = "+" if imag > 0 else "-"
    return f"{real:.{digits}g} {sign} {abs(imag):.{digits}g}j"
