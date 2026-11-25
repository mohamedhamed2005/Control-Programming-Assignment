"""Build the Routh table, classify stability, and verify it with numerical poles."""

from dataclasses import dataclass
from fractions import Fraction

import numpy as np


class RouthSpecialCaseError(ValueError):
    """Raised for the special cases this assignment excludes.

    A zero first-column entry (which also covers an all-zero row, because a row
    that is entirely zero has a zero first entry) needs the epsilon or
    auxiliary-polynomial methods, which are outside the assignment's scope.
    """


@dataclass(frozen=True, slots=True)
class RouthStep:
    """One calculated Routh-table entry and the four numbers it was built from.

    For the new row ``k`` the two rows above it are named ``upper`` (row k-2)
    and ``pivot`` (row k-1)::

        value = (pivot_lead * upper_next - upper_lead * pivot_next) / pivot_lead
    """

    power: int  # power of s labelling the row being computed
    column: int  # zero-based column inside that row
    pivot_lead: Fraction
    upper_next: Fraction
    upper_lead: Fraction
    pivot_next: Fraction
    value: Fraction


@dataclass(frozen=True, slots=True)
class RouthResult:
    """The complete Routh table together with its stability conclusion."""

    coefficients: tuple[Fraction, ...]  # highest power of s first
    rows: tuple[tuple[Fraction, ...], ...]  # rows[0] is the s^n row
    steps: tuple[RouthStep, ...]

    @property
    def degree(self) -> int:
        return len(self.coefficients) - 1

    @property
    def row_powers(self) -> tuple[int, ...]:
        """Power of s that labels each row: n, n-1, ..., 0."""
        return tuple(range(self.degree, -1, -1))

    @property
    def first_column(self) -> tuple[Fraction, ...]:
        return tuple(row[0] for row in self.rows)

    @property
    def sign_change_positions(self) -> tuple[int, ...]:
        """Indices ``i`` where first_column[i] and first_column[i+1] differ in sign."""
        column = self.first_column
        return tuple(
            index
            for index in range(len(column) - 1)
            if (column[index] > 0) != (column[index + 1] > 0)
        )

    @property
    def sign_changes(self) -> int:
        """Number of right-half-plane poles predicted by the Routh criterion."""
        return len(self.sign_change_positions)

    @property
    def is_stable(self) -> bool:
        return self.sign_changes == 0


@dataclass(frozen=True, slots=True)
class PoleVerification:
    """Numerically computed poles compared against the Routh prediction."""

    poles: tuple[complex, ...]
    tolerance: float
    rhp_poles: tuple[complex, ...]
    near_axis_poles: tuple[complex, ...]
    routh_rhp_count: int

    @property
    def rhp_count(self) -> int:
        return len(self.rhp_poles)

    @property
    def agrees(self) -> bool:
        return self.rhp_count == self.routh_rhp_count


def build_routh_table(coefficients: tuple[Fraction, ...]) -> RouthResult:
    """Construct the Routh table for coefficients ordered from s^n down to s^0.

    Exact ``Fraction`` arithmetic is used so a first-column entry is zero only
    when it really is zero, never because of rounding.
    """
    if len(coefficients) < 2:
        raise ValueError("The characteristic equation needs degree 1 or higher.")

    degree = len(coefficients) - 1
    width = degree // 2 + 1  # number of entries in the widest (s^n) row

    def padded(values: list[Fraction]) -> tuple[Fraction, ...]:
        return tuple(values) + (Fraction(0),) * (width - len(values))

    # First two rows are copied alternately from the coefficients.
    rows: list[tuple[Fraction, ...]] = [
        padded(list(coefficients[0::2])),
        padded(list(coefficients[1::2])),
    ]
    steps: list[RouthStep] = []

    for row_index in range(2, degree + 1):
        power = degree - row_index
        upper = rows[row_index - 2]
        pivot = rows[row_index - 1]
        pivot_lead = pivot[0]

        if pivot_lead == 0:
            raise RouthSpecialCaseError(
                f"The first-column entry of the s^{power + 1} row is zero. "
                "This special case is outside the assignment's scope."
            )

        # Row s^p has floor(p / 2) + 1 meaningful entries; the rest stay zero.
        new_row = [Fraction(0)] * width
        for column in range(power // 2 + 1):
            upper_next = upper[column + 1] if column + 1 < width else Fraction(0)
            pivot_next = pivot[column + 1] if column + 1 < width else Fraction(0)
            value = (pivot_lead * upper_next - upper[0] * pivot_next) / pivot_lead
            new_row[column] = value
            steps.append(
                RouthStep(
                    power=power,
                    column=column,
                    pivot_lead=pivot_lead,
                    upper_next=upper_next,
                    upper_lead=upper[0],
                    pivot_next=pivot_next,
                    value=value,
                )
            )
        rows.append(tuple(new_row))

    if rows[-1][0] == 0:
        raise RouthSpecialCaseError(
            "The first-column entry of the s^0 row is zero. "
            "This special case is outside the assignment's scope."
        )

    return RouthResult(
        coefficients=tuple(coefficients), rows=tuple(rows), steps=tuple(steps)
    )


def verify_with_poles(
    result: RouthResult, tolerance: float = 1e-8
) -> PoleVerification:
    """Find the roots numerically and count those in the right half-plane.

    A root counts as right-half-plane when its real part exceeds ``tolerance``.
    Roots whose real part lies within ``1e-6`` of the imaginary axis are
    reported separately because rounding could place them on either side.
    """
    poles = tuple(complex(p) for p in np.roots([float(c) for c in result.coefficients]))
    rhp = tuple(p for p in poles if p.real > tolerance)
    near_axis = tuple(p for p in poles if abs(p.real) <= 1e-6)
    return PoleVerification(
        poles=poles,
        tolerance=tolerance,
        rhp_poles=rhp,
        near_axis_poles=near_axis,
        routh_rhp_count=result.sign_changes,
    )
