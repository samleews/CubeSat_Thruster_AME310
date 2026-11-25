GUIDED_STEPS = [
    {
        "title": "Step 1 of 5 — Transient Propellant Tank",
        "component_name": "Propellant Tank (Transient Control Volume)",
        "cv_type": "Variable-Mass Transient Control Volume",
        "equation": r"\frac{dm}{dt} = -\dot{m}, \qquad \frac{dT}{dt} = \frac{\dot{Q}_{\text{wall}}}{m c_v} - (\gamma - 1)\frac{T}{m}\dot{m}",
        "physics": (
            "As propellant exits the rigid tank, the remaining gas expands internally to push mass out the nozzle, "
            "causing **adiabatic blowdown cooling**. Ambient wall heating ($\\dot{Q}_{\\text{wall}}$) offsets this drop "
            "and warms the gas during coast phases."
        ),
        "summary": "Start with an unregulated nitrogen blowdown to observe how tank pressure and temperature decay together as propellant mass leaves.",
        "prompt": "Press Play on the live player below and watch tank pressure and temperature drop over the 90 s burn.",
        "hint": "Click the **Baseline** preset in the sidebar if you changed any settings.",
        "check": lambda cfg: not cfg["use_regulator"] and not cfg["use_heater"],
        "live_metrics": lambda res, cfg: f"Initial Mass: `{res['m_init']:.3f} kg`  |  Final Temp: `{res['T'][-1]:.1f} K`  |  Min Temp: `{res['T'].min():.1f} K`",
    },
    {
        "title": "Step 2 of 5 — Pressure Regulator",
        "component_name": "Pressure Regulator (SSSF Throttling Valve)",
        "cv_type": "Steady-State Steady-Flow (Isenthalpic)",
        "equation": r"h_1 = h_2 \;\; (T_2 = T_1), \qquad \dot{S}_{\text{gen,reg}} = -\dot{m} R \ln\left(\frac{P_c}{P}\right) \ge 0",
        "physics": (
            "Throttles high tank pressure down to a constant chamber setpoint ($P_c = P_{\\text{reg}}$) for steady, "
            "predictable thrust until $P_{\\text{tank}}$ drops below $P_{\\text{reg}}$. Because throttling is irreversible, "
            "it generates entropy ($\\dot{S}_{\\text{gen,reg}} > 0$) without doing shaft work."
        ),
        "summary": "Unregulated blowdown produces a huge initial thrust spike that decays rapidly. A regulator flattens the thrust profile for easier attitude control.",
        "prompt": "Toggle **Enable Pressure Regulator** ON in Core Controls and observe the flat thrust plateau.",
        "hint": "Turn on **Enable Pressure Regulator** (e.g., 5.0 MPa setpoint) in the sidebar.",
        "check": lambda cfg: cfg["use_regulator"],
        "live_metrics": lambda res, cfg: f"Status: `{'ACTIVE' if cfg['use_regulator'] else 'BYPASSED'}`  |  Peak Thrust: `{res['F'].max():.2f} N`  |  Final Thrust: `{res['F'][-1]:.2f} N`",
    },
    {
        "title": "Step 3 of 5 — Resistojet Heater",
        "component_name": "Resistojet Heater (SSSF Electrical Heat Addition)",
        "cv_type": "Steady-State Steady-Flow (Isobaric Heating)",
        "equation": r"T_{0,\text{exit}} = T + \frac{\dot{Q}_{\text{heater}}}{\dot{m} c_p}",
        "physics": (
            "Adds electrical power ($\\dot{Q}_{\\text{heater}}$) to raise the stagnation temperature entering the nozzle. "
            "Because exhaust velocity scales with $\\sqrt{T_{0,\\text{exit}}}$, heating increases specific impulse ($I_{sp}$) "
            "and total $\\Delta v$, especially late in the burn when $\\dot{m}$ is smaller."
        ),
        "summary": "Turn a cold-gas thruster into a resistojet by heating the propellant stream right before it enters the nozzle.",
        "prompt": "Toggle **Enable Resistojet Heater** ON and set Heater Power to at least **25 W**.",
        "hint": "Enable **Resistojet Heater** in Core Controls or click the **Resistojet** preset.",
        "check": lambda cfg: cfg["use_heater"] and cfg["Q_heater"] >= 25.0,
        "live_metrics": lambda res, cfg: f"Heater Power: `{cfg['Q_heater']:.0f} W`  |  Peak Isp: `{res['isp'].max():.1f} s`  |  Total Δv: `{res['dv'][-1]:.2f} m/s`",
    },
    {
        "title": "Step 4 of 5 — Choked Vacuum C-D Nozzle",
        "component_name": "Converging-Diverging Nozzle (SSSF Supersonic Expansion)",
        "cv_type": "Steady-State Steady-Flow (Adiabatic Choked Flow)",
        "equation": r"\dot{m} = \frac{P_c A^*}{\sqrt{T_{0,\text{exit}}}}\sqrt{\frac{\gamma}{R}}\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}}, \qquad F = \dot{m} v_e + P_e A_e",
        "physics": (
            "Exhausting into vacuum ($P_a = 0$) keeps the throat choked ($M^* = 1$). Mass flow rate and thrust scale "
            "linearly with throat area $A^* \\propto (d^*)^2$. Larger throats deliver more thrust but empty the tank faster, "
            "driving rapid adiabatic cooling below the **230 K valve-freezing limit**."
        ),
        "summary": "Explore how nozzle throat sizing controls both thrust magnitude and the risk of freezing the propellant valve.",
        "prompt": "Trigger a **Valve Freeze Warning (< 230 K)** by enlarging the throat diameter or using the Freeze Risk preset.",
        "hint": "Click the **Freeze Risk** preset in the sidebar, or enable Advanced Controls and set Throat Diameter ≥ 1.8 mm.",
        "check": lambda cfg: cfg["min_T"] < 230.0 or cfg["d_throat_mm"] >= 1.8,
        "live_metrics": lambda res, cfg: f"Throat d*: `{cfg['d_throat_mm']:.1f} mm`  |  Peak Thrust: `{res['F'].max():.2f} N`  |  Valve Freeze: `{'YES (< 230 K)' if res['T'].min() < 230 else 'NO'}`",
    },
    {
        "title": "Step 5 of 5 — Coupled System Trade-Offs",
        "component_name": "Integrated Spacecraft Propulsion System",
        "cv_type": "Coupled Transient Tank + SSSF Thruster",
        "equation": r"\frac{d(\Delta v)}{dt} = \frac{F}{m_{\text{dry}} + m(t)}, \qquad I_{sp} = \frac{F}{\dot{m} g_0}",
        "physics": (
            "Mission performance depends on both **specific impulse** (favors low molar mass like Helium) and "
            "**stored propellant mass** in a fixed tank volume (favors higher molar mass like Nitrogen or Argon). "
            "Use Case A and Case B to compare configurations directly."
        ),
        "summary": "Save two different thruster configurations to compare their $\\Delta v$, thrust, and thermal curves side-by-side.",
        "prompt": "Click **Save as Case A**, change a setting (like propellant or heater power), click **Save as Case B**, then open **Comparison Mode**.",
        "hint": "Use the **💾 Save as Case A** and **💾 Save as Case B** buttons above this box.",
        "check": lambda cfg: cfg["has_case_a"] and cfg["has_case_b"],
        "live_metrics": lambda res, cfg: f"Total Δv: `{res['dv'][-1]:.2f} m/s`  |  Propellant Used: `{res['m_init'] - res['m'][-1]:.3f} kg`  |  Saved Cases: `{'A' if cfg['has_case_a'] else '—'} / {'B' if cfg['has_case_b'] else '—'}`",
    },
]