# CubeSat Cold-Gas & Resistojet Thruster Virtual Lab (AME 310)

An interactive virtual thermodynamics laboratory modeling a **Category 6 Integrated SSSF + Transient System**: a variable-mass pressurized CubeSat propellant tank coupled to Steady-State Steady-Flow (SSSF) propulsion hardware (optional isenthalpic pressure regulator, optional electrical resistojet heater, and a choked converging-diverging vacuum nozzle).

**Live App:** [Launch Virtual Lab on Streamlit Community Cloud](https://cubesatthrusterame310-lzfcrvyux5qb8kdlqt8q4r.streamlit.app/)

---

## Key Features

* **Free-Play Mode:** Interactive 60 FPS blowdown simulation with quick presets, Core/Advanced controls, and a 5-step Guided Component Walkthrough featuring rendered LaTeX governing equations and live state readouts.
* **Mission Mode (Hohmann Transfers):** Three escalating two-burn orbit-raising missions with locked CubeSat bus hardware (`V_tank`, `P_0`, `T_0`, `m_dry`), upfront pass/fail criteria, explicit burn execution, and animated Burn 1 → Coast → Burn 2 playback.
* **Comparison Mode:** Save any two Free-Play runs as **Case A** and **Case B** to overlay $\Delta v$, thrust, pressure, temperature, and $I_{sp}$ trajectories side by side.
* **Validation Audit:** Real-time First Law energy conservation and Second Law entropy generation verification.

---

## Verification Summary

| Benchmark | Acceptance Criterion | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| First Law Energy Conservation | Relative Error $< 10^{-5}$ | $3.58 \times 10^{-10}$ ($0.0001\text{ J}$) | PASS |
| Second Law (SSSF Nozzle) | $\min(\dot{S}_{\text{gen}}) \ge 0\text{ W/K}$ | $11.60\text{ W/K}$ | PASS |
| Analytical Isentropic Blowdown | Max Temp Rel. Error $< 10^{-5}$ | $1.26 \times 10^{-10}$ ($3.23 \times 10^{-8}\text{ K}$) | PASS |
| ODE Solver Tolerance Stability | Baseline vs. Fine Diff $< 10^{-4}$ | $1.25 \times 10^{-10}$ | PASS |

---

## Run Locally

```bash
git clone [https://github.com/samleews/CubeSat_Thruster_AME310.git](https://github.com/samleews/CubeSat_Thruster_AME310.git)
cd CubeSat_Thruster_AME310
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

---

## Repository Structure

```text
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── thermo_engine/          # Ideal-gas properties, SSSF nozzle, transient ODE solver, validation
├── visuals/                # Live Canvas player, Plotly dashboards, Hohmann animations
└── game/                   # Guided component walkthrough & locked-bus mission definitions
```