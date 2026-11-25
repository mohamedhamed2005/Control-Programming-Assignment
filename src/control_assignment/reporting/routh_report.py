"""Write the step-by-step Part 2 report: table, steps, stability, pole check."""

from control_assignment.analysis.routh import PoleVerification, RouthResult
from control_assignment.reporting.formatting import (
    complex_text,
    fmt,
    fmt_paren,
    polynomial_text,
)


def _heading(lines: list[str], title: str) -> None:
    lines.extend(["", title, "=" * len(title)])


def routh_table_text(result: RouthResult) -> str:
    """Return the table with aligned columns and ``s^k`` row labels."""
    cells = [[fmt(value) for value in row] for row in result.rows]
    width = max(len(text) for row in cells for text in row)
    out = []
    for power, row in zip(result.row_powers, cells, strict=True):
        label = f"s^{power}".ljust(4)
        out.append(f"{label}| " + "  ".join(text.rjust(width) for text in row))
    return "\n".join(out)


def build_routh_report(result: RouthResult, verification: PoleVerification) -> str:
    """Return the whole Part 2 report as plain text."""
    lines: list[str] = []
    n = result.degree

    _heading(lines, "1. Characteristic equation")
    lines.append(f"{polynomial_text(result.coefficients)} = 0")
    lines.append(f"Degree n = {n}; coefficients (s^{n} ... s^0): "
                 + ", ".join(fmt(c) for c in result.coefficients))

    _heading(lines, "2. First two rows")
    lines.append(f"s^{n}  row: coefficients of s^{n}, s^{n - 2}, s^{n - 4}, ...")
    lines.append(f"   = {', '.join(fmt(v) for v in result.coefficients[0::2])}")
    lines.append(f"s^{n - 1}  row: coefficients of s^{n - 1}, s^{n - 3}, s^{n - 5}, ...")
    lines.append(f"   = {', '.join(fmt(v) for v in result.coefficients[1::2])}")

    _heading(lines, "3. Calculation steps")
    lines.append("Each new entry = (P1 × U(j+1) - U1 × P(j+1)) / P1, where")
    lines.append("   U = row two above, P = row directly above (pivot row),")
    lines.append("   P1, U1 = first entries of those rows, (j+1) = next column.")
    for step in result.steps:
        label = f"s^{step.power}, column {step.column + 1}"
        lines.append(f"{label}:")
        lines.append(
            f"   = ({fmt_paren(step.pivot_lead)} × {fmt_paren(step.upper_next)} - "
            f"{fmt_paren(step.upper_lead)} × {fmt_paren(step.pivot_next)}) / {fmt_paren(step.pivot_lead)}"
        )
        numerator = step.pivot_lead * step.upper_next - step.upper_lead * step.pivot_next
        lines.append(f"   = {fmt_paren(numerator)} / {fmt_paren(step.pivot_lead)} = {fmt(step.value)}")
    if not result.steps:
        lines.append("(no further rows to calculate)")

    _heading(lines, "4. Complete Routh table")
    lines.append(routh_table_text(result))

    _heading(lines, "5. Stability by the Routh criterion")
    column = result.first_column
    lines.append("First column: " + ", ".join(fmt(v) for v in column))
    positions = result.sign_change_positions
    for index in range(len(column) - 1):
        a, b = column[index], column[index + 1]
        change = "sign change" if index in positions else "same sign"
        lines.append(
            f"   s^{result.row_powers[index]} → s^{result.row_powers[index + 1]}: "
            f"{fmt(a)} → {fmt(b)}  ({change})"
        )
    lines.append(f"Number of sign changes = number of right-half-plane poles = {result.sign_changes}")
    if result.is_stable:
        lines.append("Conclusion: STABLE - no sign change, all poles lie in the left half-plane.")
    else:
        lines.append(
            f"Conclusion: UNSTABLE - {result.sign_changes} pole(s) in the right half-plane."
        )

    _heading(lines, "6. Numerical pole verification")
    lines.append("Roots of the characteristic polynomial (numpy.roots):")
    for index, pole in enumerate(verification.poles, start=1):
        side = "RIGHT half-plane" if pole in verification.rhp_poles else "left half-plane"
        lines.append(f"   p{index} = {complex_text(pole)}   ({side})")
    lines.append(
        f"Tolerance: a pole is counted as right-half-plane when Re(p) > {verification.tolerance:g}"
    )
    lines.append(f"Right-half-plane poles found numerically = {verification.rhp_count}")
    lines.append(f"Right-half-plane poles predicted by Routh = {verification.routh_rhp_count}")
    if verification.near_axis_poles:
        lines.append("Note: some poles lie within 1e-6 of the imaginary axis, so the numerical count is sensitive to rounding.")
    lines.append(
        "Verification: AGREES ✔" if verification.agrees else "Verification: DOES NOT AGREE ✘"
    )
    return "\n".join(lines) + "\n"
