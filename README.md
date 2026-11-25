# Signal Flow Graphs & Routh Stability (CSE 341 Programming Assignment)

Desktop program (Python + PySide6) with two tabs:

* **Part 1** – draw a signal flow graph, list forward paths / loops / non-touching loops,
  compute Δ, Δᵢ and Mason's gain formula with every substitution shown.
* **Part 2** – build the Routh table with calculation steps, classify stability, count
  right-half-plane poles and verify them with numerically computed roots.

## Set up and run

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                       # installs numpy, PySide6 and the dev tools
uv run python -m control_assignment      # or: uv run control-assignment
uv run pytest                 # run the test-suite
```

### Running from the `src/` folder (without uv run)

You can also run the program directly with Python by changing into the `src/` directory.
The package lives in `src/`, so Python can only find it from there (or if `src` is on `PYTHONPATH`).

```bash
# 1. Install the dependencies once (from the project root)
uv sync                       # or: pip install numpy PySide6

# 2. Change into src/ and run the package
cd src
python -m control_assignment
```

If you used `uv sync`, activate the virtual environment first so `python` can see the installed packages:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (cmd)
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

Optional Windows/macOS/Linux executable:

```bash
uv add --dev pyinstaller
uv run pyinstaller --noconsole --name ControlAssignment --paths src src/control_assignment/__main__.py
```
The executable is created in `dist/ControlAssignment/`.

## Using Part 1

1. Type the node names in **Nodes** (commas or spaces), e.g. `R, x1, x2, C`.
2. Pick the **Input node** and **Output node**.
3. Fill the branch table: *From*, *To*, *Gain* (`2`, `-0.5` or `1/3`). Use **Add branch** / **Remove selected**.
   A branch with the same From and To is a self-loop; two rows with the same endpoints are parallel branches.
4. Press **Analyze**. The graph is drawn (forward branches curve above the line, feedback
   branches below) and the report lists M₁…Mₘ, L₁…Lₙ, non-touching combinations, Δ, each Δᵢ and T.
5. **Load example** fills three ready-made graphs. **Save report…** / **Save graph image…** export results.

## Using Part 2

Type the characteristic equation (`s^5 + s^4 + 10s^3 + 72s^2 + 152s + 240 = 0`) or just
the coefficients (`1 1 10 72 152 240`) and press **Analyze**.
All powers from s⁰ to sⁿ must be present with the same sign; special cases are rejected with a message.

How to read the result: the yellow/red column is the first column of the Routh table; every sign
change between consecutive first-column entries is one right-half-plane pole. The s-plane plot and the
report confirm the count with the roots from `numpy.roots` (a pole is "right half-plane" if Re(p) > 1e-8).

## Code map

| Path | Role |
|---|---|
| `models/signal_graph.py` | Immutable `Node`, `Branch`, `SignalFlowGraph` with validation |
| `analysis/forward_paths.py` | DFS for all simple forward paths |
| `analysis/loops.py` | Simple loops (canonical start node) + non-touching combinations |
| `analysis/mason.py` | Δ, Δᵢ and Mason's formula (`calculate_mason_gain`) |
| `analysis/routh.py` | Exact (`Fraction`) Routh table, steps, sign changes, numerical pole check |
| `parsing/` | Equation parser and graph-table validation |
| `reporting/` | Step-by-step text for both parts |
| `gui/` | Main window, two tabs, graph canvas, pole plot |
| `examples.py` | Example graphs and polynomials |
