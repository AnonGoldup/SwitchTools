# SwitchTools

CEC-based electrical calculators (Python / PyQt6).

## Run

```
python app.py        (or double-click run.bat)
```

Requires Python 3.10+ and PyQt6 (`pip install PyQt6`).
`build.bat` builds a standalone `dist\SwitchTools.exe` with PyInstaller.

## Layout

```
app.py                      entry point
libraries/
    cec_data.py             all CEC table data + sizing helpers
    UI/
        main_window.py      main window / tab host
        pipe_fill_tab.py    Pipe Fill tab
        voltage_drop_tab.py Voltage Drop tab
        transformer_tab.py  Transformers tab
```

## Tools

### Pipe Fill (CEC Rule 12-910, Tables 8 / 9 / 10)
- Pick a conduit type (all CEC Table 9 types, plus **Custom** — enter an
  internal diameter in mm), a wire type (CEC Tables 10A–10D), and a max
  fill % (default 40%; a hint shows the CEC Table 8 value for the current
  conductor count: 53% for 1, 31% for 2, 40% for 3+).
- Type a quantity beside any wire size — the required conduit trade size and
  actual fill % update automatically.
- **Ampacity derating (CEC Table 5C):** shows the correction factor for the
  total conductor count (1–3: 100%, 4–6: 80%, 7–24: 70%, 25–42: 60%,
  43+: 50%) and a per-size table of base vs derated ampacity (CEC Table 2
  copper / Table 4 aluminum, at the selected 60/75/90 °C column).

### Voltage Drop (CEC Rule 8-102)
- Enter system voltage, phase, load current, one-way run length (m or ft),
  material, size, and parallel sets.
- Shows drop in volts and %, voltage at the load, pass/fail vs your limit
  (default 3%), the minimum size that meets the limit, and the maximum run
  length for the selected size. Uses DC resistance at 75 °C.

### Transformers (CEC Rules 26-250s, dry-type ≤ 750 V)
- Enter kVA, phase, and primary/secondary voltages.
- Shows primary and secondary full-load current, conductor sizes at 125%
  (Rules 26-256 / 26-258), and primary breaker min/max — max 125% with
  round-up per Rule 26-252 (no round-up below 9 A), or up to 300% when the
  "secondary OCP" box is checked (Rule 26-254), which also sizes the
  secondary breaker at ≤ 125%.

## Data

All table data lives in `libraries/cec_data.py`. Values were compiled from
published dimensional data for the same conduit/conductor products and match
the CEC tables to within rounding — verify against your current code book
before relying on results for permit/inspection work.
